import psycopg2
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from cryptography.fernet import Fernet
import os
from db import get_db_connection
from models import (
    TestConnectionResult, DatabaseSchema, TableSchema, SchemaDifference, MigrationSuggestion
)

class DatabaseCompareService:
    def __init__(self):
        # Use a consistent encryption key for passwords (in production, use proper key management)
        encryption_key_string = os.getenv('DB_PASSWORD_ENCRYPTION_KEY', 'your-secret-key-here-change-this-in-production')
        if len(encryption_key_string) < 32:
            encryption_key_string = encryption_key_string.ljust(32, '0')[:32]
        
        # Create a deterministic Fernet key from the string
        import base64
        import hashlib
        key_bytes = hashlib.sha256(encryption_key_string.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.fernet = Fernet(fernet_key)
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a database password"""
        return self.fernet.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a database password"""
        return self.fernet.decrypt(encrypted_password.encode()).decode()
    
    def test_connection(self, host: str, port: int, database_name: str, 
                       username: str, password: str) -> TestConnectionResult:
        """Test if we can connect to the remote database"""
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database_name,
                user=username,
                password=password,
                connect_timeout=10
            )
            
            # Get server version
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            connection_time = (time.time() - start_time) * 1000
            
            conn.close()
            
            return TestConnectionResult(
                success=True,
                message="Connection successful",
                connection_time_ms=connection_time,
                server_version=version
            )
            
        except Exception as e:
            return TestConnectionResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_details=str(e)
            )
    
    def get_database_schema(self, host: str, port: int, database_name: str, 
                           username: str, password: str) -> DatabaseSchema:
        """Extract the complete schema from a database"""
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database_name,
            user=username,
            password=password
        )
        
        try:
            cursor = conn.cursor()
            tables = []
            
            # Get all tables
            cursor.execute("""
                SELECT table_name, table_schema 
                FROM information_schema.tables 
                WHERE table_type = 'BASE TABLE' 
                AND table_schema NOT IN ('information_schema', 'pg_catalog')
                ORDER BY table_schema, table_name
            """)
            
            for table_name, schema_name in cursor.fetchall():
                table_schema = self._get_table_schema(cursor, table_name, schema_name)
                tables.append(table_schema)
            
            return DatabaseSchema(tables=tables)
            
        finally:
            conn.close()
    
    def _get_table_schema(self, cursor, table_name: str, schema_name: str) -> TableSchema:
        """Get detailed schema for a single table"""
        # Get columns with proper PostgreSQL data types
        cursor.execute("""
            SELECT 
                c.column_name, 
                CASE 
                    WHEN c.data_type = 'character varying' THEN 'varchar'
                    WHEN c.data_type = 'character' THEN 'char'
                    WHEN c.data_type = 'timestamp without time zone' THEN 'timestamp'
                    WHEN c.data_type = 'timestamp with time zone' THEN 'timestamptz'
                    WHEN c.data_type = 'double precision' THEN 'double precision'
                    ELSE c.data_type
                END as data_type,
                c.is_nullable, 
                c.column_default,
                c.character_maximum_length,
                c.numeric_precision,
                c.numeric_scale
            FROM information_schema.columns c
            WHERE c.table_name = %s AND c.table_schema = %s
            ORDER BY c.ordinal_position
        """, (table_name, schema_name))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'column_name': row[0],
                'data_type': row[1],
                'is_nullable': row[2],
                'column_default': row[3],
                'character_maximum_length': row[4],
                'numeric_precision': row[5],
                'numeric_scale': row[6]
            })
        
        # Get indexes
        cursor.execute("""
            SELECT 
                i.relname as index_name,
                array_agg(a.attname ORDER BY c.ordinality) as column_names,
                idx.indisunique as is_unique,
                idx.indisprimary as is_primary
            FROM pg_index idx
            JOIN pg_class i ON i.oid = idx.indexrelid
            JOIN pg_class t ON t.oid = idx.indrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN unnest(idx.indkey) WITH ORDINALITY AS c(attnum, ordinality) ON true
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = c.attnum
            WHERE t.relname = %s AND n.nspname = %s
            GROUP BY i.relname, idx.indisunique, idx.indisprimary
            ORDER BY i.relname
        """, (table_name, schema_name))
        
        indexes = []
        for row in cursor.fetchall():
            indexes.append({
                'index_name': row[0],
                'column_names': row[1],
                'is_unique': row[2],
                'is_primary': row[3]
            })
        
        # Get constraints
        cursor.execute("""
            SELECT 
                con.conname as constraint_name,
                con.contype as constraint_type,
                array_agg(att.attname) as column_names
            FROM pg_constraint con
            JOIN pg_class rel ON rel.oid = con.conrelid
            JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
            JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = ANY(con.conkey)
            WHERE rel.relname = %s AND nsp.nspname = %s
            GROUP BY con.conname, con.contype
            ORDER BY con.conname
        """, (table_name, schema_name))
        
        constraints = []
        for row in cursor.fetchall():
            constraints.append({
                'constraint_name': row[0],
                'constraint_type': row[1],
                'column_names': row[2]
            })
        
        return TableSchema(
            table_name=table_name,
            schema_name=schema_name,
            columns=columns,
            indexes=indexes,
            constraints=constraints
        )
    
    def compare_schemas(self, local_schema: DatabaseSchema, 
                       remote_schema: DatabaseSchema) -> Tuple[List[SchemaDifference], List[MigrationSuggestion]]:
        """Compare two database schemas and generate differences and migration suggestions"""
        differences = []
        migrations = []
        
        # Create lookup dictionaries
        local_tables = {(t.schema_name, t.table_name): t for t in local_schema.tables}
        remote_tables = {(t.schema_name, t.table_name): t for t in remote_schema.tables}
        
        # Find missing tables in remote
        for table_key, local_table in local_tables.items():
            if table_key not in remote_tables:
                differences.append(SchemaDifference(
                    type="missing_table",
                    table_name=local_table.table_name,
                    description=f"Table '{local_table.table_name}' exists locally but not in remote database",
                    severity="high"
                ))
                
                # Generate CREATE TABLE migration
                create_sql = self._generate_create_table_sql(local_table)
                migrations.append(MigrationSuggestion(
                    action="CREATE TABLE",
                    sql=create_sql,
                    description=f"Create missing table '{local_table.table_name}'",
                    risk_level="medium"
                ))
        
        # Find tables that exist in both and compare columns
        for table_key, local_table in local_tables.items():
            if table_key in remote_tables:
                remote_table = remote_tables[table_key]
                table_diffs, table_migrations = self._compare_table_structures(local_table, remote_table)
                differences.extend(table_diffs)
                migrations.extend(table_migrations)
        
        return differences, migrations
    
    def _generate_create_table_sql(self, table: TableSchema) -> str:
        """Generate CREATE TABLE SQL for a table"""
        columns_sql = []
        
        for col in table.columns:
            # Get the proper PostgreSQL data type
            data_type = self._get_proper_postgresql_type(col)
            col_sql = f'"{col["column_name"]}" {data_type}'
            
            # SERIAL types are automatically NOT NULL, don't add redundant constraint
            if col["is_nullable"] == "NO" and not data_type.endswith("SERIAL"):
                col_sql += " NOT NULL"
            
            # SERIAL types automatically handle sequences, don't add DEFAULT
            if col["column_default"] and not data_type.endswith("SERIAL"):
                # Clean up the default value
                default_value = self._clean_default_value(col["column_default"])
                if default_value:
                    col_sql += f' DEFAULT {default_value}'
            
            columns_sql.append(col_sql)
        
        return f'CREATE TABLE "{table.schema_name}"."{table.table_name}" (\n  ' + ',\n  '.join(columns_sql) + '\n);'
    
    def _clean_default_value(self, default_value: str) -> str:
        """Clean up default values for PostgreSQL compatibility"""
        if not default_value:
            return ""
        
        # Skip sequence-based defaults as they should be handled by SERIAL
        if "nextval(" in str(default_value):
            return ""
        
        # Handle common PostgreSQL defaults
        str_default = str(default_value).strip()
        
        # Boolean defaults
        if str_default.lower() in ["true", "false"]:
            return str_default.lower()
        
        # String defaults (add quotes if missing)
        if str_default and not str_default.startswith("'") and not str_default.endswith("'"):
            # Check if it's a function call or special value
            if any(func in str_default.upper() for func in ["CURRENT_TIMESTAMP", "NOW()", "CURRENT_DATE", "CURRENT_TIME"]):
                return str_default
            # Check if it's a number
            try:
                float(str_default)
                return str_default
            except ValueError:
                # It's a string literal, quote it
                return f"'{str_default}'"
        
        return str_default
    
    def _get_proper_postgresql_type(self, column: Dict[str, Any]) -> str:
        """Get the proper PostgreSQL data type with length/precision only where appropriate"""
        data_type = column["data_type"]
        column_default = column.get("column_default", "")
        
        # Handle auto-increment columns by converting to SERIAL types
        if column_default and "nextval(" in str(column_default):
            if data_type == "integer":
                return "SERIAL"
            elif data_type == "bigint":
                return "BIGSERIAL"
            elif data_type == "smallint":
                return "SMALLSERIAL"
        
        # Handle character varying (varchar)
        if data_type == "character varying" and column["character_maximum_length"]:
            return f'varchar({column["character_maximum_length"]})'
        elif data_type == "character varying":
            return "varchar"
            
        # Handle character (char)
        elif data_type == "character" and column["character_maximum_length"]:
            return f'char({column["character_maximum_length"]})'
        elif data_type == "character":
            return "char"
            
        # Handle numeric types that support precision/scale
        elif data_type == "numeric" and column["numeric_precision"]:
            if column["numeric_scale"]:
                return f'numeric({column["numeric_precision"]},{column["numeric_scale"]})'
            else:
                return f'numeric({column["numeric_precision"]})'
        elif data_type == "decimal" and column["numeric_precision"]:
            if column["numeric_scale"]:
                return f'decimal({column["numeric_precision"]},{column["numeric_scale"]})'
            else:
                return f'decimal({column["numeric_precision"]})'
                
        # Handle timestamp types
        elif data_type == "timestamp without time zone":
            return "timestamp"
        elif data_type == "timestamp with time zone":
            return "timestamptz"
            
        # Handle types that should NOT have precision/length
        elif data_type in ["integer", "bigint", "smallint", "boolean", "text", "date", "time"]:
            return data_type
            
        # Default case
        else:
            return data_type
    
    def _normalize_postgresql_type(self, data_type: str) -> str:
        """Normalize data types for PostgreSQL compatibility"""
        # Remove any parentheses and content for types that don't support them
        type_mappings = {
            'integer(32)': 'integer',
            'int(32)': 'integer', 
            'bigint(64)': 'bigint',
            'smallint(16)': 'smallint',
            'boolean(1)': 'boolean',
            'text(65535)': 'text',
            'timestamp(6)': 'timestamp',
            'timestamptz(6)': 'timestamptz'
        }
        
        # Direct mapping
        if data_type in type_mappings:
            return type_mappings[data_type]
        
        # Remove invalid length specifications for integer types
        if data_type.startswith('integer('):
            return 'integer'
        if data_type.startswith('bigint('):
            return 'bigint'
        if data_type.startswith('smallint('):
            return 'smallint'
        if data_type.startswith('boolean('):
            return 'boolean'
        if data_type.startswith('text('):
            return 'text'
            
        return data_type
    
    def _compare_table_structures(self, local_table: TableSchema, 
                                 remote_table: TableSchema) -> Tuple[List[SchemaDifference], List[MigrationSuggestion]]:
        """Compare two table structures"""
        differences = []
        migrations = []
        
        # Create column lookups
        local_columns = {col["column_name"]: col for col in local_table.columns}
        remote_columns = {col["column_name"]: col for col in remote_table.columns}
        
        # Find missing columns in remote
        for col_name, local_col in local_columns.items():
            if col_name not in remote_columns:
                differences.append(SchemaDifference(
                    type="missing_column",
                    table_name=local_table.table_name,
                    column_name=col_name,
                    description=f"Column '{col_name}' exists locally but not in remote table '{local_table.table_name}'",
                    severity="high"
                ))
                
                # Generate ADD COLUMN migration
                add_col_sql = self._generate_add_column_sql(local_table, local_col)
                migrations.append(MigrationSuggestion(
                    action="ADD COLUMN",
                    sql=add_col_sql,
                    description=f"Add missing column '{col_name}' to table '{local_table.table_name}'",
                    risk_level="low"
                ))
        
        return differences, migrations
    
    def _generate_add_column_sql(self, table: TableSchema, column: Dict[str, Any]) -> str:
        """Generate ADD COLUMN SQL"""
        # Get the proper PostgreSQL data type
        data_type = self._get_proper_postgresql_type(column)
        col_sql = data_type
        
        # SERIAL types are automatically NOT NULL, don't add redundant constraint
        if column["is_nullable"] == "NO" and not data_type.endswith("SERIAL"):
            col_sql += " NOT NULL"
        
        # SERIAL types automatically handle sequences, don't add DEFAULT
        if column["column_default"] and not data_type.endswith("SERIAL"):
            # Clean up the default value
            default_value = self._clean_default_value(column["column_default"])
            if default_value:
                col_sql += f' DEFAULT {default_value}'
        
        return f'ALTER TABLE "{table.schema_name}"."{table.table_name}" ADD COLUMN "{column["column_name"]}" {col_sql};' 
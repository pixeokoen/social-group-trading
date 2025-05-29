import os
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user():
    """Create admin user if it doesn't exist"""
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    try:
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone():
            print("Admin user already exists")
            return
        
        # Create admin user
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')  # Change this in production
        hashed_password = pwd_context.hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (username, email, password, is_active)
            VALUES (%s, %s, %s, %s)
        """, ('admin', 'admin@example.com', hashed_password, True))
        
        conn.commit()
        print("Admin user created successfully")
        print(f"Username: admin")
        print(f"Password: {admin_password}")
        print("\nIMPORTANT: Please change the admin password in production!")
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_user() 
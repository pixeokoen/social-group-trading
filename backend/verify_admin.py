import os
import sys
import psycopg2
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_admin_user():
    """Verify admin user exists and can authenticate"""
    try:
        # Connect to database
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return
            
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id, username, email, password, is_active FROM users WHERE username = 'admin'")
        admin_data = cursor.fetchone()
        
        if not admin_data:
            print("❌ Admin user does not exist")
            
            # Create admin user
            response = input("Create admin user? (y/n): ")
            if response.lower() == 'y':
                password = input("Enter password for admin (default: admin123): ").strip() or 'admin123'
                hashed_password = pwd_context.hash(password)
                
                cursor.execute("""
                    INSERT INTO users (username, email, password, is_active)
                    VALUES (%s, %s, %s, %s)
                """, ('admin', 'admin@example.com', hashed_password, True))
                
                conn.commit()
                print("✅ Admin user created successfully!")
                print(f"Username: admin")
                print(f"Password: {password}")
            return
            
        print("✅ Admin user exists")
        print(f"   ID: {admin_data[0]}")
        print(f"   Username: {admin_data[1]}")
        print(f"   Email: {admin_data[2]}")
        print(f"   Active: {admin_data[4]}")
        
        # Test password
        test_password = input("\nEnter password to test (or press Enter to skip): ").strip()
        if test_password:
            if pwd_context.verify(test_password, admin_data[3]):
                print("✅ Password is correct!")
            else:
                print("❌ Password is incorrect!")
                
                # Offer to reset password
                response = input("Reset admin password? (y/n): ")
                if response.lower() == 'y':
                    new_password = input("Enter new password: ").strip()
                    if new_password:
                        hashed_password = pwd_context.hash(new_password)
                        cursor.execute(
                            "UPDATE users SET password = %s WHERE username = 'admin'",
                            (hashed_password,)
                        )
                        conn.commit()
                        print("✅ Password updated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_admin_user() 
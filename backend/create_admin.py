import requests
import sys

# Get the backend URL from command line or use default
if len(sys.argv) > 1:
    backend_url = sys.argv[1]
else:
    backend_url = input("Enter your backend URL (e.g., https://social-group-trading-backend.onrender.com): ")

# Create admin user
data = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123"
}

try:
    response = requests.post(f"{backend_url}/api/auth/register", json=data)
    
    if response.status_code == 200:
        print("✅ Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.json())
        
except Exception as e:
    print(f"❌ Error connecting to backend: {e}")
    print("Make sure your backend URL is correct and the service is running.") 
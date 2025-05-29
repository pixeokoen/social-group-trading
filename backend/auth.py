from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv

from models import User, TokenData
from db import get_db_connection

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, created_at, is_active FROM users WHERE username = %s",
            (token_data.username,)
        )
        user_data = cursor.fetchone()
        
        if user_data is None:
            raise credentials_exception
        
        user = User(
            id=user_data[0],
            username=user_data[1],
            email=user_data[2],
            created_at=user_data[3],
            is_active=user_data[4]
        )
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        return user
    finally:
        conn.close()

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, password, created_at, is_active FROM users WHERE username = %s",
            (username,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
        
        if not verify_password(password, user_data[3]):
            return None
        
        return User(
            id=user_data[0],
            username=user_data[1],
            email=user_data[2],
            created_at=user_data[4],
            is_active=user_data[5]
        )
    finally:
        conn.close()

def create_user(username: str, email: str, password: str) -> Optional[User]:
    """Create a new user"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed_password = get_password_hash(password)
        
        cursor.execute(
            """
            INSERT INTO users (username, email, password) 
            VALUES (%s, %s, %s) 
            RETURNING id, username, email, created_at, is_active
            """,
            (username, email, hashed_password)
        )
        
        user_data = cursor.fetchone()
        conn.commit()
        
        if user_data:
            return User(
                id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                created_at=user_data[3],
                is_active=user_data[4]
            )
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        conn.close()

# Additional auth endpoints for main.py
async def register(username: str, email: str, password: str):
    """Register a new user"""
    # Check if user exists
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )
    finally:
        conn.close()
    
    # Create new user
    user = create_user(username, email, password)
    if not user:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"} 
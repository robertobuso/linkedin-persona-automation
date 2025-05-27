"""
Security utilities for LinkedIn Presence Automation Application.

Provides JWT token management, password hashing, and authentication
utilities with FastAPI integration.
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database.connection import get_db_session
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.utils.exceptions import InvalidCredentialsError

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in token
        expires_delta: Token expiration time
        
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type (access or refresh)
        
    Returns:
        Decoded token payload
        
    Raises:
        InvalidCredentialsError: If token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise InvalidCredentialsError("Invalid token type")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise InvalidCredentialsError("Token has expired")
        
        return payload
        
    except JWTError:
        raise InvalidCredentialsError("Could not validate credentials")


def verify_refresh_token(token: str) -> dict:
    """
    Verify refresh token.
    
    Args:
        token: Refresh token string
        
    Returns:
        Decoded token payload
    """
    return verify_token(token, "refresh")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Get current user from JWT token.
    
    Args:
        token: JWT token from request
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidCredentialsError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def create_password_reset_token(email: str) -> str:
    """
    Create password reset token.
    
    Args:
        email: User email
        
    Returns:
        Password reset token
    """
    delta = timedelta(hours=1)  # 1 hour expiration
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    
    encoded_jwt = jwt.encode(
        {"exp": exp, "email": email, "type": "password_reset"},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token.
    
    Args:
        token: Password reset token
        
    Returns:
        Email if token is valid, None otherwise
    """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if decoded_token.get("type") != "password_reset":
            return None
        
        return decoded_token.get("email")
    except JWTError:
        return None


def generate_api_key() -> str:
    """
    Generate API key for external integrations.
    
    Returns:
        Generated API key
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """
    Verify API key against stored hash.
    
    Args:
        api_key: API key to verify
        stored_hash: Stored hash of the API key
        
    Returns:
        True if API key is valid
    """
    return pwd_context.verify(api_key, stored_hash)


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage.
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    return pwd_context.hash(api_key)
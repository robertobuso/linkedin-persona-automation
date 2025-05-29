"""
Security utilities for LinkedIn Presence Automation Application.

Provides JWT token management, password hashing, and authentication
utilities with FastAPI integration.
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional # Removed Dict as it's covered by Any or specific types
from uuid import UUID # Import UUID
import logging # For logging potential errors

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.database.connection import get_db_session # Your @asynccontextmanager dependency
from app.repositories.user_repository import UserRepository
from app.models.user import User # Your SQLAlchemy User model
from app.utils.exceptions import InvalidCredentialsError # Your custom exception

logger = logging.getLogger(__name__)

# Security configuration
# It's good practice to load these from a settings/config object rather than directly from os.getenv here
# For example, from app.core.config import settings
# SECRET_KEY = settings.SECRET_KEY
# ALGORITHM = settings.ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
# This assumes you have a global 'settings' object from app.core.config
# If not, os.getenv is fine but less organized. For this revision, I'll keep os.getenv
# as per your original to minimize unexpected changes.

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-in-env-file")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(24 * 60))) # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", # Ensure this matches your actual login route
    scheme_name="JWT"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
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
    """Create JWT refresh token."""
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
    Raises InvalidCredentialsError if token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            raise InvalidCredentialsError("Invalid token type")
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise InvalidCredentialsError("Token missing expiration")
        if datetime.utcnow() > datetime.fromtimestamp(exp):
            raise InvalidCredentialsError("Token has expired")
        
        return payload
        
    except JWTError as e: # Catches various JWT errors like ExpiredSignatureError, InvalidTokenError
        raise InvalidCredentialsError(f"Could not validate credentials: {str(e)}")
    except Exception as e: # Catch any other unexpected error during decoding
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        raise InvalidCredentialsError(f"Token verification failed unexpectedly: {str(e)}")


def verify_refresh_token(token: str) -> dict:
    """Verify refresh token."""
    return verify_token(token, "refresh")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session_cm: AsyncSession = Depends(get_db_session) # Renamed for clarity
) -> User:
    """
    Get current user from JWT access token.
    This is a dependency used by other dependencies or routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token, "access") # verify_token should raise InvalidCredentialsError
        user_id_str: Optional[str] = payload.get("sub")

        if user_id_str is None:
            # This case should ideally be caught by verify_token if 'sub' is mandatory for valid tokens
            logger.warning("Token payload missing 'sub' (user identifier).")
            raise InvalidCredentialsError("Token payload missing user identifier")
        
        try:
            user_id = UUID(user_id_str) # Attempt to convert to UUID
        except ValueError:
            logger.warning(f"Invalid UUID format for user_id in token: {user_id_str}")
            raise InvalidCredentialsError("Invalid user identifier format in token")

    except InvalidCredentialsError as e: # Catch specific error from verify_token
        raise credentials_exception from e # Propagate with FastAPI's HTTPException
    
    # The database interaction MUST happen within the async with block
    async with db_session_cm as actual_session: # Use async with to get the actual session
        user_repo = UserRepository(actual_session) # Pass the actual session
        user = await user_repo.get_by_id(user_id) # Pass UUID object
    
    if user is None:
        logger.warning(f"User with ID {user_id} not found in database (from token).")
        raise credentials_exception # User from token not found in DB
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user) # This now uses the fixed get_current_user
) -> User:
    """
    Get current active user.
    Ensures the user obtained from get_current_user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 might be more appropriate than 400
            detail="Inactive user account"
        )
    return current_user


def create_password_reset_token(email: str) -> str:
    """Create password reset token."""
    delta = timedelta(hours=1)
    now = datetime.utcnow()
    expires = now + delta
    
    encoded_jwt = jwt.encode(
        {"exp": expires, "email": email, "type": "password_reset"}, # exp should be timestamp
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token."""
    try:
        payload = verify_token(token, "password_reset") # Use verify_token for consistency
        return payload.get("email")
    except InvalidCredentialsError:
        return None


def generate_api_key() -> str:
    """Generate API key for external integrations."""
    import secrets
    return secrets.token_urlsafe(32)


def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Verify API key against stored hash."""
    return pwd_context.verify(api_key, stored_hash)


def hash_api_key(api_key: str) -> str:
    """Hash API key for storage."""
    return pwd_context.hash(api_key)
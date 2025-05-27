"""
Authentication endpoints for LinkedIn Presence Automation Application.

Provides user registration, login, token refresh, and profile management
endpoints with JWT-based authentication.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    get_current_user,
    get_current_active_user,
    verify_refresh_token
)
from app.database.connection import get_db_session
from app.repositories.user_repository import UserRepository
from app.schemas.api_schemas import (
    UserCreate,
    UserResponse,
    Token,
    TokenRefresh,
    UserUpdate,
    PasswordChange
)
from app.utils.exceptions import InvalidCredentialsError, ValidationError
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user information and access token
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    user_repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user
    try:
        user = await user_repo.create_user(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=24)
        )
        
        return UserResponse(
            user=user.to_dict(),
            access_token=access_token,
            token_type="bearer"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    User login with email and password.
    
    Args:
        form_data: Login form data (username=email, password)
        db: Database session
        
    Returns:
        Access token and user information
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user_repo = UserRepository(db)
    
    # Get user by email
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise InvalidCredentialsError("Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    await user_repo.update_last_login(user.id)
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(hours=24)
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=30)
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user.to_dict()
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Refresh access token using refresh token.
    
    Args:
        token_data: Refresh token data
        db: Database session
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = verify_refresh_token(token_data.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise InvalidCredentialsError("Invalid refresh token")
        
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(user_id)
        
        if user is None or not user.is_active:
            raise InvalidCredentialsError("User not found or inactive")
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(hours=24)
        )
        
        return Token(
            access_token=access_token,
            refresh_token=token_data.refresh_token,
            token_type="bearer",
            user=user.to_dict()
        )
        
    except Exception as e:
        raise InvalidCredentialsError("Invalid refresh token")


@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return current_user.to_dict()


@router.put("/me", response_model=dict)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Update current user information.
    
    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    user_repo = UserRepository(db)
    
    update_data = {}
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.linkedin_profile_url is not None:
        update_data["linkedin_profile_url"] = user_update.linkedin_profile_url
    
    if update_data:
        updated_user = await user_repo.update(current_user.id, **update_data)
        if updated_user:
            return updated_user.to_dict()
    
    return current_user.to_dict()


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Change user password.
    
    Args:
        password_data: Password change data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Hash new password
    new_password_hash = get_password_hash(password_data.new_password)
    
    # Update password
    user_repo = UserRepository(db)
    await user_repo.update_password(current_user.id, new_password_hash)
    
    return {"message": "Password updated successfully"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout user (client should discard tokens).
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    # In a production system, you might want to blacklist the token
    return {"message": "Successfully logged out"}


@router.put("/preferences")
async def update_preferences(
    preferences: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Update user preferences.
    
    Args:
        preferences: User preferences data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated preferences
    """
    user_repo = UserRepository(db)
    
    try:
        updated_user = await user_repo.update_preferences(current_user.id, preferences)
        if updated_user:
            return updated_user.preferences
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.put("/tone-profile")
async def update_tone_profile(
    tone_profile: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Update user tone profile.
    
    Args:
        tone_profile: Tone profile data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated tone profile
    """
    user_repo = UserRepository(db)
    
    try:
        updated_user = await user_repo.update_tone_profile(current_user.id, tone_profile)
        if updated_user:
            return updated_user.tone_profile
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tone profile: {str(e)}"
        )
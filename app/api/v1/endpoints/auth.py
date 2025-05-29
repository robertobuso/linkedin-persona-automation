"""
Authentication endpoints for LinkedIn Presence Automation Application.

Provides user registration, login, token refresh, and profile management
endpoints with JWT-based authentication.
"""

from datetime import timedelta
from typing import Any, Optional # Added Optional for clarity in some Pydantic models
from uuid import UUID # Import UUID if your user IDs are UUIDs

from fastapi import APIRouter, Depends, HTTPException, status, Body # Added Body for PasswordChange
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging # For logging errors

# Assuming your logger is configured
logger = logging.getLogger(__name__)

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    # get_current_user, # This will be effectively replaced or its logic moved
    # get_current_active_user, # This will be effectively replaced
    verify_refresh_token, # Assuming this raises InvalidCredentialsError on failure
    verify_token, # For get_current_active_user
    oauth2_scheme # For get_current_active_user
)
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.user_repository import UserRepository
from app.schemas.api_schemas import (
    UserCreate,
    Token,
    TokenRefresh,
    UserUpdate,
    PasswordChange,
    UserProfileData,
    # MessageResponse # If you want a structured message for logout/password change
)

from app.utils.exceptions import InvalidCredentialsError, ValidationError # Assuming ValidationError is defined
from app.models.user import User

router = APIRouter()

# --- Corrected get_current_active_user Dependency ---
# This dependency will now handle getting the session correctly
async def get_current_active_user_dependency(
    token: str = Depends(oauth2_scheme),
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token, "access") # verify_token should raise error or return payload
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        user_id = UUID(user_id_str) # Convert to UUID if your IDs are UUIDs

    except InvalidCredentialsError: # Catch specific error from verify_token
        raise credentials_exception
    except ValueError: # Catch UUID conversion error
        raise credentials_exception


    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user
# --- End Corrected Dependency ---


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED) # Changed response to Token
async def register(
    user_data: UserCreate,
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> Token:
    """Register a new user."""
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
        hashed_password = get_password_hash(user_data.password)
        
        try:
            # User creation must also be within the session context
            user = await user_repo.create_user(
                email=user_data.email,
                password_hash=hashed_password,
                full_name=user_data.full_name
                # Pass other default fields if your create_user expects them (like preferences, tone_profile)
            )
            
            access_token = create_access_token(data={"sub": str(user.id)})
            refresh_token_val = create_refresh_token(data={"sub": str(user.id)})
            
            # Assuming your Token Pydantic model can take a User model and convert it
            # Or that user.to_dict() is compatible with what Token expects for its 'user' field
            return Token(
                access_token=access_token,
                refresh_token=refresh_token_val,
                token_type="bearer",
                user=user.to_dict() if hasattr(user, 'to_dict') else user # Adjust as needed
            )
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> Token:
    """User login with email and password."""
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        
        user = await user_repo.get_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user.password_hash):
            raise InvalidCredentialsError("Incorrect email or password") # Your custom error
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        await user_repo.update_last_login(user.id) # This needs to be within the session
        
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token_val = create_refresh_token(data={"sub": str(user.id)})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token_val,
            token_type="bearer",
            user=user.to_dict() if hasattr(user, 'to_dict') else user
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> Token:
    """Refresh access token using refresh token."""
    try:
        payload = verify_refresh_token(token_data.refresh_token)
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            raise InvalidCredentialsError("Invalid refresh token payload")
        
        user_id = UUID(user_id_str) # Convert to UUID if your IDs are UUIDs

        async with db_session_context_manager as actual_session:
            user_repo = UserRepository(actual_session)
            user = await user_repo.get_by_id(user_id)
            
            if user is None or not user.is_active:
                raise InvalidCredentialsError("User not found or inactive for this refresh token")
            
            new_access_token = create_access_token(data={"sub": str(user.id)})
            
            return Token(
                access_token=new_access_token,
                refresh_token=token_data.refresh_token,
                token_type="bearer",
                user=user.to_dict() if hasattr(user, 'to_dict') else user
            )
            
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except ValueError: # For UUID conversion error
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user identifier in token")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh token due to an internal error"
        )


@router.get("/me", response_model=UserProfileData) # Use the new schema
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user_dependency)
) -> UserProfileData: # Return type matches response_model
    """Get current user information."""
    # This will now work because UserProfileData inherits from_attributes=True
    # from BaseResponseModel and its fields directly map to the User ORM object's attributes.
    return UserProfileData.model_validate(current_user)

@router.put("/me", response_model=UserProfileData) # Also use it here
async def update_current_user(
    user_update: UserUpdate, # UserUpdate schema is fine for input
    current_user: User = Depends(get_current_active_user_dependency),
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> UserProfileData: # Return the updated profile using the correct schema
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        update_data = user_update.model_dump(exclude_unset=True)

        if not update_data:
             return UserProfileData.model_validate(current_user) # Return current state

        updated_user_obj = await user_repo.update(id=current_user.id, **update_data)

        if not updated_user_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update attempt")

        return UserProfileData.model_validate(updated_user_obj)


@router.post("/change-password", response_model=dict) # Or a MessageResponse schema
async def change_password(
    password_data: PasswordChange = Body(...), # Use Body for complex request bodies if needed
    current_user: User = Depends(get_current_active_user_dependency), # Use corrected dependency
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """Change user password."""
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)

        if not verify_password(password_data.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )
        
        new_password_hash = get_password_hash(password_data.new_password)
        
        await user_repo.update_password(current_user.id, new_password_hash)
    
    return {"message": "Password updated successfully"}


@router.post("/logout", response_model=dict) # Or a MessageResponse schema
async def logout(
    # If you implement server-side token blacklisting, you'd need the token and auth_service
    # current_user: User = Depends(get_current_active_user_dependency) # Optional, if you want to log the logout
) -> dict:
    """Logout user (client should discard tokens)."""
    # Server-side blacklisting would happen here if implemented (e.g., using AuthService)
    # For a simple client-side logout, this endpoint might just return success.
    return {"message": "Successfully logged out. Please clear tokens on client-side."}


@router.put("/preferences", response_model=dict) # Or a more specific preferences schema
async def update_preferences(
    preferences: dict = Body(...),
    current_user: User = Depends(get_current_active_user_dependency), # Use corrected dependency
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """Update user preferences."""
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        
        try:
            updated_user = await user_repo.update_preferences(current_user.id, preferences)
            if updated_user and hasattr(updated_user, 'preferences'):
                return updated_user.preferences
            else: # Should not happen if user exists
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update preferences: {str(e)}"
            )


@router.put("/tone-profile", response_model=dict) # Or a more specific tone profile schema
async def update_tone_profile(
    tone_profile: dict = Body(...),
    current_user: User = Depends(get_current_active_user_dependency), # Use corrected dependency
    db_session_context_manager: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """Update user tone profile."""
    async with db_session_context_manager as actual_session:
        user_repo = UserRepository(actual_session)
        
        try:
            updated_user = await user_repo.update_tone_profile(current_user.id, tone_profile)
            if updated_user and hasattr(updated_user, 'tone_profile'):
                return updated_user.tone_profile
            else: # Should not happen if user exists
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        except Exception as e:
            logger.error(f"Failed to update tone profile: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update tone profile: {str(e)}"
            )
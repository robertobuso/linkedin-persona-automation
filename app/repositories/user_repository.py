"""
User repository for LinkedIn Presence Automation Application.

Provides specialized database operations for User model including authentication,
profile management, and user-specific queries.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository, NotFoundError, DuplicateError


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with specialized user management operations.
    
    Extends BaseRepository to provide user-specific database operations
    including authentication, profile updates, and user preferences management.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize UserRepository with database session."""
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_user(
        self, 
        email: str, 
        password_hash: str, 
        full_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        tone_profile: Optional[Dict[str, Any]] = None
    ) -> User:
        """
        Create a new user with validation.
        
        Args:
            email: User email address
            password_hash: Hashed password
            full_name: Optional full name
            preferences: Optional user preferences
            tone_profile: Optional AI tone profile
            
        Returns:
            Created User instance
            
        Raises:
            DuplicateError: If email already exists
        """
        # Check if email already exists
        existing_user = await self.get_by_email(email)
        if existing_user:
            raise DuplicateError(f"User with email '{email}' already exists")
        
        # Set default preferences and tone profile if not provided
        if preferences is None:
            preferences = {
                "posting_frequency": "daily",
                "preferred_posting_times": ["09:00", "13:00", "17:00"],
                "content_categories": ["technology", "business", "leadership"],
                "auto_posting_enabled": False,
                "engagement_auto_reply": False,
                "notification_settings": {
                    "email_notifications": True,
                    "draft_ready_notifications": True,
                    "engagement_notifications": True
                }
            }
        
        if tone_profile is None:
            tone_profile = {
                "writing_style": "professional",
                "tone": "informative",
                "personality_traits": ["analytical", "thoughtful"],
                "industry_focus": [],
                "expertise_areas": [],
                "communication_preferences": {
                    "use_emojis": False,
                    "include_hashtags": True,
                    "max_hashtags": 3,
                    "call_to_action_style": "subtle"
                }
            }
        
        return await self.create(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            preferences=preferences,
            tone_profile=tone_profile
        )
    
    async def update_password(self, user_id: UUID, new_password_hash: str) -> Optional[User]:
        """
        Update user password.
        
        Args:
            user_id: User ID
            new_password_hash: New hashed password
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(user_id, password_hash=new_password_hash)
    
    async def update_tone_profile(self, user_id: UUID, tone_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user's AI tone profile.
        
        Args:
            user_id: User ID
            tone_data: Tone profile updates
            
        Returns:
            Updated User instance or None if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Merge with existing tone profile
        current_tone = user.tone_profile or {}
        updated_tone = {**current_tone, **tone_data}
        
        return await self.update(user_id, tone_profile=updated_tone)
    
    async def update_preferences(self, user_id: UUID, preferences_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences_data: Preferences updates
            
        Returns:
            Updated User instance or None if not found
        """
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Merge with existing preferences
        current_prefs = user.preferences or {}
        updated_prefs = {**current_prefs, **preferences_data}
        
        return await self.update(user_id, preferences=updated_prefs)
    
    async def update_linkedin_tokens(
        self, 
        user_id: UUID, 
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Optional[User]:
        """
        Update LinkedIn OAuth tokens for user.
        
        Args:
            user_id: User ID
            access_token: LinkedIn access token
            refresh_token: LinkedIn refresh token
            expires_at: Token expiration time
            
        Returns:
            Updated User instance or None if not found
        """
        update_data = {
            "linkedin_access_token": access_token,
            "linkedin_token_expires_at": expires_at
        }
        
        if refresh_token:
            update_data["linkedin_refresh_token"] = refresh_token
        
        return await self.update(user_id, **update_data)
    
    async def clear_linkedin_tokens(self, user_id: UUID) -> Optional[User]:
        """
        Clear LinkedIn OAuth tokens for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(
            user_id,
            linkedin_access_token=None,
            linkedin_refresh_token=None,
            linkedin_token_expires_at=None
        )
    
    async def update_last_login(self, user_id: UUID) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(user_id, last_login_at=datetime.utcnow())
    
    async def activate_user(self, user_id: UUID) -> Optional[User]:
        """
        Activate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(user_id, is_active=True)
    
    async def deactivate_user(self, user_id: UUID) -> Optional[User]:
        """
        Deactivate user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(user_id, is_active=False)
    
    async def verify_user(self, user_id: UUID) -> Optional[User]:
        """
        Mark user as verified.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated User instance or None if not found
        """
        return await self.update(user_id, is_verified=True)
    
    async def get_active_users(self, limit: Optional[int] = None, offset: int = 0) -> List[User]:
        """
        Get all active users.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of active User instances
        """
        stmt = select(User).where(User.is_active == True).offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_users_with_linkedin_tokens(self) -> List[User]:
        """
        Get users who have valid LinkedIn tokens.
        
        Returns:
            List of User instances with LinkedIn integration
        """
        stmt = select(User).where(
            and_(
                User.is_active == True,
                User.linkedin_access_token.isnot(None),
                or_(
                    User.linkedin_token_expires_at.is_(None),
                    User.linkedin_token_expires_at > datetime.utcnow()
                )
            )
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_users_with_expired_tokens(self) -> List[User]:
        """
        Get users whose LinkedIn tokens have expired.
        
        Returns:
            List of User instances with expired tokens
        """
        stmt = select(User).where(
            and_(
                User.is_active == True,
                User.linkedin_access_token.isnot(None),
                User.linkedin_token_expires_at.isnot(None),
                User.linkedin_token_expires_at <= datetime.utcnow()
            )
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def search_users(
        self, 
        query: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[User]:
        """
        Search users by email or name.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching User instances
        """
        search_term = f"%{query.lower()}%"
        stmt = (
            select(User)
            .where(
                or_(
                    User.email.ilike(search_term),
                    User.full_name.ilike(search_term)
                )
            )
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user statistics including content sources, drafts, and engagement.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with user statistics
        """
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        # This would typically involve joins with other tables
        # For now, return basic user info
        return {
            "user_id": str(user_id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "has_linkedin_integration": user.has_valid_linkedin_token(),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "posting_frequency": user.preferences.get("posting_frequency") if user.preferences else None,
            "auto_posting_enabled": user.is_auto_posting_enabled(),
        }
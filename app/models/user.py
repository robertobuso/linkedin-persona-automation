"""
User model for LinkedIn Presence Automation Application.

Defines the User entity with authentication, preferences, and tone profile management.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class User(Base):
    """
    User model representing application users with LinkedIn automation preferences.
    
    Stores user authentication data, content preferences, tone profiles,
    and LinkedIn integration settings.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique user identifier"
    )
    
    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User email address for authentication"
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        doc="Hashed password for authentication"
    )
    
    # Profile information
    full_name = Column(
        String(255),
        nullable=True,
        doc="User's full name"
    )
    
    linkedin_profile_url = Column(
        String(500),
        nullable=True,
        doc="LinkedIn profile URL"
    )
    
    # Account status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the user account is active"
    )
    
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user email is verified"
    )
    
    # LinkedIn integration
    linkedin_access_token = Column(
        Text,
        nullable=True,
        doc="Encrypted LinkedIn OAuth access token"
    )
    
    linkedin_refresh_token = Column(
        Text,
        nullable=True,
        doc="Encrypted LinkedIn OAuth refresh token"
    )
    
    linkedin_token_expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="LinkedIn access token expiration time"
    )
    
    # User preferences stored as JSONB
    preferences = Column(
        JSONB,
        nullable=False,
        default=lambda: {
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
        },
        doc="User preferences for content and posting behavior"
    )
    
    # Tone profile for content generation
    tone_profile = Column(
        JSONB,
        nullable=False,
        default=lambda: {
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
        },
        doc="AI tone profile for content generation"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Account creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last account update timestamp"
    )
    
    last_login_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful login timestamp"
    )
    
    # Relationships
    content_sources = relationship(
        "ContentSource",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's configured content sources"
    )
    
    post_drafts = relationship(
        "PostDraft",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's post drafts"
    )
    
    engagement_opportunities = relationship(
        "EngagementOpportunity",
        back_populates="user",
        cascade="all, delete-orphan",
        doc="User's engagement opportunities"
    )
    
    def __repr__(self) -> str:
        """String representation of User instance."""
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert User instance to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields like tokens
            
        Returns:
            Dict containing user data
        """
        data = {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "linkedin_profile_url": self.linkedin_profile_url,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "preferences": self.preferences,
            "tone_profile": self.tone_profile,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
        
        if include_sensitive:
            data.update({
                "linkedin_access_token": self.linkedin_access_token,
                "linkedin_refresh_token": self.linkedin_refresh_token,
                "linkedin_token_expires_at": (
                    self.linkedin_token_expires_at.isoformat() 
                    if self.linkedin_token_expires_at else None
                ),
            })
        
        return data
    
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """
        Update user preferences with validation.
        
        Args:
            new_preferences: Dictionary of preference updates
        """
        if self.preferences is None:
            self.preferences = {}
        
        # Deep merge preferences
        current_prefs = dict(self.preferences)
        current_prefs.update(new_preferences)
        self.preferences = current_prefs
    
    def update_tone_profile(self, tone_updates: Dict[str, Any]) -> None:
        """
        Update user tone profile with validation.
        
        Args:
            tone_updates: Dictionary of tone profile updates
        """
        if self.tone_profile is None:
            self.tone_profile = {}
        
        # Deep merge tone profile
        current_tone = dict(self.tone_profile)
        current_tone.update(tone_updates)
        self.tone_profile = current_tone
    
    def has_valid_linkedin_token(self) -> bool:
        """
        Check if user has a valid LinkedIn access token.
        
        Returns:
            True if token exists and is not expired
        """
        if not self.linkedin_access_token:
            return False
        
        if not self.linkedin_token_expires_at:
            return False
        
        return datetime.utcnow() < self.linkedin_token_expires_at
    
    def get_posting_schedule(self) -> List[str]:
        """
        Get user's preferred posting times.
        
        Returns:
            List of preferred posting times in HH:MM format
        """
        if not self.preferences:
            return ["09:00", "13:00", "17:00"]
        
        return self.preferences.get("preferred_posting_times", ["09:00", "13:00", "17:00"])
    
    def is_auto_posting_enabled(self) -> bool:
        """
        Check if auto-posting is enabled for this user.
        
        Returns:
            True if auto-posting is enabled
        """
        if not self.preferences:
            return False
        
        return self.preferences.get("auto_posting_enabled", False)
"""
Updated User model with content preferences support.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class User(Base):
    """
    User model with enhanced content preferences.
    """
    
    __tablename__ = "users"
    
    # Existing fields...
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    linkedin_profile_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # LinkedIn integration
    linkedin_access_token = Column(Text, nullable=True)
    linkedin_refresh_token = Column(Text, nullable=True)
    linkedin_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Enhanced content preferences
    content_preferences = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            # Professional context
            "job_role": "",
            "industry": "",
            "experience_level": "intermediate",
            "company_size": "",
            
            # Content interests with weights
            "primary_interests": [],
            "secondary_interests": [],
            "topics_to_avoid": [],
            
            # Custom AI instructions
            "custom_prompt": "",
            "content_style_preferences": "balanced",  # concise, balanced, detailed
            
            # Content filters
            "content_types": ["articles", "news", "analysis"],
            "min_relevance_score": 0.7,
            "max_articles_per_day": 15,
            "preferred_content_length": "medium",  # short, medium, long
            "min_word_count": 200,
            "max_word_count": 5000,
            
            # Advanced preferences
            "companies_to_follow": [],
            "authors_to_follow": [],
            "sources_to_prioritize": [],
            "language_preference": "en",
            
            # Timing preferences
            "content_freshness_hours": 72,
            "check_frequency": "daily",
            
            # LinkedIn-specific
            "linkedin_post_style": "professional",
            "include_industry_hashtags": True,
            "max_hashtags": 5,
            
            # Learning preferences
            "learn_from_interactions": True,
            "feedback_weight": 0.3,
            
            # Version tracking
            "preferences_version": 1,
            "last_updated": datetime.utcnow().isoformat()
        },
        doc="User content preferences and AI instructions"
    )
    
    # Legacy preferences (keeping for backward compatibility)
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
        doc="Legacy user preferences for posting behavior"
    )
    
    # AI tone profile
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    content_sources = relationship("ContentSource", back_populates="user", cascade="all, delete-orphan")
    post_drafts = relationship("PostDraft", back_populates="user", cascade="all, delete-orphan")
    engagement_opportunities = relationship("EngagementOpportunity", back_populates="user", cascade="all, delete-orphan")
    content_selections = relationship("ContentSelection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
    
    def get_content_preferences(self) -> Dict[str, Any]:
        """Get content preferences with defaults."""
        defaults = {
            "job_role": "",
            "industry": "",
            "primary_interests": [],
            "custom_prompt": "",
            "min_relevance_score": 0.7,
            "max_articles_per_day": 15,
            "content_types": ["articles", "news"],
            "learn_from_interactions": True
        }
        
        prefs = self.content_preferences or {}
        return {**defaults, **prefs}
    
    def update_content_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update content preferences with validation and versioning."""
        current_prefs = self.content_preferences or {}
        
        # Update preferences
        updated_prefs = {**current_prefs, **new_preferences}
        updated_prefs["last_updated"] = datetime.utcnow().isoformat()
        updated_prefs["preferences_version"] = current_prefs.get("preferences_version", 1) + 1
        
        self.content_preferences = updated_prefs
    
    def get_interests_for_llm(self) -> str:
        """Format interests for LLM consumption."""
        prefs = self.get_content_preferences()
        
        interests = []
        
        # Primary interests
        primary = prefs.get("primary_interests", [])
        if primary:
            interests.append(f"Primary interests: {', '.join(primary)}")
        
        # Secondary interests
        secondary = prefs.get("secondary_interests", [])
        if secondary:
            interests.append(f"Secondary interests: {', '.join(secondary)}")
        
        # Job context
        if prefs.get("job_role"):
            interests.append(f"Job role: {prefs['job_role']}")
        
        if prefs.get("industry"):
            interests.append(f"Industry: {prefs['industry']}")
        
        # Custom prompt
        if prefs.get("custom_prompt"):
            interests.append(f"Custom instructions: {prefs['custom_prompt']}")
        
        return ". ".join(interests) if interests else "General professional content"
    
    def should_process_content(self, content_metadata: Dict[str, Any]) -> bool:
        """Quick check if content might be relevant to user."""
        prefs = self.get_content_preferences()
        
        # Check topics to avoid
        topics_to_avoid = prefs.get("topics_to_avoid", [])
        if topics_to_avoid:
            content_text = (content_metadata.get("title", "") + " " + 
                          content_metadata.get("description", "")).lower()
            
            for avoid_topic in topics_to_avoid:
                if avoid_topic.lower() in content_text:
                    return False
        
        # Check minimum word count
        word_count = content_metadata.get("word_count", 0)
        if word_count < prefs.get("min_word_count", 200):
            return False
        
        # Check maximum word count
        if word_count > prefs.get("max_word_count", 5000):
            return False
        
        # Check content age
        content_age_hours = content_metadata.get("age_hours", 0)
        max_age = prefs.get("content_freshness_hours", 72)
        if content_age_hours > max_age:
            return False
        
        return True

    # Legacy utility functions
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
    
class ContentSelection(Base):
    """
    Track content selection decisions for analytics and learning.
    """
    
    __tablename__ = "content_selections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("content_sources.id", ondelete="CASCADE"), nullable=False)
    
    # Selection details
    selection_date = Column(DateTime(timezone=True), nullable=False, index=True)
    articles_considered = Column(Integer, nullable=False)
    articles_selected = Column(Integer, nullable=False)
    
    # LLM details
    llm_model_used = Column(String(100), nullable=True)
    selection_criteria = Column(JSONB, nullable=False)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Results
    selected_article_ids = Column(JSONB, nullable=False, default=list)
    selection_scores = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="content_selections")
    source = relationship("ContentSource")
    
    def __repr__(self) -> str:
        return f"<ContentSelection(user_id={self.user_id}, selected={self.articles_selected}/{self.articles_considered})>"
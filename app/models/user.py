"""
Updated User model with enhanced content preferences support and relationships.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Float, desc
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base
from app.models.user_content_preferences import UserContentPreferences


class User(Base):
    """
    User model with enhanced content preferences and relationship to separate preferences table.
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
    
    # Legacy content preferences (keeping for backward compatibility)
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
            "content_style_preferences": "balanced",
            
            # Content filters
            "content_types": ["articles", "news", "analysis"],
            "min_relevance_score": 0.7,
            "max_articles_per_day": 15,
            "preferred_content_length": "medium",
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
        doc="Legacy user content preferences stored as JSONB"
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
    
    # NEW: Relationship to separate preferences table
    content_preferences_records = relationship(
        "UserContentPreferences", 
        back_populates="user", 
        cascade="all, delete-orphan",
        order_by=lambda: desc(UserContentPreferences.created_at)
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
    
    def get_active_content_preferences(self) -> Optional['UserContentPreferences']:
        """
        Return the most recent active content preferences if they are already loaded.

        NOTE: This does NOT trigger a database query. It assumes the relationship
        `content_preferences_records` is already eagerly loaded or set manually.
        """
        if hasattr(self, "content_preferences_records") and self.content_preferences_records:
            for prefs in self.content_preferences_records:
                if prefs.is_active:
                    return prefs
        return None
    
    def get_content_preferences_dict(self) -> Dict[str, Any]:
        """
        Get content preferences as dictionary, prioritizing separate table over JSONB.
        """
        active_prefs = self.get_active_content_preferences()
        if active_prefs:
            return active_prefs.to_dict()
        
        # Fallback to JSONB field with defaults
        defaults = {
            "job_role": "",
            "industry": "",
            "primary_interests": [],
            "secondary_interests": [],
            "topics_to_avoid": [],
            "custom_prompt": "",
            "min_relevance_score": 0.7,
            "max_articles_per_day": 15,
            "content_types": ["articles", "news"],
            "learn_from_interactions": True,
            "min_word_count": 200,
            "max_word_count": 5000,
            "content_freshness_hours": 72,
            "language_preference": "en"
        }
        
        prefs = self.content_preferences or {}
        return {**defaults, **prefs}
    
    def should_process_content(self, content_metadata: Dict[str, Any]) -> tuple[bool, str]:
        """
        Check if content should be processed based on user preferences.
        
        Args:
            content_metadata: Dictionary with content metadata
            
        Returns:
            Tuple of (should_process, reason)
        """
        active_prefs = self.get_active_content_preferences()
        if active_prefs:
            return active_prefs.should_process_content(content_metadata)
        
        # Fallback to JSONB-based filtering
        prefs = self.get_content_preferences_dict()
        
        # Check topics to avoid
        topics_to_avoid = prefs.get("topics_to_avoid", [])
        if topics_to_avoid:
            content_text = (content_metadata.get("title", "") + " " + 
                          content_metadata.get("description", "")).lower()
            
            for avoid_topic in topics_to_avoid:
                if avoid_topic.lower() in content_text:
                    return False, f"Contains avoided topic: {avoid_topic}"
        
        # Check minimum word count
        word_count = content_metadata.get("word_count", 0)
        min_word_count = prefs.get("min_word_count", 200)
        if word_count < min_word_count:
            return False, f"Word count {word_count} below minimum {min_word_count}"
        
        # Check maximum word count
        max_word_count = prefs.get("max_word_count", 5000)
        if word_count > max_word_count:
            return False, f"Word count {word_count} above maximum {max_word_count}"
        
        # Check content age
        content_age_hours = content_metadata.get("age_hours", 0)
        max_age = prefs.get("content_freshness_hours", 72)
        if content_age_hours > max_age:
            return False, f"Content age {content_age_hours}h exceeds freshness limit {max_age}h"
        
        return True, "Passes initial filters"
    
    def get_interests_for_llm(self) -> str:
        """Format interests for LLM consumption."""
        active_prefs = self.get_active_content_preferences()
        if active_prefs:
            return active_prefs.get_interests_for_llm()
        
        # Fallback to JSONB-based interests
        prefs = self.get_content_preferences_dict()
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
    
    # Legacy utility functions (keeping for backward compatibility)
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert User instance to dictionary without triggering database queries."""
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
            # Only include the raw JSONB column here. Let service layer inject enhanced prefs.
            "content_preferences": self.content_preferences,
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
    
    # Keep existing methods for backward compatibility...
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update user preferences with validation."""
        if self.preferences is None:
            self.preferences = {}
        
        current_prefs = dict(self.preferences)
        current_prefs.update(new_preferences)
        self.preferences = current_prefs
    
    def update_tone_profile(self, tone_updates: Dict[str, Any]) -> None:
        """Update user tone profile with validation."""
        if self.tone_profile is None:
            self.tone_profile = {}
        
        current_tone = dict(self.tone_profile)
        current_tone.update(tone_updates)
        self.tone_profile = current_tone
    
    def has_valid_linkedin_token(self) -> bool:
        """Check if user has a valid LinkedIn access token."""
        if not self.linkedin_access_token:
            return False
        
        if not self.linkedin_token_expires_at:
            return False
        
        return datetime.utcnow() < self.linkedin_token_expires_at
    
    def get_posting_schedule(self) -> List[str]:
        """Get user's preferred posting times."""
        if not self.preferences:
            return ["09:00", "13:00", "17:00"]
        
        return self.preferences.get("preferred_posting_times", ["09:00", "13:00", "17:00"])
    
    def is_auto_posting_enabled(self) -> bool:
        """Check if auto-posting is enabled for this user."""
        if not self.preferences:
            return False
        
        return self.preferences.get("auto_posting_enabled", False)


class ContentSelection(Base):
    """
    Track content selection decisions for analytics and learning.
    Enhanced to support LLM-based selection tracking.
    """
    
    __tablename__ = "content_selections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("content_sources.id", ondelete="CASCADE"), nullable=True)
    
    # Selection details
    selection_date = Column(DateTime(timezone=True), nullable=False, index=True)
    selection_type = Column(String(50), default="keyword_filter")  # keyword_filter, llm_selection, manual
    articles_considered = Column(Integer, nullable=False)
    articles_selected = Column(Integer, nullable=False)
    
    # LLM details
    llm_model_used = Column(String(100), nullable=True)
    selection_criteria = Column(JSONB, nullable=False, default=dict)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Results
    selected_article_ids = Column(JSONB, nullable=False, default=list)
    selection_scores = Column(JSONB, nullable=False, default=dict)
    selection_reasons = Column(JSONB, nullable=False, default=dict)  # LLM reasoning for each selection
    
    # Performance tracking
    articles_that_became_drafts = Column(Integer, default=0)
    articles_that_were_published = Column(Integer, default=0)
    avg_engagement_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="content_selections")
    source = relationship("ContentSource")
    
    def __repr__(self) -> str:
        return f"<ContentSelection(user_id={self.user_id}, selected={self.articles_selected}/{self.articles_considered}, type={self.selection_type})>"
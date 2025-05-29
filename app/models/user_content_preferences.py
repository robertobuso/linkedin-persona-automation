# app/models/user_content_preferences.py
"""
Enhanced user content preferences model for LinkedIn Presence Automation Application.

Defines comprehensive content preference management with versioning and validation.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, validator
from app.database.connection import Base


class UserContentPreferences(Base):
    """
    Separate table for user content preferences with versioning support.
    This allows for more complex preference management and analytics.
    """
    
    __tablename__ = "user_content_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Professional context
    job_role = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    experience_level = Column(String(50), default="intermediate")  # beginner, intermediate, senior, executive
    company_size = Column(String(50), nullable=True)  # startup, small, medium, large, enterprise
    
    # Content interests with structured storage
    primary_interests = Column(JSONB, nullable=False, default=list)  # List[str]
    secondary_interests = Column(JSONB, nullable=False, default=list)  # List[str]
    topics_to_avoid = Column(JSONB, nullable=False, default=list)  # List[str]
    
    # Custom AI instructions
    custom_prompt = Column(Text, nullable=True)
    content_style_preferences = Column(String(50), default="balanced")  # concise, balanced, detailed
    
    # Content filtering preferences
    content_types = Column(JSONB, nullable=False, default=lambda: ["articles", "news", "analysis"])
    min_relevance_score = Column(Float, default=0.7)
    max_articles_per_day = Column(Integer, default=15)
    preferred_content_length = Column(String(20), default="medium")  # short, medium, long
    min_word_count = Column(Integer, default=200)
    max_word_count = Column(Integer, default=5000)
    
    # Advanced preferences
    companies_to_follow = Column(JSONB, nullable=False, default=list)  # List[str]
    authors_to_follow = Column(JSONB, nullable=False, default=list)  # List[str]
    sources_to_prioritize = Column(JSONB, nullable=False, default=list)  # List[str]
    language_preference = Column(String(10), default="en")
    
    # Timing preferences
    content_freshness_hours = Column(Integer, default=72)
    check_frequency = Column(String(20), default="daily")  # hourly, daily, weekly
    
    # LinkedIn-specific preferences
    linkedin_post_style = Column(String(50), default="professional")
    include_industry_hashtags = Column(Boolean, default=True)
    max_hashtags = Column(Integer, default=5)
    
    # Learning and feedback
    learn_from_interactions = Column(Boolean, default=True)
    feedback_weight = Column(Float, default=0.3)
    
    # Versioning and metadata
    preferences_version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="content_preferences_records")
    
    def __repr__(self) -> str:
        return f"<UserContentPreferences(user_id={self.user_id}, version={self.preferences_version})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preferences to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "job_role": self.job_role,
            "industry": self.industry,
            "experience_level": self.experience_level,
            "company_size": self.company_size,
            "primary_interests": self.primary_interests,
            "secondary_interests": self.secondary_interests,
            "topics_to_avoid": self.topics_to_avoid,
            "custom_prompt": self.custom_prompt,
            "content_style_preferences": self.content_style_preferences,
            "content_types": self.content_types,
            "min_relevance_score": self.min_relevance_score,
            "max_articles_per_day": self.max_articles_per_day,
            "preferred_content_length": self.preferred_content_length,
            "min_word_count": self.min_word_count,
            "max_word_count": self.max_word_count,
            "companies_to_follow": self.companies_to_follow,
            "authors_to_follow": self.authors_to_follow,
            "sources_to_prioritize": self.sources_to_prioritize,
            "language_preference": self.language_preference,
            "content_freshness_hours": self.content_freshness_hours,
            "check_frequency": self.check_frequency,
            "linkedin_post_style": self.linkedin_post_style,
            "include_industry_hashtags": self.include_industry_hashtags,
            "max_hashtags": self.max_hashtags,
            "learn_from_interactions": self.learn_from_interactions,
            "feedback_weight": self.feedback_weight,
            "preferences_version": self.preferences_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_interests_for_llm(self) -> str:
        """Format interests for LLM consumption."""
        interests = []
        
        if self.primary_interests:
            interests.append(f"Primary interests: {', '.join(self.primary_interests)}")
        
        if self.secondary_interests:
            interests.append(f"Secondary interests: {', '.join(self.secondary_interests)}")
        
        if self.job_role:
            interests.append(f"Job role: {self.job_role}")
        
        if self.industry:
            interests.append(f"Industry: {self.industry}")
        
        if self.custom_prompt:
            interests.append(f"Custom instructions: {self.custom_prompt}")
        
        return ". ".join(interests) if interests else "General professional content"
    
    def should_process_content(self, content_metadata: Dict[str, Any]) -> tuple[bool, str]:
        """
        Quick check if content might be relevant to user preferences.
        
        Args:
            content_metadata: Dictionary with content metadata
            
        Returns:
            Tuple of (should_process, reason)
        """
        # Check topics to avoid
        if self.topics_to_avoid:
            content_text = (content_metadata.get("title", "") + " " + 
                          content_metadata.get("description", "")).lower()
            
            for avoid_topic in self.topics_to_avoid:
                if avoid_topic.lower() in content_text:
                    return False, f"Contains avoided topic: {avoid_topic}"
        
        # Check minimum word count
        word_count = content_metadata.get("word_count", 0)
        if word_count < self.min_word_count:
            return False, f"Word count {word_count} below minimum {self.min_word_count}"
        
        # Check maximum word count
        if word_count > self.max_word_count:
            return False, f"Word count {word_count} above maximum {self.max_word_count}"
        
        # Check content age
        content_age_hours = content_metadata.get("age_hours", 0)
        if content_age_hours > self.content_freshness_hours:
            return False, f"Content age {content_age_hours}h exceeds freshness limit {self.content_freshness_hours}h"
        
        # Check content type
        content_type = content_metadata.get("content_type", "article")
        if content_type not in self.content_types:
            return False, f"Content type {content_type} not in preferred types"
        
        return True, "Passes initial filters"


# Pydantic models for API validation
class ContentPreferencesCreate(BaseModel):
    """Schema for creating content preferences."""
    job_role: Optional[str] = None
    industry: Optional[str] = None
    experience_level: str = Field(default="intermediate", pattern="^(beginner|intermediate|senior|executive)$")
    company_size: Optional[str] = None
    primary_interests: List[str] = Field(default_factory=list, max_items=10)
    secondary_interests: List[str] = Field(default_factory=list, max_items=10)
    topics_to_avoid: List[str] = Field(default_factory=list, max_items=20)
    custom_prompt: Optional[str] = Field(None, max_length=1000)
    content_style_preferences: str = Field(default="balanced", pattern="^(concise|balanced|detailed)$")
    content_types: List[str] = Field(default_factory=lambda: ["articles", "news", "analysis"])
    min_relevance_score: float = Field(default=0.7, ge=0.0, le=1.0)
    max_articles_per_day: int = Field(default=15, ge=1, le=100)
    preferred_content_length: str = Field(default="medium", pattern="^(short|medium|long)$")
    min_word_count: int = Field(default=200, ge=50)
    max_word_count: int = Field(default=5000, ge=200)
    companies_to_follow: List[str] = Field(default_factory=list, max_items=50)
    authors_to_follow: List[str] = Field(default_factory=list, max_items=50)
    sources_to_prioritize: List[str] = Field(default_factory=list, max_items=20)
    language_preference: str = Field(default="en", max_length=10)
    content_freshness_hours: int = Field(default=72, ge=1, le=720)  # Max 30 days
    check_frequency: str = Field(default="daily", pattern="^(hourly|daily|weekly)$")
    linkedin_post_style: str = Field(default="professional")
    include_industry_hashtags: bool = True
    max_hashtags: int = Field(default=5, ge=0, le=20)
    learn_from_interactions: bool = True
    feedback_weight: float = Field(default=0.3, ge=0.0, le=1.0)

    @validator('primary_interests', 'secondary_interests', 'topics_to_avoid')
    def validate_interest_lists(cls, v):
        """Validate interest lists have valid content."""
        if not isinstance(v, list):
            return []
        return [str(item).strip() for item in v if str(item).strip()]
    
    @validator('companies_to_follow', 'authors_to_follow', 'sources_to_prioritize')
    def validate_follow_lists(cls, v):  
        """Validate follow lists have valid content."""
        if not isinstance(v, list):
            return []
        return [str(item).strip() for item in v if str(item).strip()]


class ContentPreferencesUpdate(BaseModel):
    """Schema for updating content preferences."""
    job_role: Optional[str] = None
    industry: Optional[str] = None
    experience_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|senior|executive)$")
    company_size: Optional[str] = None
    primary_interests: Optional[List[str]] = Field(None, max_items=10)
    secondary_interests: Optional[List[str]] = Field(None, max_items=10)
    topics_to_avoid: Optional[List[str]] = Field(None, max_items=20)
    custom_prompt: Optional[str] = Field(None, max_length=1000)
    content_style_preferences: Optional[str] = Field(None, pattern="^(concise|balanced|detailed)$")
    content_types: Optional[List[str]] = None
    min_relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_articles_per_day: Optional[int] = Field(None, ge=1, le=100)
    preferred_content_length: Optional[str] = Field(None, pattern="^(short|medium|long)$")
    min_word_count: Optional[int] = Field(None, ge=50)
    max_word_count: Optional[int] = Field(None, ge=200)
    companies_to_follow: Optional[List[str]] = Field(None, max_items=50)
    authors_to_follow: Optional[List[str]] = Field(None, max_items=50)
    sources_to_prioritize: Optional[List[str]] = Field(None, max_items=20)
    language_preference: Optional[str] = Field(None, max_length=10)
    content_freshness_hours: Optional[int] = Field(None, ge=1, le=720)
    check_frequency: Optional[str] = Field(None, pattern="^(hourly|daily|weekly)$")
    linkedin_post_style: Optional[str] = None
    include_industry_hashtags: Optional[bool] = None
    max_hashtags: Optional[int] = Field(None, ge=0, le=20)
    learn_from_interactions: Optional[bool] = None
    feedback_weight: Optional[float] = Field(None, ge=0.0, le=1.0)


class ContentPreferencesResponse(BaseModel):
    """Schema for content preferences response."""
    id: str
    user_id: str
    job_role: Optional[str]
    industry: Optional[str]
    experience_level: str
    company_size: Optional[str]
    primary_interests: List[str]
    secondary_interests: List[str]
    topics_to_avoid: List[str]
    custom_prompt: Optional[str]
    content_style_preferences: str
    content_types: List[str]
    min_relevance_score: float
    max_articles_per_day: int
    preferred_content_length: str
    min_word_count: int
    max_word_count: int
    companies_to_follow: List[str]
    authors_to_follow: List[str]
    sources_to_prioritize: List[str]
    language_preference: str
    content_freshness_hours: int
    check_frequency: str
    linkedin_post_style: str
    include_industry_hashtags: bool
    max_hashtags: int
    learn_from_interactions: bool
    feedback_weight: float
    preferences_version: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
"""
Content models for LinkedIn Presence Automation Application.

Defines ContentSource, ContentItem, and PostDraft entities for content management
and post generation workflow.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from app.database.connection import Base


class SourceType(str, Enum):
    """Enumeration of supported content source types."""
    RSS_FEED = "rss_feed"
    WEBSITE = "website"
    NEWSLETTER = "newsletter"
    MANUAL = "manual"


class ContentStatus(str, Enum):
    """Enumeration of content item processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DraftStatus(str, Enum):
    """Enumeration of post draft statuses."""
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


def truncate_field(value: Optional[str], max_length: int) -> Optional[str]:
    """Safely truncate a string field to maximum length."""
    if value is None:
        return None
    if len(value) <= max_length:
        return value
    # Truncate with ellipsis if too long
    return value[:max_length-3] + "..." if max_length > 3 else value[:max_length]


class ContentSource(Base):
    """
    Content source model representing external sources for content aggregation.
    
    Stores configuration for RSS feeds, websites, newsletters, and manual sources
    that provide content for LinkedIn post generation.
    """
    
    __tablename__ = "content_sources"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique content source identifier"
    )
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who owns this content source"
    )
    
    # Source configuration
    name = Column(
        String(255),
        nullable=False,
        doc="Human-readable name for the content source"
    )
    
    source_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of content source (rss_feed, website, newsletter, manual)"
    )
    
    url = Column(
        String(1000),
        nullable=True,
        doc="Source URL for RSS feeds, websites, or newsletters"
    )
    
    description = Column(
        Text,
        nullable=True,
        doc="Optional description of the content source"
    )
    
    # Source status and settings
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether this source is actively monitored"
    )
    
    check_frequency_hours = Column(
        Integer,
        default=24,
        nullable=False,
        doc="How often to check this source for new content (in hours)"
    )
    
    # Source-specific configuration
    source_config = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Source-specific configuration (RSS selectors, API keys, etc.)"
    )
    
    # Content filtering and processing
    content_filters = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "keywords_include": [],
            "keywords_exclude": [],
            "min_content_length": 100,
            "max_content_age_days": 30,
            "categories": [],
            "language": "en"
        },
        doc="Filters for content selection and processing"
    )
    
    # Processing statistics
    last_checked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this source was checked for new content"
    )
    
    last_successful_check_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful content check"
    )
    
    total_items_found = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of content items found from this source"
    )
    
    total_items_processed = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of content items successfully processed"
    )
    
    # Error tracking
    consecutive_failures = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of consecutive failed checks"
    )
    
    last_error_message = Column(
        Text,
        nullable=True,
        doc="Last error message from failed check"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Source creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last source update timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="content_sources",
        doc="User who owns this content source"
    )
    
    content_items = relationship(
        "ContentItem",
        back_populates="source",
        cascade="all, delete-orphan",
        doc="Content items from this source"
    )
    
    def __repr__(self) -> str:
        """String representation of ContentSource instance."""
        return f"<ContentSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"


class ContentItem(Base):
    """
    Content item model representing individual pieces of content from sources.
    
    Updated with increased field lengths to handle real-world content data.
    """
    
    __tablename__ = "content_items"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique content item identifier"
    )
    
    # Foreign key to content source
    source_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Content source that provided this item"
    )
    
    # Content metadata - INCREASED FIELD LENGTHS
    title = Column(
        String(1000),  # Increased from 500 to 1000
        nullable=False,
        doc="Content title or headline"
    )
    
    url = Column(
        String(2000),  # Increased from 1000 to 2000
        nullable=False,
        unique=True,
        index=True,
        doc="Original URL of the content item"
    )
    
    author = Column(
        String(500),  # Increased from 255 to 500
        nullable=True,
        doc="Content author or publisher"
    )
    
    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Original publication date of the content"
    )
    
    # Content data
    content = Column(
        Text,
        nullable=False,
        doc="Full text content or summary"
    )
    
    excerpt = Column(
        Text,
        nullable=True,
        doc="Short excerpt or summary of the content"
    )
    
    # Content classification
    category = Column(
        String(200),  # Increased from 100 to 200
        nullable=True,
        index=True,
        doc="Content category or topic"
    )
    
    tags = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="List of tags or keywords associated with the content"
    )
    
    # Processing status
    status = Column(
        String(50),
        default=ContentStatus.PENDING,
        nullable=False,
        index=True,
        doc="Processing status of the content item"
    )
    
    # AI analysis results
    ai_analysis = Column(
        JSONB,
        nullable=True,
        doc="AI analysis results including sentiment, topics, relevance score"
    )
    
    relevance_score = Column(
        Integer,
        nullable=True,
        index=True,
        doc="AI-calculated relevance score (0-100)"
    )
    
    # Content metrics
    word_count = Column(
        Integer,
        nullable=True,
        doc="Word count of the content"
    )
    
    reading_time_minutes = Column(
        Integer,
        nullable=True,
        doc="Estimated reading time in minutes"
    )
    
    # Processing metadata
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the content was processed by AI"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        doc="Error message if processing failed"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Content item creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last content item update timestamp"
    )
    
    # Relationships
    source = relationship(
        "ContentSource",
        back_populates="content_items",
        doc="Content source that provided this item"
    )
    
    post_drafts = relationship(
        "PostDraft",
        back_populates="source_content",
        doc="Post drafts generated from this content"
    )
    
    # Validation methods
    @validates('title')
    def validate_title(self, key, title):
        """Validate and truncate title if necessary."""
        return truncate_field(title, 1000)
    
    @validates('url')
    def validate_url(self, key, url):
        """Validate and truncate URL if necessary."""
        return truncate_field(url, 2000)
    
    @validates('author')
    def validate_author(self, key, author):
        """Validate and truncate author if necessary."""
        return truncate_field(author, 500)
    
    @validates('category')
    def validate_category(self, key, category):
        """Validate and truncate category if necessary."""
        return truncate_field(category, 200)
    
    def __repr__(self) -> str:
        """String representation of ContentItem instance."""
        title_preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return f"<ContentItem(id={self.id}, title='{title_preview}', status='{self.status}')>"
    
    @classmethod
    def create_safe(cls, **kwargs):
        """
        Create ContentItem with automatic field truncation.
        
        This method ensures all string fields are within their limits
        before creating the instance.
        """
        # Safely truncate fields before creation
        if 'title' in kwargs:
            kwargs['title'] = truncate_field(kwargs['title'], 1000)
        if 'url' in kwargs:
            kwargs['url'] = truncate_field(kwargs['url'], 2000)
        if 'author' in kwargs:
            kwargs['author'] = truncate_field(kwargs['author'], 500)
        if 'category' in kwargs:
            kwargs['category'] = truncate_field(kwargs['category'], 200)
        
        return cls(**kwargs)
    

class PostDraft(Base):
    """
    Post draft model representing generated LinkedIn posts ready for review/publishing.
    
    Stores AI-generated post content, scheduling information, and publication status.
    """
    
    __tablename__ = "post_drafts"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique post draft identifier"
    )
    
    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who owns this post draft"
    )
    
    source_content_id = Column(
        UUID(as_uuid=True),
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Source content item used to generate this draft"
    )
    
    # Post content
    content = Column(
        Text,
        nullable=False,
        doc="Generated LinkedIn post content"
    )
    
    hashtags = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="List of hashtags for the post"
    )
    
    # Post metadata
    title = Column(
        String(255),
        nullable=True,
        doc="Optional title or subject for the post"
    )
    
    post_type = Column(
        String(50),
        default="text",
        nullable=False,
        doc="Type of post (text, image, video, article, etc.)"
    )
    
    # Scheduling and status
    status = Column(
        String(50),
        default=DraftStatus.DRAFT,
        nullable=False,
        index=True,
        doc="Current status of the post draft"
    )
    
    scheduled_for = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Scheduled publication time"
    )
    
    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Actual publication timestamp"
    )
    
    # LinkedIn integration
    linkedin_post_id = Column(
        String(255),
        nullable=True,
        unique=True,
        doc="LinkedIn post ID after publication"
    )
    
    linkedin_post_url = Column(
        String(500),
        nullable=True,
        doc="LinkedIn post URL after publication"
    )
    
    # AI generation metadata
    generation_prompt = Column(
        Text,
        nullable=True,
        doc="AI prompt used to generate this post"
    )
    
    ai_model_used = Column(
        String(100),
        nullable=True,
        doc="AI model used for generation"
    )
    
    generation_metadata = Column(
        JSONB,
        nullable=True,
        doc="Additional metadata from AI generation process"
    )
    
    # Performance tracking
    engagement_metrics = Column(
        JSONB,
        nullable=False,
        default=lambda: {
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "views": 0,
            "clicks": 0,
            "last_updated": None
        },
        doc="LinkedIn engagement metrics for published posts"
    )
    
    # Error tracking
    publication_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of publication attempts"
    )
    
    last_error_message = Column(
        Text,
        nullable=True,
        doc="Last error message from failed publication"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Draft creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last draft update timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="post_drafts",
        doc="User who owns this post draft"
    )
    
    source_content = relationship(
        "ContentItem",
        back_populates="post_drafts",
        doc="Source content item used to generate this draft"
    )
    
    def __repr__(self) -> str:
        """String representation of PostDraft instance."""
        return f"<PostDraft(id={self.id}, status='{self.status}', user_id={self.user_id})>"
    
    def is_scheduled(self) -> bool:
        """Check if the draft is scheduled for future publication."""
        return (
            self.status == DraftStatus.SCHEDULED and 
            self.scheduled_for is not None and 
            self.scheduled_for > datetime.utcnow()
        )
    
    def is_ready_to_publish(self) -> bool:
        """Check if the draft is ready for immediate publication."""
        return (
            self.status == DraftStatus.SCHEDULED and 
            self.scheduled_for is not None and 
            self.scheduled_for <= datetime.utcnow()
        )
    
    def update_engagement_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update engagement metrics for published posts.
        
        Args:
            metrics: Dictionary containing engagement data
        """
        if self.engagement_metrics is None:
            self.engagement_metrics = {}
        
        current_metrics = dict(self.engagement_metrics)
        current_metrics.update(metrics)
        current_metrics["last_updated"] = datetime.utcnow().isoformat()
        self.engagement_metrics = current_metrics
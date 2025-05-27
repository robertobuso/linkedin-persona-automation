"""
Pydantic schemas for content-related data validation and serialization.

Defines request/response schemas for content ingestion, processing,
and management operations.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, HttpUrl
from enum import Enum


class SourceTypeEnum(str, Enum):
    """Enumeration of supported content source types."""
    RSS_FEED = "rss_feed"
    WEBSITE = "website"
    NEWSLETTER = "newsletter"
    LINKEDIN = "linkedin"
    MANUAL = "manual"


class ContentStatusEnum(str, Enum):
    """Enumeration of content processing statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DraftStatusEnum(str, Enum):
    """Enumeration of post draft statuses."""
    DRAFT = "draft"
    READY = "ready"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


# Content Source Schemas
class ContentSourceBase(BaseModel):
    """Base schema for content source data."""
    name: str = Field(..., min_length=1, max_length=255, description="Source name")
    source_type: SourceTypeEnum = Field(..., description="Type of content source")
    url: Optional[HttpUrl] = Field(None, description="Source URL")
    description: Optional[str] = Field(None, max_length=1000, description="Source description")
    is_active: bool = Field(True, description="Whether source is active")
    check_frequency_hours: int = Field(24, ge=1, le=168, description="Check frequency in hours")


class ContentSourceCreate(ContentSourceBase):
    """Schema for creating a new content source."""
    source_config: Dict[str, Any] = Field(default_factory=dict, description="Source-specific configuration")
    content_filters: Dict[str, Any] = Field(
        default_factory=lambda: {
            "keywords_include": [],
            "keywords_exclude": [],
            "min_content_length": 100,
            "max_content_age_days": 30,
            "categories": [],
            "language": "en"
        },
        description="Content filtering preferences"
    )
    
    @validator('url')
    def validate_url_for_type(cls, v, values):
        """Validate URL is required for certain source types."""
        source_type = values.get('source_type')
        if source_type in [SourceTypeEnum.RSS_FEED, SourceTypeEnum.WEBSITE, SourceTypeEnum.LINKEDIN]:
            if not v:
                raise ValueError(f"URL is required for {source_type} sources")
        return v


class ContentSourceUpdate(BaseModel):
    """Schema for updating a content source."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    check_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    source_config: Optional[Dict[str, Any]] = None
    content_filters: Optional[Dict[str, Any]] = None


class ContentSourceResponse(ContentSourceBase):
    """Schema for content source response data."""
    id: UUID
    user_id: UUID
    source_config: Dict[str, Any]
    content_filters: Dict[str, Any]
    last_checked_at: Optional[datetime]
    last_successful_check_at: Optional[datetime]
    total_items_found: int
    total_items_processed: int
    consecutive_failures: int
    last_error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Content Item Schemas
class ContentItemBase(BaseModel):
    """Base schema for content item data."""
    title: str = Field(..., min_length=1, max_length=500, description="Content title")
    url: HttpUrl = Field(..., description="Content URL")
    author: Optional[str] = Field(None, max_length=255, description="Content author")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    content: str = Field(..., min_length=1, description="Content text")
    excerpt: Optional[str] = Field(None, max_length=1000, description="Content excerpt")
    category: Optional[str] = Field(None, max_length=100, description="Content category")
    tags: List[str] = Field(default_factory=list, description="Content tags")


class ContentItemCreate(ContentItemBase):
    """Schema for creating a new content item."""
    source_id: UUID = Field(..., description="Source that provided this content")


class ContentItemUpdate(BaseModel):
    """Schema for updating a content item."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    status: Optional[ContentStatusEnum] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    relevance_score: Optional[int] = Field(None, ge=0, le=100)


class ContentItemResponse(ContentItemBase):
    """Schema for content item response data."""
    id: UUID
    source_id: UUID
    status: ContentStatusEnum
    ai_analysis: Optional[Dict[str, Any]]
    relevance_score: Optional[int]
    word_count: Optional[int]
    reading_time_minutes: Optional[int]
    processed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Post Draft Schemas
class PostDraftBase(BaseModel):
    """Base schema for post draft data."""
    content: str = Field(..., min_length=1, description="Post content")
    hashtags: List[str] = Field(default_factory=list, description="Post hashtags")
    title: Optional[str] = Field(None, max_length=255, description="Post title")
    post_type: str = Field("text", description="Type of post")


class PostDraftCreate(PostDraftBase):
    """Schema for creating a new post draft."""
    source_content_id: Optional[UUID] = Field(None, description="Source content used for generation")
    generation_prompt: Optional[str] = Field(None, description="AI prompt used")
    ai_model_used: Optional[str] = Field(None, max_length=100, description="AI model used")
    generation_metadata: Optional[Dict[str, Any]] = Field(None, description="Generation metadata")


class PostDraftUpdate(BaseModel):
    """Schema for updating a post draft."""
    content: Optional[str] = Field(None, min_length=1)
    hashtags: Optional[List[str]] = None
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[DraftStatusEnum] = None
    scheduled_for: Optional[datetime] = None


class PostDraftResponse(PostDraftBase):
    """Schema for post draft response data."""
    id: UUID
    user_id: UUID
    source_content_id: Optional[UUID]
    status: DraftStatusEnum
    scheduled_for: Optional[datetime]
    published_at: Optional[datetime]
    linkedin_post_id: Optional[str]
    linkedin_post_url: Optional[str]
    generation_prompt: Optional[str]
    ai_model_used: Optional[str]
    generation_metadata: Optional[Dict[str, Any]]
    engagement_metrics: Dict[str, Any]
    publication_attempts: int
    last_error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Processing and Ingestion Schemas
class ProcessingResultSchema(BaseModel):
    """Schema for content processing results."""
    processed_count: int = Field(0, description="Number of items processed")
    error_count: int = Field(0, description="Number of errors")
    skipped_count: int = Field(0, description="Number of items skipped")
    total_sources: int = Field(0, description="Number of sources processed")
    success_rate: float = Field(0.0, description="Success rate percentage")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")


class ContentIngestionRequest(BaseModel):
    """Schema for content ingestion requests."""
    user_id: Optional[UUID] = Field(None, description="User ID to process sources for")
    source_ids: Optional[List[UUID]] = Field(None, description="Specific source IDs to process")
    force_refresh: bool = Field(False, description="Force refresh even if recently checked")


class ContentIngestionResponse(BaseModel):
    """Schema for content ingestion response."""
    task_id: Optional[str] = Field(None, description="Background task ID")
    status: str = Field("started", description="Ingestion status")
    message: str = Field("Content ingestion started", description="Status message")
    result: Optional[ProcessingResultSchema] = Field(None, description="Processing results if completed")


class ContentStatsSchema(BaseModel):
    """Schema for content processing statistics."""
    total_sources: int
    active_sources: int
    inactive_sources: int
    total_items_found: int
    total_items_processed: int
    processing_rate: float
    failed_sources: int
    sources_due_for_check: int
    last_updated: datetime


# Feed Validation Schemas
class FeedValidationRequest(BaseModel):
    """Schema for RSS feed validation requests."""
    url: HttpUrl = Field(..., description="RSS feed URL to validate")


class FeedValidationResponse(BaseModel):
    """Schema for RSS feed validation response."""
    valid: bool = Field(..., description="Whether the feed is valid")
    title: Optional[str] = Field(None, description="Feed title")
    description: Optional[str] = Field(None, description="Feed description")
    link: Optional[str] = Field(None, description="Feed website link")
    language: Optional[str] = Field(None, description="Feed language")
    entry_count: Optional[int] = Field(None, description="Number of entries in feed")
    last_updated: Optional[str] = Field(None, description="Last update time")
    feed_type: Optional[str] = Field(None, description="Feed format type")
    error: Optional[str] = Field(None, description="Error message if validation failed")


# LinkedIn Profile Validation Schemas
class LinkedInProfileValidationRequest(BaseModel):
    """Schema for LinkedIn profile validation requests."""
    profile_url: HttpUrl = Field(..., description="LinkedIn profile URL to validate")


class LinkedInProfileValidationResponse(BaseModel):
    """Schema for LinkedIn profile validation response."""
    valid: bool = Field(..., description="Whether the profile is valid and accessible")
    profile_name: Optional[str] = Field(None, description="Profile name")
    url: Optional[str] = Field(None, description="Validated profile URL")
    error: Optional[str] = Field(None, description="Error message if validation failed")


# Content Filtering Schemas
class ContentFiltersSchema(BaseModel):
    """Schema for content filtering configuration."""
    keywords_include: List[str] = Field(default_factory=list, description="Keywords that must be present")
    keywords_exclude: List[str] = Field(default_factory=list, description="Keywords to exclude")
    min_content_length: int = Field(200, ge=50, description="Minimum content length")
    max_content_age_days: int = Field(30, ge=1, le=365, description="Maximum content age in days")
    categories: List[str] = Field(default_factory=list, description="Allowed categories")
    language: str = Field("en", description="Content language")
    
    @validator('min_content_length')
    def validate_min_length(cls, v):
        """Validate minimum content length."""
        if v < 50:
            raise ValueError("Minimum content length must be at least 50 characters")
        return v


# Source Configuration Schemas
class RSSSourceConfigSchema(BaseModel):
    """Schema for RSS source configuration."""
    custom_headers: Dict[str, str] = Field(default_factory=dict, description="Custom HTTP headers")
    auth_username: Optional[str] = Field(None, description="HTTP basic auth username")
    auth_password: Optional[str] = Field(None, description="HTTP basic auth password")
    follow_redirects: bool = Field(True, description="Follow HTTP redirects")
    timeout_seconds: int = Field(30, ge=5, le=120, description="Request timeout")


class LinkedInSourceConfigSchema(BaseModel):
    """Schema for LinkedIn source configuration."""
    max_posts: int = Field(20, ge=1, le=100, description="Maximum posts to scrape")
    include_reposts: bool = Field(False, description="Include reposted content")
    min_engagement: int = Field(0, ge=0, description="Minimum engagement threshold")


# Bulk Operations Schemas
class BulkContentItemCreate(BaseModel):
    """Schema for bulk content item creation."""
    items: List[ContentItemCreate] = Field(..., min_items=1, max_items=100, description="Content items to create")


class BulkContentItemResponse(BaseModel):
    """Schema for bulk content item creation response."""
    created_count: int = Field(..., description="Number of items created")
    skipped_count: int = Field(..., description="Number of items skipped (duplicates)")
    error_count: int = Field(..., description="Number of items that failed")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    created_items: List[UUID] = Field(default_factory=list, description="IDs of created items")
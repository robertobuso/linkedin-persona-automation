"""
API schemas for LinkedIn Presence Automation Application.

Defines Pydantic models for API request/response validation and serialization
across all endpoints with comprehensive data validation.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, validator, EmailStr, HttpUrl, ConfigDict
from enum import Enum


# Authentication Schemas
class BaseResponseModel(BaseModel):
    """Base response model with UUID serialization."""
    model_config = ConfigDict(
        from_attributes=True,
        # FIX: Ensure UUIDs are serialized as strings
        json_encoders={
            UUID: str,
            datetime: lambda v: v.isoformat() if v else None
        },
        arbitrary_types_allowed=True
    )

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user profile updates."""
    full_name: Optional[str] = Field(None, max_length=255)
    linkedin_profile_url: Optional[HttpUrl] = None


class UserResponse(BaseResponseModel):
    """Schema for user response data."""
    user: Dict[str, Any] = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class UserProfileData(BaseResponseModel): # Inherit from BaseResponseModel
    """Schema for detailed user profile information."""
    id: UUID # Will be serialized as str by BaseResponseModel's json_encoders
    email: EmailStr
    full_name: Optional[str] = None
    linkedin_profile_url: Optional[HttpUrl] = None # Use HttpUrl if it's a URL
    is_active: bool
    is_verified: bool
    # For JSONB fields from your User model:
    preferences: Dict[str, Any] # Or a more specific Pydantic model if you have one for preferences
    tone_profile: Dict[str, Any] # Or a more specific Pydantic model
    created_at: datetime # Will be serialized as str
    updated_at: datetime # Will be serialized as str
    last_login_at: Optional[datetime] = None # Will be serialized as str or None


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    user: Dict[str, Any] = Field(..., description="User information")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordChange(BaseModel):
    """Schema for password change request."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# Content Management Schemas
class ContentSourceCreate(BaseModel):
    """Schema for creating content sources."""
    name: str = Field(..., min_length=1, max_length=255, description="Source name")
    source_type: str = Field(..., description="Type of content source")
    url: Optional[HttpUrl] = Field(None, description="Source URL")
    description: Optional[str] = Field(None, max_length=1000, description="Source description")
    is_active: bool = Field(True, description="Whether source is active")
    check_frequency_hours: int = Field(24, ge=1, le=168, description="Check frequency in hours")
    source_config: Dict[str, Any] = Field(default_factory=dict, description="Source configuration")
    content_filters: Dict[str, Any] = Field(default_factory=dict, description="Content filters")


class ContentSourceUpdate(BaseModel):
    """Schema for updating content sources."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    check_frequency_hours: Optional[int] = Field(None, ge=1, le=168)
    source_config: Optional[Dict[str, Any]] = None
    content_filters: Optional[Dict[str, Any]] = None


class ContentSourceResponse(BaseResponseModel):
    """Schema for content source response."""
    id: str = Field(..., description="Source ID")  # Will be auto-converted from UUID
    user_id: str = Field(..., description="User ID")  # Will be auto-converted from UUID
    name: str = Field(..., description="Source name")
    source_type: str = Field(..., description="Source type")
    url: Optional[str] = Field(None, description="Source URL")
    description: Optional[str] = Field(None, description="Source description")
    is_active: bool = Field(..., description="Whether source is active")
    check_frequency_hours: int = Field(..., description="Check frequency")
    last_checked_at: Optional[datetime] = Field(None, description="Last check time")
    total_items_found: int = Field(..., description="Total items found")
    total_items_processed: int = Field(..., description="Total items processed")
    created_at: datetime = Field(..., description="Creation time")
    
    # FIX: Add UUID validation and conversion
    @validator('id', 'user_id', pre=True)
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string for JSON serialization."""
        if isinstance(v, UUID):
            return str(v)
        return v

class ContentItemResponse(BaseResponseModel):
    """Schema for content item response."""
    id: str = Field(..., description="Content item ID")
    source_id: str = Field(..., description="Source ID")
    title: str = Field(..., description="Content title")
    url: str = Field(..., description="Content URL")
    author: Optional[str] = Field(None, description="Content author")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    content: str = Field(..., description="Content text")
    category: Optional[str] = Field(None, description="Content category")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    status: str = Field(..., description="Processing status")
    relevance_score: Optional[int] = Field(None, description="Relevance score")
    created_at: datetime = Field(..., description="Creation time")
    
    @validator('id', 'source_id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class ContentIngestionResponse(BaseResponseModel):
    """Schema for content ingestion response."""
    task_id: Optional[str] = Field(None, description="Background task ID")
    status: str = Field(..., description="Ingestion status")
    message: str = Field(..., description="Status message")


class FeedValidationRequest(BaseModel):
    """Schema for feed validation request."""
    url: HttpUrl = Field(..., description="RSS feed URL to validate")


class FeedValidationResponse(BaseResponseModel):
    """Schema for feed validation response."""
    valid: bool = Field(..., description="Whether feed is valid")
    title: Optional[str] = Field(None, description="Feed title")
    description: Optional[str] = Field(None, description="Feed description")
    entry_count: Optional[int] = Field(None, description="Number of entries")
    error: Optional[str] = Field(None, description="Error message if invalid")


class ContentStatsResponse(BaseResponseModel):
    """Schema for content statistics response."""
    total_sources: int = Field(..., description="Total content sources")
    active_sources: int = Field(..., description="Active sources")
    total_items_found: int = Field(..., description="Total items found")
    total_items_processed: int = Field(..., description="Total items processed")
    processing_rate: float = Field(..., description="Processing success rate")
    last_updated: datetime = Field(..., description="Last update time")


# Draft Management Schemas
class PostDraftCreate(BaseModel):
    """Schema for creating post drafts."""
    content_item_id: str = Field(..., description="Source content item ID")  # Accept string
    
    @validator('content_item_id')
    def validate_content_item_id(cls, v):
        """Validate and convert content item ID to UUID format."""
        try:
            # Validate it's a valid UUID
            UUID(v)
            return v
        except ValueError:
            raise ValueError("content_item_id must be a valid UUID")


class PostDraftUpdate(BaseModel):
    """Schema for updating post drafts."""
    content: Optional[str] = Field(None, min_length=1, description="Post content")
    hashtags: Optional[List[str]] = Field(None, description="Post hashtags")
    title: Optional[str] = Field(None, max_length=255, description="Post title")
    status: Optional[str] = Field(None, description="Draft status")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled time")


class PostDraftResponse(BaseResponseModel):
    """Schema for post draft response."""
    id: str = Field(..., description="Draft ID")
    user_id: str = Field(..., description="User ID")
    content: str = Field(..., description="Post content")
    hashtags: List[str] = Field(default_factory=list, description="Post hashtags")
    title: Optional[str] = Field(None, description="Post title")
    status: str = Field(..., description="Draft status")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled time")
    published_at: Optional[datetime] = Field(None, description="Publication time")
    linkedin_post_id: Optional[str] = Field(None, description="LinkedIn post ID")
    linkedin_post_url: Optional[str] = Field(None, description="LinkedIn post URL")
    created_at: datetime = Field(..., description="Creation time")
    
    class Config:
        from_attributes = True


class PublishRequest(BaseModel):
    """Schema for post publishing request."""
    scheduled_time: Optional[datetime] = Field(None, description="Optional scheduled time")


class PublishResponse(BaseResponseModel):
    """Schema for post publishing response."""
    draft_id: str = Field(..., description="Draft ID")
    status: str = Field(..., description="Publication status")
    scheduled_time: Optional[datetime] = Field(None, description="Scheduled time")
    linkedin_post_id: Optional[str] = Field(None, description="LinkedIn post ID")
    linkedin_post_url: Optional[str] = Field(None, description="LinkedIn post URL")
    message: str = Field(..., description="Status message")


class DraftStatsResponse(BaseResponseModel):
    """Schema for draft statistics response."""
    total_drafts: int = Field(..., description="Total drafts")
    draft: int = Field(..., description="Draft status count")
    ready: int = Field(..., description="Ready status count")
    scheduled: int = Field(..., description="Scheduled status count")
    published: int = Field(..., description="Published status count")
    failed: int = Field(..., description="Failed status count")
    archived: int = Field(..., description="Archived status count")


# Engagement Schemas
class EngagementOpportunityResponse(BaseResponseModel):
    """Schema for engagement opportunity response."""
    id: str = Field(..., description="Opportunity ID")
    target_type: str = Field(..., description="Target type")
    target_url: str = Field(..., description="Target URL")
    target_author: Optional[str] = Field(None, description="Target author")
    target_title: Optional[str] = Field(None, description="Target title")
    engagement_type: str = Field(..., description="Engagement type")
    priority: str = Field(..., description="Priority level")
    suggested_comment: Optional[str] = Field(None, description="Suggested comment")
    engagement_reason: Optional[str] = Field(None, description="Engagement reason")
    relevance_score: Optional[int] = Field(None, description="Relevance score")
    status: str = Field(..., description="Opportunity status")
    created_at: datetime = Field(..., description="Creation time")
    
    class Config:
        from_attributes = True


class CommentRequest(BaseModel):
    """Schema for comment creation request."""
    opportunity_id: UUID = Field(..., description="Engagement opportunity ID")
    comment_text: Optional[str] = Field(None, description="Custom comment text")


class CommentResponse(BaseResponseModel):
    """Schema for comment creation response."""
    opportunity_id: str = Field(..., description="Opportunity ID")
    comment_text: str = Field(..., description="Generated/posted comment")
    status: str = Field(..., description="Comment status")
    ai_generated: bool = Field(..., description="Whether comment was AI-generated")
    confidence_score: float = Field(..., description="AI confidence score")
    alternative_comments: List[str] = Field(default_factory=list, description="Alternative comments")


class EngagementStatsResponse(BaseResponseModel):
    """Schema for engagement statistics response."""
    total_opportunities: int = Field(..., description="Total opportunities")
    completion_rate: float = Field(..., description="Completion rate percentage")
    status_breakdown: Dict[str, int] = Field(..., description="Status breakdown")
    type_breakdown: Dict[str, int] = Field(..., description="Type breakdown")
    period_days: int = Field(..., description="Analysis period")
    generated_at: datetime = Field(..., description="Generation time")


# Analytics Schemas
class DashboardResponse(BaseResponseModel):
    """Schema for analytics dashboard response."""
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    trends: Dict[str, Any] = Field(..., description="Content trends")
    engagement_history: Dict[str, Any] = Field(..., description="Engagement history")
    period_days: int = Field(..., description="Analysis period")
    user_id: str = Field(..., description="User ID")


class RecommendationsResponse(BaseResponseModel):
    """Schema for recommendations response."""
    recommendations: List[Dict[str, Any]] = Field(..., description="Content recommendations")
    optimal_times: List[Dict[str, Any]] = Field(..., description="Optimal posting times")
    total_count: int = Field(..., description="Total recommendations")
    generated_at: datetime = Field(..., description="Generation time")


class PerformanceMetricsResponse(BaseResponseModel):
    """Schema for performance metrics response."""
    user_id: str = Field(..., description="User ID")
    period_days: int = Field(..., description="Analysis period")
    total_posts: int = Field(..., description="Total posts")
    avg_engagement_rate: float = Field(..., description="Average engagement rate")
    total_reach: int = Field(..., description="Total reach")
    total_impressions: int = Field(..., description="Total impressions")
    click_through_rate: float = Field(..., description="Click-through rate")
    engagement_trend: str = Field(..., description="Engagement trend")
    calculated_at: datetime = Field(..., description="Calculation time")


class WeeklyReportResponse(BaseResponseModel):
    """Schema for weekly report response."""
    user_id: str = Field(..., description="User ID")
    period_start: datetime = Field(..., description="Period start")
    period_end: datetime = Field(..., description="Period end")
    total_posts: int = Field(..., description="Total posts")
    total_engagement: Dict[str, int] = Field(..., description="Total engagement")
    avg_engagement_rate: float = Field(..., description="Average engagement rate")
    top_performing_posts: List[Dict[str, Any]] = Field(..., description="Top posts")
    insights: List[Dict[str, Any]] = Field(..., description="Generated insights")
    recommendations: List[str] = Field(..., description="Recommendations")
    generated_at: datetime = Field(..., description="Generation time")


# Error Response Schemas
class ErrorResponse(BaseResponseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(..., description="Error timestamp")


class ValidationErrorResponse(BaseResponseModel):
    """Schema for validation error responses."""
    error: str = Field("Validation Error", description="Error type")
    message: str = Field(..., description="Error message")
    details: List[Dict[str, Any]] = Field(..., description="Validation error details")
    timestamp: datetime = Field(..., description="Error timestamp")


# Pagination Schemas
class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseResponseModel):
    """Schema for paginated responses."""
    items: List[Any] = Field(..., description="Items for current page")
    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


# Health Check Schema
class HealthCheckResponse(BaseResponseModel):
    """Schema for health check response."""
    status: str = Field("healthy", description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field("1.0.0", description="API version")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Dependency status")
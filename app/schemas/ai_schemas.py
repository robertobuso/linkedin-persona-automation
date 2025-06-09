"""
Pydantic schemas for AI service data validation and serialization.

Defines request/response schemas for AI operations including content summarization,
post generation, comment creation, and tone analysis.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class WritingStyleEnum(str, Enum):
    """Enumeration of writing styles."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    STORYTELLING = "storytelling"
    HUMOROUS = "humorous"
    PROFESSIONAL_THOUGHT_LEADER = "professional_thought_leader"
    EDUCATIONAL = "educational"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"


class ToneEnum(str, Enum):
    """Enumeration of communication tones."""
    INFORMATIVE = "informative"
    ENTHUSIASTIC = "enthusiastic"
    INSPIRATIONAL = "inspirational"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"


class ToneStyle(str, Enum):
    """Available tone styles for draft generation."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    STORYTELLING = "storytelling"
    HUMOROUS = "humorous"
    THOUGHT_LEADERSHIP = "thought_leadership"
    EDUCATIONAL = "educational"
    ENGAGEMENT_OPTIMIZED = "engagement_optimized"


class PostStyleEnum(str, Enum):
    """Enumeration of post styles."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    THOUGHT_PROVOKING = "thought_provoking"
    EDUCATIONAL = "educational"
    MOTIVATIONAL = "motivational"
    STORYTELLING = "storytelling"
    PROFESSIONAL_THOUGHT_LEADER = "professional_thought_leader"
    HUMOROUS = "humorous"


class EngagementTypeEnum(str, Enum):
    """Enumeration of engagement types for comments."""
    THOUGHTFUL = "thoughtful"
    SUPPORTIVE = "supportive"
    QUESTIONING = "questioning"
    CONGRATULATORY = "congratulatory"
    INSIGHTFUL = "insightful"


class ToneProfile(BaseModel):
    """Schema for user tone profile."""
    writing_style: WritingStyleEnum = Field(WritingStyleEnum.PROFESSIONAL, description="Overall writing style")
    tone: ToneEnum = Field(ToneEnum.INFORMATIVE, description="Communication tone")
    personality_traits: List[str] = Field(default_factory=list, description="Personality characteristics")
    industry_focus: List[str] = Field(default_factory=list, description="Industry areas of focus")
    expertise_areas: List[str] = Field(default_factory=list, description="Areas of expertise")
    communication_preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "use_emojis": False,
            "include_hashtags": True,
            "max_hashtags": 3,
            "call_to_action_style": "subtle"
        },
        description="Communication preferences and style settings"
    )
    
    @validator('personality_traits')
    def validate_personality_traits(cls, v):
        """Validate personality traits list."""
        if len(v) > 5:
            return v[:5]  # Limit to 5 traits
        return v
    
    @validator('industry_focus')
    def validate_industry_focus(cls, v):
        """Validate industry focus list."""
        if len(v) > 3:
            return v[:3]  # Limit to 3 industries
        return v
    
    @validator('expertise_areas')
    def validate_expertise_areas(cls, v):
        """Validate expertise areas list."""
        if len(v) > 5:
            return v[:5]  # Limit to 5 areas
        return v


# Content Summarization Schemas
class SummaryRequest(BaseModel):
    """Schema for content summarization requests."""
    content: str = Field(..., min_length=100, description="Content to summarize")
    tone_profile: ToneProfile = Field(..., description="User tone profile for matching")
    max_length: Optional[int] = Field(200, ge=50, le=500, description="Maximum summary length")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")
    
    @validator('content')
    def validate_content_length(cls, v):
        """Validate content is not too long."""
        if len(v) > 10000:
            raise ValueError("Content too long for summarization (max 10,000 characters)")
        return v


class SummaryResponse(BaseModel):
    """Schema for content summarization response."""
    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(..., description="Key points extracted from content")
    word_count: int = Field(..., description="Word count of summary")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="AI model used for generation")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    cost: float = Field(..., description="Cost of generation in USD")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in summary quality")


# Post Generation Schemas
class PostGenerationRequest(BaseModel):
    """Schema for LinkedIn post generation requests."""
    summary: str = Field(..., min_length=50, description="Content summary to generate post from")
    tone_profile: ToneProfile = Field(..., description="User tone profile")
    user_examples: Optional[List[str]] = Field(default=None, description="User's historical posts for style matching")
    style: Optional[PostStyleEnum] = Field(PostStyleEnum.PROFESSIONAL_THOUGHT_LEADER, description="Desired post style")
    num_variations: Optional[int] = Field(3, ge=1, le=5, description="Number of variations to generate")
    include_hashtags: Optional[bool] = Field(True, description="Whether to include hashtags")
    max_length: Optional[int] = Field(3000, ge=100, le=3000, description="Maximum post length")
    custom_prompt_text: Optional[str] = None
    
    @validator('user_examples')
    def validate_user_examples(cls, v):
        """Validate user examples list."""
        if v and len(v) > 10:
            return v[:10]  # Limit to 10 examples
        return v


class PostGenerationResponse(BaseModel):
    """Schema for LinkedIn post generation response."""
    content: str = Field(..., description="Generated post content")
    hashtags: List[str] = Field(..., description="Generated hashtags")
    variations: List[str] = Field(..., description="Alternative post variations")
    engagement_hooks: List[str] = Field(default_factory=list, description="Engagement hooks used")
    call_to_action: Optional[str] = Field(None, description="Call to action if included")
    estimated_reach: Dict[str, int] = Field(default_factory=dict, description="Estimated reach metrics")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="AI model used for generation")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    cost: float = Field(..., description="Cost of generation in USD")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score of generated content")


# Comment Generation Schemas
class CommentGenerationRequest(BaseModel):
    """Schema for LinkedIn comment generation requests."""
    post_content: str = Field(..., min_length=10, description="LinkedIn post content to comment on")
    post_author: Optional[str] = Field(None, description="Author of the post")
    tone_profile: ToneProfile = Field(..., description="User tone profile")
    engagement_type: Optional[EngagementTypeEnum] = Field(
        EngagementTypeEnum.THOUGHTFUL, 
        description="Type of engagement desired"
    )
    max_length: Optional[int] = Field(150, ge=10, le=300, description="Maximum comment length")
    context: Optional[str] = Field(None, description="Additional context for comment generation")
    
    @validator('post_content')
    def validate_post_content_length(cls, v):
        """Validate post content length."""
        if len(v) > 5000:
            raise ValueError("Post content too long (max 5,000 characters)")
        return v


class CommentGenerationResponse(BaseModel):
    """Schema for LinkedIn comment generation response."""
    comment: str = Field(..., description="Generated comment")
    engagement_type: EngagementTypeEnum = Field(..., description="Type of engagement used")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in comment quality")
    alternative_comments: List[str] = Field(default_factory=list, description="Alternative comment options")
    processing_time: float = Field(..., description="Processing time in seconds")
    model_used: str = Field(..., description="AI model used for generation")
    tokens_used: int = Field(..., description="Number of tokens consumed")
    cost: float = Field(..., description="Cost of generation in USD")


# Tone Analysis Schemas
class ToneAnalysisRequest(BaseModel):
    """Schema for tone analysis requests."""
    user_id: str = Field(..., description="User ID to analyze")
    min_posts: Optional[int] = Field(5, ge=3, le=50, description="Minimum posts required for analysis")
    include_recent_only: Optional[bool] = Field(True, description="Only analyze recent posts")
    days_back: Optional[int] = Field(90, ge=7, le=365, description="Days back to analyze")


class ToneAnalysisResponse(BaseModel):
    """Schema for tone analysis response."""
    tone_profile: ToneProfile = Field(..., description="Analyzed tone profile")
    analysis_summary: Dict[str, Any] = Field(..., description="Human-readable analysis summary")
    posts_analyzed: int = Field(..., description="Number of posts analyzed")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis")
    analysis_date: datetime = Field(..., description="When analysis was performed")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


# Batch Processing Schemas
class BatchPostGenerationRequest(BaseModel):
    """Schema for batch post generation requests."""
    user_id: str = Field(..., description="User ID to generate posts for")
    max_posts: Optional[int] = Field(5, ge=1, le=10, description="Maximum posts to generate")
    min_relevance_score: Optional[int] = Field(70, ge=0, le=100, description="Minimum content relevance score")
    style_preferences: Optional[List[PostStyleEnum]] = Field(None, description="Preferred post styles")
    
    @validator('style_preferences')
    def validate_style_preferences(cls, v):
        """Validate style preferences list."""
        if v and len(v) > 3:
            return v[:3]  # Limit to 3 styles
        return v


class BatchPostGenerationResponse(BaseModel):
    """Schema for batch post generation response."""
    posts_generated: int = Field(..., description="Number of posts generated")
    posts_failed: int = Field(..., description="Number of posts that failed generation")
    total_processing_time: float = Field(..., description="Total processing time")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total cost in USD")
    post_ids: List[str] = Field(..., description="IDs of generated posts")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Generation errors")


# AI Service Status and Metrics Schemas
class AIServiceStatus(BaseModel):
    """Schema for AI service status."""
    primary_provider: str = Field(..., description="Primary LLM provider")
    fallback_provider: Optional[str] = Field(None, description="Fallback LLM provider")
    providers_available: List[str] = Field(..., description="Available LLM providers")
    service_healthy: bool = Field(..., description="Whether service is healthy")
    last_health_check: datetime = Field(..., description="Last health check timestamp")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")


class AIUsageMetrics(BaseModel):
    """Schema for AI usage metrics."""
    total_requests: int = Field(..., description="Total requests processed")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    success_rate: float = Field(..., description="Success rate percentage")
    total_tokens: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total cost in USD")
    average_response_time: float = Field(..., description="Average response time in seconds")
    provider_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Usage breakdown by provider")
    period_hours: int = Field(..., description="Time period for metrics")
    generated_at: datetime = Field(..., description="When metrics were generated")


# Content Quality Validation Schemas
class ContentQualityCheck(BaseModel):
    """Schema for content quality validation."""
    content: str = Field(..., description="Content to validate")
    check_professionalism: Optional[bool] = Field(True, description="Check professional tone")
    check_length: Optional[bool] = Field(True, description="Check appropriate length")
    check_hashtags: Optional[bool] = Field(True, description="Validate hashtags")
    check_engagement: Optional[bool] = Field(True, description="Check engagement potential")


class ContentQualityResponse(BaseModel):
    """Schema for content quality validation response."""
    is_valid: bool = Field(..., description="Whether content passes quality checks")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    issues: List[str] = Field(default_factory=list, description="Quality issues found")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    character_count: int = Field(..., description="Character count")
    word_count: int = Field(..., description="Word count")
    hashtag_count: int = Field(..., description="Number of hashtags")
    readability_score: Optional[float] = Field(None, description="Readability score")


# Error Response Schemas
class AIServiceError(BaseModel):
    """Schema for AI service error responses."""
    error_type: str = Field(..., description="Type of error")
    error_message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(..., description="When error occurred")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")


# Configuration Schemas
class LLMProviderConfig(BaseModel):
    """Schema for LLM provider configuration."""
    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name")
    api_key_configured: bool = Field(..., description="Whether API key is configured")
    max_tokens: int = Field(..., description="Maximum tokens per request")
    rate_limit_rpm: int = Field(..., description="Rate limit requests per minute")
    rate_limit_tpm: int = Field(..., description="Rate limit tokens per minute")
    cost_per_token: float = Field(..., description="Cost per token in USD")


class AIServiceConfig(BaseModel):
    """Schema for AI service configuration."""
    primary_provider: LLMProviderConfig = Field(..., description="Primary LLM provider config")
    fallback_provider: Optional[LLMProviderConfig] = Field(None, description="Fallback provider config")
    default_temperature: float = Field(0.7, description="Default temperature for generation")
    default_max_tokens: int = Field(1000, description="Default max tokens")
    retry_attempts: int = Field(3, description="Number of retry attempts")
    timeout_seconds: int = Field(60, description="Request timeout in seconds")
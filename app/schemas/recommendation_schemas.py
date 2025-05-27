"""
Recommendation schemas for LinkedIn Presence Automation Application.

Defines Pydantic models for recommendation engine data validation and serialization
including content scoring, timing optimization, and analytics insights.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ContentScore(BaseModel):
    """Schema for content scoring breakdown."""
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Topic relevance score")
    source_credibility: float = Field(..., ge=0.0, le=1.0, description="Source credibility score")
    timeliness_score: float = Field(..., ge=0.0, le=1.0, description="Content timeliness score")
    engagement_potential: float = Field(..., ge=0.0, le=1.0, description="Predicted engagement potential")
    composite_score: float = Field(..., ge=0.0, le=1.0, description="Overall composite score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in scoring")


class OptimalTimingResponse(BaseModel):
    """Schema for optimal posting time recommendations."""
    recommended_time: datetime = Field(..., description="Recommended posting time")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday)")
    hour: int = Field(..., ge=0, le=23, description="Hour of day")
    minute: int = Field(..., ge=0, le=59, description="Minute of hour")
    expected_engagement: float = Field(..., ge=0.0, description="Expected engagement rate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    reasoning: str = Field(..., description="Explanation for the recommendation")
    alternative_times: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative time options")


class ScoredRecommendation(BaseModel):
    """Schema for scored content recommendation."""
    draft_id: UUID = Field(..., description="Post draft ID")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall recommendation score")
    action: str = Field(..., description="Recommended action (post_now, schedule_later, review_and_edit, skip)")
    reasoning: str = Field(..., description="Human-readable explanation for the recommendation")
    content_score: ContentScore = Field(..., description="Detailed scoring breakdown")
    optimal_timing: Optional[Dict[str, Any]] = Field(None, description="Optimal timing recommendation")
    estimated_performance: Dict[str, Any] = Field(..., description="Estimated performance metrics")
    scored_at: datetime = Field(..., description="When the scoring was performed")


class RecommendationRequest(BaseModel):
    """Schema for content recommendation requests."""
    user_id: UUID = Field(..., description="User ID to generate recommendations for")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of recommendations")
    min_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum score threshold")
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")


class RecommendationResponse(BaseModel):
    """Schema for content recommendation response."""
    user_id: UUID = Field(..., description="User ID")
    recommendations: List[ScoredRecommendation] = Field(..., description="Scored recommendations")
    optimal_times: List[Dict[str, Any]] = Field(..., description="Optimal posting times")
    generated_at: datetime = Field(..., description="When recommendations were generated")


class SchedulingRecommendation(BaseModel):
    """Schema for post scheduling recommendations."""
    post_id: UUID = Field(..., description="Post ID to schedule")
    recommended_time: datetime = Field(..., description="Recommended posting time")
    expected_engagement: float = Field(..., ge=0.0, description="Expected engagement rate")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation")
    reasoning: str = Field(..., description="Explanation for the timing")
    alternative_times: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative options")


class EngagementPrediction(BaseModel):
    """Schema for engagement prediction results."""
    predicted_engagement_rate: float = Field(..., ge=0.0, description="Predicted engagement rate")
    predicted_likes: int = Field(..., ge=0, description="Predicted number of likes")
    predicted_comments: int = Field(..., ge=0, description="Predicted number of comments")
    predicted_shares: int = Field(..., ge=0, description="Predicted number of shares")
    predicted_views: int = Field(..., ge=0, description="Predicted number of views")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in prediction")
    features_used: Dict[str, Any] = Field(..., description="Features used for prediction")
    model_type: str = Field(..., description="Type of model used")
    predicted_at: datetime = Field(..., description="When prediction was made")


class PerformanceMetrics(BaseModel):
    """Schema for performance metrics."""
    user_id: UUID = Field(..., description="User ID")
    period_days: int = Field(..., description="Analysis period in days")
    total_posts: int = Field(..., description="Total posts in period")
    avg_engagement_rate: float = Field(..., ge=0.0, description="Average engagement rate")
    total_reach: int = Field(..., ge=0, description="Total reach")
    total_impressions: int = Field(..., ge=0, description="Total impressions")
    click_through_rate: float = Field(..., ge=0.0, description="Click-through rate")
    follower_growth: int = Field(..., description="Follower growth in period")
    best_performing_time: Optional[Dict[str, Any]] = Field(None, description="Best performing time slot")
    engagement_trend: str = Field(..., description="Engagement trend direction")
    calculated_at: datetime = Field(..., description="When metrics were calculated")


class TrendAnalysis(BaseModel):
    """Schema for content trend analysis."""
    user_id: UUID = Field(..., description="User ID")
    period_days: int = Field(..., description="Analysis period in days")
    posting_frequency_trend: str = Field(..., description="Posting frequency trend")
    engagement_trend: str = Field(..., description="Engagement trend direction")
    best_content_types: List[Dict[str, Any]] = Field(..., description="Best performing content types")
    optimal_posting_times: List[Dict[str, Any]] = Field(..., description="Optimal posting times")
    hashtag_performance: Dict[str, Any] = Field(..., description="Hashtag performance analysis")
    content_length_analysis: Dict[str, Any] = Field(..., description="Content length performance")
    recommendations: List[str] = Field(..., description="Trend-based recommendations")
    analyzed_at: datetime = Field(..., description="When analysis was performed")


class AnalyticsInsight(BaseModel):
    """Schema for analytics insights."""
    type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Insight description")
    value: Optional[float] = Field(None, description="Numerical value if applicable")
    recommendation: str = Field(..., description="Actionable recommendation")


class WeeklyReport(BaseModel):
    """Schema for weekly performance reports."""
    user_id: UUID = Field(..., description="User ID")
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")
    total_posts: int = Field(..., description="Total posts in period")
    total_engagement: Dict[str, int] = Field(..., description="Total engagement metrics")
    avg_engagement_rate: float = Field(..., ge=0.0, description="Average engagement rate")
    top_performing_posts: List[Dict[str, Any]] = Field(..., description="Top performing posts")
    insights: List[AnalyticsInsight] = Field(..., description="Generated insights")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    generated_at: datetime = Field(..., description="When report was generated")
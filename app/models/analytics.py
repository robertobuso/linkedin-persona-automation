"""
Analytics models for LinkedIn Presence Automation Application.

Defines analytics entities for tracking post performance, user metrics,
and engagement trends with comprehensive data storage.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class PostPerformance(Base):
    """
    Post performance tracking model for detailed analytics.
    
    Stores comprehensive performance metrics for published posts
    including engagement data, reach metrics, and temporal analysis.
    """
    
    __tablename__ = "post_performance"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique performance record identifier"
    )
    
    # Foreign keys
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey("post_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Post being tracked"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who owns the post"
    )
    
    # Performance metrics
    likes_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of likes received"
    )
    
    comments_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of comments received"
    )
    
    shares_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of shares/reposts"
    )
    
    views_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of views/impressions"
    )
    
    clicks_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of clicks on post content"
    )
    
    # Calculated metrics
    engagement_rate = Column(
        Float,
        nullable=True,
        doc="Calculated engagement rate (engagement/views)"
    )
    
    click_through_rate = Column(
        Float,
        nullable=True,
        doc="Click-through rate (clicks/views)"
    )
    
    # Temporal metrics
    post_age_hours = Column(
        Float,
        nullable=True,
        doc="Age of post when metrics were recorded (hours)"
    )
    
    peak_engagement_hour = Column(
        Integer,
        nullable=True,
        doc="Hour when peak engagement occurred"
    )
    
    # Detailed metrics
    detailed_metrics = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Detailed engagement breakdown and additional metrics"
    )
    
    # Audience insights
    audience_insights = Column(
        JSONB,
        nullable=True,
        doc="Audience demographics and behavior insights"
    )
    
    # Performance comparison
    performance_vs_average = Column(
        Float,
        nullable=True,
        doc="Performance compared to user's average (multiplier)"
    )
    
    # Timestamps
    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When metrics were recorded"
    )
    
    # Relationships
    post = relationship(
        "PostDraft",
        doc="Post being tracked"
    )
    
    user = relationship(
        "User",
        doc="User who owns the post"
    )
    
    def __repr__(self) -> str:
        """String representation of PostPerformance instance."""
        return f"<PostPerformance(post_id={self.post_id}, engagement_rate={self.engagement_rate})>"
    
    @property
    def total_engagement(self) -> int:
        """Calculate total engagement."""
        return self.likes_count + self.comments_count + self.shares_count
    
    def calculate_engagement_rate(self) -> float:
        """Calculate and update engagement rate."""
        if self.views_count > 0:
            self.engagement_rate = self.total_engagement / self.views_count
        else:
            self.engagement_rate = 0.0
        return self.engagement_rate
    
    def calculate_click_through_rate(self) -> float:
        """Calculate and update click-through rate."""
        if self.views_count > 0:
            self.click_through_rate = self.clicks_count / self.views_count
        else:
            self.click_through_rate = 0.0
        return self.click_through_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "post_id": str(self.post_id),
            "user_id": str(self.user_id),
            "likes_count": self.likes_count,
            "comments_count": self.comments_count,
            "shares_count": self.shares_count,
            "views_count": self.views_count,
            "clicks_count": self.clicks_count,
            "total_engagement": self.total_engagement,
            "engagement_rate": self.engagement_rate,
            "click_through_rate": self.click_through_rate,
            "post_age_hours": self.post_age_hours,
            "peak_engagement_hour": self.peak_engagement_hour,
            "detailed_metrics": self.detailed_metrics,
            "audience_insights": self.audience_insights,
            "performance_vs_average": self.performance_vs_average,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


class UserAnalytics(Base):
    """
    User analytics model for aggregated performance tracking.
    
    Stores user-level analytics including averages, trends,
    and performance summaries over time.
    """
    
    __tablename__ = "user_analytics"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique analytics record identifier"
    )
    
    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User being analyzed"
    )
    
    # Time period
    period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Start of analytics period"
    )
    
    period_end = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="End of analytics period"
    )
    
    period_type = Column(
        String(20),
        nullable=False,
        index=True,
        doc="Type of period (daily, weekly, monthly)"
    )
    
    # Post metrics
    total_posts = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total posts in period"
    )
    
    avg_engagement_rate = Column(
        Float,
        nullable=True,
        doc="Average engagement rate for period"
    )
    
    total_likes = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total likes in period"
    )
    
    total_comments = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total comments in period"
    )
    
    total_shares = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total shares in period"
    )
    
    total_views = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total views in period"
    )
    
    total_clicks = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Total clicks in period"
    )
    
    # Performance metrics
    best_performing_post_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        doc="ID of best performing post in period"
    )
    
    best_engagement_rate = Column(
        Float,
        nullable=True,
        doc="Best engagement rate achieved in period"
    )
    
    worst_engagement_rate = Column(
        Float,
        nullable=True,
        doc="Worst engagement rate in period"
    )
    
    # Growth metrics
    follower_growth = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Net follower growth in period"
    )
    
    reach_growth = Column(
        Float,
        nullable=True,
        doc="Reach growth percentage"
    )
    
    # Trend indicators
    engagement_trend = Column(
        String(20),
        nullable=True,
        doc="Engagement trend direction (improving, declining, stable)"
    )
    
    posting_frequency = Column(
        Float,
        nullable=True,
        doc="Average posts per day in period"
    )
    
    # Detailed analytics
    detailed_analytics = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Detailed analytics data and breakdowns"
    )
    
    # Insights and recommendations
    insights = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Generated insights for the period"
    )
    
    recommendations = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Generated recommendations for improvement"
    )
    
    # Timestamps
    calculated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When analytics were calculated"
    )
    
    # Relationships
    user = relationship(
        "User",
        doc="User being analyzed"
    )
    
    def __repr__(self) -> str:
        """String representation of UserAnalytics instance."""
        return f"<UserAnalytics(user_id={self.user_id}, period={self.period_type}, posts={self.total_posts})>"
    
    @property
    def total_engagement(self) -> int:
        """Calculate total engagement for period."""
        return self.total_likes + self.total_comments + self.total_shares
    
    def calculate_metrics(self) -> None:
        """Calculate derived metrics."""
        if self.total_views > 0:
            self.avg_engagement_rate = self.total_engagement / self.total_views
        
        # Calculate posting frequency
        if self.period_start and self.period_end:
            period_days = (self.period_end - self.period_start).days
            if period_days > 0:
                self.posting_frequency = self.total_posts / period_days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "period_type": self.period_type,
            "total_posts": self.total_posts,
            "avg_engagement_rate": self.avg_engagement_rate,
            "total_engagement": self.total_engagement,
            "total_likes": self.total_likes,
            "total_comments": self.total_comments,
            "total_shares": self.total_shares,
            "total_views": self.total_views,
            "total_clicks": self.total_clicks,
            "best_performing_post_id": str(self.best_performing_post_id) if self.best_performing_post_id else None,
            "best_engagement_rate": self.best_engagement_rate,
            "worst_engagement_rate": self.worst_engagement_rate,
            "follower_growth": self.follower_growth,
            "reach_growth": self.reach_growth,
            "engagement_trend": self.engagement_trend,
            "posting_frequency": self.posting_frequency,
            "detailed_analytics": self.detailed_analytics,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None
        }


class EngagementTrend(Base):
    """
    Engagement trend tracking model for time-series analysis.
    
    Stores engagement trends over time for pattern analysis
    and predictive modeling.
    """
    
    __tablename__ = "engagement_trends"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique trend record identifier"
    )
    
    # Foreign key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User being tracked"
    )
    
    # Time dimension
    date = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Date of the trend data point"
    )
    
    hour_of_day = Column(
        Integer,
        nullable=True,
        doc="Hour of day (0-23) for hourly trends"
    )
    
    day_of_week = Column(
        Integer,
        nullable=True,
        doc="Day of week (0-6) for weekly patterns"
    )
    
    # Engagement metrics
    posts_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of posts in this time period"
    )
    
    avg_engagement_rate = Column(
        Float,
        nullable=True,
        doc="Average engagement rate for time period"
    )
    
    avg_likes = Column(
        Float,
        nullable=True,
        doc="Average likes per post"
    )
    
    avg_comments = Column(
        Float,
        nullable=True,
        doc="Average comments per post"
    )
    
    avg_shares = Column(
        Float,
        nullable=True,
        doc="Average shares per post"
    )
    
    avg_views = Column(
        Float,
        nullable=True,
        doc="Average views per post"
    )
    
    # Trend indicators
    trend_direction = Column(
        String(20),
        nullable=True,
        doc="Trend direction (up, down, stable)"
    )
    
    trend_strength = Column(
        Float,
        nullable=True,
        doc="Strength of trend (0-1)"
    )
    
    # Comparative metrics
    vs_previous_period = Column(
        Float,
        nullable=True,
        doc="Performance vs previous period (percentage change)"
    )
    
    vs_user_average = Column(
        Float,
        nullable=True,
        doc="Performance vs user's overall average"
    )
    
    # Additional data
    trend_data = Column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Additional trend analysis data"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When trend record was created"
    )
    
    # Relationships
    user = relationship(
        "User",
        doc="User being tracked"
    )
    
    def __repr__(self) -> str:
        """String representation of EngagementTrend instance."""
        return f"<EngagementTrend(user_id={self.user_id}, date={self.date}, rate={self.avg_engagement_rate})>"
    
    def calculate_trend_direction(self, previous_rate: Optional[float]) -> str:
        """Calculate trend direction compared to previous period."""
        if not previous_rate or not self.avg_engagement_rate:
            return "stable"
        
        change_threshold = 0.1  # 10% change threshold
        change_ratio = (self.avg_engagement_rate - previous_rate) / previous_rate
        
        if change_ratio > change_threshold:
            self.trend_direction = "up"
        elif change_ratio < -change_threshold:
            self.trend_direction = "down"
        else:
            self.trend_direction = "stable"
        
        self.trend_strength = abs(change_ratio)
        return self.trend_direction
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "date": self.date.isoformat() if self.date else None,
            "hour_of_day": self.hour_of_day,
            "day_of_week": self.day_of_week,
            "posts_count": self.posts_count,
            "avg_engagement_rate": self.avg_engagement_rate,
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
            "avg_shares": self.avg_shares,
            "avg_views": self.avg_views,
            "trend_direction": self.trend_direction,
            "trend_strength": self.trend_strength,
            "vs_previous_period": self.vs_previous_period,
            "vs_user_average": self.vs_user_average,
            "trend_data": self.trend_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
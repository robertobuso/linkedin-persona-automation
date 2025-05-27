"""
Analytics service for LinkedIn Presence Automation Application.

Provides comprehensive analytics tracking, performance metrics calculation,
and insights generation for user content and engagement.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.repositories.content_repository import PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import PostDraft, DraftStatus
from app.models.analytics import PostPerformance, UserAnalytics, EngagementTrend
from app.schemas.recommendation_schemas import (
    WeeklyReport, AnalyticsInsight, PerformanceMetrics, TrendAnalysis
)

logger = logging.getLogger(__name__)


@dataclass
class EngagementMetrics:
    """Container for engagement metrics."""
    likes: int = 0
    comments: int = 0
    shares: int = 0
    views: int = 0
    clicks: int = 0
    
    @property
    def total_engagement(self) -> int:
        """Calculate total engagement."""
        return self.likes + self.comments + self.shares
    
    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate."""
        if self.views == 0:
            return 0.0
        return self.total_engagement / self.views


class AnalyticsError(Exception):
    """Base exception for analytics service errors."""
    pass


class AnalyticsService:
    """
    Service for analytics tracking and performance analysis.
    
    Tracks post performance, calculates engagement metrics, generates insights,
    and provides trend analysis for user content strategy optimization.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize analytics service.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.post_repo = PostDraftRepository(session)
        self.user_repo = UserRepository(session)
    
    async def track_post_performance(
        self,
        post_id: UUID,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Track performance metrics for a published post.
        
        Args:
            post_id: Post ID to track performance for
            metrics: Performance metrics data
        """
        try:
            logger.info(f"Tracking performance for post {post_id}")
            
            # Get the post
            post = await self.post_repo.get_by_id(post_id)
            if not post:
                raise AnalyticsError(f"Post {post_id} not found")
            
            # Update engagement metrics
            await self.post_repo.update_engagement_metrics(post_id, metrics)
            
            # Create performance record
            performance_record = {
                'post_id': post_id,
                'user_id': post.user_id,
                'metrics': metrics,
                'recorded_at': datetime.utcnow(),
                'post_age_hours': self._calculate_post_age_hours(post.published_at)
            }
            
            # Store in analytics table (would be implemented with actual analytics model)
            await self._store_performance_record(performance_record)
            
            # Update user engagement averages
            await self._update_user_engagement_averages(post.user_id)
            
            logger.info(f"Performance tracked for post {post_id}")
            
        except Exception as e:
            logger.error(f"Failed to track post performance: {str(e)}")
            raise AnalyticsError(f"Failed to track performance: {str(e)}")
    
    async def generate_weekly_report(self, user_id: UUID) -> WeeklyReport:
        """
        Generate weekly performance report for user.
        
        Args:
            user_id: User ID to generate report for
            
        Returns:
            WeeklyReport with performance summary and insights
        """
        try:
            logger.info(f"Generating weekly report for user {user_id}")
            
            # Get posts from last week
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            posts = await self._get_user_posts_in_period(user_id, start_date, end_date)
            
            if not posts:
                return WeeklyReport(
                    user_id=user_id,
                    period_start=start_date,
                    period_end=end_date,
                    total_posts=0,
                    total_engagement=EngagementMetrics(),
                    avg_engagement_rate=0.0,
                    top_performing_posts=[],
                    insights=[],
                    recommendations=[]
                )
            
            # Calculate total engagement
            total_engagement = self._calculate_total_engagement(posts)
            
            # Find top performing posts
            top_performing = self._find_top_posts(posts, limit=3)
            
            # Generate insights
            insights = await self._generate_insights(posts, user_id)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(posts, user_id)
            
            # Calculate average engagement rate
            avg_engagement_rate = self._calculate_average_engagement_rate(posts)
            
            return WeeklyReport(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                total_posts=len(posts),
                total_engagement=total_engagement,
                avg_engagement_rate=avg_engagement_rate,
                top_performing_posts=top_performing,
                insights=insights,
                recommendations=recommendations,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {str(e)}")
            raise AnalyticsError(f"Failed to generate report: {str(e)}")
    
    async def get_user_engagement_history(
        self,
        user_id: UUID,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get user's engagement history for analysis.
        
        Args:
            user_id: User ID to get history for
            days: Number of days to look back
            
        Returns:
            Dictionary with engagement history data
        """
        try:
            logger.info(f"Getting engagement history for user {user_id}")
            
            # Get posts from specified period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            posts = await self._get_user_posts_in_period(user_id, start_date, end_date)
            
            # Process posts for analysis
            processed_posts = []
            for post in posts:
                if post.published_at and post.engagement_metrics:
                    processed_posts.append({
                        'id': str(post.id),
                        'published_at': post.published_at.isoformat(),
                        'engagement_metrics': post.engagement_metrics,
                        'content_length': len(post.content),
                        'hashtag_count': len(post.hashtags or []),
                        'post_type': post.post_type
                    })
            
            return {
                'user_id': str(user_id),
                'period_days': days,
                'posts': processed_posts,
                'total_posts': len(processed_posts),
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get engagement history: {str(e)}")
            return {
                'user_id': str(user_id),
                'period_days': days,
                'posts': [],
                'total_posts': 0,
                'error': str(e)
            }
    
    async def calculate_performance_metrics(
        self,
        user_id: UUID,
        period_days: int = 30
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics for user.
        
        Args:
            user_id: User ID to calculate metrics for
            period_days: Period to analyze
            
        Returns:
            PerformanceMetrics with calculated values
        """
        try:
            logger.info(f"Calculating performance metrics for user {user_id}")
            
            # Get posts from period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            posts = await self._get_user_posts_in_period(user_id, start_date, end_date)
            
            if not posts:
                return PerformanceMetrics(
                    user_id=user_id,
                    period_days=period_days,
                    total_posts=0,
                    avg_engagement_rate=0.0,
                    total_reach=0,
                    total_impressions=0,
                    click_through_rate=0.0,
                    follower_growth=0,
                    best_performing_time=None,
                    engagement_trend='stable'
                )
            
            # Calculate metrics
            total_posts = len(posts)
            avg_engagement_rate = self._calculate_average_engagement_rate(posts)
            total_reach = sum(post.engagement_metrics.get('views', 0) for post in posts)
            total_impressions = total_reach  # Simplified - in real implementation would be different
            
            # Calculate CTR
            total_clicks = sum(post.engagement_metrics.get('clicks', 0) for post in posts)
            click_through_rate = (total_clicks / total_impressions) if total_impressions > 0 else 0.0
            
            # Find best performing time
            best_time = await self._find_best_performing_time(posts)
            
            # Calculate engagement trend
            engagement_trend = self._calculate_engagement_trend(posts)
            
            return PerformanceMetrics(
                user_id=user_id,
                period_days=period_days,
                total_posts=total_posts,
                avg_engagement_rate=avg_engagement_rate,
                total_reach=total_reach,
                total_impressions=total_impressions,
                click_through_rate=click_through_rate,
                follower_growth=0,  # Would need separate tracking
                best_performing_time=best_time,
                engagement_trend=engagement_trend,
                calculated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {str(e)}")
            raise AnalyticsError(f"Failed to calculate metrics: {str(e)}")
    
    async def analyze_content_trends(
        self,
        user_id: UUID,
        period_days: int = 90
    ) -> TrendAnalysis:
        """
        Analyze content performance trends.
        
        Args:
            user_id: User ID to analyze trends for
            period_days: Period to analyze
            
        Returns:
            TrendAnalysis with trend insights
        """
        try:
            logger.info(f"Analyzing content trends for user {user_id}")
            
            # Get posts from period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            posts = await self._get_user_posts_in_period(user_id, start_date, end_date)
            
            if not posts:
                return TrendAnalysis(
                    user_id=user_id,
                    period_days=period_days,
                    posting_frequency_trend='stable',
                    engagement_trend='stable',
                    best_content_types=[],
                    optimal_posting_times=[],
                    hashtag_performance={},
                    content_length_analysis={},
                    recommendations=[]
                )
            
            # Analyze posting frequency trend
            posting_frequency_trend = self._analyze_posting_frequency(posts)
            
            # Analyze engagement trend
            engagement_trend = self._calculate_engagement_trend(posts)
            
            # Find best content types
            best_content_types = self._analyze_content_types(posts)
            
            # Find optimal posting times
            optimal_times = await self._analyze_optimal_times(posts)
            
            # Analyze hashtag performance
            hashtag_performance = self._analyze_hashtag_performance(posts)
            
            # Analyze content length
            content_length_analysis = self._analyze_content_length(posts)
            
            # Generate trend-based recommendations
            recommendations = self._generate_trend_recommendations(
                posting_frequency_trend, engagement_trend, best_content_types
            )
            
            return TrendAnalysis(
                user_id=user_id,
                period_days=period_days,
                posting_frequency_trend=posting_frequency_trend,
                engagement_trend=engagement_trend,
                best_content_types=best_content_types,
                optimal_posting_times=optimal_times,
                hashtag_performance=hashtag_performance,
                content_length_analysis=content_length_analysis,
                recommendations=recommendations,
                analyzed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze content trends: {str(e)}")
            raise AnalyticsError(f"Failed to analyze trends: {str(e)}")
    
    def _calculate_post_age_hours(self, published_at: Optional[datetime]) -> Optional[float]:
        """Calculate post age in hours."""
        if not published_at:
            return None
        
        age = datetime.utcnow() - published_at
        return age.total_seconds() / 3600
    
    async def _store_performance_record(self, record: Dict[str, Any]) -> None:
        """Store performance record in analytics table."""
        # In a real implementation, this would store in PostPerformance table
        # For now, we'll just log it
        logger.info(f"Storing performance record: {record}")
    
    async def _update_user_engagement_averages(self, user_id: UUID) -> None:
        """Update user's engagement averages."""
        try:
            # Get recent posts for average calculation
            recent_posts = await self.post_repo.get_recent_published_drafts(
                user_id=user_id, days=30, limit=50
            )
            
            if not recent_posts:
                return
            
            # Calculate averages
            total_engagement = 0
            total_posts = 0
            
            for post in recent_posts:
                if post.engagement_metrics:
                    metrics = post.engagement_metrics
                    engagement = (metrics.get('likes', 0) + 
                                metrics.get('comments', 0) + 
                                metrics.get('shares', 0))
                    total_engagement += engagement
                    total_posts += 1
            
            if total_posts > 0:
                avg_engagement = total_engagement / total_posts
                
                # Store in user preferences
                user = await self.user_repo.get_by_id(user_id)
                if user:
                    current_prefs = user.preferences or {}
                    current_prefs['avg_engagement'] = avg_engagement
                    current_prefs['engagement_updated_at'] = datetime.utcnow().isoformat()
                    await self.user_repo.update_preferences(user_id, current_prefs)
            
        except Exception as e:
            logger.warning(f"Failed to update user engagement averages: {str(e)}")
    
    async def _get_user_posts_in_period(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[PostDraft]:
        """Get user's published posts in specified period."""
        try:
            # Get published posts in date range
            stmt = select(PostDraft).where(
                and_(
                    PostDraft.user_id == user_id,
                    PostDraft.status == DraftStatus.PUBLISHED,
                    PostDraft.published_at >= start_date,
                    PostDraft.published_at <= end_date
                )
            ).order_by(PostDraft.published_at.desc())
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Failed to get user posts in period: {str(e)}")
            return []
    
    def _calculate_total_engagement(self, posts: List[PostDraft]) -> EngagementMetrics:
        """Calculate total engagement across posts."""
        total_metrics = EngagementMetrics()
        
        for post in posts:
            if post.engagement_metrics:
                metrics = post.engagement_metrics
                total_metrics.likes += metrics.get('likes', 0)
                total_metrics.comments += metrics.get('comments', 0)
                total_metrics.shares += metrics.get('shares', 0)
                total_metrics.views += metrics.get('views', 0)
                total_metrics.clicks += metrics.get('clicks', 0)
        
        return total_metrics
    
    def _find_top_posts(self, posts: List[PostDraft], limit: int = 3) -> List[Dict[str, Any]]:
        """Find top performing posts."""
        # Calculate engagement score for each post
        scored_posts = []
        
        for post in posts:
            if post.engagement_metrics:
                metrics = post.engagement_metrics
                engagement_score = (
                    metrics.get('likes', 0) * 1 +
                    metrics.get('comments', 0) * 3 +  # Comments weighted higher
                    metrics.get('shares', 0) * 5      # Shares weighted highest
                )
                
                scored_posts.append({
                    'post_id': str(post.id),
                    'content': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'engagement_score': engagement_score,
                    'metrics': metrics
                })
        
        # Sort by engagement score and return top posts
        scored_posts.sort(key=lambda x: x['engagement_score'], reverse=True)
        return scored_posts[:limit]
    
    async def _generate_insights(self, posts: List[PostDraft], user_id: UUID) -> List[AnalyticsInsight]:
        """Generate insights from post performance."""
        insights = []
        
        if not posts:
            return insights
        
        # Insight 1: Best performing content type
        content_type_performance = {}
        for post in posts:
            post_type = post.post_type or 'text'
            if post_type not in content_type_performance:
                content_type_performance[post_type] = {'count': 0, 'total_engagement': 0}
            
            content_type_performance[post_type]['count'] += 1
            if post.engagement_metrics:
                engagement = (post.engagement_metrics.get('likes', 0) + 
                            post.engagement_metrics.get('comments', 0) + 
                            post.engagement_metrics.get('shares', 0))
                content_type_performance[post_type]['total_engagement'] += engagement
        
        # Find best performing type
        best_type = None
        best_avg = 0
        for post_type, data in content_type_performance.items():
            if data['count'] > 0:
                avg_engagement = data['total_engagement'] / data['count']
                if avg_engagement > best_avg:
                    best_avg = avg_engagement
                    best_type = post_type
        
        if best_type:
            insights.append(AnalyticsInsight(
                type='content_type_performance',
                title=f'Best Performing Content Type: {best_type.title()}',
                description=f'Your {best_type} posts average {best_avg:.1f} engagements',
                value=best_avg,
                recommendation=f'Consider creating more {best_type} content'
            ))
        
        # Insight 2: Posting frequency analysis
        posting_days = set()
        for post in posts:
            if post.published_at:
                posting_days.add(post.published_at.date())
        
        avg_posts_per_day = len(posts) / max(1, len(posting_days))
        
        if avg_posts_per_day < 0.5:
            insights.append(AnalyticsInsight(
                type='posting_frequency',
                title='Low Posting Frequency',
                description=f'You post {avg_posts_per_day:.1f} times per day on average',
                value=avg_posts_per_day,
                recommendation='Consider increasing posting frequency to 1-2 posts per day'
            ))
        elif avg_posts_per_day > 3:
            insights.append(AnalyticsInsight(
                type='posting_frequency',
                title='High Posting Frequency',
                description=f'You post {avg_posts_per_day:.1f} times per day on average',
                value=avg_posts_per_day,
                recommendation='Consider reducing frequency to avoid audience fatigue'
            ))
        
        # Insight 3: Engagement trend
        if len(posts) >= 5:
            recent_posts = posts[:len(posts)//2]  # First half (most recent)
            older_posts = posts[len(posts)//2:]   # Second half (older)
            
            recent_avg = self._calculate_average_engagement_rate(recent_posts)
            older_avg = self._calculate_average_engagement_rate(older_posts)
            
            if recent_avg > older_avg * 1.2:
                insights.append(AnalyticsInsight(
                    type='engagement_trend',
                    title='Improving Engagement',
                    description=f'Recent posts perform {((recent_avg/older_avg - 1) * 100):.1f}% better',
                    value=recent_avg - older_avg,
                    recommendation='Keep up the great work with your current content strategy'
                ))
            elif recent_avg < older_avg * 0.8:
                insights.append(AnalyticsInsight(
                    type='engagement_trend',
                    title='Declining Engagement',
                    description=f'Recent posts perform {((1 - recent_avg/older_avg) * 100):.1f}% worse',
                    value=older_avg - recent_avg,
                    recommendation='Review and refresh your content strategy'
                ))
        
        return insights
    
    async def _generate_recommendations(self, posts: List[PostDraft], user_id: UUID) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if not posts:
            recommendations.append("Start posting regularly to build engagement")
            return recommendations
        
        # Analyze hashtag usage
        hashtag_counts = [len(post.hashtags or []) for post in posts]
        avg_hashtags = sum(hashtag_counts) / len(hashtag_counts)
        
        if avg_hashtags < 2:
            recommendations.append("Use 3-5 relevant hashtags to increase discoverability")
        elif avg_hashtags > 8:
            recommendations.append("Reduce hashtag count to 3-5 for better engagement")
        
        # Analyze content length
        content_lengths = [len(post.content) for post in posts]
        avg_length = sum(content_lengths) / len(content_lengths)
        
        if avg_length < 100:
            recommendations.append("Consider writing longer posts (150-300 words) for better engagement")
        elif avg_length > 500:
            recommendations.append("Try shorter posts (150-300 words) for better readability")
        
        # Analyze posting consistency
        if len(posts) < 7:  # Less than 1 post per day in a week
            recommendations.append("Post more consistently - aim for 3-5 posts per week")
        
        return recommendations
    
    def _calculate_average_engagement_rate(self, posts: List[PostDraft]) -> float:
        """Calculate average engagement rate across posts."""
        if not posts:
            return 0.0
        
        total_rate = 0.0
        valid_posts = 0
        
        for post in posts:
            if post.engagement_metrics:
                metrics = post.engagement_metrics
                views = metrics.get('views', 0)
                if views > 0:
                    engagement = (metrics.get('likes', 0) + 
                                metrics.get('comments', 0) + 
                                metrics.get('shares', 0))
                    rate = engagement / views
                    total_rate += rate
                    valid_posts += 1
        
        return total_rate / valid_posts if valid_posts > 0 else 0.0
    
    async def _find_best_performing_time(self, posts: List[PostDraft]) -> Optional[Dict[str, Any]]:
        """Find best performing time of day."""
        if not posts:
            return None
        
        time_performance = {}
        
        for post in posts:
            if post.published_at and post.engagement_metrics:
                hour = post.published_at.hour
                day_of_week = post.published_at.weekday()
                
                key = f"{day_of_week}_{hour}"
                
                if key not in time_performance:
                    time_performance[key] = {
                        'day_of_week': day_of_week,
                        'hour': hour,
                        'total_engagement': 0,
                        'post_count': 0
                    }
                
                engagement = (post.engagement_metrics.get('likes', 0) + 
                            post.engagement_metrics.get('comments', 0) + 
                            post.engagement_metrics.get('shares', 0))
                
                time_performance[key]['total_engagement'] += engagement
                time_performance[key]['post_count'] += 1
        
        # Find best time
        best_time = None
        best_avg = 0
        
        for time_data in time_performance.values():
            if time_data['post_count'] >= 2:  # Need at least 2 posts for reliability
                avg_engagement = time_data['total_engagement'] / time_data['post_count']
                if avg_engagement > best_avg:
                    best_avg = avg_engagement
                    best_time = {
                        'day_of_week': time_data['day_of_week'],
                        'hour': time_data['hour'],
                        'avg_engagement': avg_engagement
                    }
        
        return best_time
    
    def _calculate_engagement_trend(self, posts: List[PostDraft]) -> str:
        """Calculate engagement trend direction."""
        if len(posts) < 4:
            return 'stable'
        
        # Split posts into two halves
        mid_point = len(posts) // 2
        recent_posts = posts[:mid_point]
        older_posts = posts[mid_point:]
        
        recent_avg = self._calculate_average_engagement_rate(recent_posts)
        older_avg = self._calculate_average_engagement_rate(older_posts)
        
        if recent_avg > older_avg * 1.1:
            return 'improving'
        elif recent_avg < older_avg * 0.9:
            return 'declining'
        else:
            return 'stable'
    
    def _analyze_posting_frequency(self, posts: List[PostDraft]) -> str:
        """Analyze posting frequency trend."""
        if not posts:
            return 'stable'
        
        # Group posts by week
        weekly_counts = {}
        for post in posts:
            if post.published_at:
                # Get week start (Monday)
                week_start = post.published_at - timedelta(days=post.published_at.weekday())
                week_key = week_start.strftime('%Y-%W')
                weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
        
        if len(weekly_counts) < 2:
            return 'stable'
        
        # Calculate trend
        weeks = sorted(weekly_counts.keys())
        recent_weeks = weeks[-2:]
        older_weeks = weeks[:-2] if len(weeks) > 2 else weeks[:1]
        
        recent_avg = sum(weekly_counts[week] for week in recent_weeks) / len(recent_weeks)
        older_avg = sum(weekly_counts[week] for week in older_weeks) / len(older_weeks)
        
        if recent_avg > older_avg * 1.2:
            return 'increasing'
        elif recent_avg < older_avg * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _analyze_content_types(self, posts: List[PostDraft]) -> List[Dict[str, Any]]:
        """Analyze performance by content type."""
        type_performance = {}
        
        for post in posts:
            post_type = post.post_type or 'text'
            
            if post_type not in type_performance:
                type_performance[post_type] = {
                    'type': post_type,
                    'count': 0,
                    'total_engagement': 0,
                    'avg_engagement': 0
                }
            
            type_performance[post_type]['count'] += 1
            
            if post.engagement_metrics:
                engagement = (post.engagement_metrics.get('likes', 0) + 
                            post.engagement_metrics.get('comments', 0) + 
                            post.engagement_metrics.get('shares', 0))
                type_performance[post_type]['total_engagement'] += engagement
        
        # Calculate averages and sort
        for data in type_performance.values():
            if data['count'] > 0:
                data['avg_engagement'] = data['total_engagement'] / data['count']
        
        return sorted(type_performance.values(), key=lambda x: x['avg_engagement'], reverse=True)
    
    async def _analyze_optimal_times(self, posts: List[PostDraft]) -> List[Dict[str, Any]]:
        """Analyze optimal posting times."""
        return await self._find_best_performing_time(posts)
    
    def _analyze_hashtag_performance(self, posts: List[PostDraft]) -> Dict[str, Any]:
        """Analyze hashtag performance."""
        hashtag_performance = {}
        
        for post in posts:
            if post.hashtags and post.engagement_metrics:
                engagement = (post.engagement_metrics.get('likes', 0) + 
                            post.engagement_metrics.get('comments', 0) + 
                            post.engagement_metrics.get('shares', 0))
                
                for hashtag in post.hashtags:
                    if hashtag not in hashtag_performance:
                        hashtag_performance[hashtag] = {
                            'usage_count': 0,
                            'total_engagement': 0,
                            'avg_engagement': 0
                        }
                    
                    hashtag_performance[hashtag]['usage_count'] += 1
                    hashtag_performance[hashtag]['total_engagement'] += engagement
        
        # Calculate averages
        for hashtag, data in hashtag_performance.items():
            if data['usage_count'] > 0:
                data['avg_engagement'] = data['total_engagement'] / data['usage_count']
        
        # Return top performing hashtags
        sorted_hashtags = sorted(
            hashtag_performance.items(),
            key=lambda x: x[1]['avg_engagement'],
            reverse=True
        )
        
        return dict(sorted_hashtags[:10])  # Top 10 hashtags
    
    def _analyze_content_length(self, posts: List[PostDraft]) -> Dict[str, Any]:
        """Analyze content length performance."""
        length_buckets = {
            'short': {'range': '0-150', 'posts': [], 'avg_engagement': 0},
            'medium': {'range': '151-300', 'posts': [], 'avg_engagement': 0},
            'long': {'range': '301+', 'posts': [], 'avg_engagement': 0}
        }
        
        for post in posts:
            content_length = len(post.content)
            
            if content_length <= 150:
                bucket = 'short'
            elif content_length <= 300:
                bucket = 'medium'
            else:
                bucket = 'long'
            
            length_buckets[bucket]['posts'].append(post)
        
        # Calculate average engagement for each bucket
        for bucket, data in length_buckets.items():
            if data['posts']:
                total_engagement = 0
                for post in data['posts']:
                    if post.engagement_metrics:
                        engagement = (post.engagement_metrics.get('likes', 0) + 
                                    post.engagement_metrics.get('comments', 0) + 
                                    post.engagement_metrics.get('shares', 0))
                        total_engagement += engagement
                
                data['avg_engagement'] = total_engagement / len(data['posts'])
                data['post_count'] = len(data['posts'])
                del data['posts']  # Remove posts from output
        
        return length_buckets
    
    def _generate_trend_recommendations(
        self,
        posting_frequency_trend: str,
        engagement_trend: str,
        best_content_types: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on trends."""
        recommendations = []
        
        # Posting frequency recommendations
        if posting_frequency_trend == 'decreasing':
            recommendations.append("Your posting frequency is declining. Try to maintain consistent posting schedule.")
        elif posting_frequency_trend == 'increasing':
            recommendations.append("Great job increasing your posting frequency! Monitor engagement to ensure quality.")
        
        # Engagement trend recommendations
        if engagement_trend == 'declining':
            recommendations.append("Engagement is declining. Consider refreshing your content strategy or trying new formats.")
        elif engagement_trend == 'improving':
            recommendations.append("Engagement is improving! Continue with your current content strategy.")
        
        # Content type recommendations
        if best_content_types:
            best_type = best_content_types[0]
            recommendations.append(f"Your {best_type['type']} posts perform best. Consider creating more of this content type.")
        
        return recommendations
"""
Scheduling optimizer service for LinkedIn Presence Automation Application.

Optimizes post scheduling based on audience engagement patterns, time zones,
and posting frequency preferences with intelligent spacing algorithms.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.content_repository import PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import PostDraft, DraftStatus
from app.models.user import User
from app.schemas.recommendation_schemas import OptimalTimingResponse, SchedulingRecommendation

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """Represents an optimal time slot for posting."""
    datetime: datetime
    day_of_week: int
    hour: int
    minute: int
    expected_engagement: float
    confidence: float
    reasoning: str


@dataclass
class SchedulingConstraints:
    """Constraints for post scheduling."""
    max_posts_per_day: int = 2
    max_posts_per_week: int = 7
    min_hours_between_posts: int = 4
    preferred_time_zones: List[str] = None
    avoid_weekends: bool = False
    business_hours_only: bool = False


class SchedulingOptimizer:
    """
    Service for optimizing post scheduling based on engagement patterns.
    
    Analyzes user's audience engagement patterns, considers posting frequency
    preferences, and provides intelligent scheduling recommendations.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize scheduling optimizer.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.post_repo = PostDraftRepository(session)
        self.user_repo = UserRepository(session)
        
        # LinkedIn best practice time slots (UTC)
        self.default_optimal_times = [
            {'day': 1, 'hour': 9, 'minute': 0},   # Tuesday 9 AM
            {'day': 1, 'hour': 10, 'minute': 0},  # Tuesday 10 AM
            {'day': 2, 'hour': 9, 'minute': 0},   # Wednesday 9 AM
            {'day': 3, 'hour': 10, 'minute': 0},  # Thursday 10 AM
            {'day': 4, 'hour': 9, 'minute': 0},   # Friday 9 AM
        ]
    
    async def get_optimal_posting_schedule(
        self,
        user_id: UUID,
        posts_to_schedule: List[PostDraft],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SchedulingRecommendation]:
        """
        Get optimal posting schedule for multiple posts.
        
        Args:
            user_id: User ID to optimize schedule for
            posts_to_schedule: List of posts to schedule
            start_date: Start date for scheduling window
            end_date: End date for scheduling window
            
        Returns:
            List of scheduling recommendations
        """
        try:
            logger.info(f"Optimizing schedule for {len(posts_to_schedule)} posts for user {user_id}")
            
            # Get user profile and constraints
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            constraints = self._extract_user_constraints(user)
            
            # Set default scheduling window if not provided
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=14)  # 2 weeks
            
            # Get user's optimal time slots
            optimal_times = await self._get_user_optimal_times(user_id)
            
            # Get existing scheduled posts to avoid conflicts
            existing_posts = await self._get_existing_scheduled_posts(user_id, start_date, end_date)
            
            # Generate scheduling recommendations
            recommendations = await self._generate_schedule_recommendations(
                posts_to_schedule,
                optimal_times,
                existing_posts,
                constraints,
                start_date,
                end_date
            )
            
            logger.info(f"Generated {len(recommendations)} scheduling recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to optimize posting schedule: {str(e)}")
            return []
    
    async def find_next_optimal_time(
        self,
        user_id: UUID,
        after_time: Optional[datetime] = None
    ) -> OptimalTimingResponse:
        """
        Find the next optimal posting time for a user.
        
        Args:
            user_id: User ID to find optimal time for
            after_time: Find time after this datetime (default: now)
            
        Returns:
            OptimalTimingResponse with next optimal time
        """
        try:
            logger.info(f"Finding next optimal time for user {user_id}")
            
            if not after_time:
                after_time = datetime.utcnow()
            
            # Get user's optimal time slots
            optimal_times = await self._get_user_optimal_times(user_id)
            
            # Get user constraints
            user = await self.user_repo.get_by_id(user_id)
            constraints = self._extract_user_constraints(user) if user else SchedulingConstraints()
            
            # Find next available optimal time
            next_time = self._find_next_available_time(
                optimal_times, after_time, constraints
            )
            
            if next_time:
                return OptimalTimingResponse(
                    recommended_time=next_time.datetime,
                    day_of_week=next_time.day_of_week,
                    hour=next_time.hour,
                    minute=next_time.minute,
                    expected_engagement=next_time.expected_engagement,
                    confidence=next_time.confidence,
                    reasoning=next_time.reasoning,
                    alternative_times=self._get_alternative_times(optimal_times, next_time.datetime)
                )
            else:
                # Fallback to default time
                fallback_time = after_time + timedelta(hours=24)
                return OptimalTimingResponse(
                    recommended_time=fallback_time,
                    day_of_week=fallback_time.weekday(),
                    hour=fallback_time.hour,
                    minute=0,
                    expected_engagement=0.1,
                    confidence=0.3,
                    reasoning="Using fallback time - insufficient data for optimization",
                    alternative_times=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to find next optimal time: {str(e)}")
            # Return fallback response
            fallback_time = (after_time or datetime.utcnow()) + timedelta(hours=24)
            return OptimalTimingResponse(
                recommended_time=fallback_time,
                day_of_week=fallback_time.weekday(),
                hour=fallback_time.hour,
                minute=0,
                expected_engagement=0.1,
                confidence=0.2,
                reasoning=f"Error in optimization: {str(e)}",
                alternative_times=[]
            )
    
    async def validate_posting_schedule(
        self,
        user_id: UUID,
        proposed_times: List[datetime]
    ) -> Dict[str, Any]:
        """
        Validate a proposed posting schedule against user constraints.
        
        Args:
            user_id: User ID to validate schedule for
            proposed_times: List of proposed posting times
            
        Returns:
            Validation results with recommendations
        """
        try:
            logger.info(f"Validating schedule with {len(proposed_times)} posts for user {user_id}")
            
            # Get user constraints
            user = await self.user_repo.get_by_id(user_id)
            constraints = self._extract_user_constraints(user) if user else SchedulingConstraints()
            
            # Validate constraints
            validation_results = {
                'is_valid': True,
                'violations': [],
                'recommendations': [],
                'schedule_score': 0.0
            }
            
            # Check posting frequency constraints
            frequency_violations = self._check_frequency_constraints(proposed_times, constraints)
            validation_results['violations'].extend(frequency_violations)
            
            # Check spacing constraints
            spacing_violations = self._check_spacing_constraints(proposed_times, constraints)
            validation_results['violations'].extend(spacing_violations)
            
            # Check time preferences
            time_violations = self._check_time_preferences(proposed_times, constraints)
            validation_results['violations'].extend(time_violations)
            
            # Calculate overall score
            validation_results['schedule_score'] = self._calculate_schedule_score(
                proposed_times, constraints
            )
            
            # Set validity
            validation_results['is_valid'] = len(validation_results['violations']) == 0
            
            # Generate recommendations for improvements
            if validation_results['violations']:
                validation_results['recommendations'] = self._generate_schedule_improvements(
                    proposed_times, validation_results['violations'], constraints
                )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate posting schedule: {str(e)}")
            return {
                'is_valid': False,
                'violations': [f"Validation error: {str(e)}"],
                'recommendations': [],
                'schedule_score': 0.0
            }
    
    async def _get_user_optimal_times(self, user_id: UUID) -> List[TimeSlot]:
        """Get user's optimal posting times based on historical performance."""
        try:
            # Get user's historical posting performance
            historical_posts = await self.post_repo.get_recent_published_drafts(
                user_id=user_id, days=90, limit=100
            )
            
            if len(historical_posts) < 10:
                # Use default optimal times if insufficient data
                return self._get_default_time_slots()
            
            # Analyze performance by time
            time_performance = self._analyze_time_performance(historical_posts)
            
            # Convert to TimeSlot objects
            optimal_slots = []
            for time_data in time_performance:
                slot = TimeSlot(
                    datetime=datetime.utcnow(),  # Placeholder, will be calculated
                    day_of_week=time_data['day_of_week'],
                    hour=time_data['hour'],
                    minute=time_data.get('minute', 0),
                    expected_engagement=time_data['avg_engagement'],
                    confidence=time_data['confidence'],
                    reasoning=f"Based on {time_data['post_count']} historical posts"
                )
                optimal_slots.append(slot)
            
            return optimal_slots[:10]  # Return top 10 slots
            
        except Exception as e:
            logger.warning(f"Failed to get user optimal times: {str(e)}")
            return self._get_default_time_slots()
    
    def _get_default_time_slots(self) -> List[TimeSlot]:
        """Get default optimal time slots based on LinkedIn best practices."""
        slots = []
        
        for time_config in self.default_optimal_times:
            slot = TimeSlot(
                datetime=datetime.utcnow(),  # Placeholder
                day_of_week=time_config['day'],
                hour=time_config['hour'],
                minute=time_config['minute'],
                expected_engagement=0.12,  # Default engagement rate
                confidence=0.3,  # Lower confidence for default
                reasoning="LinkedIn best practice timing"
            )
            slots.append(slot)
        
        return slots
    
    def _analyze_time_performance(self, posts: List[PostDraft]) -> List[Dict[str, Any]]:
        """Analyze posting performance by time of day and day of week."""
        time_buckets = {}
        
        for post in posts:
            if not post.published_at or not post.engagement_metrics:
                continue
            
            # Create time bucket key
            day_of_week = post.published_at.weekday()
            hour = post.published_at.hour
            key = f"{day_of_week}_{hour}"
            
            if key not in time_buckets:
                time_buckets[key] = {
                    'day_of_week': day_of_week,
                    'hour': hour,
                    'posts': [],
                    'total_engagement': 0
                }
            
            # Calculate engagement
            metrics = post.engagement_metrics
            engagement = (
                metrics.get('likes', 0) +
                metrics.get('comments', 0) * 2 +  # Weight comments higher
                metrics.get('shares', 0) * 3      # Weight shares highest
            )
            
            time_buckets[key]['posts'].append(post)
            time_buckets[key]['total_engagement'] += engagement
        
        # Calculate averages and confidence
        time_performance = []
        for bucket_data in time_buckets.values():
            post_count = len(bucket_data['posts'])
            if post_count >= 2:  # Need at least 2 posts for reliability
                avg_engagement = bucket_data['total_engagement'] / post_count
                confidence = min(1.0, post_count / 10)  # Higher confidence with more data
                
                time_performance.append({
                    'day_of_week': bucket_data['day_of_week'],
                    'hour': bucket_data['hour'],
                    'minute': 0,
                    'avg_engagement': avg_engagement,
                    'post_count': post_count,
                    'confidence': confidence
                })
        
        # Sort by average engagement
        time_performance.sort(key=lambda x: x['avg_engagement'], reverse=True)
        return time_performance
    
    def _extract_user_constraints(self, user: User) -> SchedulingConstraints:
        """Extract scheduling constraints from user preferences."""
        preferences = user.preferences or {}
        
        # Get posting frequency preference
        frequency = preferences.get('posting_frequency', 'daily')
        
        if frequency == 'multiple_daily':
            max_per_day = 3
            max_per_week = 15
        elif frequency == 'daily':
            max_per_day = 1
            max_per_week = 7
        elif frequency == 'few_times_week':
            max_per_day = 1
            max_per_week = 4
        else:  # weekly or less
            max_per_day = 1
            max_per_week = 2
        
        return SchedulingConstraints(
            max_posts_per_day=max_per_day,
            max_posts_per_week=max_per_week,
            min_hours_between_posts=preferences.get('min_hours_between_posts', 4),
            avoid_weekends=preferences.get('avoid_weekends', False),
            business_hours_only=preferences.get('business_hours_only', False)
        )
    
    async def _get_existing_scheduled_posts(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[PostDraft]:
        """Get existing scheduled posts in the time window."""
        try:
            # Get scheduled posts in date range
            scheduled_posts = await self.post_repo.get_drafts_by_status(
                user_id=user_id,
                status=DraftStatus.SCHEDULED,
                limit=100
            )
            
            # Filter by date range
            filtered_posts = []
            for post in scheduled_posts:
                if (post.scheduled_for and 
                    start_date <= post.scheduled_for <= end_date):
                    filtered_posts.append(post)
            
            return filtered_posts
            
        except Exception as e:
            logger.warning(f"Failed to get existing scheduled posts: {str(e)}")
            return []
    
    async def _generate_schedule_recommendations(
        self,
        posts_to_schedule: List[PostDraft],
        optimal_times: List[TimeSlot],
        existing_posts: List[PostDraft],
        constraints: SchedulingConstraints,
        start_date: datetime,
        end_date: datetime
    ) -> List[SchedulingRecommendation]:
        """Generate scheduling recommendations for posts."""
        recommendations = []
        
        # Create list of occupied time slots
        occupied_times = [post.scheduled_for for post in existing_posts if post.scheduled_for]
        
        # Sort posts by priority (could be based on score, urgency, etc.)
        sorted_posts = sorted(posts_to_schedule, key=lambda p: getattr(p, 'priority_score', 0.5), reverse=True)
        
        current_time = start_date
        
        for post in sorted_posts:
            # Find next available optimal time
            recommended_time = self._find_next_available_time_for_post(
                optimal_times, current_time, occupied_times, constraints
            )
            
            if recommended_time and recommended_time.datetime <= end_date:
                recommendation = SchedulingRecommendation(
                    post_id=post.id,
                    recommended_time=recommended_time.datetime,
                    expected_engagement=recommended_time.expected_engagement,
                    confidence=recommended_time.confidence,
                    reasoning=recommended_time.reasoning,
                    alternative_times=self._get_alternative_times(
                        optimal_times, recommended_time.datetime, occupied_times
                    )
                )
                
                recommendations.append(recommendation)
                occupied_times.append(recommended_time.datetime)
                current_time = recommended_time.datetime + timedelta(hours=constraints.min_hours_between_posts)
            else:
                # Could not find suitable time in window
                logger.warning(f"Could not find suitable time for post {post.id}")
        
        return recommendations
    
    def _find_next_available_time(
        self,
        optimal_times: List[TimeSlot],
        after_time: datetime,
        constraints: SchedulingConstraints
    ) -> Optional[TimeSlot]:
        """Find next available optimal time after given time."""
        # Generate candidate times for next 30 days
        candidates = []
        
        for days_ahead in range(30):
            candidate_date = after_time.date() + timedelta(days=days_ahead)
            
            for time_slot in optimal_times:
                candidate_datetime = datetime.combine(
                    candidate_date,
                    datetime.min.time().replace(hour=time_slot.hour, minute=time_slot.minute)
                )
                
                # Skip if before after_time
                if candidate_datetime <= after_time:
                    continue
                
                # Check constraints
                if self._time_meets_constraints(candidate_datetime, constraints):
                    candidate_slot = TimeSlot(
                        datetime=candidate_datetime,
                        day_of_week=candidate_datetime.weekday(),
                        hour=time_slot.hour,
                        minute=time_slot.minute,
                        expected_engagement=time_slot.expected_engagement,
                        confidence=time_slot.confidence,
                        reasoning=time_slot.reasoning
                    )
                    candidates.append(candidate_slot)
        
        # Return earliest candidate
        if candidates:
            return min(candidates, key=lambda x: x.datetime)
        
        return None
    
    def _find_next_available_time_for_post(
        self,
        optimal_times: List[TimeSlot],
        after_time: datetime,
        occupied_times: List[datetime],
        constraints: SchedulingConstraints
    ) -> Optional[TimeSlot]:
        """Find next available time avoiding occupied slots."""
        candidate_time = self._find_next_available_time(optimal_times, after_time, constraints)
        
        if not candidate_time:
            return None
        
        # Check for conflicts with occupied times
        while candidate_time:
            conflict = False
            for occupied in occupied_times:
                time_diff = abs((candidate_time.datetime - occupied).total_seconds() / 3600)
                if time_diff < constraints.min_hours_between_posts:
                    conflict = True
                    break
            
            if not conflict:
                return candidate_time
            
            # Find next time after conflict
            next_after = candidate_time.datetime + timedelta(hours=constraints.min_hours_between_posts)
            candidate_time = self._find_next_available_time(optimal_times, next_after, constraints)
        
        return None
    
    def _time_meets_constraints(self, candidate_time: datetime, constraints: SchedulingConstraints) -> bool:
        """Check if candidate time meets user constraints."""
        # Check weekend constraint
        if constraints.avoid_weekends and candidate_time.weekday() >= 5:
            return False
        
        # Check business hours constraint
        if constraints.business_hours_only:
            if candidate_time.hour < 9 or candidate_time.hour > 17:
                return False
        
        return True
    
    def _get_alternative_times(
        self,
        optimal_times: List[TimeSlot],
        primary_time: datetime,
        occupied_times: Optional[List[datetime]] = None
    ) -> List[Dict[str, Any]]:
        """Get alternative posting times."""
        alternatives = []
        occupied_times = occupied_times or []
        
        for time_slot in optimal_times[:3]:  # Top 3 alternatives
            # Calculate next occurrence of this time slot
            days_ahead = 0
            while days_ahead < 7:  # Look within next week
                candidate = primary_time.replace(
                    hour=time_slot.hour,
                    minute=time_slot.minute,
                    second=0,
                    microsecond=0
                ) + timedelta(days=days_ahead)
                
                # Skip if too close to primary time or occupied times
                if candidate != primary_time:
                    too_close = any(
                        abs((candidate - occupied).total_seconds()) < 3600  # 1 hour buffer
                        for occupied in occupied_times + [primary_time]
                    )
                    
                    if not too_close:
                        alternatives.append({
                            'datetime': candidate,
                            'expected_engagement': time_slot.expected_engagement,
                            'confidence': time_slot.confidence,
                            'reasoning': f"Alternative optimal time: {time_slot.reasoning}"
                        })
                        break
                
                days_ahead += 1
        
        return alternatives
    
    def _check_frequency_constraints(
        self,
        proposed_times: List[datetime],
        constraints: SchedulingConstraints
    ) -> List[str]:
        """Check posting frequency constraints."""
        violations = []
        
        # Group by day
        daily_counts = {}
        for post_time in proposed_times:
            date_key = post_time.date()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        # Check daily limits
        for date, count in daily_counts.items():
            if count > constraints.max_posts_per_day:
                violations.append(
                    f"Too many posts on {date}: {count} > {constraints.max_posts_per_day}"
                )
        
        # Group by week
        weekly_counts = {}
        for post_time in proposed_times:
            # Get Monday of the week
            week_start = post_time - timedelta(days=post_time.weekday())
            week_key = week_start.date()
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
        
        # Check weekly limits
        for week, count in weekly_counts.items():
            if count > constraints.max_posts_per_week:
                violations.append(
                    f"Too many posts in week of {week}: {count} > {constraints.max_posts_per_week}"
                )
        
        return violations
    
    def _check_spacing_constraints(
        self,
        proposed_times: List[datetime],
        constraints: SchedulingConstraints
    ) -> List[str]:
        """Check spacing constraints between posts."""
        violations = []
        
        # Sort times
        sorted_times = sorted(proposed_times)
        
        # Check spacing between consecutive posts
        for i in range(1, len(sorted_times)):
            time_diff = (sorted_times[i] - sorted_times[i-1]).total_seconds() / 3600
            if time_diff < constraints.min_hours_between_posts:
                violations.append(
                    f"Posts too close together: {time_diff:.1f}h < {constraints.min_hours_between_posts}h"
                )
        
        return violations
    
    def _check_time_preferences(
        self,
        proposed_times: List[datetime],
        constraints: SchedulingConstraints
    ) -> List[str]:
        """Check time preference constraints."""
        violations = []
        
        for post_time in proposed_times:
            # Check weekend constraint
            if constraints.avoid_weekends and post_time.weekday() >= 5:
                violations.append(f"Post scheduled on weekend: {post_time}")
            
            # Check business hours constraint
            if constraints.business_hours_only:
                if post_time.hour < 9 or post_time.hour > 17:
                    violations.append(f"Post outside business hours: {post_time}")
        
        return violations
    
    def _calculate_schedule_score(
        self,
        proposed_times: List[datetime],
        constraints: SchedulingConstraints
    ) -> float:
        """Calculate overall score for the proposed schedule."""
        if not proposed_times:
            return 0.0
        
        score = 1.0
        
        # Penalize frequency violations
        frequency_violations = self._check_frequency_constraints(proposed_times, constraints)
        score -= len(frequency_violations) * 0.2
        
        # Penalize spacing violations
        spacing_violations = self._check_spacing_constraints(proposed_times, constraints)
        score -= len(spacing_violations) * 0.15
        
        # Penalize time preference violations
        time_violations = self._check_time_preferences(proposed_times, constraints)
        score -= len(time_violations) * 0.1
        
        return max(0.0, score)
    
    def _generate_schedule_improvements(
        self,
        proposed_times: List[datetime],
        violations: List[str],
        constraints: SchedulingConstraints
    ) -> List[str]:
        """Generate recommendations to improve the schedule."""
        recommendations = []
        
        # Analyze violation types and suggest improvements
        if any('Too many posts' in v for v in violations):
            recommendations.append("Reduce posting frequency or spread posts over more days")
        
        if any('too close together' in v for v in violations):
            recommendations.append(
                f"Space posts at least {constraints.min_hours_between_posts} hours apart"
            )
        
        if any('weekend' in v for v in violations):
            recommendations.append("Move weekend posts to weekdays for better engagement")
        
        if any('business hours' in v for v in violations):
            recommendations.append("Schedule posts during business hours (9 AM - 5 PM)")
        
        return recommendations
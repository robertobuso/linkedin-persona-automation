"""
Recommendation service for LinkedIn Presence Automation Application.

Provides intelligent content scoring, ranking, and posting recommendations
using multi-factor analysis and user engagement patterns.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import AnalyticsService
from app.services.engagement_predictor import EngagementPredictor
from app.services.scheduling_optimizer import SchedulingOptimizer
from app.repositories.content_repository import ContentItemRepository, PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import ContentItem, PostDraft, DraftStatus
from app.models.user import User
from app.schemas.recommendation_schemas import (
    ScoredRecommendation, RecommendationRequest, RecommendationResponse,
    ContentScore, OptimalTimingResponse
)

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for content scoring components."""
    source_credibility: float = 0.25
    topic_relevance: float = 0.30
    timeliness: float = 0.20
    engagement_potential: float = 0.25


class RecommendationError(Exception):
    """Base exception for recommendation service errors."""
    pass


class RecommendationService:
    """
    Service for generating intelligent content recommendations.
    
    Analyzes content items and provides scoring, ranking, and optimal
    posting recommendations based on user preferences and engagement patterns.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize recommendation service.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.analytics_service = AnalyticsService(session)
        self.engagement_predictor = EngagementPredictor(session)
        self.scheduling_optimizer = SchedulingOptimizer(session)
        self.content_repo = ContentItemRepository(session)
        self.post_repo = PostDraftRepository(session)
        self.user_repo = UserRepository(session)
        
        # Default scoring weights
        self.default_weights = ScoringWeights()
        
        # Cache for user-specific weights
        self._user_weights_cache: Dict[str, ScoringWeights] = {}
    
    async def score_content(
        self,
        draft: PostDraft,
        user_profile: User
    ) -> ScoredRecommendation:
        """
        Score content draft and generate recommendation.
        
        Args:
            draft: Post draft to score
            user_profile: User profile for personalization
            
        Returns:
            ScoredRecommendation with score and action recommendation
        """
        try:
            logger.info(f"Scoring content draft {draft.id} for user {user_profile.id}")
            
            # Get user-specific scoring weights
            weights = await self._get_user_scoring_weights(user_profile.id)
            
            # Calculate individual scores
            relevance_score = await self._calculate_topic_relevance(draft, user_profile)
            source_score = await self._get_source_credibility(draft.source_content_id)
            timeliness_score = self._calculate_timeliness(draft.created_at)
            engagement_score = await self.engagement_predictor.predict_engagement(draft, user_profile)
            
            # Calculate weighted composite score
            composite_score = (
                relevance_score * weights.topic_relevance +
                source_score * weights.source_credibility +
                timeliness_score * weights.timeliness +
                engagement_score.predicted_engagement_rate * weights.engagement_potential
            )
            
            # Determine recommended action
            recommendation = self._determine_action(composite_score, user_profile)
            
            # Generate explanation
            explanation = self._generate_explanation(
                relevance_score, source_score, timeliness_score,
                engagement_score.predicted_engagement_rate, recommendation
            )
            
            # Create content score breakdown
            content_score = ContentScore(
                relevance_score=relevance_score,
                source_credibility=source_score,
                timeliness_score=timeliness_score,
                engagement_potential=engagement_score.predicted_engagement_rate,
                composite_score=composite_score,
                confidence=engagement_score.confidence
            )
            
            return ScoredRecommendation(
                draft_id=draft.id,
                score=composite_score,
                action=recommendation,
                reasoning=explanation,
                content_score=content_score,
                optimal_timing=await self._get_optimal_timing_for_draft(draft, user_profile),
                estimated_performance=engagement_score.dict(),
                scored_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Content scoring failed for draft {draft.id}: {str(e)}")
            raise RecommendationError(f"Failed to score content: {str(e)}")
    
    async def get_optimal_posting_times(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get optimal posting times for a user.
        
        Args:
            user_id: User ID to get optimal times for
            
        Returns:
            List of optimal time slots with performance data
        """
        try:
            logger.info(f"Getting optimal posting times for user {user_id}")
            
            # Get user's historical engagement data
            historical_data = await self.analytics_service.get_user_engagement_history(
                user_id, days=90
            )
            
            # If insufficient historical data, use default optimal times
            if len(historical_data.get('posts', [])) < 10:
                return self._get_default_optimal_times()
            
            # Analyze performance by time
            time_performance = await self._analyze_performance_by_time(historical_data)
            
            # Find peak engagement times
            optimal_slots = self._find_peak_engagement_times(time_performance)
            
            return optimal_slots
            
        except Exception as e:
            logger.error(f"Failed to get optimal posting times for user {user_id}: {str(e)}")
            return self._get_default_optimal_times()
    
    async def get_content_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """
        Get content recommendations for a user.
        
        Args:
            request: Recommendation request with user preferences
            
        Returns:
            RecommendationResponse with scored and ranked content
        """
        try:
            logger.info(f"Getting content recommendations for user {request.user_id}")
            
            # Get user profile
            user = await self.user_repo.get_by_id(request.user_id)
            if not user:
                raise RecommendationError(f"User {request.user_id} not found")
            
            # Get available drafts
            drafts = await self.post_repo.get_drafts_by_status(
                user_id=request.user_id,
                status=DraftStatus.READY,
                limit=request.limit or 10
            )
            
            if not drafts:
                return RecommendationResponse(
                    user_id=request.user_id,
                    recommendations=[],
                    optimal_times=await self.get_optimal_posting_times(request.user_id),
                    generated_at=datetime.utcnow()
                )
            
            # Score all drafts
            scored_recommendations = []
            for draft in drafts:
                try:
                    scored_rec = await self.score_content(draft, user)
                    
                    # Apply filters if specified
                    if request.min_score and scored_rec.score < request.min_score:
                        continue
                    
                    if request.content_types and draft.post_type not in request.content_types:
                        continue
                    
                    scored_recommendations.append(scored_rec)
                    
                except Exception as e:
                    logger.warning(f"Failed to score draft {draft.id}: {str(e)}")
                    continue
            
            # Sort by score (highest first)
            scored_recommendations.sort(key=lambda x: x.score, reverse=True)
            
            # Limit results
            if request.limit:
                scored_recommendations = scored_recommendations[:request.limit]
            
            return RecommendationResponse(
                user_id=request.user_id,
                recommendations=scored_recommendations,
                optimal_times=await self.get_optimal_posting_times(request.user_id),
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Failed to get content recommendations: {str(e)}")
            raise RecommendationError(f"Failed to get recommendations: {str(e)}")
    
    async def update_scoring_weights(
        self,
        user_id: UUID,
        feedback_data: Dict[str, Any]
    ) -> None:
        """
        Update scoring weights based on user feedback.
        
        Args:
            user_id: User ID to update weights for
            feedback_data: Feedback data with performance metrics
        """
        try:
            logger.info(f"Updating scoring weights for user {user_id}")
            
            # Get current weights
            current_weights = await self._get_user_scoring_weights(user_id)
            
            # Analyze feedback and adjust weights
            adjusted_weights = self._adjust_weights_from_feedback(
                current_weights, feedback_data
            )
            
            # Store updated weights
            await self._store_user_weights(user_id, adjusted_weights)
            
            # Clear cache
            if str(user_id) in self._user_weights_cache:
                del self._user_weights_cache[str(user_id)]
            
            logger.info(f"Updated scoring weights for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to update scoring weights: {str(e)}")
    
    async def _calculate_topic_relevance(
        self,
        draft: PostDraft,
        user_profile: User
    ) -> float:
        """Calculate topic relevance score for content."""
        try:
            # Get user's interests and preferences
            user_interests = user_profile.preferences.get('content_categories', [])
            user_expertise = user_profile.tone_profile.get('expertise_areas', [])
            
            if not user_interests and not user_expertise:
                return 0.7  # Default relevance if no preferences
            
            # Analyze content for topic matching
            content_lower = draft.content.lower()
            
            # Check for interest matches
            interest_matches = 0
            for interest in user_interests:
                if interest.lower() in content_lower:
                    interest_matches += 1
            
            # Check for expertise matches
            expertise_matches = 0
            for expertise in user_expertise:
                if expertise.lower() in content_lower:
                    expertise_matches += 1
            
            # Calculate relevance score
            total_categories = len(user_interests) + len(user_expertise)
            if total_categories == 0:
                return 0.7
            
            total_matches = interest_matches + expertise_matches
            relevance_score = min(1.0, (total_matches / total_categories) + 0.3)
            
            return relevance_score
            
        except Exception as e:
            logger.warning(f"Failed to calculate topic relevance: {str(e)}")
            return 0.5  # Default score on error
    
    async def _get_source_credibility(self, source_content_id: Optional[UUID]) -> float:
        """Get source credibility score."""
        try:
            if not source_content_id:
                return 0.8  # Default for manually created content
            
            # Get source content
            content_item = await self.content_repo.get_by_id(source_content_id)
            if not content_item:
                return 0.5
            
            # Get source information
            source = content_item.source
            if not source:
                return 0.5
            
            # Calculate credibility based on source metrics
            credibility_factors = []
            
            # Success rate factor
            if source.total_items_found > 0:
                success_rate = source.total_items_processed / source.total_items_found
                credibility_factors.append(success_rate)
            
            # Failure rate factor
            failure_penalty = min(0.5, source.consecutive_failures * 0.1)
            credibility_factors.append(1.0 - failure_penalty)
            
            # Source type factor
            source_type_scores = {
                'rss_feed': 0.8,
                'website': 0.7,
                'newsletter': 0.9,
                'manual': 0.8,
                'linkedin': 0.6
            }
            credibility_factors.append(source_type_scores.get(source.source_type, 0.5))
            
            # Calculate average credibility
            credibility_score = sum(credibility_factors) / len(credibility_factors)
            return min(1.0, max(0.0, credibility_score))
            
        except Exception as e:
            logger.warning(f"Failed to get source credibility: {str(e)}")
            return 0.5
    
    def _calculate_timeliness(self, created_at: datetime) -> float:
        """Calculate timeliness score based on content age."""
        try:
            now = datetime.utcnow()
            age_hours = (now - created_at).total_seconds() / 3600
            
            # Optimal posting window: 0-24 hours = 1.0 score
            # Decreasing score after 24 hours
            if age_hours <= 24:
                return 1.0
            elif age_hours <= 48:
                return 0.8
            elif age_hours <= 72:
                return 0.6
            elif age_hours <= 168:  # 1 week
                return 0.4
            else:
                return 0.2
                
        except Exception as e:
            logger.warning(f"Failed to calculate timeliness: {str(e)}")
            return 0.5
    
    def _determine_action(self, composite_score: float, user_profile: User) -> str:
        """Determine recommended action based on score."""
        try:
            # Get user's auto-posting preference
            auto_posting = user_profile.is_auto_posting_enabled()
            
            if composite_score >= 0.8:
                return 'post_now' if auto_posting else 'ready_to_post'
            elif composite_score >= 0.6:
                return 'schedule_optimal' if auto_posting else 'schedule_later'
            elif composite_score >= 0.4:
                return 'review_and_edit'
            else:
                return 'skip'
                
        except Exception as e:
            logger.warning(f"Failed to determine action: {str(e)}")
            return 'review_and_edit'
    
    def _generate_explanation(
        self,
        relevance_score: float,
        source_score: float,
        timeliness_score: float,
        engagement_score: float,
        recommendation: str
    ) -> str:
        """Generate human-readable explanation for recommendation."""
        explanations = []
        
        # Relevance explanation
        if relevance_score >= 0.8:
            explanations.append("High relevance to your interests and expertise")
        elif relevance_score >= 0.6:
            explanations.append("Good relevance to your content preferences")
        else:
            explanations.append("Limited relevance to your focus areas")
        
        # Source explanation
        if source_score >= 0.8:
            explanations.append("High-credibility source")
        elif source_score >= 0.6:
            explanations.append("Reliable source")
        else:
            explanations.append("Source credibility could be better")
        
        # Timeliness explanation
        if timeliness_score >= 0.8:
            explanations.append("Fresh, timely content")
        elif timeliness_score >= 0.6:
            explanations.append("Recent content")
        else:
            explanations.append("Older content, may be less timely")
        
        # Engagement explanation
        if engagement_score >= 0.8:
            explanations.append("High engagement potential")
        elif engagement_score >= 0.6:
            explanations.append("Good engagement potential")
        else:
            explanations.append("Moderate engagement potential")
        
        # Action explanation
        action_explanations = {
            'post_now': "Recommended for immediate posting",
            'ready_to_post': "Ready for posting when convenient",
            'schedule_optimal': "Schedule for optimal engagement time",
            'schedule_later': "Consider scheduling for better timing",
            'review_and_edit': "Review and potentially edit before posting",
            'skip': "Consider skipping or significantly revising"
        }
        
        explanation = ". ".join(explanations)
        explanation += f". {action_explanations.get(recommendation, 'Review recommended')}"
        
        return explanation
    
    async def _get_optimal_timing_for_draft(
        self,
        draft: PostDraft,
        user_profile: User
    ) -> Optional[Dict[str, Any]]:
        """Get optimal timing recommendation for specific draft."""
        try:
            optimal_times = await self.get_optimal_posting_times(user_profile.id)
            
            if not optimal_times:
                return None
            
            # Get next optimal time
            now = datetime.utcnow()
            
            for time_slot in optimal_times:
                # Calculate next occurrence of this time
                next_time = self._calculate_next_occurrence(
                    time_slot['hour'], time_slot['minute'], time_slot['day_of_week']
                )
                
                if next_time > now:
                    return {
                        'recommended_time': next_time,
                        'day_of_week': time_slot['day_of_week'],
                        'hour': time_slot['hour'],
                        'expected_engagement': time_slot.get('avg_engagement_rate', 0.1),
                        'confidence': time_slot.get('confidence', 0.5)
                    }
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get optimal timing: {str(e)}")
            return None
    
    def _calculate_next_occurrence(
        self,
        hour: int,
        minute: int,
        day_of_week: Optional[int] = None
    ) -> datetime:
        """Calculate next occurrence of specified time."""
        now = datetime.utcnow()
        
        if day_of_week is None:
            # Next occurrence today or tomorrow
            next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= now:
                next_time += timedelta(days=1)
        else:
            # Next occurrence on specific day of week
            days_ahead = day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            next_time = now + timedelta(days=days_ahead)
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_time
    
    async def _get_user_scoring_weights(self, user_id: UUID) -> ScoringWeights:
        """Get user-specific scoring weights."""
        user_key = str(user_id)
        
        # Check cache first
        if user_key in self._user_weights_cache:
            return self._user_weights_cache[user_key]
        
        try:
            # Try to load from user preferences
            user = await self.user_repo.get_by_id(user_id)
            if user and user.preferences:
                weights_data = user.preferences.get('scoring_weights', {})
                
                weights = ScoringWeights(
                    source_credibility=weights_data.get('source_credibility', self.default_weights.source_credibility),
                    topic_relevance=weights_data.get('topic_relevance', self.default_weights.topic_relevance),
                    timeliness=weights_data.get('timeliness', self.default_weights.timeliness),
                    engagement_potential=weights_data.get('engagement_potential', self.default_weights.engagement_potential)
                )
                
                # Cache the weights
                self._user_weights_cache[user_key] = weights
                return weights
        
        except Exception as e:
            logger.warning(f"Failed to load user weights: {str(e)}")
        
        # Return default weights
        self._user_weights_cache[user_key] = self.default_weights
        return self.default_weights
    
    def _adjust_weights_from_feedback(
        self,
        current_weights: ScoringWeights,
        feedback_data: Dict[str, Any]
    ) -> ScoringWeights:
        """Adjust scoring weights based on feedback data."""
        # Simple learning algorithm - adjust weights based on performance
        adjustment_factor = 0.1  # Conservative adjustment
        
        # Get performance metrics
        accepted_posts = feedback_data.get('accepted_posts', [])
        rejected_posts = feedback_data.get('rejected_posts', [])
        
        if not accepted_posts and not rejected_posts:
            return current_weights
        
        # Calculate average scores for accepted vs rejected
        def get_avg_scores(posts):
            if not posts:
                return {}
            
            totals = {'relevance': 0, 'source': 0, 'timeliness': 0, 'engagement': 0}
            for post in posts:
                scores = post.get('scores', {})
                for key in totals:
                    totals[key] += scores.get(key, 0)
            
            return {key: total / len(posts) for key, total in totals.items()}
        
        accepted_avg = get_avg_scores(accepted_posts)
        rejected_avg = get_avg_scores(rejected_posts)
        
        # Adjust weights based on which factors correlate with acceptance
        new_weights = ScoringWeights(
            source_credibility=current_weights.source_credibility,
            topic_relevance=current_weights.topic_relevance,
            timeliness=current_weights.timeliness,
            engagement_potential=current_weights.engagement_potential
        )
        
        if accepted_avg and rejected_avg:
            # Increase weight for factors that are higher in accepted posts
            if accepted_avg.get('relevance', 0) > rejected_avg.get('relevance', 0):
                new_weights.topic_relevance = min(0.5, current_weights.topic_relevance + adjustment_factor)
            
            if accepted_avg.get('source', 0) > rejected_avg.get('source', 0):
                new_weights.source_credibility = min(0.5, current_weights.source_credibility + adjustment_factor)
            
            if accepted_avg.get('timeliness', 0) > rejected_avg.get('timeliness', 0):
                new_weights.timeliness = min(0.5, current_weights.timeliness + adjustment_factor)
            
            if accepted_avg.get('engagement', 0) > rejected_avg.get('engagement', 0):
                new_weights.engagement_potential = min(0.5, current_weights.engagement_potential + adjustment_factor)
        
        # Normalize weights to sum to 1.0
        total_weight = (new_weights.source_credibility + new_weights.topic_relevance + 
                       new_weights.timeliness + new_weights.engagement_potential)
        
        if total_weight > 0:
            new_weights.source_credibility /= total_weight
            new_weights.topic_relevance /= total_weight
            new_weights.timeliness /= total_weight
            new_weights.engagement_potential /= total_weight
        
        return new_weights
    
    async def _store_user_weights(self, user_id: UUID, weights: ScoringWeights) -> None:
        """Store user-specific scoring weights."""
        try:
            weights_data = {
                'source_credibility': weights.source_credibility,
                'topic_relevance': weights.topic_relevance,
                'timeliness': weights.timeliness,
                'engagement_potential': weights.engagement_potential,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Update user preferences
            user = await self.user_repo.get_by_id(user_id)
            if user:
                current_prefs = user.preferences or {}
                current_prefs['scoring_weights'] = weights_data
                await self.user_repo.update_preferences(user_id, current_prefs)
                
        except Exception as e:
            logger.error(f"Failed to store user weights: {str(e)}")
    
    async def _analyze_performance_by_time(
        self,
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze posting performance by time of day and day of week."""
        posts = historical_data.get('posts', [])
        
        # Initialize time performance tracking
        time_performance = {}
        
        for post in posts:
            published_at = post.get('published_at')
            if not published_at:
                continue
            
            try:
                pub_time = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                hour = pub_time.hour
                day_of_week = pub_time.weekday()
                
                key = f"{day_of_week}_{hour}"
                
                if key not in time_performance:
                    time_performance[key] = {
                        'day_of_week': day_of_week,
                        'hour': hour,
                        'posts': [],
                        'total_engagement': 0,
                        'avg_engagement': 0
                    }
                
                engagement = post.get('engagement_metrics', {})
                total_eng = (engagement.get('likes', 0) + 
                           engagement.get('comments', 0) + 
                           engagement.get('shares', 0))
                
                time_performance[key]['posts'].append(post)
                time_performance[key]['total_engagement'] += total_eng
                
            except Exception as e:
                logger.warning(f"Failed to parse post time: {str(e)}")
                continue
        
        # Calculate averages
        for key, data in time_performance.items():
            if data['posts']:
                data['avg_engagement'] = data['total_engagement'] / len(data['posts'])
                data['post_count'] = len(data['posts'])
        
        return time_performance
    
    def _find_peak_engagement_times(
        self,
        time_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find peak engagement times from performance data."""
        # Sort by average engagement
        sorted_times = sorted(
            time_performance.values(),
            key=lambda x: x.get('avg_engagement', 0),
            reverse=True
        )
        
        # Filter for times with sufficient data (at least 2 posts)
        significant_times = [
            time_data for time_data in sorted_times
            if time_data.get('post_count', 0) >= 2
        ]
        
        # Return top 5 times
        optimal_times = []
        for time_data in significant_times[:5]:
            optimal_times.append({
                'day_of_week': time_data['day_of_week'],
                'hour': time_data['hour'],
                'minute': 0,  # Default to top of hour
                'avg_engagement_rate': time_data['avg_engagement'] / 100,  # Normalize
                'post_count': time_data['post_count'],
                'confidence': min(1.0, time_data['post_count'] / 10)  # Higher confidence with more data
            })
        
        return optimal_times
    
    def _get_default_optimal_times(self) -> List[Dict[str, Any]]:
        """Get default optimal posting times based on LinkedIn best practices."""
        return [
            {
                'day_of_week': 1,  # Tuesday
                'hour': 9,
                'minute': 0,
                'avg_engagement_rate': 0.12,
                'post_count': 0,
                'confidence': 0.3,
                'source': 'linkedin_best_practices'
            },
            {
                'day_of_week': 1,  # Tuesday
                'hour': 10,
                'minute': 0,
                'avg_engagement_rate': 0.15,
                'post_count': 0,
                'confidence': 0.3,
                'source': 'linkedin_best_practices'
            },
            {
                'day_of_week': 2,  # Wednesday
                'hour': 9,
                'minute': 0,
                'avg_engagement_rate': 0.13,
                'post_count': 0,
                'confidence': 0.3,
                'source': 'linkedin_best_practices'
            },
            {
                'day_of_week': 3,  # Thursday
                'hour': 10,
                'minute': 0,
                'avg_engagement_rate': 0.14,
                'post_count': 0,
                'confidence': 0.3,
                'source': 'linkedin_best_practices'
            },
            {
                'day_of_week': 4,  # Friday
                'hour': 9,
                'minute': 0,
                'avg_engagement_rate': 0.11,
                'post_count': 0,
                'confidence': 0.3,
                'source': 'linkedin_best_practices'
            }
        ]
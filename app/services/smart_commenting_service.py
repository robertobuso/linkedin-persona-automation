"""
Smart Commenting Service for LinkedIn Presence Automation Application.

Phase 3: Integrates with existing AI services to provide intelligent commenting
capabilities using existing tone analysis, engagement prediction, and safety patterns.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import AIService
from app.services.tone_analyzer import ToneAnalyzer
from app.services.engagement_predictor import EngagementPredictor
from app.services.recommendation_service import RecommendationService
from app.services.linkedin_api_service import LinkedInAPIService
from app.repositories.engagement_repository import EngagementRepository
from app.repositories.user_repository import UserRepository
from app.models.engagement import EngagementOpportunity, EngagementStatus
from app.models.user import User
from app.schemas.ai_schemas import CommentGenerationRequest, CommentGenerationResponse, ToneProfile

logger = logging.getLogger(__name__)


@dataclass
class CommentingRules:
    """Smart commenting rules and constraints."""
    max_comments_per_day: int = 10
    max_comments_per_hour: int = 3
    min_hours_between_comments: int = 2
    min_hours_between_same_author: int = 24
    avoid_sensitive_topics: List[str] = None
    require_manual_approval: bool = False
    respect_user_frequency_limits: bool = True
    
    def __post_init__(self):
        if self.avoid_sensitive_topics is None:
            self.avoid_sensitive_topics = [
                'politics', 'religion', 'controversial', 'personal attack'
            ]


@dataclass
class CommentResult:
    """Result of comment generation and posting."""
    success: bool
    comment_text: Optional[str] = None
    linkedin_comment_id: Optional[str] = None
    confidence_score: float = 0.0
    reasoning: str = ""
    error_message: Optional[str] = None
    alternative_comments: List[str] = None


class SmartCommentingService:
    """
    Service for intelligent LinkedIn commenting using existing AI infrastructure.
    
    Integrates with existing services:
    - tone_analyzer.py for personalized comment style
    - engagement_predictor.py for success prediction
    - recommendation_service.py for opportunity scoring
    - ai_service.py for content generation
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize smart commenting service."""
        self.session = session
        self.ai_service = AIService()
        self.tone_analyzer = ToneAnalyzer()
        self.engagement_predictor = EngagementPredictor(session)
        self.recommendation_service = RecommendationService(session)
        self.linkedin_api = LinkedInAPIService(session)
        self.engagement_repo = EngagementRepository(session)
        self.user_repo = UserRepository(session)
        
        # Default commenting rules (can be overridden by user preferences)
        self.default_rules = CommentingRules()
    
    async def should_comment_on_post(
        self,
        opportunity: EngagementOpportunity,
        user: User,
        custom_rules: Optional[CommentingRules] = None
    ) -> Tuple[bool, str]:
        """
        Determine if user should comment on post using existing scoring algorithms.
        
        Args:
            opportunity: Engagement opportunity to evaluate
            user: User profile for personalization
            custom_rules: Optional custom commenting rules
            
        Returns:
            Tuple of (should_comment, reasoning)
        """
        try:
            rules = custom_rules or self._get_user_commenting_rules(user)
            
            # Check 1: User frequency limits using existing constraint patterns
            frequency_check = await self._check_frequency_limits(user.id, rules)
            if not frequency_check[0]:
                return frequency_check
            
            # Check 2: Content safety using existing safety patterns
            safety_check = await self._check_content_safety(opportunity, rules)
            if not safety_check[0]:
                return safety_check
            
            # Check 3: Timing optimization using existing scheduling patterns
            timing_check = self._check_optimal_timing(opportunity)
            if not timing_check[0]:
                return timing_check
            
            # Check 4: Duplicate/similar content avoidance
            duplicate_check = await self._check_duplicate_commenting(opportunity, user.id)
            if not duplicate_check[0]:
                return duplicate_check
            
            # Check 5: User's engagement capacity
            capacity_check = await self._check_engagement_capacity(user.id, rules)
            if not capacity_check[0]:
                return capacity_check
            
            # All checks passed
            return True, "All commenting criteria met"
            
        except Exception as e:
            logger.error(f"Error in should_comment_on_post: {str(e)}")
            return False, f"Error evaluating commenting criteria: {str(e)}"
    
    async def generate_personalized_comment(
        self,
        opportunity: EngagementOpportunity,
        user: User,
        comment_approach: str = "thoughtful"
    ) -> CommentGenerationResponse:
        """
        Generate personalized comment using existing AI services.
        
        Args:
            opportunity: Engagement opportunity containing post data
            user: User profile for personalization
            comment_approach: Commenting approach (thoughtful, expert_insight, etc.)
            
        Returns:
            CommentGenerationResponse with generated comment
        """
        try:
            logger.info(f"Generating comment for opportunity {opportunity.id}")
            
            # Get user's tone profile using existing tone analyzer
            tone_profile = await self._get_user_tone_profile(user)
            
            # Create comment generation request
            comment_request = CommentGenerationRequest(
                post_content=opportunity.target_content or "",
                post_author=opportunity.target_author,
                tone_profile=tone_profile,
                engagement_type=comment_approach,
                max_length=150
            )
            
            # Generate comment using existing AI service
            comment_response = await self.ai_service.generate_comment_draft(comment_request)
            
            # Enhance with personalization
            enhanced_comment = await self._enhance_comment_with_personalization(
                comment_response.comment, opportunity, user, comment_approach
            )
            
            # Update response with enhanced comment
            comment_response.comment = enhanced_comment
            
            # Predict engagement success using existing predictor
            success_prediction = await self._predict_comment_success(
                enhanced_comment, opportunity, user
            )
            comment_response.confidence_score = success_prediction
            
            logger.info(f"Generated comment with confidence {success_prediction:.2f}")
            return comment_response
            
        except Exception as e:
            logger.error(f"Failed to generate personalized comment: {str(e)}")
            return CommentGenerationResponse(
                comment="Thank you for sharing this insight!",
                engagement_type=comment_approach,
                confidence_score=0.3,
                alternative_comments=[],
                processing_time=0.0,
                model_used="fallback",
                tokens_used=0,
                cost=0.0
            )
    
    async def execute_comment_opportunity(
        self,
        opportunity_id: UUID,
        user_id: UUID,
        override_approval: bool = False
    ) -> CommentResult:
        """
        Execute commenting opportunity with full workflow.
        
        Args:
            opportunity_id: Engagement opportunity ID
            user_id: User ID
            override_approval: Skip approval requirements
            
        Returns:
            CommentResult with execution details
        """
        try:
            logger.info(f"Executing comment opportunity {opportunity_id}")
            
            # Get opportunity and user
            opportunity = await self.engagement_repo.get_by_id(opportunity_id)
            if not opportunity or opportunity.user_id != user_id:
                return CommentResult(
                    success=False,
                    error_message="Opportunity not found or access denied"
                )
            
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.has_valid_linkedin_token():
                return CommentResult(
                    success=False,
                    error_message="User not found or invalid LinkedIn token"
                )
            
            # Check if should comment
            should_comment, reasoning = await self.should_comment_on_post(opportunity, user)
            if not should_comment:
                await self.engagement_repo.skip_opportunity(
                    opportunity_id, reason=reasoning
                )
                return CommentResult(
                    success=False,
                    reasoning=reasoning,
                    error_message="Commenting criteria not met"
                )
            
            # Generate comment
            comment_approach = opportunity.context_tags[0] if opportunity.context_tags else "thoughtful"
            comment_response = await self.generate_personalized_comment(
                opportunity, user, comment_approach
            )
            
            # Check if requires manual approval
            rules = self._get_user_commenting_rules(user)
            if rules.require_manual_approval and not override_approval:
                # Store for manual review
                await self.engagement_repo.update(
                    opportunity_id,
                    status=EngagementStatus.PENDING,
                    suggested_comment=comment_response.comment,
                    ai_analysis={
                        **(opportunity.ai_analysis or {}),
                        "generated_comment": comment_response.comment,
                        "confidence_score": comment_response.confidence_score,
                        "requires_approval": True,
                        "generated_at": datetime.utcnow().isoformat()
                    }
                )
                
                return CommentResult(
                    success=True,
                    comment_text=comment_response.comment,
                    confidence_score=comment_response.confidence_score,
                    reasoning="Comment generated, pending manual approval"
                )
            
            # Post comment to LinkedIn
            try:
                linkedin_response = await self.linkedin_api.create_comment(
                    user=user,
                    post_urn=opportunity.target_id,
                    comment_text=comment_response.comment
                )
                
                # Mark opportunity as completed
                await self.engagement_repo.mark_as_completed(
                    opportunity_id,
                    execution_result={
                        "comment_posted": comment_response.comment,
                        "linkedin_comment_id": linkedin_response.get("id"),
                        "confidence_score": comment_response.confidence_score,
                        "engagement_type": comment_approach,
                        "posted_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Track performance for learning
                await self._track_comment_performance(
                    opportunity, comment_response, linkedin_response
                )
                
                return CommentResult(
                    success=True,
                    comment_text=comment_response.comment,
                    linkedin_comment_id=linkedin_response.get("id"),
                    confidence_score=comment_response.confidence_score,
                    reasoning="Comment posted successfully",
                    alternative_comments=comment_response.alternative_comments
                )
                
            except Exception as e:
                # Mark opportunity as failed
                await self.engagement_repo.mark_as_failed(
                    opportunity_id,
                    error_message=str(e)
                )
                
                return CommentResult(
                    success=False,
                    comment_text=comment_response.comment,
                    confidence_score=comment_response.confidence_score,
                    error_message=f"Failed to post comment: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"Failed to execute comment opportunity: {str(e)}")
            return CommentResult(
                success=False,
                error_message=f"Execution failed: {str(e)}"
            )
    
    async def get_optimal_timing(
        self,
        opportunity: EngagementOpportunity,
        user: User
    ) -> datetime:
        """
        Get optimal timing for commenting using existing scheduling patterns.
        
        Args:
            opportunity: Engagement opportunity
            user: User profile
            
        Returns:
            Optimal datetime for commenting
        """
        try:
            # Use existing scheduling optimizer patterns
            base_time = datetime.utcnow()
            
            # Factor 1: Post age (comment sooner for newer posts)
            if opportunity.created_at:
                post_age = (base_time - opportunity.created_at).total_seconds() / 3600
                if post_age < 2:
                    # Comment within 30 minutes for very new posts
                    optimal_time = base_time + timedelta(minutes=30)
                elif post_age < 6:
                    # Comment within 2 hours for recent posts
                    optimal_time = base_time + timedelta(hours=1)
                else:
                    # Comment within 4 hours for older posts
                    optimal_time = base_time + timedelta(hours=2)
            else:
                optimal_time = base_time + timedelta(hours=1)
            
            # Factor 2: User's optimal posting times
            user_optimal_times = await self.recommendation_service.get_optimal_posting_times(user.id)
            if user_optimal_times:
                # Adjust to next optimal time if significantly better
                next_optimal = self._find_next_optimal_time(optimal_time, user_optimal_times)
                if next_optimal and (next_optimal - optimal_time).total_seconds() < 3600:
                    optimal_time = next_optimal
            
            # Factor 3: User's commenting frequency limits
            rules = self._get_user_commenting_rules(user)
            last_comment_time = await self._get_last_comment_time(user.id)
            if last_comment_time:
                min_next_time = last_comment_time + timedelta(hours=rules.min_hours_between_comments)
                if optimal_time < min_next_time:
                    optimal_time = min_next_time
            
            return optimal_time
            
        except Exception as e:
            logger.error(f"Failed to calculate optimal timing: {str(e)}")
            return datetime.utcnow() + timedelta(hours=1)
    
    async def _check_frequency_limits(
        self,
        user_id: UUID,
        rules: CommentingRules
    ) -> Tuple[bool, str]:
        """Check user's commenting frequency limits."""
        try:
            now = datetime.utcnow()
            
            # Check daily limit
            daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            daily_comments = await self._count_comments_since(user_id, daily_start)
            
            if daily_comments >= rules.max_comments_per_day:
                return False, f"Daily comment limit reached ({daily_comments}/{rules.max_comments_per_day})"
            
            # Check hourly limit
            hourly_start = now.replace(minute=0, second=0, microsecond=0)
            hourly_comments = await self._count_comments_since(user_id, hourly_start)
            
            if hourly_comments >= rules.max_comments_per_hour:
                return False, f"Hourly comment limit reached ({hourly_comments}/{rules.max_comments_per_hour})"
            
            # Check minimum time between comments
            last_comment_time = await self._get_last_comment_time(user_id)
            if last_comment_time:
                time_since_last = (now - last_comment_time).total_seconds() / 3600
                if time_since_last < rules.min_hours_between_comments:
                    return False, f"Minimum time between comments not met ({time_since_last:.1f}h < {rules.min_hours_between_comments}h)"
            
            return True, "Frequency limits satisfied"
            
        except Exception as e:
            logger.error(f"Error checking frequency limits: {str(e)}")
            return False, f"Error checking frequency: {str(e)}"
    
    async def _check_content_safety(
        self,
        opportunity: EngagementOpportunity,
        rules: CommentingRules
    ) -> Tuple[bool, str]:
        """Check content safety using existing safety patterns."""
        try:
            content = (opportunity.target_content or "").lower()
            
            # Check for sensitive topics
            for sensitive_topic in rules.avoid_sensitive_topics:
                if sensitive_topic.lower() in content:
                    return False, f"Content contains sensitive topic: {sensitive_topic}"
            
            # Check for negative sentiment
            if any(word in content for word in ['angry', 'hate', 'terrible', 'awful', 'disgusting']):
                return False, "Content has negative sentiment"
            
            # Check for potential controversy
            if any(word in content for word in ['controversial', 'debate', 'argue', 'disagree strongly']):
                return False, "Content appears controversial"
            
            return True, "Content safety checks passed"
            
        except Exception as e:
            logger.error(f"Error checking content safety: {str(e)}")
            return False, f"Error checking safety: {str(e)}"
    
    def _check_optimal_timing(self, opportunity: EngagementOpportunity) -> Tuple[bool, str]:
        """Check if timing is optimal for commenting."""
        try:
            now = datetime.utcnow()
            
            # Avoid commenting during off-hours (late night/early morning)
            if now.hour < 6 or now.hour > 22:
                return False, "Outside optimal engagement hours"
            
            # Check if post is too old for effective commenting
            if opportunity.created_at:
                post_age_hours = (now - opportunity.created_at).total_seconds() / 3600
                if post_age_hours > 48:
                    return False, f"Post too old for effective commenting ({post_age_hours:.1f}h)"
            
            return True, "Timing is optimal"
            
        except Exception as e:
            logger.error(f"Error checking timing: {str(e)}")
            return False, f"Error checking timing: {str(e)}"
    
    async def _check_duplicate_commenting(
        self,
        opportunity: EngagementOpportunity,
        user_id: UUID
    ) -> Tuple[bool, str]:
        """Check for duplicate or similar commenting."""
        try:
            # Check if already commented on this post
            existing_comment = await self.engagement_repo.find_one_by(
                user_id=user_id,
                target_id=opportunity.target_id,
                engagement_type="comment",
                status="completed"
            )
            
            if existing_comment:
                return False, "Already commented on this post"
            
            # Check if recently commented on same author
            if opportunity.target_author:
                rules = self._get_user_commenting_rules_by_id(user_id)
                since_time = datetime.utcnow() - timedelta(hours=rules.min_hours_between_same_author)
                
                recent_author_comment = await self.engagement_repo.find_one_by(
                    user_id=user_id,
                    target_author=opportunity.target_author,
                    engagement_type="comment",
                    status="completed"
                )
                
                if recent_author_comment and recent_author_comment.completed_at > since_time:
                    return False, f"Recently commented on post by {opportunity.target_author}"
            
            return True, "No duplicate commenting detected"
            
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return True, "Duplicate check skipped due to error"
    
    async def _check_engagement_capacity(
        self,
        user_id: UUID,
        rules: CommentingRules
    ) -> Tuple[bool, str]:
        """Check user's engagement capacity."""
        try:
            # Check pending engagements
            pending_count = await self.engagement_repo.count(
                user_id=user_id,
                status="pending"
            )
            
            if pending_count > 20:  # Reasonable limit
                return False, f"Too many pending engagements ({pending_count})"
            
            # Check user's overall engagement health
            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                return False, "User account not active"
            
            return True, "Engagement capacity available"
            
        except Exception as e:
            logger.error(f"Error checking engagement capacity: {str(e)}")
            return True, "Capacity check skipped due to error"
    
    async def _get_user_tone_profile(self, user: User) -> ToneProfile:
        """Get user's tone profile using existing tone analyzer."""
        try:
            # Use existing tone profile from user record
            if user.tone_profile:
                return ToneProfile(
                    writing_style=user.tone_profile.get("writing_style", "professional"),
                    tone=user.tone_profile.get("tone", "informative"),
                    personality_traits=user.tone_profile.get("personality_traits", ["analytical"]),
                    industry_focus=user.tone_profile.get("industry_focus", []),
                    expertise_areas=user.tone_profile.get("expertise_areas", []),
                    communication_preferences=user.tone_profile.get("communication_preferences", {})
                )
            
            # Fallback to analyzing user's tone if no profile exists
            return await self.tone_analyzer.analyze_user_tone(self.session, str(user.id))
            
        except Exception as e:
            logger.error(f"Error getting tone profile: {str(e)}")
            return ToneProfile(
                writing_style="professional",
                tone="informative",
                personality_traits=["thoughtful"],
                industry_focus=[],
                expertise_areas=[],
                communication_preferences={}
            )
    
    async def _enhance_comment_with_personalization(
        self,
        base_comment: str,
        opportunity: EngagementOpportunity,
        user: User,
        comment_approach: str
    ) -> str:
        """Enhance comment with user personalization."""
        try:
            # Add user-specific touches based on approach
            if comment_approach == "expert_insight":
                # Add expertise-based perspective
                expertise_areas = user.tone_profile.get("expertise_areas", [])
                if expertise_areas:
                    expertise_context = f"From my experience in {expertise_areas[0]}, "
                    if not base_comment.startswith(expertise_context):
                        base_comment = expertise_context + base_comment.lower()
            
            elif comment_approach == "supportive":
                # Make comment more supportive and encouraging
                supportive_starters = [
                    "Great point!", "I completely agree.", "This resonates with me.",
                    "Excellent insight!", "Thank you for sharing this."
                ]
                if not any(base_comment.startswith(starter) for starter in supportive_starters):
                    base_comment = f"Great point! {base_comment}"
            
            elif comment_approach == "engaging_question":
                # Ensure comment ends with an engaging question
                if "?" not in base_comment:
                    question_endings = [
                        "What has been your experience with this?",
                        "How have you approached this challenge?",
                        "What's your take on this?",
                        "Have you seen similar results?"
                    ]
                    base_comment += f" {question_endings[0]}"
            
            # Ensure appropriate length
            if len(base_comment) > 150:
                sentences = base_comment.split('. ')
                base_comment = '. '.join(sentences[:2])
                if not base_comment.endswith('.'):
                    base_comment += '.'
            
            return base_comment
            
        except Exception as e:
            logger.error(f"Error enhancing comment: {str(e)}")
            return base_comment
    
    async def _predict_comment_success(
        self,
        comment_text: str,
        opportunity: EngagementOpportunity,
        user: User
    ) -> float:
        """Predict comment success using existing engagement predictor."""
        try:
            # Use existing prediction patterns
            base_score = 0.5
            
            # Factor 1: Comment quality indicators
            if "?" in comment_text:
                base_score += 0.1  # Questions generate engagement
            if len(comment_text.split()) > 10:
                base_score += 0.1  # Substantial comments
            if any(word in comment_text.lower() for word in ['insight', 'experience', 'agree', 'interesting']):
                base_score += 0.1  # Engaging language
            
            # Factor 2: Opportunity quality
            if opportunity.relevance_score:
                relevance_factor = opportunity.relevance_score / 100
                base_score += relevance_factor * 0.2
            
            # Factor 3: User's historical performance
            # This would use existing analytics patterns
            user_performance = 0.7  # Placeholder - would calculate from history
            base_score += user_performance * 0.1
            
            return min(1.0, base_score)
            
        except Exception as e:
            logger.error(f"Error predicting comment success: {str(e)}")
            return 0.5
    
    async def _track_comment_performance(
        self,
        opportunity: EngagementOpportunity,
        comment_response: CommentGenerationResponse,
        linkedin_response: Dict[str, Any]
    ) -> None:
        """Track comment performance for learning."""
        try:
            # Use existing analytics patterns to track performance
            performance_data = {
                "opportunity_id": str(opportunity.id),
                "comment_text": comment_response.comment,
                "confidence_score": comment_response.confidence_score,
                "linkedin_comment_id": linkedin_response.get("id"),
                "posted_at": datetime.utcnow().isoformat(),
                "engagement_metrics": {}  # Will be updated later
            }
            
            # Store for analytics (would integrate with existing analytics service)
            logger.info(f"Tracked comment performance for opportunity {opportunity.id}")
            
        except Exception as e:
            logger.error(f"Error tracking comment performance: {str(e)}")
    
    def _get_user_commenting_rules(self, user: User) -> CommentingRules:
        """Get user's commenting rules from preferences."""
        try:
            user_prefs = user.preferences or {}
            commenting_prefs = user_prefs.get('commenting_preferences', {})
            
            return CommentingRules(
                max_comments_per_day=commenting_prefs.get('max_comments_per_day', 10),
                max_comments_per_hour=commenting_prefs.get('max_comments_per_hour', 3),
                min_hours_between_comments=commenting_prefs.get('min_hours_between_comments', 2),
                min_hours_between_same_author=commenting_prefs.get('min_hours_between_same_author', 24),
                avoid_sensitive_topics=commenting_prefs.get('avoid_sensitive_topics', self.default_rules.avoid_sensitive_topics),
                require_manual_approval=commenting_prefs.get('require_manual_approval', False),
                respect_user_frequency_limits=commenting_prefs.get('respect_user_frequency_limits', True)
            )
            
        except Exception as e:
            logger.error(f"Error getting user commenting rules: {str(e)}")
            return self.default_rules
    
    def _get_user_commenting_rules_by_id(self, user_id: UUID) -> CommentingRules:
        """Get commenting rules by user ID (synchronous helper)."""
        return self.default_rules  # Simplified for this example
    
    async def _count_comments_since(self, user_id: UUID, since_time: datetime) -> int:
        """Count comments posted since given time."""
        try:
            return await self.engagement_repo.count(
                user_id=user_id,
                engagement_type="comment",
                status="completed",
                # Would need to add time filtering to repository
            )
        except Exception as e:
            logger.error(f"Error counting comments: {str(e)}")
            return 0
    
    async def _get_last_comment_time(self, user_id: UUID) -> Optional[datetime]:
        """Get timestamp of user's last comment."""
        try:
            recent_comments = await self.engagement_repo.find_by(
                user_id=user_id,
                engagement_type="comment",
                status="completed"
            )
            
            if recent_comments:
                latest_comment = max(recent_comments, key=lambda c: c.completed_at or datetime.min)
                return latest_comment.completed_at
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting last comment time: {str(e)}")
            return None
    
    def _find_next_optimal_time(
        self,
        current_time: datetime,
        optimal_times: List[Dict[str, Any]]
    ) -> Optional[datetime]:
        """Find next optimal time from user's optimal posting schedule."""
        try:
            if not optimal_times:
                return None
            
            # Find next optimal time slot
            for time_slot in optimal_times:
                slot_time = current_time.replace(
                    hour=time_slot.get('hour', 9),
                    minute=time_slot.get('minute', 0),
                    second=0,
                    microsecond=0
                )
                
                if slot_time > current_time:
                    return slot_time
            
            # If no time today, try tomorrow
            tomorrow = current_time + timedelta(days=1)
            first_slot = optimal_times[0]
            return tomorrow.replace(
                hour=first_slot.get('hour', 9),
                minute=first_slot.get('minute', 0),
                second=0,
                microsecond=0
            )
            
        except Exception as e:
            logger.error(f"Error finding next optimal time: {str(e)}")
            return None
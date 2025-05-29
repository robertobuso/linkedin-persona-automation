"""
Deep content analysis service for LinkedIn Presence Automation Application.

Implements Phase 3 of the LLM-first content discovery pipeline:
- Structured LLM-based deep analysis of selected articles
- Extract insights, hashtags, LinkedIn angles, key points
- Store results in ContentItem database table
- Feedback tracking and performance analytics
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentItem, ContentStatus
from app.models.user import User, ContentSelection
from app.models.user_content_preferences import UserContentPreferences
from app.repositories.content_repository import ContentItemRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_content_preferences_repository import UserContentPreferencesRepository

logger = logging.getLogger(__name__)


@dataclass
class ContentAnalysisResult:
    """Result of deep content analysis."""
    content_item_id: UUID
    insights: List[str]
    key_points: List[str]
    linkedin_angles: List[str]
    suggested_hashtags: List[str]
    target_audience: str
    engagement_potential: float
    content_themes: List[str]
    actionable_takeaways: List[str]
    relevance_score: float
    selection_reason: str
    analysis_metadata: Dict[str, Any]


@dataclass
class FeedbackMetrics:
    """Feedback metrics for content performance tracking."""
    content_item_id: UUID
    user_interactions: Dict[str, Any]  # clicks, time_spent, saved, shared
    draft_created: bool
    draft_published: bool
    linkedin_engagement: Optional[Dict[str, int]]  # likes, comments, shares
    user_rating: Optional[int]  # 1-5 star rating
    feedback_timestamp: datetime


class DeepContentAnalysisService:
    """
    Service for deep analysis of content using LLM with structured output.
    
    Provides comprehensive content analysis including:
    - Key insights and themes extraction
    - LinkedIn-specific angles and opportunities
    - Hashtag suggestions
    - Engagement potential scoring
    - Performance feedback tracking
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize deep content analysis service.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.content_repo = ContentItemRepository(session)
        self.user_repo = UserRepository(session)
        self.preferences_repo = UserContentPreferencesRepository(session)
    
    async def analyze_content_deeply(
        self,
        content_item_id: UUID,
        user_id: UUID,
        selected_article_data: Optional[Dict[str, Any]] = None
    ) -> ContentAnalysisResult:
        """
        Perform deep analysis of a content item using LLM.
        
        Args:
            content_item_id: ID of content item to analyze
            user_id: User ID for personalized analysis
            selected_article_data: Optional pre-selected article data
            
        Returns:
            ContentAnalysisResult with comprehensive analysis
        """
        try:
            logger.info(f"Starting deep analysis for content {content_item_id} and user {user_id}")
            
            # Get or create content item
            content_item = await self._get_or_create_content_item(
                content_item_id, selected_article_data
            )
            
            # Get user context
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user_preferences = await self.preferences_repo.get_active_preferences_for_user(user_id)
            
            # Build analysis prompt
            analysis_prompt = await self._build_deep_analysis_prompt(
                content_item, user, user_preferences
            )
            
            # Call LLM for structured analysis
            analysis_response = await self._invoke_llm_with_structured_output(analysis_prompt)
            
            # Parse and validate response
            analysis_result = await self._parse_analysis_response(
                analysis_response, content_item_id, user_id
            )
            
            # Store results in database
            await self._store_analysis_results(content_item, analysis_result)
            
            logger.info(f"Deep analysis completed for content {content_item_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Deep content analysis failed for {content_item_id}: {str(e)}")
            raise
    
    async def batch_analyze_selected_content(
        self,
        user_id: UUID,
        selected_articles: List[Dict[str, Any]]
    ) -> List[ContentAnalysisResult]:
        """
        Perform batch deep analysis of selected articles.
        
        Args:
            user_id: User ID for personalized analysis
            selected_articles: List of selected article data
            
        Returns:
            List of ContentAnalysisResult objects
        """
        try:
            logger.info(f"Starting batch analysis for {len(selected_articles)} articles for user {user_id}")
            
            results = []
            
            for article_data in selected_articles:
                try:
                    # Create content item from article data
                    content_item = await self._create_content_item_from_article(article_data, user_id)
                    
                    # Perform deep analysis
                    analysis_result = await self.analyze_content_deeply(
                        content_item.id, user_id, article_data
                    )
                    
                    results.append(analysis_result)
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze article '{article_data.get('title', 'Unknown')}': {str(e)}")
                    continue
            
            logger.info(f"Batch analysis completed: {len(results)} successful, {len(selected_articles) - len(results)} failed")
            return results
            
        except Exception as e:
            logger.error(f"Batch content analysis failed for user {user_id}: {str(e)}")
            raise
    
    async def track_content_feedback(
        self,
        content_item_id: UUID,
        user_id: UUID,
        feedback_data: Dict[str, Any]
    ) -> FeedbackMetrics:
        """
        Track user feedback and performance metrics for content.
        
        Args:
            content_item_id: Content item ID
            user_id: User ID
            feedback_data: Dictionary with feedback information
            
        Returns:
            FeedbackMetrics object
        """
        try:
            logger.debug(f"Tracking feedback for content {content_item_id} from user {user_id}")
            
            # Create feedback metrics
            feedback_metrics = FeedbackMetrics(
                content_item_id=content_item_id,
                user_interactions=feedback_data.get("interactions", {}),
                draft_created=feedback_data.get("draft_created", False),
                draft_published=feedback_data.get("draft_published", False),
                linkedin_engagement=feedback_data.get("linkedin_engagement"),
                user_rating=feedback_data.get("user_rating"),
                feedback_timestamp=datetime.utcnow()
            )
            
            # Update content item with feedback
            await self._update_content_with_feedback(content_item_id, feedback_metrics)
            
            # Update user preferences based on positive/negative feedback
            if feedback_data.get("learn_from_feedback", True):
                await self._update_preferences_from_feedback(
                    user_id, content_item_id, feedback_metrics
                )
            
            logger.debug(f"Feedback tracking completed for content {content_item_id}")
            return feedback_metrics
            
        except Exception as e:
            logger.error(f"Feedback tracking failed for {content_item_id}: {str(e)}")
            raise
    
    async def get_content_performance_analytics(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get analytics about content performance and user engagement.
        
        Args:
            user_id: User ID to get analytics for
            days: Number of days to analyze
            
        Returns:
            Dictionary with performance analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get analyzed content items for user
            analyzed_items = await self._get_analyzed_content_for_user(user_id, since_date)
            
            if not analyzed_items:
                return {
                    "message": "No analyzed content found for the specified period",
                    "period_days": days,
                    "generated_at": datetime.utcnow().isoformat()
                }
            
            # Calculate analytics
            analytics = await self._calculate_performance_analytics(analyzed_items, days)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Performance analytics failed for user {user_id}: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _build_deep_analysis_prompt(
        self,
        content_item: ContentItem,
        user: User,
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build comprehensive analysis prompt for LLM."""
        
        user_context = self._build_user_context_for_analysis(user, user_preferences)
        
        prompt = f"""You are an expert LinkedIn content strategist and analyst. Perform a comprehensive analysis of the following article for a LinkedIn professional.

ARTICLE TO ANALYZE:
Title: {content_item.title}
Author: {content_item.author or 'Unknown'}
URL: {content_item.url}
Content: {content_item.content[:2000] if content_item.content else 'No content available'}

USER CONTEXT:
{user_context}

ANALYSIS REQUIREMENTS:
Provide a structured analysis with the following components:

1. KEY INSIGHTS: Extract 3-5 key insights that would be valuable for the user
2. MAIN THEMES: Identify 2-4 main themes or topics covered
3. LINKEDIN ANGLES: Suggest 3-4 specific angles for LinkedIn posts/discussions
4. ACTIONABLE TAKEAWAYS: List 3-5 specific, actionable items the user could implement
5. TARGET AUDIENCE: Describe who would benefit most from this content
6. HASHTAG SUGGESTIONS: Recommend 5-8 relevant LinkedIn hashtags
7. ENGAGEMENT POTENTIAL: Rate the potential for LinkedIn engagement (0.0-1.0)
8. RELEVANCE SCORE: Overall relevance score for this user (0.0-1.0)
9. SELECTION REASON: Why this content is valuable for this specific user

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
    "key_insights": ["insight 1", "insight 2", "..."],
    "main_themes": ["theme 1", "theme 2", "..."],
    "linkedin_angles": ["angle 1", "angle 2", "..."],
    "actionable_takeaways": ["takeaway 1", "takeaway 2", "..."],
    "target_audience": "description of target audience",
    "suggested_hashtags": ["#hashtag1", "#hashtag2", "..."],
    "engagement_potential": 0.85,
    "relevance_score": 0.90,
    "selection_reason": "detailed explanation of why this content is valuable for this user",
    "content_quality": "assessment of content quality and credibility",
    "linkedin_suitability": "how well this content fits LinkedIn's professional context"
}}

Focus on providing actionable, LinkedIn-specific insights that match the user's professional interests and goals."""
        
        return prompt
    
    def _build_user_context_for_analysis(
        self,
        user: User,
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build detailed user context for analysis."""
        context_parts = []
        
        if user_preferences:
            if user_preferences.job_role:
                context_parts.append(f"Job Role: {user_preferences.job_role}")
            
            if user_preferences.industry:
                context_parts.append(f"Industry: {user_preferences.industry}")
            
            if user_preferences.experience_level:
                context_parts.append(f"Experience Level: {user_preferences.experience_level}")
            
            if user_preferences.primary_interests:
                context_parts.append(f"Primary Interests: {', '.join(user_preferences.primary_interests)}")
            
            if user_preferences.secondary_interests:
                context_parts.append(f"Secondary Interests: {', '.join(user_preferences.secondary_interests)}")
            
            if user_preferences.linkedin_post_style:
                context_parts.append(f"LinkedIn Style Preference: {user_preferences.linkedin_post_style}")
            
            if user_preferences.custom_prompt:
                context_parts.append(f"Custom Instructions: {user_preferences.custom_prompt}")
        else:
            # Fallback to basic user info
            context_parts.append("Basic LinkedIn professional (no detailed preferences available)")
        
        return "\n".join(context_parts) if context_parts else "General LinkedIn professional"
    
    async def _invoke_llm_with_structured_output(self, prompt: str) -> Dict[str, Any]:
        """
        Invoke LLM with structured output for analysis.
        
        This is a placeholder for actual LLM integration.
        In production, this would call the AI service.
        """
        # TODO: Replace with actual LLM service call
        logger.debug("Invoking LLM for deep content analysis (mock implementation)")
        
        # This would be replaced with actual AI service call:
        # from app.services.ai_service import AIService
        # ai_service = AIService()
        # response = await ai_service.analyze_content_deeply(prompt)
        # return response
        
        # Mock response for development
        await asyncio.sleep(0.2)  # Simulate processing time
        return {
            "key_insights": [
                "Emerging technology trends are reshaping traditional business models",
                "Data-driven decision making is becoming critical for competitive advantage",
                "Remote work technologies are enabling new forms of collaboration"
            ],
            "main_themes": [
                "Digital Transformation",
                "Business Innovation",
                "Technology Adoption"
            ],
            "linkedin_angles": [
                "Share personal experience with digital transformation challenges",
                "Discuss how your industry is adapting to these changes",
                "Ask your network about their experiences with similar trends",
                "Position yourself as a thought leader in technology adoption"
            ],
            "actionable_takeaways": [
                "Evaluate current business processes for digitization opportunities",
                "Invest in data analytics capabilities and training",
                "Develop a remote-first technology strategy",
                "Create a change management plan for technology adoption"
            ],
            "target_audience": "Technology leaders, business executives, and professionals involved in digital transformation initiatives",
            "suggested_hashtags": [
                "#DigitalTransformation",
                "#BusinessInnovation", 
                "#TechLeadership",
                "#DataDriven",
                "#FutureOfWork",
                "#Innovation",
                "#Technology",
                "#Leadership"
            ],
            "engagement_potential": 0.82,
            "relevance_score": 0.88,
            "selection_reason": "This content aligns well with the user's interests in technology and business innovation, providing actionable insights that can be shared with their professional network",
            "content_quality": "High-quality content from a reputable source with practical insights and current relevance",
            "linkedin_suitability": "Excellent fit for LinkedIn - professional focus, actionable insights, and discussion-worthy topics"
        }
    
    async def _parse_analysis_response(
        self,
        llm_response: Dict[str, Any],
        content_item_id: UUID,
        user_id: UUID
    ) -> ContentAnalysisResult:
        """Parse LLM analysis response into structured result."""
        try:
            return ContentAnalysisResult(
                content_item_id=content_item_id,
                insights=llm_response.get("key_insights", []),
                key_points=llm_response.get("main_themes", []),
                linkedin_angles=llm_response.get("linkedin_angles", []),
                suggested_hashtags=llm_response.get("suggested_hashtags", []),
                target_audience=llm_response.get("target_audience", "General professional audience"),
                engagement_potential=llm_response.get("engagement_potential", 0.7),
                content_themes=llm_response.get("main_themes", []),
                actionable_takeaways=llm_response.get("actionable_takeaways", []),
                relevance_score=llm_response.get("relevance_score", 0.7),
                selection_reason=llm_response.get("selection_reason", "AI-generated content analysis"),
                analysis_metadata={
                    "llm_model": "gpt-4",
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "content_quality": llm_response.get("content_quality", "Not assessed"),
                    "linkedin_suitability": llm_response.get("linkedin_suitability", "Not assessed"),
                    "user_id": str(user_id)
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            # Return fallback analysis
            return ContentAnalysisResult(
                content_item_id=content_item_id,
                insights=["Content analysis unavailable due to parsing error"],
                key_points=["Analysis failed"],
                linkedin_angles=["Share as interesting professional content"],
                suggested_hashtags=["#Professional", "#Content"],
                target_audience="General professional audience",
                engagement_potential=0.5,
                content_themes=["Unknown"],
                actionable_takeaways=["Review content manually"],
                relevance_score=0.5,
                selection_reason="Fallback analysis due to parsing error",
                analysis_metadata={
                    "error": str(e),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "user_id": str(user_id)
                }
            )
    
    async def _store_analysis_results(
        self,
        content_item: ContentItem,
        analysis_result: ContentAnalysisResult
    ) -> None:
        """Store analysis results in ContentItem database table."""
        try:
            # Prepare AI analysis data
            ai_analysis = {
                "insights": analysis_result.insights,
                "key_points": analysis_result.key_points,
                "linkedin_angles": analysis_result.linkedin_angles,
                "suggested_hashtags": analysis_result.suggested_hashtags,
                "target_audience": analysis_result.target_audience,
                "engagement_potential": analysis_result.engagement_potential,
                "content_themes": analysis_result.content_themes,
                "actionable_takeaways": analysis_result.actionable_takeaways,
                "analysis_metadata": analysis_result.analysis_metadata
            }
            
            # Update content item
            await self.content_repo.update_processing_status(
                content_item.id,
                ContentStatus.PROCESSED,
                ai_analysis=ai_analysis,
                relevance_score=int(analysis_result.relevance_score * 100),  # Convert to 0-100 scale
                error_message=None
            )
            
            # Also update the processed_at timestamp and selection reason
            content_item.processed_at = datetime.utcnow()
            
            # Store selection reason in a way that can be queried
            if not content_item.ai_analysis:
                content_item.ai_analysis = {}
            
            content_item.ai_analysis["selection_reason"] = analysis_result.selection_reason
            
            logger.debug(f"Stored analysis results for content {content_item.id}")
            
        except Exception as e:
            logger.error(f"Failed to store analysis results for {content_item.id}: {str(e)}")
            raise
    
    async def _get_or_create_content_item(
        self,
        content_item_id: UUID,
        article_data: Optional[Dict[str, Any]] = None
    ) -> ContentItem:
        """Get existing content item or create from article data."""
        content_item = await self.content_repo.get_by_id(content_item_id)
        
        if content_item:
            return content_item
        
        if not article_data:
            raise ValueError(f"Content item {content_item_id} not found and no article data provided")
        
        # Create content item from article data
        return await self._create_content_item_from_article(article_data, None)
    
    async def _create_content_item_from_article(
        self,
        article_data: Dict[str, Any],
        user_id: Optional[UUID]
    ) -> ContentItem:
        """Create ContentItem from selected article data."""
        try:
            # For this implementation, we'll create a basic content item
            # In production, you'd need to link to a proper content source
            content_item = ContentItem(
                title=article_data.get("title", "Unknown Title"),
                url=article_data.get("url", ""),
                content=article_data.get("content", ""),
                author=article_data.get("author"),
                published_at=datetime.fromisoformat(article_data["published_at"]) if article_data.get("published_at") else None,
                word_count=article_data.get("word_count", 0),
                status=ContentStatus.PENDING,
                relevance_score=int((article_data.get("relevance_score", 0.7) * 100)),
                tags=[]
            )
            
            self.session.add(content_item)
            await self.session.flush()
            await self.session.refresh(content_item)
            
            return content_item
            
        except Exception as e:
            logger.error(f"Failed to create content item from article data: {str(e)}")
            raise
    
    async def _update_content_with_feedback(
        self,
        content_item_id: UUID,
        feedback_metrics: FeedbackMetrics
    ) -> None:
        """Update content item with feedback metrics."""
        try:
            content_item = await self.content_repo.get_by_id(content_item_id)
            if not content_item:
                logger.warning(f"Content item {content_item_id} not found for feedback update")
                return
            
            # Update AI analysis with feedback data
            if not content_item.ai_analysis:
                content_item.ai_analysis = {}
            
            content_item.ai_analysis["feedback_metrics"] = {
                "user_interactions": feedback_metrics.user_interactions,
                "draft_created": feedback_metrics.draft_created,
                "draft_published": feedback_metrics.draft_published,
                "linkedin_engagement": feedback_metrics.linkedin_engagement,
                "user_rating": feedback_metrics.user_rating,
                "feedback_timestamp": feedback_metrics.feedback_timestamp.isoformat()
            }
            
            logger.debug(f"Updated content {content_item_id} with feedback metrics")
            
        except Exception as e:
            logger.error(f"Failed to update content with feedback: {str(e)}")
    
    async def _update_preferences_from_feedback(
        self,
        user_id: UUID,
        content_item_id: UUID,
        feedback_metrics: FeedbackMetrics
    ) -> None:
        """Update user preferences based on feedback (learning mechanism)."""
        try:
            # This is a stub for future ML-based preference learning
            # For now, we'll just log the feedback for future implementation
            
            learning_data = {
                "user_id": str(user_id),
                "content_item_id": str(content_item_id),
                "positive_feedback": feedback_metrics.user_rating and feedback_metrics.user_rating >= 4,
                "engagement_created": feedback_metrics.draft_created or feedback_metrics.draft_published,
                "interaction_quality": feedback_metrics.user_interactions,
                "timestamp": feedback_metrics.feedback_timestamp.isoformat()
            }
            
            # TODO: Implement actual learning algorithm
            # This could involve:
            # 1. Analyzing content themes that get positive feedback
            # 2. Adjusting relevance thresholds based on user behavior
            # 3. Learning preferred content types and sources
            # 4. Adjusting hashtag preferences based on engagement
            
            logger.debug(f"Logged learning data for user {user_id}: {learning_data}")
            
        except Exception as e:
            logger.error(f"Failed to update preferences from feedback: {str(e)}")
    
    async def _get_analyzed_content_for_user(
        self,
        user_id: UUID,
        since_date: datetime
    ) -> List[ContentItem]:
        """Get analyzed content items for user within date range."""
        try:
            # This is a simplified query - in production you'd need proper joins
            # based on how content items are linked to users (through sources, selections, etc.)
            
            analyzed_items = await self.content_repo.find_by(
                status=ContentStatus.PROCESSED
            )
            
            # Filter items that have AI analysis and are recent
            filtered_items = [
                item for item in analyzed_items
                if (item.ai_analysis and 
                    item.processed_at and 
                    item.processed_at >= since_date)
            ]
            
            return filtered_items
            
        except Exception as e:
            logger.error(f"Failed to get analyzed content for user {user_id}: {str(e)}")
            return []
    
    async def _calculate_performance_analytics(
        self,
        analyzed_items: List[ContentItem],
        days: int
    ) -> Dict[str, Any]:
        """Calculate performance analytics from analyzed content items."""
        try:
            total_items = len(analyzed_items)
            
            # Calculate basic metrics
            avg_relevance_score = sum(item.relevance_score or 0 for item in analyzed_items) / total_items if total_items > 0 else 0
            
            # Count items with feedback
            items_with_feedback = [
                item for item in analyzed_items
                if item.ai_analysis and item.ai_analysis.get("feedback_metrics")
            ]
            
            # Calculate engagement metrics
            drafts_created = sum(
                1 for item in items_with_feedback
                if item.ai_analysis.get("feedback_metrics", {}).get("draft_created", False)
            )
            
            drafts_published = sum(
                1 for item in items_with_feedback
                if item.ai_analysis.get("feedback_metrics", {}).get("draft_published", False)
            )
            
            # Calculate theme distribution
            all_themes = []
            for item in analyzed_items:
                if item.ai_analysis and item.ai_analysis.get("content_themes"):
                    all_themes.extend(item.ai_analysis["content_themes"])
            
            from collections import Counter
            theme_distribution = Counter(all_themes).most_common(10)
            
            return {
                "total_analyzed_items": total_items,
                "items_with_feedback": len(items_with_feedback),
                "average_relevance_score": avg_relevance_score / 100,  # Convert back to 0-1 scale
                "drafts_created": drafts_created,
                "drafts_published": drafts_published,
                "draft_creation_rate": drafts_created / total_items if total_items > 0 else 0,
                "publish_rate": drafts_published / total_items if total_items > 0 else 0,
                "top_content_themes": [{"theme": theme, "count": count} for theme, count in theme_distribution],
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate performance analytics: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }


# Factory function for dependency injection
async def get_deep_content_analysis_service() -> DeepContentAnalysisService:
    """
    Factory function to create DeepContentAnalysisService with database session.
    
    Returns:
        DeepContentAnalysisService instance
    """
    from app.database.connection import get_db_session
    async with get_db_session() as session:
        return DeepContentAnalysisService(session)
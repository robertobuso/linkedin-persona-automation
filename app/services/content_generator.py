"""
Content generator service for LinkedIn Presence Automation Application.

Orchestrates the content generation pipeline from raw content to LinkedIn posts
using AI services, tone analysis, and quality validation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import AIService
from app.services.tone_analyzer import ToneAnalyzer
from app.repositories.content_repository import ContentItemRepository, PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import ContentItem, PostDraft, DraftStatus
from app.models.user import User
from app.schemas.ai_schemas import (
    SummaryRequest, PostGenerationRequest, ToneProfile
)

logger = logging.getLogger(__name__)


class ContentGenerationError(Exception):
    """Base exception for content generation errors."""
    pass


class ContentGenerator:
    """
    Service for generating LinkedIn posts from content items.
    
    Orchestrates the complete pipeline from content analysis to post draft creation
    with quality validation and user tone matching.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize content generator with database session.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.ai_service = AIService()
        self.tone_analyzer = ToneAnalyzer()
        self.content_repo = ContentItemRepository(session)
        self.post_repo = PostDraftRepository(session)
        self.user_repo = UserRepository(session)
    
    async def generate_post_from_content(
        self,
        content_item_id: UUID,
        user_id: UUID,
        style: Optional[str] = None,
        num_variations: int = 3
    ) -> PostDraft:
        """
        Generate LinkedIn post draft from content item.
        
        Args:
            content_item_id: ID of content item to generate post from
            user_id: ID of user generating the post
            style: Optional style preference (professional, casual, thought-provoking)
            num_variations: Number of variations to generate
            
        Returns:
            Created PostDraft instance
            
        Raises:
            ContentGenerationError: If generation fails
        """
        try:
            logger.info(f"Generating post from content {content_item_id} for user {user_id}")
            
            # Get content item and user
            content_item = await self.content_repo.get_by_id(content_item_id)
            if not content_item:
                raise ContentGenerationError(f"Content item {content_item_id} not found")
            
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ContentGenerationError(f"User {user_id} not found")
            
            # Extract user tone profile
            tone_profile = self._extract_tone_profile(user)
            
            # Step 1: Summarize content
            summary_response = await self._summarize_content(content_item, tone_profile)
            
            # Step 2: Get user's historical posts for examples
            user_examples = await self._get_user_post_examples(user_id)
            
            # Step 3: Generate post variations
            post_response = await self._generate_post_variations(
                summary_response.summary,
                tone_profile,
                user_examples,
                style,
                num_variations
            )
            
            # Step 4: Validate and create draft
            validated_content = await self._validate_post_content(
                post_response.content,
                post_response.hashtags
            )
            
            # Create post draft
            post_draft = await self.post_repo.create(
                user_id=user_id,
                source_content_id=content_item_id,
                content=validated_content["content"],
                hashtags=validated_content["hashtags"],
                title=content_item.title[:255] if content_item.title else None,
                status=DraftStatus.READY,
                generation_prompt=f"Generated from: {content_item.title}",
                ai_model_used=post_response.model_used,
                generation_metadata={
                    "summary": summary_response.summary,
                    "key_points": summary_response.key_points,
                    "variations_generated": len(post_response.variations),
                    "style": style or "professional",
                    "tone_profile_used": tone_profile.dict(),
                    "processing_time": post_response.processing_time,
                    "tokens_used": post_response.tokens_used,
                    "cost": post_response.cost,
                    "estimated_reach": post_response.estimated_reach,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Successfully generated post draft {post_draft.id}")
            return post_draft
            
        except Exception as e:
            logger.error(f"Post generation failed: {str(e)}")
            raise ContentGenerationError(f"Failed to generate post: {str(e)}")
    
    async def batch_generate_posts(
        self,
        user_id: UUID,
        max_posts: int = 5,
        min_relevance_score: int = 70
    ) -> List[PostDraft]:
        """
        Generate multiple posts from high-relevance content items.
        
        Args:
            user_id: ID of user to generate posts for
            max_posts: Maximum number of posts to generate
            min_relevance_score: Minimum relevance score for content selection
            
        Returns:
            List of created PostDraft instances
        """
        try:
            logger.info(f"Batch generating up to {max_posts} posts for user {user_id}")
            
            # Get high-relevance content items
            content_items = await self.content_repo.get_high_relevance_items(
                user_id=user_id,
                min_score=min_relevance_score,
                limit=max_posts * 2  # Get more items to have options
            )
            
            if not content_items:
                logger.warning(f"No high-relevance content found for user {user_id}")
                return []
            
            # Check for existing drafts to avoid duplicates
            existing_drafts = await self.post_repo.get_drafts_by_status(
                user_id=user_id,
                status=DraftStatus.READY,
                limit=50
            )
            
            existing_content_ids = {
                draft.source_content_id for draft in existing_drafts 
                if draft.source_content_id
            }
            
            # Filter out content that already has drafts
            available_content = [
                item for item in content_items 
                if item.id not in existing_content_ids
            ]
            
            if not available_content:
                logger.warning(f"No new content available for post generation for user {user_id}")
                return []
            
            # Generate posts
            generated_drafts = []
            for i, content_item in enumerate(available_content[:max_posts]):
                try:
                    draft = await self.generate_post_from_content(
                        content_item_id=content_item.id,
                        user_id=user_id,
                        style="professional",
                        num_variations=2  # Fewer variations for batch processing
                    )
                    generated_drafts.append(draft)
                    
                    # Small delay between generations to avoid rate limiting
                    if i < len(available_content) - 1:
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.error(f"Failed to generate post from content {content_item.id}: {str(e)}")
                    continue
            
            logger.info(f"Batch generation completed: {len(generated_drafts)} posts created")
            return generated_drafts
            
        except Exception as e:
            logger.error(f"Batch post generation failed: {str(e)}")
            raise ContentGenerationError(f"Batch generation failed: {str(e)}")
    
    async def regenerate_post_draft(
        self,
        draft_id: UUID,
        style: Optional[str] = None,
        preserve_hashtags: bool = False
    ) -> PostDraft:
        """
        Regenerate an existing post draft with new content.
        
        Args:
            draft_id: ID of draft to regenerate
            style: Optional new style preference
            preserve_hashtags: Whether to preserve existing hashtags
            
        Returns:
            Updated PostDraft instance
        """
        try:
            logger.info(f"Regenerating post draft {draft_id}")
            
            # Get existing draft
            draft = await self.post_repo.get_by_id(draft_id)
            if not draft:
                raise ContentGenerationError(f"Draft {draft_id} not found")
            
            # Get source content if available
            if draft.source_content_id:
                content_item = await self.content_repo.get_by_id(draft.source_content_id)
                if content_item:
                    # Regenerate from source content
                    new_draft = await self.generate_post_from_content(
                        content_item_id=content_item.id,
                        user_id=draft.user_id,
                        style=style,
                        num_variations=2
                    )
                    
                    # Update existing draft with new content
                    update_data = {
                        "content": new_draft.content,
                        "generation_metadata": new_draft.generation_metadata
                    }
                    
                    if not preserve_hashtags:
                        update_data["hashtags"] = new_draft.hashtags
                    
                    updated_draft = await self.post_repo.update(draft_id, **update_data)
                    
                    # Clean up temporary draft
                    await self.post_repo.delete(new_draft.id)
                    
                    return updated_draft
            
            # If no source content, regenerate from existing content
            user = await self.user_repo.get_by_id(draft.user_id)
            tone_profile = self._extract_tone_profile(user)
            user_examples = await self._get_user_post_examples(draft.user_id)
            
            # Use existing content as summary
            post_response = await self._generate_post_variations(
                summary=draft.content[:500],  # Use first 500 chars as summary
                tone_profile=tone_profile,
                user_examples=user_examples,
                style=style or "professional",
                num_variations=2
            )
            
            # Update draft
            update_data = {
                "content": post_response.content,
                "generation_metadata": {
                    **draft.generation_metadata,
                    "regenerated_at": datetime.utcnow().isoformat(),
                    "regeneration_style": style,
                    "regeneration_tokens": post_response.tokens_used,
                    "regeneration_cost": post_response.cost
                }
            }
            
            if not preserve_hashtags:
                update_data["hashtags"] = post_response.hashtags
            
            updated_draft = await self.post_repo.update(draft_id, **update_data)
            
            logger.info(f"Successfully regenerated draft {draft_id}")
            return updated_draft
            
        except Exception as e:
            logger.error(f"Draft regeneration failed: {str(e)}")
            raise ContentGenerationError(f"Failed to regenerate draft: {str(e)}")
    
    async def _summarize_content(self, content_item: ContentItem, tone_profile: ToneProfile):
        """Summarize content item with user tone matching."""
        summary_request = SummaryRequest(
            content=content_item.content,
            tone_profile=tone_profile,
            max_length=200
        )
        
        return await self.ai_service.summarize_content(summary_request)
    
    async def _get_user_post_examples(self, user_id: UUID, limit: int = 5) -> List[str]:
        """Get user's historical posts as examples for tone matching."""
        try:
            # Get recent published posts
            recent_drafts = await self.post_repo.get_drafts_by_status(
                user_id=user_id,
                status=DraftStatus.PUBLISHED,
                limit=limit
            )
            
            return [draft.content for draft in recent_drafts if draft.content]
            
        except Exception as e:
            logger.warning(f"Failed to get user post examples: {str(e)}")
            return []
    
    async def _generate_post_variations(
        self,
        summary: str,
        tone_profile: ToneProfile,
        user_examples: List[str],
        style: Optional[str],
        num_variations: int
    ):
        """Generate post variations using AI service."""
        post_request = PostGenerationRequest(
            summary=summary,
            tone_profile=tone_profile,
            user_examples=user_examples,
            style=style or "professional",
            num_variations=num_variations
        )
        
        return await self.ai_service.generate_post_draft(post_request)
    
    async def _validate_post_content(self, content: str, hashtags: List[str]) -> Dict[str, Any]:
        """Validate and clean post content for LinkedIn."""
        # LinkedIn character limit
        max_length = 3000
        
        # Trim content if too long
        if len(content) > max_length:
            content = content[:max_length - 3] + "..."
        
        # Validate hashtags
        valid_hashtags = []
        for hashtag in hashtags:
            # Ensure hashtag starts with #
            if not hashtag.startswith('#'):
                hashtag = '#' + hashtag
            
            # Remove spaces and special characters
            hashtag = ''.join(c for c in hashtag if c.isalnum() or c == '#')
            
            # Limit hashtag length
            if len(hashtag) <= 100 and len(hashtag) > 1:
                valid_hashtags.append(hashtag)
        
        # Limit number of hashtags
        valid_hashtags = valid_hashtags[:10]
        
        # Check for professional tone
        inappropriate_words = ['damn', 'hell', 'crap', 'stupid', 'idiot']
        content_lower = content.lower()
        
        for word in inappropriate_words:
            if word in content_lower:
                logger.warning(f"Potentially inappropriate word detected: {word}")
        
        return {
            "content": content.strip(),
            "hashtags": valid_hashtags
        }
    
    def _extract_tone_profile(self, user: User) -> ToneProfile:
        """Extract tone profile from user data."""
        tone_data = user.tone_profile or {}
        
        return ToneProfile(
            writing_style=tone_data.get("writing_style", "professional"),
            tone=tone_data.get("tone", "informative"),
            personality_traits=tone_data.get("personality_traits", ["analytical", "thoughtful"]),
            industry_focus=tone_data.get("industry_focus", []),
            expertise_areas=tone_data.get("expertise_areas", []),
            communication_preferences=tone_data.get("communication_preferences", {
                "use_emojis": False,
                "include_hashtags": True,
                "max_hashtags": 3,
                "call_to_action_style": "subtle"
            })
        )
    
    async def get_generation_stats(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Get content generation statistics for a user.
        
        Args:
            user_id: User ID to get stats for
            days: Number of days to analyze
            
        Returns:
            Dictionary with generation statistics
        """
        try:
            # Get drafts summary
            drafts_summary = await self.post_repo.get_user_drafts_summary(user_id)
            
            # Get recent drafts for analysis
            recent_drafts = await self.post_repo.get_recent_published_drafts(
                user_id=user_id,
                days=days,
                limit=50
            )
            
            # Calculate generation metrics
            total_generated = drafts_summary["total_drafts"]
            published_count = drafts_summary["published"]
            
            # Analyze generation metadata
            total_cost = 0.0
            total_tokens = 0
            avg_processing_time = 0.0
            
            for draft in recent_drafts:
                if draft.generation_metadata:
                    metadata = draft.generation_metadata
                    total_cost += metadata.get("cost", 0.0)
                    total_tokens += metadata.get("tokens_used", 0)
                    avg_processing_time += metadata.get("processing_time", 0.0)
            
            if recent_drafts:
                avg_processing_time /= len(recent_drafts)
            
            return {
                "total_drafts_generated": total_generated,
                "drafts_by_status": {
                    "ready": drafts_summary["ready"],
                    "scheduled": drafts_summary["scheduled"],
                    "published": published_count,
                    "failed": drafts_summary["failed"],
                    "archived": drafts_summary["archived"]
                },
                "publication_rate": (published_count / total_generated * 100) if total_generated > 0 else 0,
                "recent_activity": {
                    "posts_published": len(recent_drafts),
                    "total_ai_cost": total_cost,
                    "total_tokens_used": total_tokens,
                    "avg_processing_time": avg_processing_time
                },
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get generation stats: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
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
from app.prompts.post_generation_prompts import PostGenerationPrompts
from app.services.tone_analyzer import ToneAnalyzer
from app.repositories.content_repository import ContentItemRepository, PostDraftRepository
from app.repositories.user_repository import UserRepository
from app.models.content import ContentItem, PostDraft, DraftStatus
from app.models.user import User
from app.schemas.ai_schemas import (
    SummaryRequest, PostGenerationRequest, ToneProfile
)
from app.schemas.api_schemas import PostDraftCreate

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
        self.post_prompts = PostGenerationPrompts()
    
    async def _get_user_and_tone_profile(self, user_id: UUID) -> tuple[User, ToneProfile]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found for draft generation.")
        
        # Assuming user.tone_profile is a JSONB field that matches ToneProfile structure
        # You might need to deserialize it properly if it's just a dict from DB
        # For now, assuming it can be passed to Pydantic's ToneProfile.model_validate
        tone_profile_data = user.tone_profile or {} # Get from user model
        tone_profile = ToneProfile(**tone_profile_data) # Validate/Create Pydantic model
        return user, tone_profile

    async def generate_post_from_content(
        self,
        content_item_id: UUID,
        user_id: UUID,
        style: str = "professional_thought_leader",
        num_variations: int = 3,
        target_platform: str = "linkedin"
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
            logger.info(f"Generating post from content {content_item_id} for user {user_id} with style '{style}'")
            content_item = await self.content_repo.get_by_id(content_item_id)
            if not content_item:
                raise ValueError(f"Content item {content_item_id} not found.")

            user, tone_profile = await self._get_user_and_tone_profile(user_id)

            # For now, user_examples might be empty or fetched from user's past posts
            user_post_examples: List[str] = [] # TODO: Implement fetching user examples if desired

            summary_text = content_item.ai_analysis.get("summary") if content_item.ai_analysis else content_item.content[:1000]
            if not summary_text:
                summary_text = content_item.title # Fallback summary

            # Build the specific prompt based on style
            prompt_text: str
            if style == "storytelling":
                prompt_text = self.post_prompts.build_storytelling_post_prompt(
                    summary=summary_text, tone_profile=tone_profile, user_examples=user_post_examples
                )
            elif style == "thought_leadership":
                prompt_text = self.post_prompts.build_thought_leadership_prompt(
                    summary=summary_text, tone_profile=tone_profile, user_examples=user_post_examples
                )
            elif style == "educational":
                prompt_text = self.post_prompts.build_educational_post_prompt(
                    summary=summary_text, tone_profile=tone_profile, user_examples=user_post_examples
                )
            elif style == "engagement_optimized":
                prompt_text = self.post_prompts.build_engagement_optimized_prompt(
                    summary=summary_text, tone_profile=tone_profile, user_examples=user_post_examples
                )
            else: # Default or "professional_thought_leader"
                prompt_text = self.post_prompts.build_post_prompt(
                    summary=summary_text, user_examples=user_post_examples, tone_profile=tone_profile, style=style
                )

            generation_request = PostGenerationRequest(
                summary=summary_text, # Summary still useful for AIService context if needed
                tone_profile=tone_profile,
                user_examples=user_post_examples,
                style=style, # Style can still be passed for AIService logging/metrics
                num_variations=num_variations,
                custom_prompt_text=prompt_text # Pass the fully constructed prompt
            )

            post_draft_response_data = await self.ai_service.generate_post_draft(generation_request)

            new_draft = await self.post_repo.create(
                user_id=user_id,
                source_content_id=content_item_id,
                title=content_item.title[:250] if content_item.title else "AI Generated Post",
                content=post_draft_response_data.content,
                hashtags=post_draft_response_data.hashtags,
                status=DraftStatus.READY, # Or DRAFT, depending on your flow
                post_type="text", # Or determine from content/style
                generation_prompt=prompt_text, # Store the actual prompt used
                ai_model_used=post_draft_response_data.model_used,
                generation_metadata={
                    "style_used": style,
                    "num_variations_generated": len(post_draft_response_data.variations),
                    "summary_length": len(summary_text),
                    "cost": post_draft_response_data.cost,
                    "tokens_used": post_draft_response_data.tokens_used,
                    "processing_time_seconds": post_draft_response_data.processing_time,
                    "estimated_reach": post_draft_response_data.estimated_reach,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Successfully generated post draft {new_draft.id} with style '{style}'")
            return new_draft
            
        except Exception as e:
            logger.error(f"Post generation failed: {str(e)}")
            raise ContentGenerationError(f"Failed to generate post: {str(e)}")
    
    async def batch_generate_posts(
        self,
        user_id: UUID,
        max_posts: int = 5,
        min_relevance_score: int = 70,
        style: str = "professional_thought_leader" 
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
            logger.info(f"Batch generating up to {max_posts} posts for user {user_id} with style '{style}' and min score {min_relevance_score}")
        
            # 1. Get high-relevance processed content items for the user
            #    (adjust limit to get a few more than max_posts to account for potential existing drafts)
            candidate_items = await self.content_repo.get_high_relevance_items(
                user_id=user_id, 
                min_score=min_relevance_score, 
                limit=max_posts * 2 # Fetch more to filter
            )

            if not candidate_items:
                logger.info(f"No suitable content items found for user {user_id} for batch generation.")
                return []

            # 2. Get IDs of content items already drafted (e.g., in 'draft' or 'ready' status)
            #    to avoid re-drafting them immediately.
            #    This might need a more sophisticated check or a new repo method.
            #    For simplicity, let's assume we fetch recent drafts.
            recent_drafts = await self.post_repo.get_drafts_by_status(user_id, DraftStatus.READY, limit=50)
            recent_drafts += await self.post_repo.get_drafts_by_status(user_id, DraftStatus.DRAFT, limit=50)
            drafted_content_ids = {draft.source_content_id for draft in recent_drafts if draft.source_content_id}

            generated_drafts: List[PostDraft] = []
            items_to_draft_from = [item for item in candidate_items if item.id not in drafted_content_ids]

            for content_item in items_to_draft_from:
                if len(generated_drafts) >= max_posts:
                    break
                try:
                    draft = await self.generate_post_from_content(
                        content_item_id=content_item.id,
                        user_id=user_id,
                        style=style, # Use the passed style
                        num_variations=1 
                    )
                    generated_drafts.append(draft)
                except Exception as e:
                    logger.error(f"Failed to generate draft for content_item {content_item.id} in batch: {e}", exc_info=True)
                    continue
            
            logger.info(f"Batch generation completed: {len(generated_drafts)} posts created for user {user_id}")
            return generated_drafts
            
        except Exception as e:
            logger.error(f"Batch post generation failed: {str(e)}")
            raise ContentGenerationError(f"Batch generation failed: {str(e)}")
    
    async def regenerate_post_draft(
        self,
        draft_id: UUID,
        user_id: UUID,
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
            logger.info(f"Regenerating draft {draft_id} with style '{style}' for user {user_id}")
            original_draft = await self.post_repo.get_by_id(draft_id)
            if not original_draft or original_draft.user_id != user_id:
                raise ValueError("Draft not found or access denied.")
            if not original_draft.source_content_id:
                raise ValueError("Original content source not found for this draft, cannot regenerate.")

            content_item = await self.content_repo.get_by_id(original_draft.source_content_id)
            if not content_item:
                raise ValueError(f"Source content item {original_draft.source_content_id} not found.")

            # Generate new post content using the specified style
            # For regeneration, we create a new draft object rather than updating in place,
            # or you could update if that's the desired behavior.
            # Here, let's assume it creates a *new variation* or overwrites content.
            
            user, tone_profile = await self._get_user_and_tone_profile(user_id)
            user_post_examples: List[str] = [] # TODO: Fetch if needed

            summary_text = content_item.ai_analysis.get("summary") if content_item.ai_analysis else content_item.content[:1000]
            if not summary_text:
                summary_text = content_item.title

            prompt_text: str
            if style == "storytelling":
                prompt_text = self.post_prompts.build_storytelling_post_prompt(summary_text, tone_profile, user_post_examples)
            # Add other elif style == "..." blocks here for other prompt builders
            else: # Default
                prompt_text = self.post_prompts.build_post_prompt(summary_text, user_post_examples, tone_profile, style)

            generation_request = PostGenerationRequest(
                summary=summary_text,
                tone_profile=tone_profile,
                user_examples=user_post_examples,
                style=style,
                num_variations=1, # Regenerate one primary version
                custom_prompt_text=prompt_text
            )
            
            post_draft_response_data = await self.ai_service.generate_post_draft(generation_request)

            update_data: Dict[str, Any] = {
                "content": post_draft_response_data.content,
                "generation_prompt": prompt_text, # Store the new prompt
                "ai_model_used": post_draft_response_data.model_used,
                "generation_metadata": {
                    **(original_draft.generation_metadata or {}), # Preserve old metadata if any
                    "regenerated_with_style": style,
                    "summary_length": len(summary_text),
                    "cost": post_draft_response_data.cost,
                    "tokens_used": post_draft_response_data.tokens_used,
                    "processing_time_seconds": post_draft_response_data.processing_time,
                    "regenerated_at": datetime.utcnow().isoformat()
                }
            }
            if not preserve_hashtags:
                update_data["hashtags"] = post_draft_response_data.hashtags

            updated_draft = await self.post_repo.update(draft_id, **update_data)
            if not updated_draft:
                raise ValueError(f"Failed to update draft {draft_id} during regeneration.")
            logger.info(f"Successfully regenerated draft {draft_id} with style '{style}'")
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
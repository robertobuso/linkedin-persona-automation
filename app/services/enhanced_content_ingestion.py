"""
Enhanced content ingestion service with LLM-based content selection and user preference filtering.

Implements Phase 1 and Phase 2 of the LLM-first content discovery pipeline:
- Removes hardcoded AI filters
- Adds user preference-based filtering
- Implements LLM-based content selection
- Adds Redis caching for selection results
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.content import ContentSource, ContentItem, ContentStatus
from app.models.user import User, ContentSelection
from app.models.user_content_preferences import UserContentPreferences
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_content_preferences_repository import UserContentPreferencesRepository
from app.services.rss_parser import RSSParser
from app.services.linkedin_scraper import LinkedInScraper
from app.utils.content_extractor import ContentExtractor
from app.utils.deduplication import ContentDeduplicator
from app.database.connection import get_db_session
from app.schemas.api_schemas import ContentStatsResponse

logger = logging.getLogger(__name__)


@dataclass
class ContentSelectionResult:
    """Result of LLM-based content selection."""
    selected_articles: List[Dict[str, Any]]
    selection_reasons: Dict[str, str]
    processing_details: Dict[str, Any]
    cache_key: str
    selection_timestamp: datetime


@dataclass
class ArticleCandidate:
    """Candidate article for LLM evaluation."""
    title: str
    url: str
    content: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    source_name: str = ""
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source_name": self.source_name,
            "word_count": self.word_count
        }


class EnhancedContentIngestionService:
    """
    Enhanced content ingestion service with LLM-based selection and user preferences.
    
    Implements intelligent content discovery that:
    1. Filters content based on user preferences (Phase 1)
    2. Uses LLM to select most relevant articles (Phase 2) 
    3. Caches selection results in Redis
    4. Tracks selection performance
    """
    
    def __init__(self, session: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the enhanced content ingestion service.
        
        Args:
            session: Database session for repository operations
            redis_client: Optional Redis client for caching
        """
        self.session = session
        self.redis_client = redis_client
        self.source_repo = ContentSourceRepository(session)
        self.content_repo = ContentItemRepository(session)
        self.user_repo = UserRepository(session)
        self.preferences_repo = UserContentPreferencesRepository(session)
        self.rss_parser = RSSParser()
        self.linkedin_scraper = LinkedInScraper()
        self.content_extractor = ContentExtractor()
        self.deduplicator = ContentDeduplicator()
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour
        self.max_articles_for_llm = 50  # Limit articles sent to LLM
    
    async def process_content_with_llm_selection(
        self, 
        user_id: UUID, 
        force_refresh: bool = False
    ) -> ContentSelectionResult:
        """
        Process content for a user using LLM-based selection.
        
        This implements Phase 2 of the pipeline:
        1. Check Redis cache for recent selections
        2. Gather candidate articles from all user sources
        3. Apply basic user preference filtering
        4. Use LLM to select most relevant articles
        5. Cache results in Redis
        
        Args:
            user_id: User ID to process content for
            force_refresh: Whether to bypass cache and force new selection
            
        Returns:
            ContentSelectionResult with selected articles and metadata
        """
        try:
            logger.info(f"Processing content with LLM selection for user {user_id}")
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_result = await self._get_cached_selection(user_id)
                if cached_result:
                    logger.info(f"Returning cached selection for user {user_id}")
                    return cached_result
            
            # Get user and preferences
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user_preferences = await self.preferences_repo.get_active_preferences_for_user(user_id)
            
            # Get user's content sources
            sources = await self.source_repo.get_active_sources_by_user(user_id)
            if not sources:
                logger.warning(f"No active sources found for user {user_id}")
                return self._empty_selection_result(user_id)
            
            # Gather candidate articles from all sources
            candidates = await self._gather_candidate_articles(sources, user, user_preferences)
            if not candidates:
                logger.warning(f"No candidate articles found for user {user_id}")
                return self._empty_selection_result(user_id)
            
            # Use LLM to select most relevant articles
            selection_result = await self._select_articles_with_llm(
                user_id, candidates, user, user_preferences
            )
            
            # Cache the results
            await self._cache_selection_result(selection_result)
            
            # Track selection in database
            await self._record_content_selection(
                user_id, len(candidates), len(selection_result.selected_articles), 
                selection_result.processing_details
            )
            
            logger.info(f"LLM selection completed for user {user_id}: {len(selection_result.selected_articles)} articles selected from {len(candidates)} candidates")
            return selection_result
            
        except Exception as e:
            logger.error(f"LLM content selection failed for user {user_id}: {str(e)}")
            raise
    
    async def _gather_candidate_articles(
        self, 
        sources: List[ContentSource], 
        user: User, 
        user_preferences: Optional[UserContentPreferences]
    ) -> List[ArticleCandidate]:
        """
        Gather candidate articles from all user sources with basic filtering.
        
        Args:
            sources: List of content sources to process
            user: User object
            user_preferences: User's content preferences
            
        Returns:
            List of ArticleCandidate objects
        """
        candidates = []
        
        for source in sources:
            try:
                logger.debug(f"Gathering candidates from source: {source.name}")
                
                # Parse content based on source type
                if source.source_type == "rss_feed":
                    items = await self.rss_parser.parse_feed(source.url)
                elif source.source_type == "linkedin":
                    items = await self.linkedin_scraper.scrape_profile_posts(source.url)
                else:
                    logger.warning(f"Unsupported source type: {source.source_type}")
                    continue
                
                # Convert to candidates and apply basic filtering
                for item in items:
                    try:
                        # Create metadata for filtering
                        content_age_hours = 0
                        if item.published_at:
                            age_delta = datetime.utcnow() - item.published_at
                            content_age_hours = age_delta.total_seconds() / 3600
                        
                        content_metadata = {
                            "title": item.title,
                            "description": item.content[:200] if item.content else "",
                            "word_count": len(item.content.split()) if item.content else 0,
                            "age_hours": content_age_hours,
                            "content_type": "article",  # Default type
                            "author": item.author,
                            "source_name": source.name
                        }
                        
                        # Apply user preference filtering (Phase 1)
                        should_process, reason = user.should_process_content(content_metadata)
                        if not should_process:
                            logger.debug(f"Filtered out article '{item.title}': {reason}")
                            continue
                        
                        # Check for duplicates
                        if await self.content_repo.check_duplicate_url(item.url):
                            logger.debug(f"Skipping duplicate URL: {item.url}")
                            continue
                        
                        # Create candidate
                        candidate = ArticleCandidate(
                            title=item.title,
                            url=item.url,
                            content=item.content,
                            author=item.author,
                            published_at=item.published_at,
                            source_name=source.name,
                            word_count=content_metadata["word_count"]
                        )
                        
                        candidates.append(candidate)
                        
                        # Limit total candidates to avoid overwhelming LLM
                        if len(candidates) >= self.max_articles_for_llm:
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error processing item from {source.name}: {str(e)}")
                        continue
                
                # Break if we have enough candidates
                if len(candidates) >= self.max_articles_for_llm:
                    break
                    
            except Exception as e:
                logger.error(f"Error gathering candidates from source {source.name}: {str(e)}")
                continue
        
        logger.info(f"Gathered {len(candidates)} candidate articles")
        return candidates
    
    async def _select_articles_with_llm(
        self,
        user_id: UUID,
        candidates: List[ArticleCandidate],
        user: User,
        user_preferences: Optional[UserContentPreferences]
    ) -> ContentSelectionResult:
        """
        Use LLM to select the most relevant articles from candidates.
        
        Args:
            user_id: User ID
            candidates: List of candidate articles
            user: User object
            user_preferences: User's content preferences
            
        Returns:
            ContentSelectionResult with selected articles
        """
        try:
            start_time = datetime.utcnow()
            
            # Build LLM prompt
            user_context = self._build_user_context(user, user_preferences)
            selection_prompt = self._build_selection_prompt(candidates, user_context, user_preferences)
            
            # Call LLM for selection
            logger.debug(f"Calling LLM for article selection (user: {user_id})")
            llm_response = await self._invoke_llm_with_structured_output(selection_prompt)
            
            # Parse LLM response
            selected_articles, selection_reasons = self._parse_llm_selection_response(
                llm_response, candidates
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Build result
            cache_key = self._build_cache_key(user_id)
            result = ContentSelectionResult(
                selected_articles=selected_articles,
                selection_reasons=selection_reasons,
                processing_details={
                    "llm_model": "gpt-4",  # This would come from the LLM service
                    "candidates_evaluated": len(candidates),
                    "articles_selected": len(selected_articles),
                    "processing_time_seconds": processing_time,
                    "user_context_used": user_context,
                    "selection_criteria": {
                        "min_relevance_score": user_preferences.min_relevance_score if user_preferences else 0.7,
                        "max_articles": user_preferences.max_articles_per_day if user_preferences else 15,
                        "content_types": user_preferences.content_types if user_preferences else ["articles"]
                    }
                },
                cache_key=cache_key,
                selection_timestamp=datetime.utcnow()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM article selection failed: {str(e)}")
            raise
    
    def _build_user_context(
        self, 
        user: User, 
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build user context string for LLM prompt."""
        if user_preferences:
            context_parts = []
            
            if user_preferences.job_role:
                context_parts.append(f"Job role: {user_preferences.job_role}")
            
            if user_preferences.industry:
                context_parts.append(f"Industry: {user_preferences.industry}")
            
            if user_preferences.primary_interests:
                context_parts.append(f"Primary interests: {', '.join(user_preferences.primary_interests)}")
            
            if user_preferences.secondary_interests:
                context_parts.append(f"Secondary interests: {', '.join(user_preferences.secondary_interests)}")
            
            if user_preferences.custom_prompt:
                context_parts.append(f"Custom instructions: {user_preferences.custom_prompt}")
            
            return ". ".join(context_parts)
        else:
            # Fallback to legacy preferences
            return user.get_interests_for_llm()
    
    def _build_selection_prompt(
        self, 
        candidates: List[ArticleCandidate], 
        user_context: str,
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build the LLM prompt for article selection."""
        max_articles = user_preferences.max_articles_per_day if user_preferences else 15
        target_articles = min(max_articles, len(candidates), 15)  # Cap at 15 for now
        
        articles_json = json.dumps([candidate.to_dict() for candidate in candidates], indent=2)
        
        prompt = f"""You are an expert content curator for LinkedIn professionals. Your task is to select the {target_articles} most relevant and valuable articles from the following candidates for a user with these preferences:

USER CONTEXT:
{user_context}

CANDIDATE ARTICLES:
{articles_json}

SELECTION CRITERIA:
- Select exactly {target_articles} articles that would be most valuable for this user
- Prioritize articles that match the user's interests and professional context
- Consider content quality, relevance, and professional value
- Avoid duplicate or very similar topics
- Prefer recent, actionable content over old news

RESPONSE FORMAT:
Return a JSON object with this structure:
{{
    "selected_articles": [
        {{
            "url": "article_url",
            "title": "article_title", 
            "relevance_score": 0.85,
            "selection_reason": "Brief explanation of why this article was selected"
        }}
    ]
}}

Be sure to select exactly {target_articles} articles and provide clear reasoning for each selection."""
        
        return prompt
    
    async def _invoke_llm_with_structured_output(self, prompt: str) -> Dict[str, Any]:
        """
        Invoke LLM with structured output parsing.
        
        This is a placeholder for the actual LLM integration.
        In production, this would call the AI service.
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            Parsed LLM response as dictionary
        """
        # TODO: Replace with actual LLM service call
        # For now, return a mock response for testing
        logger.debug("Invoking LLM for content selection (mock implementation)")
        
        # This would be replaced with actual AI service call:
        # from app.services.ai_service import AIService
        # ai_service = AIService()
        # response = await ai_service.invoke_structured(prompt)
        # return response
        
        # Mock response for development
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            "selected_articles": [
                {
                    "url": "https://example.com/article1",
                    "title": "Sample Article 1",
                    "relevance_score": 0.85,
                    "selection_reason": "Highly relevant to user's interests in technology"
                },
                {
                    "url": "https://example.com/article2", 
                    "title": "Sample Article 2",
                    "relevance_score": 0.78,
                    "selection_reason": "Matches user's industry focus"
                }
            ]
        }
    
    def _parse_llm_selection_response(
        self, 
        llm_response: Dict[str, Any], 
        candidates: List[ArticleCandidate]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Parse the LLM response and match with candidate articles.
        
        Args:
            llm_response: Response from LLM
            candidates: Original candidate articles
            
        Returns:
            Tuple of (selected_articles, selection_reasons)
        """
        try:
            selected_articles = []
            selection_reasons = {}
            
            # Create URL to candidate mapping
            url_to_candidate = {candidate.url: candidate for candidate in candidates}
            
            for selection in llm_response.get("selected_articles", []):
                url = selection.get("url")
                if url in url_to_candidate:
                    candidate = url_to_candidate[url]
                    
                    article_data = {
                        "title": candidate.title,
                        "url": candidate.url,
                        "content": candidate.content,
                        "author": candidate.author,
                        "published_at": candidate.published_at.isoformat() if candidate.published_at else None,
                        "source_name": candidate.source_name,
                        "word_count": candidate.word_count,
                        "relevance_score": selection.get("relevance_score", 0.7),
                        "selection_reason": selection.get("selection_reason", "Selected by AI")
                    }
                    
                    selected_articles.append(article_data)
                    selection_reasons[url] = selection.get("selection_reason", "Selected by AI")
            
            return selected_articles, selection_reasons
            
        except Exception as e:
            logger.error(f"Error parsing LLM selection response: {str(e)}")
            # Fallback: return first few candidates
            fallback_articles = []
            fallback_reasons = {}
            
            for i, candidate in enumerate(candidates[:5]):  # Return first 5 as fallback
                article_data = {
                    "title": candidate.title,
                    "url": candidate.url,
                    "content": candidate.content,
                    "author": candidate.author,
                    "published_at": candidate.published_at.isoformat() if candidate.published_at else None,
                    "source_name": candidate.source_name,
                    "word_count": candidate.word_count,
                    "relevance_score": 0.7,
                    "selection_reason": "Fallback selection due to LLM parsing error"
                }
                
                fallback_articles.append(article_data)
                fallback_reasons[candidate.url] = "Fallback selection due to LLM parsing error"
            
            return fallback_articles, fallback_reasons
    
    async def _get_cached_selection(self, user_id: UUID) -> Optional[ContentSelectionResult]:
        """Get cached content selection for user."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._build_cache_key(user_id)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return ContentSelectionResult(
                    selected_articles=data["selected_articles"],
                    selection_reasons=data["selection_reasons"],
                    processing_details=data["processing_details"],
                    cache_key=cache_key,
                    selection_timestamp=datetime.fromisoformat(data["selection_timestamp"])
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving cached selection for user {user_id}: {str(e)}")
            return None
    
    async def _cache_selection_result(self, result: ContentSelectionResult) -> None:
        """Cache the selection result in Redis."""
        if not self.redis_client:
            return
        
        try:
            cache_data = {
                "selected_articles": result.selected_articles,
                "selection_reasons": result.selection_reasons,
                "processing_details": result.processing_details,
                "selection_timestamp": result.selection_timestamp.isoformat()
            }
            
            await self.redis_client.setex(
                result.cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached selection result with key: {result.cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching selection result: {str(e)}")
    
    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate cached content selection for user."""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._build_cache_key(user_id)
            await self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Error invalidating cache for user {user_id}: {str(e)}")
    
    def _build_cache_key(self, user_id: UUID) -> str:
        """Build cache key for user content selection."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"content_selection:{user_id}:{today}"
    
    def _empty_selection_result(self, user_id: UUID) -> ContentSelectionResult:
        """Create empty selection result."""
        return ContentSelectionResult(
            selected_articles=[],
            selection_reasons={},
            processing_details={
                "candidates_evaluated": 0,
                "articles_selected": 0,
                "processing_time_seconds": 0.0,
                "error": "No candidates found"
            },
            cache_key=self._build_cache_key(user_id),
            selection_timestamp=datetime.utcnow()
        )
    
    async def _record_content_selection(
        self,
        user_id: UUID,
        candidates_count: int,
        selected_count: int,
        processing_details: Dict[str, Any]
    ) -> None:
        """Record content selection in database for analytics."""
        try:
            selection_record = ContentSelection(
                user_id=user_id,
                selection_date=datetime.utcnow(),
                selection_type="llm_selection",
                articles_considered=candidates_count,
                articles_selected=selected_count,
                llm_model_used=processing_details.get("llm_model", "unknown"),
                selection_criteria=processing_details.get("selection_criteria", {}),
                processing_time_seconds=processing_details.get("processing_time_seconds", 0.0),
                selected_article_ids=[],  # Would be populated with actual IDs
                selection_scores={},  # Would be populated with scores
                selection_reasons={}  # Would be populated with reasons
            )
            
            self.session.add(selection_record)
            await self.session.flush()
            
            logger.debug(f"Recorded content selection for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording content selection: {str(e)}")
            # Don't raise - this is just for analytics
    
    # Legacy methods for backward compatibility
    async def process_all_sources(self, user_id: Optional[UUID] = None):
        """Legacy method - redirects to new LLM-based processing."""
        if user_id:
            return await self.process_content_with_llm_selection(user_id)
        else:
            # Process for all users with preferences
            users_with_prefs = await self.preferences_repo.get_users_with_preferences()
            results = []
            
            for user_info in users_with_prefs:
                try:
                    user_uuid = UUID(user_info["user_id"])
                    result = await self.process_content_with_llm_selection(user_uuid)
                    results.append({
                        "user_id": user_info["user_id"],
                        "selected_articles": len(result.selected_articles),
                        "success": True
                    })
                except Exception as e:
                    logger.error(f"Failed to process content for user {user_info['user_id']}: {str(e)}")
                    results.append({
                        "user_id": user_info["user_id"],
                        "selected_articles": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "users_processed": len(results),
                "total_successful": sum(1 for r in results if r["success"]),
                "total_failed": sum(1 for r in results if not r["success"]),
                "results": results
            }


# Factory function for dependency injection
async def get_enhanced_content_ingestion_service(
    redis_client: Optional[redis.Redis] = None
) -> EnhancedContentIngestionService:
    """
    Factory function to create EnhancedContentIngestionService with database session.
    
    Args:
        redis_client: Optional Redis client for caching
        
    Returns:
        EnhancedContentIngestionService instance
    """
    async with get_db_session() as session:
        return EnhancedContentIngestionService(session, redis_client)
"""
Content triage pipeline tasks for LinkedIn Presence Automation.

Implements end-to-end article processing: fetch_feeds → parse_articles → 
keyword_filter → llm_relevance_score → persist_relevant → enqueue_draft_generation
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from celery import shared_task
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.background_sessions import get_db_session_directly
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.repositories.user_repository import UserRepository
from app.services.rss_parser import RSSParser
from app.services.ai_service import AIService
from app.models.content import ContentSource, ContentItem, ContentStatus
from app.models.user import User
from app.schemas.ai_schemas import ContentRelevanceRequest

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def run_content_triage_pipeline(self, user_id: Optional[str] = None):
    """
    Run the complete content triage pipeline.
    
    Args:
        user_id: Optional specific user ID to process, otherwise processes all active users
    """
    try:
        logger.info(f"Starting content triage pipeline for user: {user_id or 'all users'}")
        
        result = asyncio.run(_run_triage_pipeline_async(user_id))
        
        logger.info(f"Content triage pipeline completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Content triage pipeline failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)

async def _run_triage_pipeline_async(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Async implementation of the content triage pipeline."""
    async with get_db_session_directly() as session:
        pipeline = ContentTriagePipeline(session)
        return await pipeline.run_complete_pipeline(user_id)

class ContentTriagePipeline:
    """Orchestrates the complete content triage pipeline."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.source_repo = ContentSourceRepository(session)
        self.content_repo = ContentItemRepository(session)
        self.user_repo = UserRepository(session)
        self.rss_parser = RSSParser()
        self.ai_service = AIService()
        
    async def run_complete_pipeline(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Run the complete pipeline for specified user or all users."""
        results = {
            "users_processed": 0,
            "sources_processed": 0,
            "articles_fetched": 0,
            "articles_filtered": 0,
            "articles_scored": 0,
            "articles_persisted": 0,
            "drafts_enqueued": 0,
            "errors": []
        }
        
        try:
            # Get users to process
            if user_id:
                users = [await self.user_repo.get_by_id(user_id)]
                users = [u for u in users if u and u.is_active]
            else:
                users = await self.user_repo.get_active_users()
            
            logger.info(f"Processing {len(users)} users")
            
            for user in users:
                try:
                    user_result = await self._process_user_pipeline(user)
                    
                    # Aggregate results
                    results["users_processed"] += 1
                    results["sources_processed"] += user_result["sources_processed"]
                    results["articles_fetched"] += user_result["articles_fetched"]
                    results["articles_filtered"] += user_result["articles_filtered"]
                    results["articles_scored"] += user_result["articles_scored"]
                    results["articles_persisted"] += user_result["articles_persisted"]
                    results["drafts_enqueued"] += user_result["drafts_enqueued"]
                    
                except Exception as e:
                    error_msg = f"Failed to process user {user.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            results["errors"].append(str(e))
            return results
    
    async def _process_user_pipeline(self, user: User) -> Dict[str, Any]:
        """Process the complete pipeline for a single user."""
        logger.info(f"Processing pipeline for user {user.id}")
        
        results = {
            "sources_processed": 0,
            "articles_fetched": 0,
            "articles_filtered": 0,
            "articles_scored": 0,
            "articles_persisted": 0,
            "drafts_enqueued": 0
        }
        
        # Step 1: Fetch feeds
        sources = await self.source_repo.get_active_sources_by_user(user.id)
        logger.info(f"Found {len(sources)} active sources for user {user.id}")
        
        all_articles = []
        for source in sources:
            try:
                articles = await self._fetch_feed_articles(source)
                all_articles.extend(articles)
                results["sources_processed"] += 1
                results["articles_fetched"] += len(articles)
                
            except Exception as e:
                logger.error(f"Failed to fetch from source {source.id}: {str(e)}")
                continue
        
        if not all_articles:
            logger.info(f"No articles found for user {user.id}")
            return results
        
        # Step 2: Keyword filtering
        filtered_articles = await self._apply_keyword_filters(all_articles, user)
        results["articles_filtered"] = len(filtered_articles)
        logger.info(f"Filtered to {len(filtered_articles)} articles for user {user.id}")
        
        # Step 3: LLM relevance scoring
        scored_articles = await self._score_articles_with_llm(filtered_articles, user)
        results["articles_scored"] = len(scored_articles)
        
        # Step 4: Persist relevant articles
        persisted_articles = await self._persist_relevant_articles(scored_articles, user)
        results["articles_persisted"] = len(persisted_articles)
        
        # Step 5: Enqueue draft generation for high-scoring articles
        drafts_enqueued = await self._enqueue_draft_generation(persisted_articles, user)
        results["drafts_enqueued"] = drafts_enqueued
        
        return results
    
    async def _fetch_feed_articles(self, source: ContentSource) -> List[Dict[str, Any]]:
        """Fetch articles from a content source."""
        try:
            if source.source_type == "rss_feed":
                feed_items = await self.rss_parser.parse_feed(source.url)
                
                articles = []
                for item in feed_items:
                    # Check for duplicates
                    if not await self.content_repo.check_duplicate_url(item.url):
                        articles.append({
                            "title": item.title,
                            "url": item.url,
                            "content": item.content,
                            "author": item.author,
                            "published_at": item.published_at,
                            "source_id": source.id,
                            "source_name": source.name
                        })
                
                return articles
                
            else:
                logger.warning(f"Unsupported source type: {source.source_type}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to fetch articles from source {source.id}: {str(e)}")
            return []
    
    async def _apply_keyword_filters(self, articles: List[Dict[str, Any]], user: User) -> List[Dict[str, Any]]:
        """Apply keyword-based filtering to articles."""
        filtered = []
        user_prefs = user.get_content_preferences_dict()
        
        # Get filtering criteria
        primary_interests = user_prefs.get("primary_interests", [])
        topics_to_avoid = user_prefs.get("topics_to_avoid", [])
        min_word_count = user_prefs.get("min_word_count", 200)
        max_age_hours = user_prefs.get("content_freshness_hours", 72)
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        for article in articles:
            try:
                # Check word count
                word_count = len(article["content"].split()) if article["content"] else 0
                if word_count < min_word_count:
                    continue
                
                # Check freshness
                if article["published_at"] and article["published_at"] < cutoff_time:
                    continue
                
                # Check avoid topics
                content_lower = (article["title"] + " " + article["content"]).lower()
                if any(avoid_topic.lower() in content_lower for avoid_topic in topics_to_avoid):
                    continue
                
                # Check interest keywords (if specified)
                if primary_interests:
                    if not any(interest.lower() in content_lower for interest in primary_interests):
                        continue
                
                filtered.append(article)
                
            except Exception as e:
                logger.warning(f"Error filtering article {article.get('url', 'unknown')}: {str(e)}")
                continue
        
        return filtered
    
    async def _score_articles_with_llm(self, articles: List[Dict[str, Any]], user: User) -> List[Dict[str, Any]]:
        """Score articles using LLM for relevance."""
        scored_articles = []
        user_context = user.get_interests_for_llm()
        
        # Process articles in batches to avoid overwhelming the LLM
        batch_size = 10
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            
            try:
                # Score each article in the batch
                for article in batch:
                    relevance_request = ContentRelevanceRequest(
                        content=article["content"][:1000],  # Limit content length
                        title=article["title"],
                        user_context=user_context,
                        user_preferences=user.get_content_preferences_dict()
                    )
                    
                    try:
                        relevance_result = await self.ai_service.assess_content_relevance(relevance_request)
                        
                        article["relevance_score"] = relevance_result.relevance_score
                        article["ai_analysis"] = {
                            "reasoning": relevance_result.reasoning,
                            "topic_category": relevance_result.topic_category,
                            "confidence": relevance_result.confidence,
                            "scored_at": datetime.utcnow().isoformat()
                        }
                        
                        # Only keep articles above threshold
                        min_score = user.get_content_preferences_dict().get("min_relevance_score", 0.7)
                        if relevance_result.relevance_score >= min_score:
                            scored_articles.append(article)
                            
                    except Exception as e:
                        logger.warning(f"Failed to score article {article['url']}: {str(e)}")
                        continue
                
                # Small delay between batches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process article batch: {str(e)}")
                continue
        
        return scored_articles
    
    async def _persist_relevant_articles(self, articles: List[Dict[str, Any]], user: User) -> List[ContentItem]:
        """Persist relevant articles to the database."""
        persisted = []
        
        for article in articles:
            try:
                # Create content item
                content_item = await self.content_repo.create(
                    source_id=article["source_id"],
                    title=article["title"],
                    url=article["url"],
                    content=article["content"],
                    author=article.get("author"),
                    published_at=article.get("published_at"),
                    relevance_score=int(article["relevance_score"] * 100),
                    ai_analysis=article["ai_analysis"],
                    status=ContentStatus.PROCESSED,
                    word_count=len(article["content"].split()) if article["content"] else 0
                )
                
                persisted.append(content_item)
                
            except Exception as e:
                logger.error(f"Failed to persist article {article['url']}: {str(e)}")
                continue
        
        return persisted
    
    async def _enqueue_draft_generation(self, articles: List[ContentItem], user: User) -> int:
        """Enqueue draft generation for high-scoring articles."""
        from app.tasks.draft_generation_tasks import generate_draft_from_content_task
        
        enqueued_count = 0
        high_score_threshold = 80  # Only auto-generate for very relevant content
        
        for article in articles:
            try:
                if article.relevance_score and article.relevance_score >= high_score_threshold:
                    # Enqueue draft generation task
                    generate_draft_from_content_task.delay(
                        content_item_id=str(article.id),
                        user_id=str(user.id)
                    )
                    enqueued_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to enqueue draft generation for article {article.id}: {str(e)}")
                continue
        
        return enqueued_count

@shared_task(bind=True, max_retries=2)
def generate_draft_from_content_task(self, content_item_id: str, user_id: str):
    """Generate a draft from a content item."""
    try:
        logger.info(f"Generating draft from content {content_item_id} for user {user_id}")
        
        result = asyncio.run(_generate_draft_async(content_item_id, user_id))
        
        logger.info(f"Draft generation completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Draft generation failed: {str(e)}")
        raise self.retry(countdown=600, exc=e)

async def _generate_draft_async(content_item_id: str, user_id: str) -> Dict[str, Any]:
    """Async implementation of draft generation."""
    async with get_db_session_directly() as session:
        from app.services.content_generator import ContentGenerator
        
        generator = ContentGenerator(session)
        
        try:
            draft = await generator.generate_post_from_content(
                content_item_id=content_item_id,
                user_id=user_id,
                style="professional_thought_leader"
            )
            
            # Mark content item as having draft generated
            content_repo = ContentItemRepository(session)
            await content_repo.update(content_item_id, draft_generated=True)
            
            return {
                "success": True,
                "draft_id": str(draft.id),
                "content_item_id": content_item_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate draft: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content_item_id": content_item_id
            }

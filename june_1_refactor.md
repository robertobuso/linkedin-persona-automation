Backend Files

### `migrations/versions/add_draft_generated_field.py`
```python
"""Add draft_generated field to content_items

Revision ID: add_draft_generated_field
Revises: previous_revision
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_draft_generated_field'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Add draft_generated field to content_items table
    op.add_column('content_items', sa.Column('draft_generated', sa.Boolean(), default=False, nullable=False))
    
    # Create index for performance
    op.create_index('ix_content_items_draft_generated', 'content_items', ['draft_generated'])

def downgrade():
    # Remove index and column
    op.drop_index('ix_content_items_draft_generated', table_name='content_items')
    op.drop_column('content_items', 'draft_generated')
```

### `app/tasks/content_triage_tasks.py`
```python
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
```

### `app/services/linkedin_client.py`
```python
"""
LinkedIn API client for reading feeds and interacting with posts.

Provides capabilities for:
- Reading user's LinkedIn feed
- Liking posts
- Commenting on posts
- Getting post details
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from playwright.async_api import async_playwright, Browser, Page

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class LinkedInClientError(Exception):
    """Base exception for LinkedIn client errors."""
    pass

class LinkedInClient:
    """
    LinkedIn API and web scraping client.
    
    Handles both official API calls and web scraping for features
    not available through the official API.
    """
    
    def __init__(self):
        self.api_base_url = "https://api.linkedin.com/v2"
        self.browser: Optional[Browser] = None
        
    async def get_user_feed(self, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's LinkedIn feed posts.
        
        Args:
            user: User with LinkedIn credentials
            limit: Number of posts to fetch
            
        Returns:
            List of feed post dictionaries
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            # Try API first, fall back to web scraping
            try:
                return await self._get_feed_via_api(user, limit)
            except Exception as api_error:
                logger.warning(f"API method failed, trying web scraping: {api_error}")
                return await self._get_feed_via_scraping(user, limit)
                
        except Exception as e:
            logger.error(f"Failed to get user feed: {str(e)}")
            raise LinkedInClientError(f"Failed to get feed: {str(e)}")
    
    async def like_post(self, user: User, post_urn: str) -> Dict[str, Any]:
        """
        Like a LinkedIn post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            
        Returns:
            Response from like action
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn API endpoint for likes
            url = f"{self.api_base_url}/socialActions/{post_urn}/likes"
            
            like_data = {
                "actor": f"urn:li:person:{user.id}",
                "object": post_urn
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=like_data, headers=headers) as response:
                    if response.status == 201:
                        return {"success": True, "message": "Post liked successfully"}
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to like post: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to like post: {str(e)}")
            raise LinkedInClientError(f"Failed to like post: {str(e)}")
    
    async def comment_on_post(self, user: User, post_urn: str, comment_text: str) -> Dict[str, Any]:
        """
        Comment on a LinkedIn post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            comment_text: Comment content
            
        Returns:
            Response from comment action
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn API endpoint for comments
            url = f"{self.api_base_url}/socialActions/{post_urn}/comments"
            
            comment_data = {
                "actor": f"urn:li:person:{user.id}",
                "object": post_urn,
                "message": {
                    "text": comment_text
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=comment_data, headers=headers) as response:
                    if response.status == 201:
                        response_data = await response.json()
                        return {
                            "success": True,
                            "comment_id": response_data.get("id"),
                            "message": "Comment posted successfully"
                        }
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to comment: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to comment on post: {str(e)}")
            raise LinkedInClientError(f"Failed to comment: {str(e)}")
    
    async def get_post_details(self, user: User, post_urn: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            
        Returns:
            Post details dictionary
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Get post data
            url = f"{self.api_base_url}/shares/{post_urn}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to get post details: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to get post details: {str(e)}")
            raise LinkedInClientError(f"Failed to get post details: {str(e)}")
    
    async def _get_feed_via_api(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get feed using LinkedIn API."""
        headers = {
            "Authorization": f"Bearer {user.linkedin_access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # LinkedIn API endpoint for feed
        url = f"{self.api_base_url}/shares"
        params = {
            "q": "owners",
            "owners": f"urn:li:person:{user.id}",
            "count": limit,
            "projection": "(elements*(id,activity,commentary,content,created,edited,lastModified,owner,resharedShare,socialCounts))"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_api_feed_response(data)
                else:
                    error_text = await response.text()
                    raise LinkedInClientError(f"API request failed: {error_text}")
    
    async def _get_feed_via_scraping(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get feed using web scraping as fallback."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
        
        context = await self.browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to LinkedIn
            await page.goto("https://www.linkedin.com/login")
            
            # Note: In production, you'd need to handle LinkedIn authentication
            # This is a simplified example
            await page.fill("#username", user.email)
            await page.fill("#password", "user_password")  # You'd need to securely store this
            await page.click("[type='submit']")
            
            # Wait for redirect to feed
            await page.wait_for_url("**/feed/**")
            
            # Scrape feed posts
            posts = await page.query_selector_all('[data-id^="urn:li:activity"]')
            
            feed_posts = []
            for i, post in enumerate(posts[:limit]):
                try:
                    post_data = await self._extract_post_data(page, post)
                    if post_data:
                        feed_posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Failed to extract post {i}: {str(e)}")
                    continue
            
            return feed_posts
            
        finally:
            await context.close()
    
    def _format_api_feed_response(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format API response into standardized feed post format."""
        posts = []
        
        for element in api_response.get("elements", []):
            try:
                post = {
                    "id": element.get("id"),
                    "urn": element.get("id"),
                    "author": self._extract_author_info(element),
                    "content": self._extract_content_text(element),
                    "created_time": element.get("created", {}).get("time"),
                    "social_counts": element.get("socialCounts", {}),
                    "type": "feed_post",
                    "platform": "linkedin"
                }
                posts.append(post)
                
            except Exception as e:
                logger.warning(f"Failed to format post: {str(e)}")
                continue
        
        return posts
    
    async def _extract_post_data(self, page: Page, post_element) -> Optional[Dict[str, Any]]:
        """Extract post data from scraped element."""
        try:
            # Extract post URN
            post_id = await post_element.get_attribute("data-id")
            
            # Extract author info
            author_element = await post_element.query_selector(".feed-shared-actor__name")
            author_name = await author_element.inner_text() if author_element else "Unknown"
            
            # Extract content
            content_element = await post_element.query_selector(".feed-shared-text")
            content_text = await content_element.inner_text() if content_element else ""
            
            # Extract engagement counts
            likes_element = await post_element.query_selector("[aria-label*='reaction']")
            likes_text = await likes_element.inner_text() if likes_element else "0"
            
            return {
                "id": post_id,
                "urn": post_id,
                "author": {"name": author_name},
                "content": content_text,
                "created_time": datetime.utcnow().timestamp() * 1000,  # Approximate
                "social_counts": {
                    "numLikes": self._parse_engagement_count(likes_text)
                },
                "type": "feed_post",
                "platform": "linkedin"
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract post data: {str(e)}")
            return None
    
    def _extract_author_info(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract author information from API response element."""
        owner = element.get("owner", {})
        return {
            "id": owner.get("id"),
            "name": owner.get("localizedName", "Unknown")
        }
    
    def _extract_content_text(self, element: Dict[str, Any]) -> str:
        """Extract content text from API response element."""
        commentary = element.get("commentary", {})
        return commentary.get("text", "")
    
    def _parse_engagement_count(self, count_text: str) -> int:
        """Parse engagement count from text."""
        try:
            # Handle formats like "123", "1.2K", "1.2M"
            count_text = count_text.strip().replace(",", "")
            
            if "K" in count_text:
                return int(float(count_text.replace("K", "")) * 1000)
            elif "M" in count_text:
                return int(float(count_text.replace("M", "")) * 1000000)
            else:
                return int(count_text) if count_text.isdigit() else 0
                
        except (ValueError, AttributeError):
            return 0
    
    async def close(self):
        """Close browser resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

# Singleton instance
linkedin_client = LinkedInClient()
```

### `app/routers/linkedin_router.py`
```python
"""
LinkedIn integration router for feed reading and interactions.

Provides endpoints for:
- Reading LinkedIn feed
- Liking posts
- Commenting on posts
- Getting post details
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.services.linkedin_client import linkedin_client, LinkedInClientError
from app.models.user import User
from app.schemas.linkedin_schemas import (
    LinkedInFeedPost,
    LinkedInInteractionRequest,
    LinkedInInteractionResponse,
    LinkedInPostDetails
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/feed", response_model=List[LinkedInFeedPost])
async def get_linkedin_feed(
    limit: int = Query(20, ge=1, le=100, description="Number of posts to fetch"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[LinkedInFeedPost]:
    """Get user's LinkedIn feed posts."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        feed_posts = await linkedin_client.get_user_feed(current_user, limit)
        
        return [LinkedInFeedPost(**post) for post in feed_posts]
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn client error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get LinkedIn feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LinkedIn feed"
        )

@router.post("/like", response_model=LinkedInInteractionResponse)
async def like_linkedin_post(
    request: LinkedInInteractionRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInInteractionResponse:
    """Like a LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        result = await linkedin_client.like_post(current_user, request.post_urn)
        
        return LinkedInInteractionResponse(
            success=result["success"],
            message=result["message"],
            interaction_type="like",
            post_urn=request.post_urn
        )
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn like error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to like LinkedIn post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like post"
        )

@router.post("/comment", response_model=LinkedInInteractionResponse)
async def comment_on_linkedin_post(
    request: LinkedInInteractionRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInInteractionResponse:
    """Comment on a LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        if not request.comment_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment text is required"
            )
        
        result = await linkedin_client.comment_on_post(
            current_user, 
            request.post_urn, 
            request.comment_text
        )
        
        return LinkedInInteractionResponse(
            success=result["success"],
            message=result["message"],
            interaction_type="comment",
            post_urn=request.post_urn,
            comment_id=result.get("comment_id")
        )
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn comment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to comment on LinkedIn post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to comment on post"
        )

@router.get("/post/{post_urn}", response_model=LinkedInPostDetails)
async def get_linkedin_post_details(
    post_urn: str,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInPostDetails:
    """Get detailed information about a specific LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        post_details = await linkedin_client.get_post_details(current_user, post_urn)
        
        return LinkedInPostDetails(**post_details)
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn post details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get LinkedIn post details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get post details"
        )

@router.get("/status")
async def get_linkedin_connection_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get LinkedIn connection status for the current user."""
    return {
        "connected": current_user.has_valid_linkedin_token(),
        "has_token": bool(current_user.linkedin_access_token),
        "token_expires_at": current_user.linkedin_token_expires_at.isoformat() if current_user.linkedin_token_expires_at else None,
        "user_id": str(current_user.id)
    }
```

### `app/schemas/linkedin_schemas.py`
```python
"""
Pydantic schemas for LinkedIn integration.

Defines data models for LinkedIn feed posts, interactions, and responses.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class LinkedInAuthor(BaseModel):
    """LinkedIn post author information."""
    id: Optional[str] = None
    name: str
    profile_url: Optional[str] = None
    profile_image: Optional[str] = None

class LinkedInSocialCounts(BaseModel):
    """LinkedIn post engagement counts."""
    numLikes: Optional[int] = 0
    numComments: Optional[int] = 0
    numShares: Optional[int] = 0
    numViews: Optional[int] = 0

class LinkedInFeedPost(BaseModel):
    """LinkedIn feed post model."""
    id: str
    urn: str
    author: LinkedInAuthor
    content: str
    created_time: Optional[int] = None
    social_counts: Optional[LinkedInSocialCounts] = None
    type: str = "feed_post"
    platform: str = "linkedin"
    
    class Config:
        extra = "allow"

class LinkedInInteractionRequest(BaseModel):
    """Request model for LinkedIn interactions."""
    post_urn: str = Field(..., description="LinkedIn post URN")
    comment_text: Optional[str] = Field(None, description="Comment text for comment interactions")
    
    class Config:
        schema_extra = {
            "example": {
                "post_urn": "urn:li:activity:123456789",
                "comment_text": "Great insights! Thanks for sharing."
            }
        }

class LinkedInInteractionResponse(BaseModel):
    """Response model for LinkedIn interactions."""
    success: bool
    message: str
    interaction_type: str  # "like", "comment", "share"
    post_urn: str
    comment_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Post liked successfully",
                "interaction_type": "like",
                "post_urn": "urn:li:activity:123456789",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class LinkedInPostDetails(BaseModel):
    """Detailed LinkedIn post information."""
    id: str
    urn: str
    author: LinkedInAuthor
    content: str
    created_time: Optional[int] = None
    last_modified: Optional[int] = None
    social_counts: Optional[LinkedInSocialCounts] = None
    comments: Optional[List[Dict[str, Any]]] = []
    media: Optional[List[Dict[str, Any]]] = []
    tags: Optional[List[str]] = []
    
    class Config:
        extra = "allow"

class LinkedInFeedResponse(BaseModel):
    """Response model for LinkedIn feed requests."""
    posts: List[LinkedInFeedPost]
    total_count: int
    has_more: bool = False
    next_cursor: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "posts": [],
                "total_count": 10,
                "has_more": False
            }
        }

class LinkedInConnectionStatus(BaseModel):
    """LinkedIn connection status model."""
    connected: bool
    has_token: bool
    token_expires_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
```

### `app/routers/enhanced_drafts_router.py`
```python
"""
Enhanced draft management router with tone selection and regeneration.

Extends existing draft functionality with:
- Tone-based regeneration
- Duplicate prevention
- Real-time updates
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.content_repository import PostDraftRepository, ContentItemRepository
from app.services.content_generator import ContentGenerator
from app.models.user import User
from app.models.content import PostDraft, DraftStatus
from app.schemas.enhanced_draft_schemas import (
    DraftRegenerateRequest,
    DraftWithContent,
    ToneStyle,
    DraftRegenerateResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{draft_id}/regenerate", response_model=DraftRegenerateResponse)
async def regenerate_draft_with_tone(
    draft_id: UUID,
    request: DraftRegenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> DraftRegenerateResponse:
    """
    Regenerate a draft with specified tone style.
    
    Args:
        draft_id: Draft ID to regenerate
        request: Regeneration request with tone style
        current_user: Current authenticated user
    
    Returns:
        Regenerated draft response
    """
    async with db_session_cm as session:
        try:
            draft_repo = PostDraftRepository(session)
            content_generator = ContentGenerator(session)
            
            # Get and validate draft
            draft = await draft_repo.get_by_id(draft_id)
            if not draft:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Draft not found"
                )
            
            if draft.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Regenerate with new tone
            regenerated_draft = await content_generator.regenerate_post_draft(
                draft_id=draft_id,
                user_id=current_user.id,
                style=request.tone_style.value,
                preserve_hashtags=request.preserve_hashtags
            )
            
            return DraftRegenerateResponse(
                draft=DraftWithContent.from_orm(regenerated_draft),
                tone_style=request.tone_style,
                regenerated_at=regenerated_draft.updated_at,
                success=True,
                message="Draft regenerated successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to regenerate draft {draft_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to regenerate draft"
            )

@router.get("/all", response_model=List[DraftWithContent])
async def get_all_user_drafts(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[DraftWithContent]:
    """
    Get all drafts for the current user ordered by updated_at DESC.
    
    Returns:
        List of all user drafts with full content
    """
    async with db_session_cm as session:
        try:
            draft_repo = PostDraftRepository(session)
            
            # Get all drafts for user, ordered by updated_at DESC
            all_drafts = await draft_repo.list_with_pagination(
                page=1,
                page_size=1000,  # Large limit to get all drafts
                order_by="updated_at",
                order_desc=True,
                user_id=current_user.id
            )
            
            return [DraftWithContent.from_orm(draft) for draft in all_drafts["items"]]
            
        except Exception as e:
            logger.error(f"Failed to get all drafts for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get drafts"
            )

@router.post("/generate-from-content", response_model=DraftWithContent, status_code=status.HTTP_201_CREATED)
async def generate_draft_from_content(
    content_item_id: UUID = Body(..., embed=True),
    tone_style: ToneStyle = Body(ToneStyle.PROFESSIONAL, embed=True),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> DraftWithContent:
    """
    Generate a draft from content with tone selection and duplicate prevention.
    
    Args:
        content_item_id: Content item to generate draft from
        tone_style: Tone style for generation
        current_user: Current authenticated user
    
    Returns:
        Generated draft with full content
    """
    async with db_session_cm as session:
        try:
            content_repo = ContentItemRepository(session)
            content_generator = ContentGenerator(session)
            
            # Check if content item exists and belongs to user
            content_item = await content_repo.get_by_id(content_item_id)
            if not content_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Content item not found"
                )
            
            # Check if draft already generated (duplicate prevention)
            if hasattr(content_item, 'draft_generated') and content_item.draft_generated:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Draft already generated for this content item"
                )
            
            # Verify user has access to this content item through sources
            # (Assuming content items are accessible through user's sources)
            
            # Generate draft
            new_draft = await content_generator.generate_post_from_content(
                content_item_id=content_item_id,
                user_id=current_user.id,
                style=tone_style.value
            )
            
            # Mark content item as having draft generated
            await content_repo.update(content_item_id, draft_generated=True)
            
            return DraftWithContent.from_orm(new_draft)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate draft from content {content_item_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate draft"
            )

@router.get("/tone-styles", response_model=List[Dict[str, str]])
async def get_available_tone_styles() -> List[Dict[str, str]]:
    """
    Get available tone styles for draft generation.
    
    Returns:
        List of available tone styles with descriptions
    """
    return [
        {
            "value": ToneStyle.PROFESSIONAL.value,
            "label": "Professional",
            "description": "Formal, business-focused tone"
        },
        {
            "value": ToneStyle.CONVERSATIONAL.value,
            "label": "Conversational",
            "description": "Friendly, approachable tone"
        },
        {
            "value": ToneStyle.STORYTELLING.value,
            "label": "Storytelling",
            "description": "Narrative-driven, engaging tone"
        },
        {
            "value": ToneStyle.HUMOROUS.value,
            "label": "Humorous",
            "description": "Light-hearted, entertaining tone"
        }
    ]

@router.get("/stats", response_model=Dict[str, Any])
async def get_draft_statistics(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get draft statistics for the current user.
    
    Returns:
        Draft statistics including counts by status
    """
    async with db_session_cm as session:
        try:
            draft_repo = PostDraftRepository(session)
            stats = await draft_repo.get_user_drafts_summary(current_user.id)
            
            return {
                **stats,
                "user_id": str(current_user.id),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get draft stats for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get draft statistics"
            )
```

### `app/schemas/enhanced_draft_schemas.py`
```python
"""
Enhanced schemas for draft management with tone selection.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field

class ToneStyle(str, Enum):
    """Available tone styles for draft generation."""
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    STORYTELLING = "storytelling"
    HUMOROUS = "humorous"

class DraftRegenerateRequest(BaseModel):
    """Request model for draft regeneration."""
    tone_style: ToneStyle = Field(..., description="Tone style for regeneration")
    preserve_hashtags: bool = Field(False, description="Whether to preserve existing hashtags")
    
    class Config:
        schema_extra = {
            "example": {
                "tone_style": "storytelling",
                "preserve_hashtags": False
            }
        }

class DraftWithContent(BaseModel):
    """Draft model with full content details."""
    id: UUID
    user_id: UUID
    content: str
    hashtags: List[str]
    title: Optional[str] = None
    status: str
    scheduled_for: Optional[datetime] = None
    published_at: Optional[datetime] = None
    linkedin_post_id: Optional[str] = None
    linkedin_post_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Generation metadata
    generation_metadata: Optional[dict] = None
    ai_model_used: Optional[str] = None
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "content": "Excited to share insights about AI in business...",
                "hashtags": ["#AI", "#Business", "#Innovation"],
                "status": "ready",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class DraftRegenerateResponse(BaseModel):
    """Response model for draft regeneration."""
    draft: DraftWithContent
    tone_style: ToneStyle
    regenerated_at: datetime
    success: bool = True
    message: str = "Draft regenerated successfully"
    
    class Config:
        schema_extra = {
            "example": {
                "draft": {},  # DraftWithContent example
                "tone_style": "storytelling",
                "regenerated_at": "2024-01-15T10:35:00Z",
                "success": True,
                "message": "Draft regenerated successfully"
            }
        }

class ContentItemWithDraftStatus(BaseModel):
    """Content item model with draft generation status."""
    id: UUID
    title: str
    content: str
    url: str
    source_name: str
    published_at: Optional[datetime]
    relevance_score: Optional[int]
    draft_generated: bool = False
    tags: List[str] = []
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "The Future of AI in Business",
                "content": "Article content here...",
                "url": "https://example.com/article",
                "source_name": "Tech News",
                "draft_generated": False,
                "relevance_score": 85
            }
        }
```

Frontend Files
### `frontend/src/components/content/ContentCard.tsx`
```tsx
import React, { useState } from 'react'
import { 
  ExternalLinkIcon, 
  SparklesIcon, 
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ContentItem } from '@/lib/api'
import { useGenerateDraft } from '@/hooks/useEnhancedDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'
import { useRouter } from 'next/router'

interface ContentCardProps {
  content: ContentItem & { draft_generated?: boolean }
  viewMode: string
}

export function ContentCard({ content, viewMode }: ContentCardProps) {
  const router = useRouter()
  const { mutateAsync: generateDraft, isLoading } = useGenerateDraft()
  const [toneStyle, setToneStyle] = useState<string>('professional')

  const handleGenerateDraft = async () => {
    if (content.draft_generated) {
      notify.warning('Draft already generated for this content')
      return
    }

    try {
      const newDraft = await generateDraft({
        content_item_id: content.id,
        tone_style: toneStyle
      })
      
      notify.success('Draft generated successfully!')
      
      // Redirect to the new draft page
      router.push(`/drafts/${newDraft.id}`)
      
    } catch (error: any) {
      if (error.status === 409) {
        notify.warning('Draft already generated for this content')
      } else {
        notify.error('Failed to generate draft')
      }
    }
  }

  const handleReadOriginal = () => {
    window.open(content.url, '_blank', 'noopener,noreferrer')
  }

  return (
    <Card hover="lift" className="relative">
      {content.ai_analysis?.llm_selected && (
        <div className="absolute top-4 right-4 z-10">
          <Badge variant="ai" icon={<SparklesIcon className="h-3 w-3" />}>
            AI Selected
          </Badge>
        </div>
      )}

      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="pr-20">
          <h3 className="text-lg font-semibold text-neural-700 mb-2 line-clamp-2">
            {content.title}
          </h3>
          <p className="text-gray-600 line-clamp-3">
            {content.content.substring(0, 200)}...
          </p>
        </div>

        {/* Content Metadata */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <span className="font-medium">{content.source_name}</span>
            <div className="flex items-center space-x-1">
              <ClockIcon className="h-4 w-4" />
              <span>{formatDistanceToNow(new Date(content.published_at), { addSuffix: true })}</span>
            </div>
            {content.relevance_score && (
              <div className="flex items-center space-x-1 text-ml-green-600">
                <span className="font-medium">{content.relevance_score}% relevant</span>
              </div>
            )}
          </div>
        </div>

        {/* Tags */}
        {content.tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {content.tags.slice(0, 6).map(tag => (
              <Badge key={tag} variant="neutral" size="sm">
                {tag}
              </Badge>
            ))}
            {content.tags.length > 6 && (
              <Badge variant="outline" size="sm">
                +{content.tags.length - 6} more
              </Badge>
            )}
          </div>
        )}

        {/* Tone Style Selector (only show when generating) */}
        {!content.draft_generated && !isLoading && (
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Tone:</label>
            <select
              value={toneStyle}
              onChange={(e) => setToneStyle(e.target.value)}
              className="text-sm border border-gray-200 rounded px-2 py-1"
            >
              <option value="professional">Professional</option>
              <option value="conversational">Conversational</option>
              <option value="storytelling">Storytelling</option>
              <option value="humorous">Humorous</option>
            </select>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            {content.draft_generated ? (
              <Badge 
                variant="success" 
                icon={<CheckCircleIcon className="h-4 w-4" />}
                className="px-3 py-2"
              >
                DRAFT GENERATED
              </Badge>
            ) : (
              <Button
                size="sm"
                onClick={handleGenerateDraft}
                loading={isLoading}
                variant="ai"
                leftIcon={<SparklesIcon className="h-4 w-4" />}
              >
                Generate Draft
              </Button>
            )}
            
            <Button 
              size="sm" 
              variant="outline"
              onClick={handleReadOriginal}
              leftIcon={<ExternalLinkIcon className="h-4 w-4" />}
            >
              Read Original
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
```

### `frontend/src/components/creation/EnhancedDraftCard.tsx`
```tsx
import React, { useState } from 'react'
import { 
  PaperAirplaneIcon, 
  PencilIcon, 
  ArrowPathIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { DraftWithContent } from '@/lib/api'
import { useUpdateDraft, usePublishDraft, useDeleteDraft } from '@/hooks/useDrafts'
import { useRegenerateDraft } from '@/hooks/useEnhancedDrafts'
import { formatDistanceToNow } from 'date-fns'
import { notify } from '@/stores/uiStore'
import { RegenerateModal } from './RegenerateModal'

interface EnhancedDraftCardProps {
  draft: DraftWithContent
  isSelected?: boolean
  onSelect?: () => void
  showFullContent?: boolean
}

export function EnhancedDraftCard({ 
  draft, 
  isSelected = false, 
  onSelect,
  showFullContent = false 
}: EnhancedDraftCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showRegenerateModal, setShowRegenerateModal] = useState(false)
  
  const { mutateAsync: publishDraft, isLoading: isPublishing } = usePublishDraft()
  const { mutateAsync: regenerateDraft, isLoading: isRegenerating } = useRegenerateDraft()
  const { mutateAsync: deleteDraft, isLoading: isDeleting } = useDeleteDraft()

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'success'
      case 'scheduled': return 'default'
      case 'published': return 'ml-green'
      case 'failed': return 'destructive'
      default: return 'secondary'
    }
  }

  const handlePublish = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await publishDraft({ draftId: draft.id })
      notify.success('Draft published successfully!')
    } catch (error) {
      notify.error('Failed to publish draft')
    }
  }

  const handleRegenerate = async (toneStyle: string, preserveHashtags: boolean) => {
    try {
      await regenerateDraft({
        draftId: draft.id,
        options: {
          tone_style: toneStyle,
          preserve_hashtags: preserveHashtags
        }
      })
      notify.success('Draft regenerated successfully! 👌')
      setShowRegenerateModal(false)
    } catch (error) {
      notify.error('Failed to regenerate draft')
    }
  }

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (window.confirm('Are you sure you want to delete this draft?')) {
      try {
        await deleteDraft(draft.id)
        notify.success('Draft deleted successfully')
      } catch (error) {
        notify.error('Failed to delete draft')
      }
    }
  }

  const shouldTruncateContent = !isExpanded && draft.content.length > 400
  const displayContent = shouldTruncateContent 
    ? draft.content.substring(0, 400) + '...'
    : draft.content

  return (
    <>
      <Card 
        hover="lift"
        className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-neural-500' : ''}`}
        onClick={onSelect}
      >
        <div className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="font-semibold text-neural-700 mb-2 line-clamp-1">
                {draft.title || 'Untitled Draft'}
              </h3>
              <Badge variant={getStatusColor(draft.status)} size="sm">
                {draft.status}
              </Badge>
            </div>
          </div>

          {/* Content with Show More/Less */}
          <div className="mb-4">
            <div 
              className={`text-gray-700 whitespace-pre-wrap ${shouldTruncateContent ? 'max-h-[400px] overflow-hidden' : ''}`}
            >
              {displayContent}
            </div>
            
            {draft.content.length > 400 && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setIsExpanded(!isExpanded)
                }}
                className="mt-2 text-sm text-neural-600 hover:text-neural-800 flex items-center space-x-1"
              >
                {isExpanded ? (
                  <>
                    <EyeSlashIcon className="h-4 w-4" />
                    <span>Show less</span>
                  </>
                ) : (
                  <>
                    <EyeIcon className="h-4 w-4" />
                    <span>Show more</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Hashtags */}
          {draft.hashtags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {draft.hashtags.map((hashtag, index) => (
                <Badge key={index} variant="outline" size="sm">
                  {hashtag.startsWith('#') ? hashtag : `#${hashtag}`}
                </Badge>
              ))}
            </div>
          )}

          {/* Metadata */}
          <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span>{formatDistanceToNow(new Date(draft.created_at), { addSuffix: true })}</span>
            {draft.generation_metadata?.word_count_validated && (
              <span>{draft.generation_metadata.word_count_validated} words</span>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-100">
            <div className="flex space-x-2">
              {draft.status === 'ready' && (
                <Button
                  size="sm"
                  variant="ai"
                  onClick={handlePublish}
                  loading={isPublishing}
                  leftIcon={<PaperAirplaneIcon className="h-3 w-3" />}
                >
                  Publish
                </Button>
              )}
              
              <Button
                size="sm"
                variant="outline"
                onClick={(e) => {
                  e.stopPropagation()
                  setShowRegenerateModal(true)
                }}
                loading={isRegenerating}
                leftIcon={<ArrowPathIcon className="h-3 w-3" />}
              >
                Regenerate
              </Button>
            </div>

            <div className="flex space-x-1">
              <Button
                size="sm"
                variant="ghost"
                leftIcon={<CalendarIcon className="h-4 w-4" />}
              >
                Schedule
              </Button>
              
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDelete}
                loading={isDeleting}
                leftIcon={<TrashIcon className="h-4 w-4" />}
                className="text-red-600 hover:text-red-700"
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Regenerate Modal */}
      <RegenerateModal
        isOpen={showRegenerateModal}
        onClose={() => setShowRegenerateModal(false)}
        onRegenerate={handleRegenerate}
        isLoading={isRegenerating}
        currentHashtags={draft.hashtags}
      />
    </>
  )
}
```

### `frontend/src/components/creation/RegenerateModal.tsx`
```tsx
import React, { useState } from 'react'
import { 
  XMarkIcon, 
  ArrowPathIcon,
  SparklesIcon 
} from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

interface RegenerateModalProps {
  isOpen: boolean
  onClose: () => void
  onRegenerate: (toneStyle: string, preserveHashtags: boolean) => void
  isLoading?: boolean
  currentHashtags?: string[]
}

export function RegenerateModal({ 
  isOpen, 
  onClose, 
  onRegenerate, 
  isLoading = false,
  currentHashtags = []
}: RegenerateModalProps) {
  const [selectedTone, setSelectedTone] = useState('professional')
  const [preserveHashtags, setPreserveHashtags] = useState(false)

  const toneOptions = [
    {
      value: 'professional',
      label: 'Professional',
      description: 'Formal, business-focused tone',
      icon: '💼'
    },
    {
      value: 'conversational',
      label: 'Conversational',
      description: 'Friendly, approachable tone',
      icon: '💬'
    },
    {
      value: 'storytelling',
      label: 'Storytelling',
      description: 'Narrative-driven, engaging tone',
      icon: '📖'
    },
    {
      value: 'humorous',
      label: 'Humorous',
      description: 'Light-hearted, entertaining tone',
      icon: '😄'
    }
  ]

  const handleRegenerate = () => {
    onRegenerate(selectedTone, preserveHashtags)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-2">
              <ArrowPathIcon className="h-5 w-5 text-neural-600" />
              <h2 className="text-lg font-semibold text-neural-700">
                Regenerate Draft
              </h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
              disabled={isLoading}
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Tone Selection */}
          <div className="space-y-4 mb-6">
            <label className="block text-sm font-medium text-gray-700">
              Choose Tone Style
            </label>
            
            <div className="space-y-3">
              {toneOptions.map((option) => (
                <label
                  key={option.value}
                  className={`flex items-start space-x-3 p-3 rounded-lg border cursor-pointer transition-all ${
                    selectedTone === option.value
                      ? 'border-neural-500 bg-neural-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="tone"
                    value={option.value}
                    checked={selectedTone === option.value}
                    onChange={(e) => setSelectedTone(e.target.value)}
                    className="mt-1"
                    disabled={isLoading}
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{option.icon}</span>
                      <span className="font-medium text-gray-900">
                        {option.label}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {option.description}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Hashtag Preservation */}
          {currentHashtags.length > 0 && (
            <div className="mb-6">
              <label className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={preserveHashtags}
                  onChange={(e) => setPreserveHashtags(e.target.checked)}
                  className="mt-1"
                  disabled={isLoading}
                />
                <div>
                  <span className="block text-sm font-medium text-gray-700">
                    Preserve current hashtags
                  </span>
                  <p className="text-sm text-gray-600 mt-1">
                    Keep existing hashtags: {currentHashtags.join(' ')}
                  </p>
                </div>
              </label>
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3">
            <Button
              onClick={handleRegenerate}
              loading={isLoading}
              variant="ai"
              leftIcon={<SparklesIcon className="h-4 w-4" />}
              className="flex-1"
            >
              Regenerate Draft
            </Button>
            <Button
              onClick={onClose}
              variant="outline"
              disabled={isLoading}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
```

### `frontend/src/components/creation/CreationStudio.tsx`
```tsx
import React, { useState } from 'react'
import { 
  DocumentTextIcon, 
  PlusIcon,
  FunnelIcon
} from '@heroicons/react/24/outline'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { EnhancedDraftCard } from './EnhancedDraftCard'
import { useDrafts, useBatchGenerateDrafts } from '@/hooks/useEnhancedDrafts'
import { DraftWithContent } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function CreationStudio() {
  const [selectedDraft, setSelectedDraft] = useState<DraftWithContent | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  
  const { data: drafts = [], isLoading, error } = useDrafts()
  const { mutateAsync: batchGenerate, isLoading: isBatchGenerating } = useBatchGenerateDrafts()

  const handleBatchGenerate = async () => {
    try {
      const newDrafts = await batchGenerate({
        max_posts: 5,
        min_relevance_score: 75,
        style: 'professional'
      })
      
      notify.success(`Generated ${newDrafts.length} new drafts!`)
    } catch (error) {
      notify.error('Failed to generate drafts')
    }
  }

  const filteredDrafts = statusFilter === 'all' 
    ? drafts 
    : drafts.filter(draft => draft.status === statusFilter)

  const statusCounts = drafts.reduce((acc, draft) => {
    acc[draft.status] = (acc[draft.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neural-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="text-center py-12">
        <p className="text-red-600">Failed to load drafts</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </Card>
    )
  }

  if (drafts.length === 0) {
    return (
      <Card className="text-center py-12">
        <DocumentTextIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No drafts yet</h3>
        <p className="text-gray-600 mb-6">
          Generate some content drafts to get started
        </p>
        <Button 
          variant="ai" 
          onClick={handleBatchGenerate}
          loading={isBatchGenerating}
          leftIcon={<PlusIcon className="h-4 w-4" />}
        >
          Generate Drafts
        </Button>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neural-700">Creation Studio</h1>
          <p className="text-gray-600">Manage and refine your content drafts</p>
        </div>
        
        <div className="flex space-x-3">
          <Button 
            variant="outline"
            onClick={handleBatchGenerate}
            loading={isBatchGenerating}
            leftIcon={<PlusIcon className="h-4 w-4" />}
          >
            Generate More
          </Button>
        </div>
      </div>

      {/* Status Filter */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <FunnelIcon className="h-5 w-5 text-gray-500" />
            <span className="font-medium text-gray-700">Filter by status:</span>
            
            <div className="flex space-x-2">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-3 py-1 rounded-full text-sm transition-colors ${
                  statusFilter === 'all'
                    ? 'bg-neural-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All ({drafts.length})
              </button>
              
              {Object.entries(statusCounts).map(([status, count]) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    statusFilter === status
                      ? 'bg-neural-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {status} ({count})
                </button>
              ))}
            </div>
          </div>
          
          <Badge variant="secondary">
            {filteredDrafts.length} draft{filteredDrafts.length !== 1 ? 's' : ''}
          </Badge>
        </div>
      </Card>

      {/* Drafts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredDrafts.map((draft) => (
          <EnhancedDraftCard
            key={draft.id}
            draft={draft}
            isSelected={selectedDraft?.id === draft.id}
            onSelect={() => setSelectedDraft(draft)}
            showFullContent={true}
          />
        ))}
      </div>

      {filteredDrafts.length === 0 && statusFilter !== 'all' && (
        <Card className="text-center py-12">
          <p className="text-gray-600">No drafts with status "{statusFilter}"</p>
          <Button 
            variant="outline" 
            onClick={() => setStatusFilter('all')}
            className="mt-4"
          >
            Show All Drafts
          </Button>
        </Card>
      )}
    </div>
  )
}
```

### `frontend/src/hooks/useEnhancedDrafts.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, type DraftWithContent } from '@/lib/api'
import { notify } from '@/stores/uiStore'

export function useDrafts() {
  return useQuery({
    queryKey: ['drafts', 'all'],
    queryFn: () => api.getAllUserDrafts(),
    refetchInterval: 30 * 1000, // Refresh every 30 seconds for real-time updates
    refetchOnWindowFocus: true,
  })
}

export function useGenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ content_item_id, tone_style }: { 
      content_item_id: string
      tone_style: string 
    }) => api.generateDraftFromContent(content_item_id, tone_style),
    onSuccess: (newDraft) => {
      // Update drafts list immediately
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      // Also update content list to show draft_generated status
      queryClient.invalidateQueries({ queryKey: ['content'] })
      
      return newDraft
    },
    onError: (error: any) => {
      if (error.status === 409) {
        notify.warning('Draft already generated for this content')
      } else {
        notify.error('Generation Failed', error.message || 'Failed to generate draft')
      }
    }
  })
}

export function useRegenerateDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ draftId, options }: { 
      draftId: string
      options: { tone_style?: string; preserve_hashtags?: boolean }
    }) => api.regenerateDraft(draftId, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: (error: any) => {
      notify.error('Failed to regenerate draft', error.message)
    }
  })
}

export function useBatchGenerateDrafts() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (options: {
      max_posts?: number
      min_relevance_score?: number
      style?: string
    }) => api.batchGenerateDrafts(options),
    onSuccess: (drafts) => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
      queryClient.invalidateQueries({ queryKey: ['content'] })
    },
    onError: (error: any) => {
      notify.error('Batch generation failed', error.message)
    }
  })
}

export function useDeleteDraft() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (draftId: string) => api.deleteDraft(draftId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drafts'] })
    },
    onError: (error: any) => {
      notify.error('Failed to delete draft', error.message)
    }
  })
}

export function useToneStyles() {
  return useQuery({
    queryKey: ['tone-styles'],
    queryFn: () => api.getToneStyles(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
```

### `frontend/src/lib/enhanced-api.ts`
```typescript
// Enhanced API methods for draft management

// Add these methods to the existing APIClient class in api.ts

export interface DraftWithContent {
  id: string
  user_id: string
  content: string
  hashtags: string[]
  title?: string
  status: string
  scheduled_for?: string
  published_at?: string
  linkedin_post_id?: string
  linkedin_post_url?: string
  created_at: string
  updated_at: string
  generation_metadata?: any
  ai_model_used?: string
}

export interface DraftRegenerateRequest {
  tone_style: string
  preserve_hashtags: boolean
}

export interface DraftRegenerateResponse {
  draft: DraftWithContent
  tone_style: string
  regenerated_at: string
  success: boolean
  message: string
}

// Add these methods to the APIClient class:

async getAllUserDrafts(): Promise<DraftWithContent[]> {
  const response = await this.client.get('/drafts/all')
  return response.data
}

async generateDraftFromContent(contentItemId: string, toneStyle: string): Promise<DraftWithContent> {
  const response = await this.client.post('/drafts/generate-from-content', {
    content_item_id: contentItemId,
    tone_style: toneStyle
  })
  return response.data
}

async regenerateDraft(draftId: string, options: {
  tone_style?: string
  preserve_hashtags?: boolean
}): Promise<DraftRegenerateResponse> {
  const response = await this.client.post(`/drafts/${draftId}/regenerate`, options)
  return response.data
}

async batchGenerateDrafts(options: {
  max_posts?: number
  min_relevance_score?: number
  style?: string
}): Promise<DraftWithContent[]> {
  const response = await this.client.post('/drafts/batch-generate', null, {
    params: options
  })
  return response.data
}

async deleteDraft(draftId: string): Promise<void> {
  await this.client.delete(`/drafts/${draftId}`)
}

async getToneStyles(): Promise<Array<{value: string, label: string, description: string}>> {
  const response = await this.client.get('/drafts/tone-styles')
  return response.data
}

async getContentWithDraftStatus(): Promise<Array<ContentItem & {draft_generated: boolean}>> {
  const response = await this.client.get('/content/with-draft-status')
  return response.data
}
```

### `frontend/src/pages/DraftPage.tsx`
```tsx
import React from 'react'
import { useRouter } from 'next/router'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { EnhancedDraftCard } from '@/components/creation/EnhancedDraftCard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

export function DraftPage() {
  const router = useRouter()
  const { draftId } = router.query

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['draft', draftId],
    queryFn: () => api.getDraft(draftId as string),
    enabled: !!draftId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neural-600"></div>
      </div>
    )
  }

  if (error || !draft) {
    return (
      <Card className="text-center py-12">
        <p className="text-red-600 mb-4">Draft not found</p>
        <Button variant="outline" onClick={() => router.push('/creation')}>
          Back to Creation Studio
        </Button>
      </Card>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          onClick={() => router.push('/creation')}
          leftIcon={<ArrowLeftIcon className="h-4 w-4" />}
        >
          Back to Studio
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-neural-700">
            {draft.title || 'Draft Preview'}
          </h1>
          <p className="text-gray-600">Review and edit your draft</p>
        </div>
      </div>

      {/* Draft Card */}
      <div className="max-w-2xl">
        <EnhancedDraftCard
          draft={draft}
          showFullContent={true}
        />
      </div>
    </div>
  )
}
```
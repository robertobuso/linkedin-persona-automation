"""
Content ingestion service for LinkedIn Presence Automation Application.

Orchestrates the content discovery and ingestion process from multiple sources
including RSS feeds and LinkedIn scraping with background task processing.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentSource, ContentItem, ContentStatus
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.services.rss_parser import RSSParser
from app.services.linkedin_scraper import LinkedInScraper
from app.utils.content_extractor import ContentExtractor
from app.utils.deduplication import ContentDeduplicator
from app.database.connection import get_db_session
from app.schemas.api_schemas import ContentStatsResponse

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Result object for content processing operations."""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.skipped_count = 0
        self.errors: List[Dict[str, Any]] = []
        self.sources_processed: List[str] = []
    
    def add_success(self, source_id: str, items_count: int = 1):
        """Add successful processing result."""
        self.processed_count += items_count
        if source_id not in self.sources_processed:
            self.sources_processed.append(source_id)
    
    def add_error(self, source_id: str, error: str, items_count: int = 1):
        """Add error processing result."""
        self.error_count += items_count
        self.errors.append({
            "source_id": source_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_skipped(self, items_count: int = 1):
        """Add skipped items count."""
        self.skipped_count += items_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count,
            "total_sources": len(self.sources_processed),
            "errors": self.errors,
            "success_rate": (
                self.processed_count / (self.processed_count + self.error_count) * 100
                if (self.processed_count + self.error_count) > 0 else 0
            )
        }


class ContentIngestionService:
    """
    Service for orchestrating content ingestion from multiple sources.
    
    Manages the discovery, extraction, filtering, and storage of content
    from RSS feeds, LinkedIn, and other configured sources.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the content ingestion service.
        
        Args:
            session: Database session for repository operations
        """
        self.session = session
        self.source_repo = ContentSourceRepository(session)
        self.content_repo = ContentItemRepository(session)
        self.rss_parser = RSSParser()
        self.linkedin_scraper = LinkedInScraper()
        self.content_extractor = ContentExtractor()
        self.deduplicator = ContentDeduplicator()
    
    async def process_all_sources(self, user_id: Optional[UUID] = None) -> ProcessingResult:
        """
        Process content from all active sources for a user or all users.
        
        Args:
            user_id: Optional user ID to process sources for specific user
            
        Returns:
            ProcessingResult with processing statistics
        """
        result = ProcessingResult()
        
        try:
            # Get active sources
            if user_id:
                sources = await self.source_repo.get_active_sources_by_user(user_id)
            else:
                sources = await self.source_repo.get_sources_due_for_check()
            
            logger.info(f"Processing {len(sources)} content sources")
            
            # Process each source
            for source in sources:
                try:
                    source_result = await self._process_single_source(source)
                    result.add_success(str(source.id), source_result.processed_count)
                    result.error_count += source_result.error_count
                    result.skipped_count += source_result.skipped_count
                    result.errors.extend(source_result.errors)
                    
                except Exception as e:
                    error_msg = f"Failed to process source {source.id}: {str(e)}"
                    logger.error(error_msg)
                    result.add_error(str(source.id), error_msg)
                    
                    # Update source with error status
                    await self.source_repo.update_check_status(
                        source.id,
                        success=False,
                        error_message=str(e)
                    )
            
            logger.info(f"Content processing completed: {result.to_dict()}")
            return result
            
        except Exception as e:
            logger.error(f"Content processing failed: {str(e)}")
            result.add_error("system", str(e))
            return result
    
    async def _process_single_source(self, source: ContentSource) -> ProcessingResult:
        """
        Process content from a single source.
        
        Args:
            source: ContentSource to process
            
        Returns:
            ProcessingResult for this source
        """
        result = ProcessingResult()
        
        try:
            logger.info(f"Processing source: {source.name} ({source.source_type})")
            
            # Parse content based on source type
            if source.source_type == "rss_feed":
                items = await self.rss_parser.parse_feed(source.url)
            elif source.source_type == "linkedin":
                items = await self.linkedin_scraper.scrape_profile_posts(source.url)
            else:
                logger.warning(f"Unsupported source type: {source.source_type}")
                return result
            
            logger.info(f"Found {len(items)} items from source {source.name}")
            
            # Filter content based on source preferences
            filtered_items = await self._filter_content(items, source)
            logger.info(f"Filtered to {len(filtered_items)} items")
            
            # Process each item
            for item in filtered_items:
                try:
                    # Check for duplicates
                    if await self.content_repo.check_duplicate_url(item.url):
                        result.add_skipped()
                        continue
                    
                    # Extract full content if needed
                    if len(item.content) < 500:
                        full_content_result = await self.content_extractor.extract_full_content(item.url)
                        if full_content_result and isinstance(full_content_result, dict):
                            item.content = full_content_result.get("content", item.content)
                    
                    # Create content item
                    await self.content_repo.create_content_item(
                        source_id=source.id,
                        title=item.title,
                        content=item.content,
                        url=item.url,
                        author=item.author,
                        published_at=item.published_at,
                        category=item.category,
                        tags=item.tags or []
                    )
                    
                    result.add_success(str(source.id))
                    
                except Exception as e:
                    error_msg = f"Failed to process item {item.url}: {str(e)}"
                    logger.error(error_msg)
                    result.add_error(str(source.id), error_msg)
            
            # Update source check status
            await self.source_repo.update_check_status(
                source.id,
                success=True,
                items_found=len(items)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Source processing failed for {source.id}: {str(e)}")
            result.add_error(str(source.id), str(e))
            return result
    
    async def _filter_content(self, items: List[Any], source: ContentSource) -> List[Any]:
        """
        Filter content items based on source preferences and quality checks.
        
        Args:
            items: List of content items to filter
            source: ContentSource with filtering preferences
            
        Returns:
            List of filtered content items
        """
        filtered_items = []
        filters = source.content_filters or {}
        
        min_length = filters.get("min_content_length", 200)
        max_age_days = filters.get("max_content_age_days", 30)
        keywords_include = filters.get("keywords_include", [])
        keywords_exclude = filters.get("keywords_exclude", [])
        language = filters.get("language", "en")
        
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        for item in items:
            try:
                # Check content length
                if len(item.content) < min_length:
                    continue
                
                # Check publication date
                if item.published_at and item.published_at < cutoff_date:
                    continue
                
                # Check include keywords
                if keywords_include:
                    content_lower = item.content.lower()
                    title_lower = item.title.lower()
                    if not any(keyword.lower() in content_lower or keyword.lower() in title_lower 
                             for keyword in keywords_include):
                        continue
                
                # Check exclude keywords
                if keywords_exclude:
                    content_lower = item.content.lower()
                    title_lower = item.title.lower()
                    if any(keyword.lower() in content_lower or keyword.lower() in title_lower 
                          for keyword in keywords_exclude):
                        continue
                
                # Language detection (basic check)
                if language == "en":
                    # Simple English detection - check for common English words
                    english_indicators = ["the", "and", "or", "but", "in", "on", "at", "to", "for"]
                    content_words = item.content.lower().split()
                    english_word_count = sum(1 for word in english_indicators if word in content_words)
                    if english_word_count < 2:  # Require at least 2 English indicators
                        continue
                
                # Spam detection - basic keyword patterns
                spam_patterns = ["click here", "buy now", "limited time", "act fast", "guaranteed"]
                content_lower = item.content.lower()
                spam_score = sum(1 for pattern in spam_patterns if pattern in content_lower)
                if spam_score >= 2:  # Skip if multiple spam indicators
                    continue
                
                filtered_items.append(item)
                
            except Exception as e:
                logger.warning(f"Error filtering item {getattr(item, 'url', 'unknown')}: {str(e)}")
                continue
        
        return filtered_items
    
    async def process_source_by_id(self, source_id: UUID) -> ProcessingResult:
        """
        Process content from a specific source by ID.
        
        Args:
            source_id: ID of the content source to process
            
        Returns:
            ProcessingResult for the source
        """
        result = ProcessingResult()
        
        try:
            source = await self.source_repo.get_by_id(source_id)
            if not source:
                result.add_error(str(source_id), "Source not found")
                return result
            
            if not source.is_active:
                result.add_error(str(source_id), "Source is not active")
                return result
            
            return await self._process_single_source(source)
            
        except Exception as e:
            logger.error(f"Failed to process source {source_id}: {str(e)}")
            result.add_error(str(source_id), str(e))
            return result
    
    async def get_processing_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get content processing statistics.
        
        Args:
            user_id: Optional user ID to get stats for specific user
            
        Returns:
            Dictionary with processing statistics
        """
        try:
            if user_id:
                sources = await self.source_repo.get_active_sources_by_user(user_id)
            else:
                sources = await self.source_repo.list_all()
            
            total_sources = len(sources)
            active_sources = len([s for s in sources if s.is_active])
            
            # Calculate total items and processing stats
            total_items_found = sum(s.total_items_found for s in sources)
            total_items_processed = sum(s.total_items_processed for s in sources)
            
            # Get sources with recent failures
            failed_sources = [s for s in sources if s.consecutive_failures > 0]
            
            # Get sources due for check
            due_sources = await self.source_repo.get_sources_due_for_check()
            
            return ContentStatsResponse(
                total_sources=total_sources,
                active_sources=active_sources,
                inactive_sources=total_sources - active_sources,
                total_items_found=total_items_found,
                total_items_processed=total_items_processed,
                processing_rate=(
                    total_items_processed / total_items_found * 100
                    if total_items_found > 0 else 0.0
                ),
                failed_sources=len(failed_sources),
                sources_due_for_check=len(due_sources),
                last_updated=datetime.utcnow() 
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to get processing stats: {str(e)}\n{traceback.format_exc()}")
            return ContentStatsResponse(error=str(e), last_updated=datetime.utcnow())

# Factory function for dependency injection
async def get_content_ingestion_service() -> ContentIngestionService:
    """
    Factory function to create ContentIngestionService with database session.
    
    Returns:
        ContentIngestionService instance
    """
    async with get_db_session() as session:
        return ContentIngestionService(session)
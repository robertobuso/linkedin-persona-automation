"""
Content repository for LinkedIn Presence Automation Application.

Provides specialized database operations for ContentSource, ContentItem, and PostDraft
models including content processing, draft management, and scheduling operations.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.content import ContentSource, ContentItem, PostDraft, ContentStatus, DraftStatus
from app.repositories.base import BaseRepository, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)

class ContentSourceRepository(BaseRepository[ContentSource]):
    """Repository for ContentSource model with source management operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize ContentSourceRepository with database session."""
        super().__init__(ContentSource, session)
    
    async def get_active_sources_by_user(self, user_id: UUID) -> List[ContentSource]:
        """
        Get all active content sources for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active ContentSource instances
        """
        stmt = select(ContentSource).where(
            and_(
                ContentSource.user_id == user_id,
                ContentSource.is_active == True
            )
        ).order_by(ContentSource.name)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_sources_due_for_check(self, before_time: Optional[datetime] = None) -> List[ContentSource]:
        """
        Get content sources that are due for checking.
        
        Args:
            before_time: Check for sources due before this time (default: now)
            
        Returns:
            List of ContentSource instances due for checking
        """
        if before_time is None:
            before_time = datetime.utcnow()
        
        stmt = select(ContentSource).where(
            and_(
                ContentSource.is_active == True,
                or_(
                    ContentSource.last_checked_at.is_(None),
                    ContentSource.last_checked_at <= (
                        before_time - func.make_interval(hours=ContentSource.check_frequency_hours)
                    )
                )
            )
        ).order_by(ContentSource.last_checked_at.asc().nullsfirst())
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_check_status(
        self, 
        source_id: UUID, 
        success: bool,
        items_found: int = 0,
        error_message: Optional[str] = None
    ) -> Optional[ContentSource]:
        """
        Update source check status and statistics.
        
        Args:
            source_id: Content source ID
            success: Whether the check was successful
            items_found: Number of new items found
            error_message: Error message if check failed
            
        Returns:
            Updated ContentSource instance or None if not found
        """
        source = await self.get_by_id(source_id)
        if not source:
            return None
        
        update_data = {
            "last_checked_at": datetime.utcnow(),
            "total_items_found": source.total_items_found + items_found
        }
        
        if success:
            update_data.update({
                "last_successful_check_at": datetime.utcnow(),
                "consecutive_failures": 0,
                "last_error_message": None
            })
        else:
            update_data.update({
                "consecutive_failures": source.consecutive_failures + 1,
                "last_error_message": error_message
            })
        
        return await self.update(source_id, **update_data)
    
    async def get_sources_by_type(self, source_type: str, user_id: Optional[UUID] = None) -> List[ContentSource]:
        """
        Get content sources by type, optionally filtered by user.
        
        Args:
            source_type: Type of content source
            user_id: Optional user ID filter
            
        Returns:
            List of ContentSource instances
        """
        conditions = [ContentSource.source_type == source_type]
        
        if user_id:
            conditions.append(ContentSource.user_id == user_id)
        
        stmt = select(ContentSource).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ContentItemRepository(BaseRepository[ContentItem]):
    """Repository for ContentItem model with content processing operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize ContentItemRepository with database session."""
        super().__init__(ContentItem, session)
    
    async def get_unprocessed_items(self, limit: int = 50) -> List[ContentItem]:
        """
        Get unprocessed content items for AI analysis.
        
        Args:
            limit: Maximum number of items to return
            
        Returns:
            List of unprocessed ContentItem instances
        """
        stmt = (
            select(ContentItem)
            .where(ContentItem.status == ContentStatus.PENDING)
            .order_by(ContentItem.created_at.asc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_content_item(
        self,
        source_id: UUID,
        title: str,
        content: str,
        url: str,
        author: Optional[str] = None,
        published_at: Optional[datetime] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ContentItem:
        """
        Create a new content item with duplicate URL checking.
        
        Args:
            source_id: Content source ID
            title: Content title
            content: Content text
            url: Content URL
            author: Optional author
            published_at: Optional publication date
            category: Optional category
            tags: Optional tags list
            
        Returns:
            Created ContentItem instance
            
        Raises:
            DuplicateError: If URL already exists
        """
        # Check for duplicate URL
        if await self.check_duplicate_url(url):
            raise DuplicateError(f"Content item with URL '{url}' already exists")
        
        return await self.create(
            source_id=source_id,
            title=title,
            content=content,
            url=url,
            author=author,
            published_at=published_at,
            category=category,
            tags=tags or [],
            word_count=len(content.split()) if content else 0,
            reading_time_minutes=max(1, len(content.split()) // 200) if content else 1
        )
    
    async def check_duplicate_url(self, url: str) -> bool:
        """
        Check if a content item with the given URL already exists.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL exists, False otherwise
        """
        stmt = select(ContentItem).where(ContentItem.url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_items_by_source(
        self, 
        source_id: UUID, 
        limit: int = 20, 
        offset: int = 0,
        status: Optional[ContentStatus] = None
    ) -> List[ContentItem]:
        """
        Get content items from a specific source.
        
        Args:
            source_id: Content source ID
            limit: Maximum number of items
            offset: Number of items to skip
            status: Optional status filter
            
        Returns:
            List of ContentItem instances
        """
        conditions = [ContentItem.source_id == source_id]
        
        if status:
            conditions.append(ContentItem.status == status)
        
        stmt = (
            select(ContentItem)
            .where(and_(*conditions))
            .order_by(ContentItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_processing_status(
        self,
        item_id: UUID,
        status: ContentStatus,
        ai_analysis: Optional[Dict[str, Any]] = None,
        relevance_score: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> Optional[ContentItem]:
        """
        Update content item processing status and AI analysis.
        
        Args:
            item_id: Content item ID
            status: New processing status
            ai_analysis: AI analysis results
            relevance_score: Relevance score (0-100)
            error_message: Error message if processing failed
            
        Returns:
            Updated ContentItem instance or None if not found
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if ai_analysis is not None:
                update_data["ai_analysis"] = ai_analysis
            
            if relevance_score is not None:
                update_data["relevance_score"] = relevance_score
            
            if error_message is not None:
                update_data["error_message"] = error_message
            
            return await self.update(item_id, **update_data)
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to update processing status: {str(e)}")
            raise
    
    async def get_high_relevance_items(
        self,
        user_id: Optional[UUID] = None,
        min_score: int = 70,
        limit: int = 20,
        offset: int = 0 
    ) -> List[ContentItem]:
        """
        Get content items with high relevance scores.
        
        Args:
            user_id: Optional user ID to filter by source ownership
            min_score: Minimum relevance score
            limit: Maximum number of items
            
        Returns:
            List of high-relevance ContentItem instances
        """
        try:
            # Join with ContentSource to filter by user
            stmt = (
                select(ContentItem)
                .join(ContentSource)
                .where(
                    and_(
                        ContentSource.user_id == user_id,
                        ContentItem.relevance_score >= min_score,
                        ContentItem.status == ContentStatus.PROCESSED
                    )
                )
                .order_by(ContentItem.relevance_score.desc(), ContentItem.created_at.desc())
                .offset(offset)  # FIX: Apply offset
                .limit(limit)
            )
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to get high relevance items: {str(e)}")
            raise


class PostDraftRepository(BaseRepository[PostDraft]):
    """Repository for PostDraft model with draft management and scheduling operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize PostDraftRepository with database session."""
        super().__init__(PostDraft, session)
    
    async def get_drafts_by_status(
        self, 
        user_id: UUID, 
        status: DraftStatus,
        limit: int = 20,
        offset: int = 0
    ) -> List[PostDraft]:
        """
        Get user's post drafts by status.
        
        Args:
            user_id: User ID
            status: Draft status to filter by
            limit: Maximum number of drafts
            offset: Number of drafts to skip
            
        Returns:
            List of PostDraft instances
        """
        stmt = (
            select(PostDraft)
            .where(
                and_(
                    PostDraft.user_id == user_id,
                    PostDraft.status == status
                )
            )
            .order_by(PostDraft.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def schedule_draft(
        self, 
        draft_id: UUID, 
        scheduled_time: datetime
    ) -> Optional[PostDraft]:
        """
        Schedule a draft for publication.
        
        Args:
            draft_id: Draft ID
            scheduled_time: When to publish the draft
            
        Returns:
            Updated PostDraft instance or None if not found
        """
        return await self.update(
            draft_id,
            status=DraftStatus.SCHEDULED,
            scheduled_for=scheduled_time
        )
    
    async def get_scheduled_drafts(
        self, 
        before_time: Optional[datetime] = None
    ) -> List[PostDraft]:
        """
        Get drafts scheduled for publication before the given time.
        
        Args:
            before_time: Get drafts scheduled before this time (default: now)
            
        Returns:
            List of PostDraft instances ready for publication
        """
        if before_time is None:
            before_time = datetime.utcnow()
        
        stmt = (
            select(PostDraft)
            .where(
                and_(
                    PostDraft.status == DraftStatus.SCHEDULED,
                    PostDraft.scheduled_for <= before_time
                )
            )
            .order_by(PostDraft.scheduled_for.asc())
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_as_published(
        self,
        draft_id: UUID,
        linkedin_post_id: str,
        linkedin_post_url: Optional[str] = None
    ) -> Optional[PostDraft]:
        """
        Mark a draft as published with LinkedIn post information.
        
        Args:
            draft_id: Draft ID
            linkedin_post_id: LinkedIn post ID
            linkedin_post_url: LinkedIn post URL
            
        Returns:
            Updated PostDraft instance or None if not found
        """
        return await self.update(
            draft_id,
            status=DraftStatus.PUBLISHED,
            published_at=datetime.utcnow(),
            linkedin_post_id=linkedin_post_id,
            linkedin_post_url=linkedin_post_url
        )
    
    async def mark_as_failed(
        self,
        draft_id: UUID,
        error_message: str
    ) -> Optional[PostDraft]:
        """
        Mark a draft as failed with error information.
        
        Args:
            draft_id: Draft ID
            error_message: Error message
            
        Returns:
            Updated PostDraft instance or None if not found
        """
        draft = await self.get_by_id(draft_id)
        if not draft:
            return None
        
        return await self.update(
            draft_id,
            status=DraftStatus.FAILED,
            publication_attempts=draft.publication_attempts + 1,
            last_error_message=error_message
        )
    
    async def get_user_drafts_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get summary of user's drafts by status.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with draft counts by status
        """
        stmt = (
            select(PostDraft.status, func.count(PostDraft.id))
            .where(PostDraft.user_id == user_id)
            .group_by(PostDraft.status)
        )
        
        result = await self.session.execute(stmt)
        status_counts = dict(result.all())
        
        return {
            "total_drafts": sum(status_counts.values()),
            "draft": status_counts.get(DraftStatus.DRAFT, 0),
            "ready": status_counts.get(DraftStatus.READY, 0),
            "scheduled": status_counts.get(DraftStatus.SCHEDULED, 0),
            "published": status_counts.get(DraftStatus.PUBLISHED, 0),
            "failed": status_counts.get(DraftStatus.FAILED, 0),
            "archived": status_counts.get(DraftStatus.ARCHIVED, 0),
        }
    
    async def get_recent_published_drafts(
        self,
        user_id: UUID,
        days: int = 30,
        limit: int = 10
    ) -> List[PostDraft]:
        """
        Get recently published drafts for performance analysis.
        
        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of drafts
            
        Returns:
            List of recently published PostDraft instances
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(PostDraft)
            .where(
                and_(
                    PostDraft.user_id == user_id,
                    PostDraft.status == DraftStatus.PUBLISHED,
                    PostDraft.published_at >= since_date
                )
            )
            .order_by(PostDraft.published_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_engagement_metrics(
        self,
        draft_id: UUID,
        metrics: Dict[str, Any]
    ) -> Optional[PostDraft]:
        """
        Update engagement metrics for a published draft.
        
        Args:
            draft_id: Draft ID
            metrics: Engagement metrics data
            
        Returns:
            Updated PostDraft instance or None if not found
        """
        draft = await self.get_by_id(draft_id)
        if not draft:
            return None
        
        # Merge with existing metrics
        current_metrics = draft.engagement_metrics or {}
        updated_metrics = {**current_metrics, **metrics}
        updated_metrics["last_updated"] = datetime.utcnow().isoformat()
        
        return await self.update(draft_id, engagement_metrics=updated_metrics)
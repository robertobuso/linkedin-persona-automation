"""
Draft management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing post drafts, scheduling, publishing,
and draft lifecycle operations.
"""

from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session
from app.repositories.content_repository import PostDraftRepository, ContentItemRepository
from app.services.content_generator import ContentGenerator
from app.schemas.api_schemas import (
    PostDraftCreate,
    PostDraftResponse,
    PostDraftUpdate,
    PublishRequest,
    PublishResponse,
    DraftStatsResponse
)
from app.models.user import User
from app.models.content import DraftStatus
from app.utils.exceptions import ContentNotFoundError, ValidationError

router = APIRouter()


@router.get("", response_model=List[PostDraftResponse])
async def get_drafts(
    status_filter: Optional[str] = Query(None, description="Filter by draft status"),
    limit: int = Query(20, ge=1, le=100, description="Number of drafts to return"),
    offset: int = Query(0, ge=0, description="Number of drafts to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get user's post drafts.
    
    Args:
        status_filter: Optional status filter
        limit: Number of drafts to return
        offset: Number of drafts to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of post drafts with pagination
    """
    draft_repo = PostDraftRepository(db)
    
    if status_filter:
        try:
            draft_status = DraftStatus(status_filter)
            drafts = await draft_repo.get_drafts_by_status(
                user_id=current_user.id,
                status=draft_status,
                limit=limit,
                offset=offset
            )
        except ValueError:
            raise ValidationError(f"Invalid status filter: {status_filter}")
    else:
        # Get all drafts with pagination
        pagination_result = await draft_repo.list_with_pagination(
            page=(offset // limit) + 1,
            page_size=limit
        )
        
        # Filter by user
        user_drafts = [
            draft for draft in pagination_result["items"]
            if draft.user_id == current_user.id
        ]
        drafts = user_drafts
    
    return [PostDraftResponse.from_orm(draft) for draft in drafts]


@router.post("", response_model=PostDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft_data: PostDraftCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Create a new post draft from content item.
    
    Args:
        draft_data: Draft creation data
        background_tasks: Background tasks for processing
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created post draft
        
    Raises:
        HTTPException: If content item not found or generation fails
    """
    # Verify content item exists and belongs to user's sources
    content_repo = ContentItemRepository(db)
    content_item = await content_repo.get_by_id(draft_data.content_item_id)
    
    if not content_item:
        raise ContentNotFoundError(f"Content item {draft_data.content_item_id} not found")
    
    # Verify content item belongs to user's source
    if content_item.source.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to content item"
        )
    
    try:
        # Generate post draft using content generator
        content_generator = ContentGenerator(db)
        draft = await content_generator.generate_post_from_content(
            content_item_id=draft_data.content_item_id,
            user_id=current_user.id,
            style="professional",
            num_variations=3
        )
        
        return PostDraftResponse.from_orm(draft)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create draft: {str(e)}"
        )


@router.get("/{draft_id}", response_model=PostDraftResponse)
async def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get a specific post draft.
    
    Args:
        draft_id: Draft ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Post draft details
        
    Raises:
        HTTPException: If draft not found or access denied
    """
    draft_repo = PostDraftRepository(db)
    draft = await draft_repo.get_by_id(draft_id)
    
    if not draft:
        raise ContentNotFoundError(f"Draft {draft_id} not found")
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return PostDraftResponse.from_orm(draft)


@router.put("/{draft_id}", response_model=PostDraftResponse)
async def update_draft(
    draft_id: str,
    draft_update: PostDraftUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Update a post draft.
    
    Args:
        draft_id: Draft ID
        draft_update: Draft update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated post draft
        
    Raises:
        HTTPException: If draft not found or access denied
    """
    draft_repo = PostDraftRepository(db)
    draft = await draft_repo.get_by_id(draft_id)
    
    if not draft:
        raise ContentNotFoundError(f"Draft {draft_id} not found")
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prepare update data
    update_data = {}
    if draft_update.content is not None:
        update_data["content"] = draft_update.content
    if draft_update.hashtags is not None:
        update_data["hashtags"] = draft_update.hashtags
    if draft_update.title is not None:
        update_data["title"] = draft_update.title
    if draft_update.status is not None:
        update_data["status"] = draft_update.status
    if draft_update.scheduled_for is not None:
        update_data["scheduled_for"] = draft_update.scheduled_for
    
    try:
        updated_draft = await draft_repo.update(draft_id, **update_data)
        if updated_draft:
            return PostDraftResponse.from_orm(updated_draft)
        else:
            raise ContentNotFoundError(f"Draft {draft_id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update draft: {str(e)}"
        )


@router.post("/{draft_id}/publish", response_model=PublishResponse)
async def publish_draft(
    draft_id: str,
    publish_request: PublishRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Publish or schedule a post draft.
    
    Args:
        draft_id: Draft ID
        publish_request: Publish request data
        background_tasks: Background tasks for processing
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Publish response with status
        
    Raises:
        HTTPException: If draft not found or publishing fails
    """
    draft_repo = PostDraftRepository(db)
    draft = await draft_repo.get_by_id(draft_id)
    
    if not draft:
        raise ContentNotFoundError(f"Draft {draft_id} not found")
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        if publish_request.scheduled_time:
            # Schedule for later
            scheduled_draft = await draft_repo.schedule_draft(
                draft_id=draft_id,
                scheduled_time=publish_request.scheduled_time
            )
            
            if scheduled_draft:
                return PublishResponse(
                    draft_id=draft_id,
                    status="scheduled",
                    scheduled_time=publish_request.scheduled_time,
                    message=f"Post scheduled for {publish_request.scheduled_time}"
                )
        else:
            # Publish immediately (in real implementation, this would integrate with LinkedIn API)
            published_draft = await draft_repo.mark_as_published(
                draft_id=draft_id,
                linkedin_post_id=f"linkedin_post_{draft_id}",  # Mock LinkedIn post ID
                linkedin_post_url=f"https://linkedin.com/posts/{draft_id}"  # Mock URL
            )
            
            if published_draft:
                # In real implementation, track analytics
                background_tasks.add_task(
                    # track_post_performance,
                    lambda: None,  # Placeholder
                    draft_id
                )
                
                return PublishResponse(
                    draft_id=draft_id,
                    status="published",
                    linkedin_post_id=f"linkedin_post_{draft_id}",
                    linkedin_post_url=f"https://linkedin.com/posts/{draft_id}",
                    message="Post published successfully"
                )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish draft"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish draft: {str(e)}"
        )


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Delete a post draft.
    
    Args:
        draft_id: Draft ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If draft not found or access denied
    """
    draft_repo = PostDraftRepository(db)
    draft = await draft_repo.get_by_id(draft_id)
    
    if not draft:
        raise ContentNotFoundError(f"Draft {draft_id} not found")
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        await draft_repo.delete(draft_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {str(e)}"
        )


@router.post("/{draft_id}/regenerate", response_model=PostDraftResponse)
async def regenerate_draft(
    draft_id: str,
    style: Optional[str] = Query("professional", description="Style for regeneration"),
    preserve_hashtags: bool = Query(False, description="Preserve existing hashtags"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Regenerate a post draft with new content.
    
    Args:
        draft_id: Draft ID
        style: Style for regeneration
        preserve_hashtags: Whether to preserve existing hashtags
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Regenerated post draft
        
    Raises:
        HTTPException: If draft not found or regeneration fails
    """
    draft_repo = PostDraftRepository(db)
    draft = await draft_repo.get_by_id(draft_id)
    
    if not draft:
        raise ContentNotFoundError(f"Draft {draft_id} not found")
    
    if draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        content_generator = ContentGenerator(db)
        regenerated_draft = await content_generator.regenerate_post_draft(
            draft_id=draft_id,
            style=style,
            preserve_hashtags=preserve_hashtags
        )
        
        if regenerated_draft:
            return PostDraftResponse.from_orm(regenerated_draft)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to regenerate draft"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate draft: {str(e)}"
        )


@router.get("/stats/summary", response_model=DraftStatsResponse)
async def get_draft_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get draft statistics summary for user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Draft statistics summary
    """
    try:
        draft_repo = PostDraftRepository(db)
        stats = await draft_repo.get_user_drafts_summary(current_user.id)
        
        return DraftStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft stats: {str(e)}"
        )


@router.post("/batch-generate", response_model=List[PostDraftResponse])
async def batch_generate_drafts(
    max_posts: int = Query(5, ge=1, le=10, description="Maximum posts to generate"),
    min_relevance_score: int = Query(70, ge=0, le=100, description="Minimum relevance score"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Generate multiple drafts from high-relevance content.
    
    Args:
        max_posts: Maximum number of posts to generate
        min_relevance_score: Minimum relevance score for content selection
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of generated post drafts
    """
    try:
        content_generator = ContentGenerator(db)
        drafts = await content_generator.batch_generate_posts(
            user_id=current_user.id,
            max_posts=max_posts,
            min_relevance_score=min_relevance_score
        )
        
        return [PostDraftResponse.from_orm(draft) for draft in drafts]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to batch generate drafts: {str(e)}"
        )
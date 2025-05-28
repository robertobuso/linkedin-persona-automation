"""
Content management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing content sources, viewing content feed,
and triggering content ingestion processes.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.services.content_ingestion import ContentIngestionService
from app.schemas.api_schemas import (
    ContentSourceCreate,
    ContentSourceResponse,
    ContentSourceUpdate,
    ContentItemResponse,
    ContentIngestionResponse,
    FeedValidationRequest,
    FeedValidationResponse,
    ContentStatsResponse
)
from app.schemas.content_schemas import ProcessingResultSchema
from app.tasks.content_tasks import process_source_task
from app.models.user import User
from app.utils.exceptions import ContentNotFoundError, ValidationError

router = APIRouter()


@router.get("/sources", response_model=List[ContentSourceResponse])
async def get_content_sources(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get user's content sources.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user's content sources
    """
    source_repo = ContentSourceRepository(db)
    sources = await source_repo.get_active_sources_by_user(current_user.id)
    
    return [ContentSourceResponse.from_orm(source) for source in sources]


@router.post("/sources", response_model=ContentSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_content_source(
    source_data: ContentSourceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Create a new content source.
    
    Args:
        source_data: Content source creation data
        background_tasks: Background tasks for processing
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created content source
        
    Raises:
        HTTPException: If creation fails or validation errors
    """
    source_repo = ContentSourceRepository(db)
    
    try:
        # Create the source
        source = await source_repo.create(
            user_id=current_user.id,
            name=source_data.name,
            source_type=source_data.source_type,
            url=str(source_data.url) if source_data.url else None,
            description=source_data.description,
            is_active=source_data.is_active,
            check_frequency_hours=source_data.check_frequency_hours,
            source_config=source_data.source_config,
            content_filters=source_data.content_filters
        )
        
        # FIX: Use FastAPI background tasks instead of Celery
        background_tasks.add_task(
            _process_source_background,
            str(source.id)
        )
        
        return ContentSourceResponse.from_orm(source)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create content source: {str(e)}"
        )


@router.get("/sources/{source_id}", response_model=ContentSourceResponse)
async def get_content_source(
    source_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get a specific content source.
    
    Args:
        source_id: Content source ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Content source details
        
    Raises:
        HTTPException: If source not found or access denied
    """
    source_repo = ContentSourceRepository(db)
    source = await source_repo.get_by_id(source_id)
    
    if not source:
        raise ContentNotFoundError(f"Content source {source_id} not found")
    
    if source.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ContentSourceResponse.from_orm(source)


@router.put("/sources/{source_id}", response_model=ContentSourceResponse)
async def update_content_source(
    source_id: str,
    source_update: ContentSourceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Update a content source.
    
    Args:
        source_id: Content source ID
        source_update: Source update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated content source
        
    Raises:
        HTTPException: If source not found or access denied
    """
    source_repo = ContentSourceRepository(db)
    source = await source_repo.get_by_id(source_id)
    
    if not source:
        raise ContentNotFoundError(f"Content source {source_id} not found")
    
    if source.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prepare update data
    update_data = {}
    if source_update.name is not None:
        update_data["name"] = source_update.name
    if source_update.description is not None:
        update_data["description"] = source_update.description
    if source_update.is_active is not None:
        update_data["is_active"] = source_update.is_active
    if source_update.check_frequency_hours is not None:
        update_data["check_frequency_hours"] = source_update.check_frequency_hours
    if source_update.source_config is not None:
        update_data["source_config"] = source_update.source_config
    if source_update.content_filters is not None:
        update_data["content_filters"] = source_update.content_filters
    
    try:
        updated_source = await source_repo.update(source_id, **update_data)
        if updated_source:
            return ContentSourceResponse.from_orm(updated_source)
        else:
            raise ContentNotFoundError(f"Content source {source_id} not found")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update content source: {str(e)}"
        )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_source(
    source_id: str, # Ensure this matches your model's ID type
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Response:
    """
    Delete a content source.
    
    Args:
        source_id: Content source ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If source not found or access denied
    """
    source_repo = ContentSourceRepository(db)
    source = await source_repo.get_by_id(source_id)
    
    if not source:
        raise ContentNotFoundError(f"Content source {source_id} not found")
    
    if source.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        await source_repo.delete(source_id) # Assuming delete doesn't return a value
        return Response(status_code=status.HTTP_204_NO_CONTENT) # Return a Response object with no body
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete content source: {str(e)}"
        )

async def _process_source_background(source_id: str):
    """Background task to process content source."""
    try:
        async with get_db_session() as session:
            ingestion_service = ContentIngestionService(session)
            from uuid import UUID
            source_uuid = UUID(source_id)
            result = await ingestion_service.process_source_by_id(source_uuid)
            logging.info(f"Background processing completed for source {source_id}: {result.to_dict()}")
    except Exception as e:
        logging.error(f"Background processing failed for source {source_id}: {str(e)}")


@router.get("/feed", response_model=List[ContentItemResponse])
async def get_content_feed(
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get content feed for user.
    
    Args:
        source_id: Optional source ID filter
        limit: Number of items to return
        offset: Number of items to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of content items with pagination
    """
    content_repo = ContentItemRepository(db)
    
    if source_id:
        # Verify source belongs to user
        source_repo = ContentSourceRepository(db)
        source = await source_repo.get_by_id(source_id)
        
        if not source or source.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to source"
            )
        
        # Get items from specific source
        items = await content_repo.get_items_by_source(
            source_id=source_id,
            limit=limit,
            offset=offset
        )
    else:
        # FIX: Add offset parameter to high relevance items
        items = await content_repo.get_high_relevance_items(
            user_id=current_user.id,
            limit=limit,
            offset=offset  # Added missing offset
        )
    
    return [ContentItemResponse.from_orm(item) for item in items]


@router.post("/trigger-ingestion", response_model=ContentIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_content_ingestion(
    background_tasks: BackgroundTasks,
    source_id: Optional[str] = Query(None, description="Specific source to process"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Trigger content ingestion process.
    
    Args:
        background_tasks: Background tasks for processing
        source_id: Optional specific source to process
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Task information for tracking
    """
    if source_id:
        # Verify source belongs to user
        source_repo = ContentSourceRepository(db)
        source = await source_repo.get_by_id(source_id)
        
        if not source or source.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to source"
            )
        
        # Process specific source
        task = process_source_task.delay(source_id)
        
        return ContentIngestionResponse(
            task_id=task.id,
            status="started",
            message=f"Content ingestion started for source {source_id}"
        )
    else:
        # Process all user sources
        from app.tasks.content_tasks import discover_content_task
        task = discover_content_task.delay(str(current_user.id))
        
        return ContentIngestionResponse(
            task_id=task.id,
            status="started",
            message="Content ingestion started for all sources"
        )


@router.post("/validate-feed", response_model=FeedValidationResponse)
async def validate_feed_url(
    validation_request: FeedValidationRequest,
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Validate RSS feed URL.
    
    Args:
        validation_request: Feed validation request
        current_user: Current authenticated user
        
    Returns:
        Feed validation results
    """
    from app.services.rss_parser import RSSParser
    
    try:
        rss_parser = RSSParser()
        validation_result = await rss_parser.validate_feed_url(str(validation_request.url))
        
        return FeedValidationResponse(**validation_result)
        
    except Exception as e:
        return FeedValidationResponse(
            valid=False,
            error=f"Validation failed: {str(e)}"
        )


@router.get("/stats", response_model=ContentStatsResponse)
async def get_content_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get content processing statistics for user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Content processing statistics
    """
    try:
        ingestion_service = ContentIngestionService(db)
        stats = await ingestion_service.get_processing_stats(current_user.id)
        
        return ContentStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content stats: {str(e)}"
        )
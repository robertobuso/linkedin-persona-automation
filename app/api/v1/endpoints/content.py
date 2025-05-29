"""
Content management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing content sources, viewing content feed,
and triggering content ingestion processes.
"""

from typing import Any, List, Optional
from uuid import UUID # Import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
import logging # For logging in background task

# Assuming your logger is configured in main.py or elsewhere
logger = logging.getLogger(__name__)

from app.core.security import get_current_active_user # Make sure this dependency is correctly defined and working
from app.database.connection import get_db_session # This is your @asynccontextmanager decorated dependency
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.services.content_ingestion import ContentIngestionService # Ensure this service is correctly implemented
from app.schemas.api_schemas import ( # Ensure these schemas are correctly defined
    ContentSourceCreate,
    ContentSourceResponse,
    ContentSourceUpdate,
    ContentItemResponse, # Assuming this is the ORM compatible one
    ContentIngestionResponse,
    FeedValidationRequest,
    FeedValidationResponse,
    ContentStatsResponse,
    PaginatedResponse # If you have a generic paginated response schema
)
# from app.schemas.content_schemas import ProcessingResultSchema # This was in your original, ensure path is correct
from app.tasks.content_tasks import process_source_task # For Celery task
from app.models.user import User
from app.utils.exceptions import ContentNotFoundError, ValidationError # Ensure these are defined

router = APIRouter()

# Helper function for background source processing (if not using Celery for this specific one)
async def _process_source_background(source_id_str: str):
    """Background task simulation to process content source."""
    # This function will run in a separate thread managed by FastAPI's BackgroundTasks
    # It needs its own database session.
    logger.info(f"Background task started for source_id: {source_id_str}")
    try:
        async with get_db_session() as session: # Create a new session for the background task
            ingestion_service = ContentIngestionService(session) # Initialize service with the new session
            source_uuid = UUID(source_id_str)
            result = await ingestion_service.process_source_by_id(source_uuid) # Assuming this method exists
            # Assuming result has a to_dict() or similar method if ProcessingResult is a class
            logger.info(f"Background processing completed for source {source_id_str}: {result.to_dict() if hasattr(result, 'to_dict') else result}")
    except Exception as e:
        logger.error(f"Background processing failed for source {source_id_str}: {str(e)}", exc_info=True)


@router.get("/sources", response_model=List[ContentSourceResponse])
async def get_content_sources(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> List[ContentSourceResponse]:
    """Get user's content sources."""
    async with db_session_cm as session:
        source_repo = ContentSourceRepository(session)
        sources = await source_repo.get_active_sources_by_user(current_user.id)
        return [ContentSourceResponse.model_validate(source) for source in sources] # Use model_validate for Pydantic v2


@router.post("/sources", response_model=ContentSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_content_source(
    source_data: ContentSourceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> ContentSourceResponse:
    """Create a new content source."""
    async with db_session_cm as session:
        # content_service = get_content_service(session) # If you have a factory/dependency for this
        # For now, let's assume RSSParser needs to be instantiated for validation
        from app.services.rss_parser import RSSParser # Temporary import, ideally inject service
        rss_parser = RSSParser()

        try:
            test_result = await rss_parser.validate_feed_url(str(source_data.url))
            if not test_result["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid feed URL: {test_result.get('error', 'Unknown validation error')}"
                )
        except Exception as ve: # Catch potential errors from validate_feed_url
             raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feed URL validation failed: {str(ve)}"
                )

        source_repo = ContentSourceRepository(session)
        try:
            source_dict = source_data.model_dump() # Pydantic v2
            source_dict["user_id"] = current_user.id
            source_dict["url"] = str(source_data.url) if source_data.url else None

            # Assuming create method in repository takes keyword arguments matching model fields
            source = await source_repo.create(**source_dict)

            # Trigger initial content fetch in background
            # Using FastAPI's BackgroundTasks for simplicity here,
            # but the prompt mentioned Celery's process_source_task
            # If process_source_task.delay is for Celery:
            # process_source_task.delay(str(source.id))
            # If using FastAPI's BackgroundTasks:
            background_tasks.add_task(_process_source_background, str(source.id))

            return ContentSourceResponse.model_validate(source)

        except Exception as e:
            logger.error(f"Failed to create content source: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create content source: {str(e)}"
            )


@router.get("/sources/{source_id}", response_model=ContentSourceResponse)
async def get_content_source(
    source_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> ContentSourceResponse:
    """Get a specific content source."""
    async with db_session_cm as session:
        source_repo = ContentSourceRepository(session)
        source = await source_repo.get_by_id(source_id)

        if not source:
            raise ContentNotFoundError(f"Content source {source_id} not found")

        if source.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return ContentSourceResponse.model_validate(source)


@router.put("/sources/{source_id}", response_model=ContentSourceResponse)
async def update_content_source(
    source_id: UUID, # Changed to UUID
    source_update: ContentSourceUpdate,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> ContentSourceResponse:
    """Update a content source."""
    async with db_session_cm as session:
        source_repo = ContentSourceRepository(session)
        source = await source_repo.get_by_id(source_id)

        if not source:
            raise ContentNotFoundError(f"Content source {source_id} not found")

        if source.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        update_data = source_update.model_dump(exclude_unset=True)

        try:
            # BaseRepository update method expects id and kwargs
            updated_source = await source_repo.update(id=source_id, **update_data)
            if not updated_source: # Should not happen if source was found initially
                 raise ContentNotFoundError(f"Content source {source_id} not found during update")
            return ContentSourceResponse.model_validate(updated_source)
        except Exception as e:
            logger.error(f"Failed to update content source {source_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update content source: {str(e)}"
            )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_source(
    source_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> Response:
    """Delete a content source."""
    async with db_session_cm as session:
        source_repo = ContentSourceRepository(session)
        source = await source_repo.get_by_id(source_id)

        if not source:
            raise ContentNotFoundError(f"Content source {source_id} not found")

        if source.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        try:
            # Assuming BaseRepository.delete takes id and returns bool
            deleted = await source_repo.delete(id=source_id)
            if not deleted:
                # This case might indicate the source was already deleted by another request,
                # or an issue with the delete method not finding it.
                # Returning 204 is still acceptable if the end state is "not found".
                logger.warning(f"Attempted to delete source {source_id}, but it was not found or delete failed.")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Failed to delete content source {source_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete content source: {str(e)}"
            )


@router.get("/feed", response_model=List[ContentItemResponse]) # Assuming ContentItemResponse is ORM compatible
async def get_content_feed(
    source_id: Optional[UUID] = Query(None, description="Filter by source ID"), # Changed to UUID
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> List[ContentItemResponse]:
    """Get content feed for user."""
    async with db_session_cm as session:
        content_repo = ContentItemRepository(session)
        items: List[Any] # Define items here for broader scope

        if source_id:
            source_repo = ContentSourceRepository(session)
            source = await source_repo.get_by_id(source_id)

            if not source or source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to source")

            items = await content_repo.get_items_by_source(
                source_id=source_id,
                limit=limit,
                offset=offset
            )
        else:
            # Assuming get_high_relevance_items takes user_id, limit, offset
            # Your previous ContentItemRepository didn't show offset for this method
            # Add it if it's there or adjust.
            items = await content_repo.get_high_relevance_items(
                user_id=current_user.id,
                limit=limit
                # offset=offset # Add if your repository method supports it
            )

        return [ContentItemResponse.model_validate(item) for item in items]


@router.post("/trigger-ingestion", response_model=ContentIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_content_ingestion(
    background_tasks: BackgroundTasks, # Keep this if you want FastAPI to manage it directly
    source_id: Optional[UUID] = Query(None, description="Specific source to process"), # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> ContentIngestionResponse:
    """Trigger content ingestion process."""
    task_id_str: Optional[str] = None

    async with db_session_cm as session: # Session needed for source verification
        if source_id:
            source_repo = ContentSourceRepository(session)
            source = await source_repo.get_by_id(source_id)

            if not source or source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to source")

            # Using Celery task as defined in app.tasks.content_tasks
            task = process_source_task.delay(str(source_id))
            task_id_str = task.id
            message = f"Content ingestion started for source {source_id}"
        else:
            from app.tasks.content_tasks import discover_content_task # Ensure this task exists
            task = discover_content_task.delay(str(current_user.id))
            task_id_str = task.id
            message = "Content ingestion started for all user sources"

    return ContentIngestionResponse(
        task_id=task_id_str,
        status="accepted", # More accurate for task submission
        message=message
    )


@router.post("/validate-feed", response_model=FeedValidationResponse)
async def validate_feed_url_endpoint( # Renamed to avoid conflict with any imported validate_feed_url
    validation_request: FeedValidationRequest,
    # current_user: User = Depends(get_current_active_user) # Auth might not be needed for a generic validator
) -> FeedValidationResponse:
    """Validate RSS feed URL."""
    # Assuming RSSParser is okay to instantiate without a db session for this utility
    from app.services.rss_parser import RSSParser
    rss_parser = RSSParser()
    try:
        validation_result = await rss_parser.validate_feed_url(str(validation_request.url))
        return FeedValidationResponse(**validation_result)
    except Exception as e:
        logger.error(f"Feed validation endpoint failed: {e}", exc_info=True)
        return FeedValidationResponse(
            valid=False,
            error=f"Validation failed: {str(e)}"
        )


@router.get("/stats", response_model=ContentStatsResponse)
async def get_content_stats(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session)
) -> ContentStatsResponse:
    """Get content processing statistics for user."""
    async with db_session_cm as session:
        try:
            # Assuming ContentIngestionService needs the session for its repositories
            ingestion_service = ContentIngestionService(session)
            stats = await ingestion_service.get_processing_stats(current_user.id)
            return ContentStatsResponse(**stats)
        except Exception as e:
            logger.error(f"Failed to get content stats: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get content stats: {str(e)}"
            )
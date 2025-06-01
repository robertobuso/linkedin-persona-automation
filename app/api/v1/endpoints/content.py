"""
Fixed content endpoints with proper async session management and error handling.

Key fixes:
- Proper background task session management
- Better error handling for database operations
- Safe async context handling
- Proper transaction boundaries
"""

from app.services.enhanced_content_ingestion import EnhancedContentIngestionService
import redis.asyncio as redis
import os
import asyncio
from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, select


logger = logging.getLogger(__name__)

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, db_manager, AsyncSessionContextManager
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.repositories.base import DuplicateError, DataValidationError, ConnectionError as DBConnectionError
from app.services.content_ingestion import ContentIngestionService
from app.schemas.api_schemas import (
    ContentSourceCreate,
    ContentSourceResponse,
    ContentSourceUpdate,
    ContentItemResponse,
    ContentIngestionResponse,
    FeedValidationRequest,
    FeedValidationResponse,
    ContentStatsResponse,
)
from app.models.user import User
from app.utils.exceptions import ContentNotFoundError, ValidationError

router = APIRouter()

redis_client = None
try:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0") 
    redis_client = redis.from_url(redis_url, decode_responses=False)
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}. Caching will be disabled.")


async def _process_source_background(source_id_str: str):
    """
    Background task with proper session management and error handling.
    
    Fixed to use proper background session management.
    """
    logger.info(f"Background task started for source_id: {source_id_str}")
    
    try:
        # Import the fixed background session helper
        from app.database.connection import get_db_session_from_existing
        
        async with get_db_session_from_existing() as session:
            try:
                # Create ingestion service with the new session
                ingestion_service = ContentIngestionService(session)
                source_uuid = UUID(source_id_str)
                
                # Process the source
                result = await ingestion_service.process_source_by_id(source_uuid)
                
                logger.info(
                    f"Background processing completed for source {source_id_str}: "
                    f"{result.processed_count} items processed, {result.error_count} errors"
                )
                
            except Exception as e:
                logger.error(f"Background processing failed for source {source_id_str}: {str(e)}")
                raise
                
    except Exception as e:
        logger.error(f"Critical error in background task for source {source_id_str}: {str(e)}", exc_info=True)


async def _trigger_deep_analysis(user_id: UUID, selected_articles: List[dict[str, Any]]):
    """
    Background task to trigger deep analysis for selected articles.
    
    Fixed to use proper background session management.
    """
    logger.info(f"Starting deep analysis for {len(selected_articles)} articles for user {user_id}")
    
    try:
        # Import the fixed background session helper
        from app.database.connection import get_db_session_from_existing
        
        async with get_db_session_from_existing() as session:
            try:
                from app.services.deep_content_analysis import DeepContentAnalysisService
                
                analysis_service = DeepContentAnalysisService(session)
                
                # Analyze each selected article
                for article_data in selected_articles:
                    try:
                        await analysis_service.batch_analyze_selected_content(
                            user_id=user_id,
                            selected_articles=[article_data]
                        )
                        
                        # Add small delay to avoid overwhelming the system
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Failed to analyze article {article_data.get('title', 'Unknown')}: {str(e)}")
                        continue
                        
                logger.info(f"Deep analysis completed for user {user_id}")
                
            except Exception as e:
                logger.error(f"Deep analysis failed: {str(e)}")
                
    except Exception as e:
        logger.error(f"Critical error in deep analysis background task: {str(e)}", exc_info=True)


@router.get("/sources", response_model=List[ContentSourceResponse])
async def get_content_sources(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[ContentSourceResponse]:
    """Get user's content sources."""
    async with db_session_cm as session:
        try:
            source_repo = ContentSourceRepository(session)
            sources = await source_repo.get_active_sources_by_user(current_user.id)
            return [ContentSourceResponse.model_validate(source) for source in sources]
        except SQLAlchemyError as e:
            logger.error(f"Database error getting sources for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve content sources"
            )


@router.post("/sources", response_model=ContentSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_content_source(
    source_data: ContentSourceCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentSourceResponse:
    """Create a new content source with proper error handling."""
    async with db_session_cm as session:
        try:
            # Validate RSS feed first
            from app.services.rss_parser import RSSParser
            rss_parser = RSSParser()

            try:
                test_result = await rss_parser.validate_feed_url(str(source_data.url))
                if not test_result["valid"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid feed URL: {test_result.get('error', 'Unknown validation error')}"
                    )
            except Exception as ve:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Feed URL validation failed: {str(ve)}"
                )

            # Create the source
            source_repo = ContentSourceRepository(session)
            source_dict = source_data.model_dump()
            source_dict["user_id"] = current_user.id
            source_dict["url"] = str(source_data.url) if source_data.url else None
            
            source_object = await source_repo.create(**source_dict)
            
            # Commit the transaction
            await session.commit()
            
            # Schedule background task after successful commit
            if source_object:
                background_tasks.add_task(_process_source_background, str(source_object.id))
                return ContentSourceResponse.model_validate(source_object)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create content source"
                )

        except HTTPException:
            raise
        except DuplicateError as de:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(de))
        except DataValidationError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except DBConnectionError as ce:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(ce))
        except SQLAlchemyError as e:
            logger.error(f"Database error creating content source: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error creating content source"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating content source: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )


@router.get("/sources/{source_id}", response_model=ContentSourceResponse)
async def get_content_source(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentSourceResponse:
    """Get a specific content source."""
    async with db_session_cm as session:
        try:
            source_repo = ContentSourceRepository(session)
            source = await source_repo.get_by_id(source_id)

            if not source:
                raise ContentNotFoundError(f"Content source {source_id} not found")

            if source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            return ContentSourceResponse.model_validate(source)
            
        except ContentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content source not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error getting source {source_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error retrieving content source"
            )


@router.put("/sources/{source_id}", response_model=ContentSourceResponse)
async def update_content_source(
    source_id: UUID,
    source_update: ContentSourceUpdate,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentSourceResponse:
    """Update a content source."""
    async with db_session_cm as session:
        try:
            source_repo = ContentSourceRepository(session)
            source = await source_repo.get_by_id(source_id)

            if not source:
                raise ContentNotFoundError(f"Content source {source_id} not found")

            if source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            update_data = source_update.model_dump(exclude_unset=True)
            
            updated_source = await source_repo.update(id=source_id, **update_data)
            
            if not updated_source:
                raise ContentNotFoundError(f"Content source {source_id} not found during update")
            
            await session.commit()
            return ContentSourceResponse.model_validate(updated_source)
            
        except ContentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content source not found")
        except DuplicateError as de:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(de))
        except DataValidationError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
        except SQLAlchemyError as e:
            logger.error(f"Database error updating source {source_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error updating content source"
            )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_source(
    source_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Response:
    """Delete a content source."""
    async with db_session_cm as session:
        try:
            source_repo = ContentSourceRepository(session)
            source = await source_repo.get_by_id(source_id)

            if not source:
                raise ContentNotFoundError(f"Content source {source_id} not found")

            if source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            deleted = await source_repo.delete(id=source_id)
            
            if deleted:
                await session.commit()
            else:
                logger.warning(f"Attempted to delete source {source_id}, but it was not found")
            
            return Response(status_code=status.HTTP_204_NO_CONTENT)
            
        except ContentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content source not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting source {source_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error deleting content source"
            )


@router.get("/debug/sources", response_model=dict[str, Any])
async def debug_content_sources(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict[str, Any]:
    """
    Debug endpoint to check content sources and their processing status.
    
    This helps troubleshoot why some sources might not be processed.
    """
    async with db_session_cm as session:
        try:
            source_repo = ContentSourceRepository(session)
            
            # Get all sources for user
            all_sources = await source_repo.find_by(user_id=current_user.id)
            active_sources = await source_repo.get_active_sources_by_user(current_user.id)
            
            source_details = []
            
            for source in all_sources:
                details = {
                    "id": str(source.id),
                    "name": source.name,
                    "source_type": source.source_type,
                    "url": source.url,
                    "is_active": source.is_active,
                    "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
                    "last_successful_check_at": source.last_successful_check_at.isoformat() if source.last_successful_check_at else None,
                    "total_items_found": source.total_items_found,
                    "total_items_processed": source.total_items_processed,
                    "consecutive_failures": source.consecutive_failures,
                    "last_error_message": source.last_error_message,
                    "content_filters": source.content_filters,
                }
                
                # Test RSS feed if it's an RSS source
                if source.source_type == "rss_feed" and source.url:
                    try:
                        from app.services.rss_parser import RSSParser
                        rss_parser = RSSParser()
                        test_result = await rss_parser.validate_feed_url(source.url)
                        details["feed_validation"] = test_result
                        
                        if test_result.get("valid"):
                            # Try to get a few items
                            items = await rss_parser.parse_feed(source.url)
                            details["current_feed_items"] = len(items)
                            details["sample_titles"] = [item.title for item in items[:3]]
                        
                    except Exception as e:
                        details["feed_validation"] = {
                            "valid": False,
                            "error": str(e)
                        }
                
                source_details.append(details)
            
            return {
                "user_id": str(current_user.id),
                "total_sources": len(all_sources),
                "active_sources": len(active_sources),
                "inactive_sources": len(all_sources) - len(active_sources),
                "sources": source_details,
                "debug_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Debug sources endpoint failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Debug endpoint failed: {str(e)}"
            )


@router.post("/debug/test-ingestion", response_model=dict[str, Any])
async def debug_test_ingestion(
    source_id: Optional[UUID] = Query(None, description="Test specific source"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict[str, Any]:
    """
    Debug endpoint to test content ingestion for troubleshooting.
    """
    async with db_session_cm as session:
        try:
            enhanced_service = EnhancedContentIngestionService(session, redis_client)
            
            if source_id:
                # Test specific source
                source_repo = ContentSourceRepository(session)
                source = await source_repo.get_by_id(source_id)
                
                if not source or source.user_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to source")
                
                # Test gathering candidates from this source
                candidates = await enhanced_service._gather_candidate_articles([source], current_user, None)
                
                return {
                    "source_id": str(source_id),
                    "source_name": source.name,
                    "source_type": source.source_type,
                    "candidates_found": len(candidates),
                    "candidate_titles": [c.title for c in candidates[:5]],
                    "test_timestamp": datetime.utcnow().isoformat()
                }
            else:
                # Test all sources
                sources = await enhanced_service.source_repo.get_active_sources_by_user(current_user.id)
                user_preferences = await enhanced_service.preferences_repo.get_active_preferences_for_user(current_user.id)
                
                candidates = await enhanced_service._gather_candidate_articles(sources, current_user, user_preferences)
                
                # Group by source
                by_source = {}
                for candidate in candidates:
                    source_name = candidate.source_name
                    if source_name not in by_source:
                        by_source[source_name] = []
                    by_source[source_name].append(candidate.title)
                
                return {
                    "total_sources": len(sources),
                    "total_candidates": len(candidates),
                    "candidates_by_source": {k: len(v) for k, v in by_source.items()},
                    "sample_titles_by_source": {k: v[:3] for k, v in by_source.items()},
                    "test_timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Debug test ingestion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Test ingestion failed: {str(e)}"
            )


@router.get("/feed", response_model=List[ContentItemResponse])
async def get_content_feed(
    source_id: Optional[UUID] = Query(None, description="Filter by source ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[ContentItemResponse]:
    """Get content feed for user."""
    async with db_session_cm as session:
        try:
            content_repo = ContentItemRepository(session)

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
                items = await content_repo.get_high_relevance_items(
                    user_id=current_user.id,
                    limit=limit
                )

            return [ContentItemResponse.model_validate(item) for item in items]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting content feed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error retrieving content feed"
            )


@router.post("/trigger-ingestion", response_model=ContentIngestionResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_content_ingestion(
    background_tasks: BackgroundTasks,
    source_id: Optional[UUID] = Query(None, description="Specific source to process"),
    force_refresh: bool = Query(False, description="Force refresh bypassing cache"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentIngestionResponse:
    """Trigger enhanced content ingestion with proper error handling."""
    
    async with db_session_cm as session:
        try:
            # Use enhanced ingestion service
            enhanced_service = EnhancedContentIngestionService(session, redis_client)
            
            if source_id:
                # Process specific source
                source_repo = ContentSourceRepository(session)
                source = await source_repo.get_by_id(source_id)
                
                if not source or source.user_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to source")
                
                # Use background task for source-specific processing
                background_tasks.add_task(_process_source_background, str(source_id))
                
                return ContentIngestionResponse(
                    task_id=None,  # No Celery task ID for background tasks
                    status="accepted",
                    message=f"Content ingestion started for source {source_id}"
                )
            else:
                # Use enhanced LLM-based selection for user's content
                logger.info(f"Starting enhanced content ingestion for user {current_user.id}")
                
                # Process content with LLM selection
                selection_result = await enhanced_service.process_content_with_llm_selection(
                    current_user.id,
                    force_refresh=force_refresh
                )
                
                # Commit the selection results
                await session.commit()
                
                # Trigger deep analysis for selected articles in background
                if selection_result.selected_articles:
                    background_tasks.add_task(
                        _trigger_deep_analysis,
                        current_user.id,
                        selection_result.selected_articles
                    )
                
                return ContentIngestionResponse(
                    task_id=None,
                    status="completed",
                    message=f"Enhanced content ingestion completed: {len(selection_result.selected_articles)} articles selected"
                )
                
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in content ingestion: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during content ingestion"
            )
        except Exception as e:
            logger.error(f"Enhanced content ingestion failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content ingestion failed: {str(e)}"
            )


@router.post("/select-content", response_model=dict[str, Any])
async def select_relevant_content(
    force_refresh: bool = Query(False, description="Force new selection, bypassing cache"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict[str, Any]:
    """Select relevant content for user using LLM-based selection."""
    async with db_session_cm as session:
        try:
            enhanced_service = EnhancedContentIngestionService(session, redis_client)
            
            selection_result = await enhanced_service.process_content_with_llm_selection(
                current_user.id,
                force_refresh=force_refresh
            )
            
            # Commit any database changes
            await session.commit()
            
            return {
                "selected_articles": selection_result.selected_articles,
                "selection_metadata": {
                    "articles_selected": len(selection_result.selected_articles),
                    "selection_timestamp": selection_result.selection_timestamp.isoformat(),
                    "processing_details": selection_result.processing_details,
                    "cached": not force_refresh and selection_result.processing_details.get("processing_time_seconds", 0) < 0.1
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in content selection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during content selection"
            )
        except Exception as e:
            logger.error(f"Content selection failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content selection failed: {str(e)}"
            )


@router.post("/validate-feed", response_model=FeedValidationResponse)
async def validate_feed_url_endpoint(
    validation_request: FeedValidationRequest,
) -> FeedValidationResponse:
    """Validate RSS feed URL."""
    try:
        from app.services.rss_parser import RSSParser
        rss_parser = RSSParser()
        
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
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentStatsResponse:
    """Get enhanced content processing statistics for user."""
    async with db_session_cm as session:
        try:
            # Use enhanced service for stats
            enhanced_service = EnhancedContentIngestionService(session, redis_client)
            
            # Try to get enhanced stats, fallback to basic stats if needed
            try:
                stats = await enhanced_service.get_processing_stats(current_user.id)
                return stats
            except AttributeError:
                # Fallback to basic ingestion service if enhanced stats not available
                ingestion_service = ContentIngestionService(session)
                stats = await ingestion_service.get_processing_stats(current_user.id)
                return stats
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting content stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error retrieving content statistics"
            )
        except Exception as e:
            logger.error(f"Failed to get enhanced content stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get content stats: {str(e)}"
            )
        
@router.get("/content-by-mode", response_model=List[ContentItemResponse])
async def get_content_by_mode(
    mode: str = Query(..., description="Content mode: ai-selected, fresh, trending, all"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[ContentItemResponse]:
    """Get content by different modes."""
    async with db_session_cm as session:
        try:
            content_repo = ContentItemRepository(session)
            
            if mode == "ai-selected":
                # Get high-relevance AI-selected content
                items = await content_repo.get_high_relevance_items(
                    user_id=current_user.id,
                    limit=limit
                )
            elif mode == "fresh":
                # Get most recent content - you may need to implement this method
                # For now, use the same as 'all' but ordered by created_at DESC
                source_repo = ContentSourceRepository(session)
                user_sources = await source_repo.get_active_sources_by_user(current_user.id)
                source_ids = [source.id for source in user_sources]
                
                if source_ids:
                    # Get recent items from user's sources
                    items = await content_repo.get_recent_items_from_sources(
                        source_ids=source_ids,
                        limit=limit,
                        offset=offset
                    )
                else:
                    items = []
            elif mode == "trending":
                # Get trending content (implement your own logic)
                # For now, get high-relevance items
                items = await content_repo.get_high_relevance_items(
                    user_id=current_user.id,
                    limit=limit
                )
            else:  # mode == "all"
                # Get all content from user's sources
                source_repo = ContentSourceRepository(session)
                user_sources = await source_repo.get_active_sources_by_user(current_user.id)
                source_ids = [source.id for source in user_sources]
                
                if source_ids:
                    items = await content_repo.get_items_from_sources(
                        source_ids=source_ids,
                        limit=limit,
                        offset=offset
                    )
                else:
                    items = []
            
            return [ContentItemResponse.model_validate(item) for item in items]
            
        except Exception as e:
            logger.error(f"Failed to get content by mode {mode}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get {mode} content"
            )

@router.get("/daily-summary", response_model=dict)
async def get_daily_article_summary(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """Get daily article summary with AI selection metadata."""
    from datetime import datetime, timedelta
    
    target_date = date or datetime.utcnow().date().isoformat()
    
    async with db_session_cm as session:
        try:
            content_repo = ContentItemRepository(session)
            source_repo = ContentSourceRepository(session)
            
            # Get user's sources
            user_sources = await source_repo.get_active_sources_by_user(current_user.id)
            source_ids = [source.id for source in user_sources]
            
            if not source_ids:
                return {
                    "date": target_date,
                    "total_articles": 0,
                    "ai_selected_count": 0,
                    "summary_text": "No content sources configured",
                    "selection_metadata": {
                        "avg_relevance_score": 0,
                        "top_categories": []
                    }
                }
            
            # Parse target date
            try:
                target_datetime = datetime.fromisoformat(target_date)
                start_date = target_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
            
            # Get total articles for the date
            total_articles = await content_repo.count_items_by_date_range(
                source_ids=source_ids,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get AI-selected articles count
            ai_selected_count = await content_repo.count_high_relevance_items_by_date(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get average relevance score
            avg_relevance = await content_repo.get_avg_relevance_score_by_date(
                user_id=current_user.id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get top categories (this might need to be implemented)
            top_categories = []  # Implement if you have category data
            
            summary_text = f"Processed {total_articles} articles, selected {ai_selected_count} high-relevance items"
            
            return {
                "date": target_date,
                "total_articles": total_articles,
                "ai_selected_count": ai_selected_count,
                "summary_text": summary_text,
                "selection_metadata": {
                    "avg_relevance_score": avg_relevance or 0,
                    "top_categories": top_categories
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get daily summary: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get daily summary"
            )

# app/api/v1/endpoints/preferences.py
"""
Content preferences management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing user content preferences with support for:
- Creating and updating preferences
- LLM-based content selection
- Cache invalidation
- Preference analytics
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.user_content_preferences_repository import UserContentPreferencesRepository
from app.services.enhanced_content_ingestion import EnhancedContentIngestionService
from app.models.user import User
from app.models.user_content_preferences import (
    ContentPreferencesCreate,
    ContentPreferencesUpdate, 
    ContentPreferencesResponse
)
from app.utils.exceptions import ContentNotFoundError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()

# Redis client for caching (would be injected in production)
redis_client = None
try:
    import os
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=False)
except Exception as e:
    logger.warning(f"Redis connection failed: {str(e)}. Caching will be disabled.")


@router.get("/preferences", response_model=ContentPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentPreferencesResponse:
    """Get user's active content preferences."""
    async with db_session_cm as session:
        preferences_repo = UserContentPreferencesRepository(session)
        
        preferences = await preferences_repo.get_active_preferences_for_user(current_user.id)
        
        if not preferences:
            raise ContentNotFoundError("No content preferences found for user")
        
        return ContentPreferencesResponse.from_orm(preferences)


@router.post("/preferences", response_model=ContentPreferencesResponse, status_code=status.HTTP_201_CREATED)
async def create_user_preferences(
    preferences_data: ContentPreferencesCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentPreferencesResponse:
    """Create new content preferences for user."""
    async with db_session_cm as session:
        try:
            preferences_repo = UserContentPreferencesRepository(session)
            
            # Create new preferences
            new_preferences = await preferences_repo.create_preferences_for_user(
                current_user.id,
                preferences_data.dict()
            )
            
            # Invalidate cache in background
            background_tasks.add_task(
                _invalidate_user_cache_task,
                current_user.id
            )
            
            logger.info(f"Created content preferences for user {current_user.id}")
            return ContentPreferencesResponse.from_orm(new_preferences)
            
        except Exception as e:
            logger.error(f"Failed to create preferences for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create preferences: {str(e)}"
            )


@router.put("/preferences", response_model=ContentPreferencesResponse)
async def update_user_preferences(
    preferences_updates: ContentPreferencesUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentPreferencesResponse:
    """Update user's content preferences."""
    async with db_session_cm as session:
        try:
            preferences_repo = UserContentPreferencesRepository(session)
            
            # Update preferences (creates new version)
            updated_preferences = await preferences_repo.update_preferences_for_user(
                current_user.id,
                preferences_updates.dict(exclude_unset=True)
            )
            
            # Invalidate cache in background
            background_tasks.add_task(
                _invalidate_user_cache_task,
                current_user.id
            )
            
            logger.info(f"Updated content preferences for user {current_user.id}")
            return ContentPreferencesResponse.from_orm(updated_preferences)
            
        except Exception as e:
            logger.error(f"Failed to update preferences for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update preferences: {str(e)}"
            )


@router.get("/preferences/history", response_model=List[ContentPreferencesResponse])
async def get_preferences_history(
    limit: int = Query(10, ge=1, le=50, description="Number of versions to return"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[ContentPreferencesResponse]:
    """Get user's preference history."""
    async with db_session_cm as session:
        preferences_repo = UserContentPreferencesRepository(session)
        
        history = await preferences_repo.get_preferences_history(current_user.id, limit)
        
        return [ContentPreferencesResponse.from_orm(prefs) for prefs in history]


@router.post("/preferences/restore/{preferences_id}", response_model=ContentPreferencesResponse)
async def restore_preferences_version(
    preferences_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentPreferencesResponse:
    """Restore a previous version of preferences."""
    async with db_session_cm as session:
        try:
            preferences_repo = UserContentPreferencesRepository(session)
            
            restored_preferences = await preferences_repo.restore_preferences_version(
                current_user.id,
                preferences_id
            )
            
            # Invalidate cache in background
            background_tasks.add_task(
                _invalidate_user_cache_task,
                current_user.id
            )
            
            logger.info(f"Restored preferences version {preferences_id} for user {current_user.id}")
            return ContentPreferencesResponse.from_orm(restored_preferences)
            
        except Exception as e:
            logger.error(f"Failed to restore preferences {preferences_id} for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to restore preferences: {str(e)}"
            )


@router.post("/content/select", response_model=Dict[str, Any])
async def select_relevant_content(
    force_refresh: bool = Query(False, description="Force new selection, bypassing cache"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Select relevant content for user using LLM-based selection.
    
    This endpoint implements Phase 2 of the content discovery pipeline:
    - Uses LLM to evaluate and select most relevant articles
    - Caches results for 1 hour
    - Returns 10-15 selected articles with selection reasoning
    """
    async with db_session_cm as session:
        try:
            # Initialize enhanced ingestion service
            ingestion_service = EnhancedContentIngestionService(session, redis_client)
            
            # Process content with LLM selection
            selection_result = await ingestion_service.process_content_with_llm_selection(
                current_user.id,
                force_refresh
            )
            
            # Format response
            response = {
                "selected_articles": selection_result.selected_articles,
                "selection_metadata": {
                    "articles_selected": len(selection_result.selected_articles),
                    "selection_timestamp": selection_result.selection_timestamp.isoformat(),
                    "processing_details": selection_result.processing_details,
                    "cached": not force_refresh and selection_result.processing_details.get("processing_time_seconds", 0) < 0.1
                }
            }
            
            # Include selection reasons if available
            if selection_result.selection_reasons:
                for article in response["selected_articles"]:
                    url = article.get("url")
                    if url in selection_result.selection_reasons:
                        article["selection_reason"] = selection_result.selection_reasons[url]
            
            logger.info(f"Content selection completed for user {current_user.id}: {len(selection_result.selected_articles)} articles")
            return response
            
        except Exception as e:
            logger.error(f"Content selection failed for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Content selection failed: {str(e)}"
            )


@router.post("/content/invalidate-cache")
async def invalidate_content_cache(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Dict[str, str]:
    """Invalidate cached content selection for current user."""
    async with db_session_cm as session:
        try:
            ingestion_service = EnhancedContentIngestionService(session, redis_client)
            await ingestion_service.invalidate_user_cache(current_user.id)
            
            return {
                "message": "Content cache invalidated successfully",
                "user_id": str(current_user.id)
            }
            
        except Exception as e:
            logger.error(f"Cache invalidation failed for user {current_user.id}: {str(e)}")
            return {
                "message": f"Cache invalidation failed: {str(e)}",
                "user_id": str(current_user.id)
            }


@router.get("/analytics/preferences", response_model=Dict[str, Any])
async def get_preferences_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get analytics about preference usage and trends."""
    async with db_session_cm as session:
        try:
            preferences_repo = UserContentPreferencesRepository(session)
            analytics = await preferences_repo.get_preference_analytics(days)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get preferences analytics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analytics retrieval failed: {str(e)}"
            )


# Background task functions
async def _invalidate_user_cache_task(user_id: UUID) -> None:
    """Background task to invalidate user cache after preference changes."""
    try:
        if redis_client:
            # Create a temporary session for the background task
            async with get_db_session() as session:
                ingestion_service = EnhancedContentIngestionService(session, redis_client)
                await ingestion_service.invalidate_user_cache(user_id)
                logger.debug(f"Cache invalidated for user {user_id} in background task")
                
    except Exception as e:
        logger.error(f"Background cache invalidation failed for user {user_id}: {str(e)}")


# Integration endpoint for frontend preferences form
@router.post("/preferences/quick-setup", response_model=ContentPreferencesResponse)
async def quick_preferences_setup(
    setup_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> ContentPreferencesResponse:
    """
    Quick setup endpoint for basic content preferences.
    Designed for the frontend preferences form.
    """
    async with db_session_cm as session:
        try:
            preferences_repo = UserContentPreferencesRepository(session)
            
            # Convert frontend data to preference format
            preferences_data = {
                "job_role": setup_data.get("jobRole", ""),
                "industry": setup_data.get("industry", ""),
                "primary_interests": setup_data.get("interests", []),
                "custom_prompt": setup_data.get("customPrompt", ""),
                "min_relevance_score": setup_data.get("relevanceThreshold", 0.7),
                "max_articles_per_day": setup_data.get("maxArticlesPerDay", 15),
                "content_types": ["articles", "news", "analysis"],
                "preferred_content_length": "medium",
                "min_word_count": 200,
                "max_word_count": 5000,
                "content_freshness_hours": 72,
                "learn_from_interactions": True
            }
            
            # Create preferences
            new_preferences = await preferences_repo.create_preferences_for_user(
                current_user.id,
                preferences_data
            )
            
            # Invalidate cache in background
            background_tasks.add_task(
                _invalidate_user_cache_task,
                current_user.id
            )
            
            logger.info(f"Quick setup completed for user {current_user.id}")
            return ContentPreferencesResponse.from_orm(new_preferences)
            
        except Exception as e:
            logger.error(f"Quick setup failed for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Quick setup failed: {str(e)}"
            )
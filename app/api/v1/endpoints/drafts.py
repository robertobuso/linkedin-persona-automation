"""
Draft management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing post drafts, scheduling, publishing,
and draft lifecycle operations.
"""

from typing import Any, List, Optional
from datetime import datetime
from uuid import UUID # Import UUID
import logging # For logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Make sure this is imported
from sqlalchemy.orm import selectinload, joinedload # Import eager loading options
from app.models.content import ContentItem, ContentSource

from app.core.security import get_current_active_user # Ensure this is correctly defined and working
from app.database.connection import get_db_session, AsyncSessionContextManager # Your @asynccontextmanager decorated dependency
from app.repositories.content_repository import PostDraftRepository, ContentItemRepository
from app.services.content_generator import ContentGenerator # Ensure this service is correctly implemented
from app.schemas.api_schemas import ( # Ensure these schemas are correctly defined and ORM compatible
    PostDraftCreate,
    PostDraftResponse,
    PostDraftUpdate,
    PublishRequest,
    PublishResponse,
    DraftStatsResponse
)
from app.models.user import User
from app.models.content import DraftStatus # Ensure this Enum is defined
from app.utils.exceptions import ContentNotFoundError, ValidationError # Ensure these are defined
from app.services.linkedin_api_service import LinkedInAPIService
from app.services.linkedin_oauth_service import LinkedInOAuthService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[PostDraftResponse])
async def get_drafts(
    status_filter: Optional[str] = Query(None, description="Filter by draft status"),
    limit: int = Query(20, ge=1, le=100, description="Number of drafts to return"),
    offset: int = Query(0, ge=0, description="Number of drafts to skip"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed for clarity
) -> List[PostDraftResponse]: # Specific return type
    """Get user's post drafts."""
    async with db_session_cm as session: # Use async with
        draft_repo = PostDraftRepository(session) # Pass actual session
        drafts_list: List[Any] # Define type for drafts_list

        if status_filter:
            try:
                draft_status_enum = DraftStatus(status_filter) # Validate against Enum
                # Assuming get_drafts_by_status returns a list of ORM objects
                drafts_list = await draft_repo.get_drafts_by_status(
                    user_id=current_user.id,
                    status=draft_status_enum,
                    limit=limit,
                    offset=offset
                )
            except ValueError:
                raise ValidationError(f"Invalid status filter: {status_filter}")
        else:
            # Assuming list_with_pagination correctly filters by user_id or you add it
            # The original code filtered *after* pagination, which is inefficient.
            # It's better if list_with_pagination can take a user_id filter.
            # For now, assuming it fetches all and then we filter (less ideal).
            # OR, if your PostDraftRepository.list_with_pagination can filter by user_id:
            # pagination_result = await draft_repo.list_with_pagination(
            #     user_id=current_user.id, # Add user_id filter here
            #     page=(offset // limit) + 1,
            #     page_size=limit
            # )
            # drafts_list = pagination_result["items"]

            # Fallback to fetching all for user then manually handling pagination (less efficient for DB)
            # This assumes PostDraftRepository doesn't have a get_all_by_user method with offset/limit.
            # Ideally, the repository method should handle user filtering and pagination.
            all_user_drafts = await draft_repo.find_by(user_id=current_user.id) # Example if find_by exists
            drafts_list = all_user_drafts[offset : offset + limit]


        # Use model_validate for Pydantic v2
        return [PostDraftResponse.model_validate(draft) for draft in drafts_list]


@router.post("", response_model=PostDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    draft_data: PostDraftCreate,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    try:
        content_item_uuid = UUID(draft_data.content_item_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid content_item_id format. Must be a valid UUID."
        )

    async with db_session_cm as session:
        content_repo = ContentItemRepository(session) # content_repo is an instance of ContentItemRepository
        
        # --- MODIFICATION HERE ---
        # Fetch content_item with its 'source' relationship eagerly loaded
        stmt = (
            select(ContentItem)
            .options(selectinload(ContentItem.source)) # Eager load the 'source' relationship
            .where(ContentItem.id == content_item_uuid)
        )
        result = await session.execute(stmt)
        content_item = result.scalar_one_or_none()
        # --- END MODIFICATION ---

        if not content_item:
            raise ContentNotFoundError(f"Content item {content_item_uuid} not found")

        # Now content_item.source should be loaded, so accessing content_item.source.user_id is safe
        # The hasattr check is still good practice.
        if not hasattr(content_item, 'source') or not content_item.source or content_item.source.user_id != current_user.id:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to content item's source")

        try:
            content_generator = ContentGenerator(session) # Assuming this is the correct service
            draft = await content_generator.generate_post_from_content(
                content_item_id=content_item_uuid, # or pass content_item object directly
                user_id=current_user.id,
                style=draft_data.style if hasattr(draft_data, 'style') and draft_data.style else "professional_thought_leader",
                num_variations=draft_data.num_variations if hasattr(draft_data, 'num_variations') else 1
            )
            return PostDraftResponse.model_validate(draft)

        except Exception as e:
            logger.error(f"Failed to create draft for content_item {content_item_uuid}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create draft: {str(e)}"
            )


@router.get("/{draft_id}", response_model=PostDraftResponse)
async def get_draft(
    draft_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    """Get a specific post draft."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        draft = await draft_repo.get_by_id(draft_id)

        if not draft:
            raise ContentNotFoundError(f"Draft {draft_id} not found")

        if draft.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return PostDraftResponse.model_validate(draft)


@router.put("/{draft_id}", response_model=PostDraftResponse)
async def update_draft(
    draft_id: UUID, # Changed to UUID
    draft_update: PostDraftUpdate,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    """Update a post draft."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        draft = await draft_repo.get_by_id(draft_id)

        if not draft:
            raise ContentNotFoundError(f"Draft {draft_id} not found")

        if draft.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        update_data = draft_update.model_dump(exclude_unset=True)

        try:
            # Assuming repository update method takes id and kwargs
            updated_draft = await draft_repo.update(id=draft_id, **update_data)
            if not updated_draft: # Should not happen if found above
                raise ContentNotFoundError(f"Draft {draft_id} not found during update")
            return PostDraftResponse.model_validate(updated_draft)
        except Exception as e:
            logger.error(f"Failed to update draft {draft_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update draft: {str(e)}"
            )


@router.post("/{draft_id}/publish", response_model=PublishResponse)
async def publish_draft(
    draft_id: UUID,
    publish_request: PublishRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PublishResponse:
    """Publish or schedule a post draft to LinkedIn."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        draft = await draft_repo.get_by_id(draft_id)
        
        if not draft:
            raise ContentNotFoundError(f"Draft {draft_id} not found")
        
        if draft.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        # Check if user has LinkedIn connected
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected. Please connect your LinkedIn account first."
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
                        draft_id=str(draft_id),
                        status="scheduled",
                        scheduled_time=publish_request.scheduled_time,
                        message=f"Post scheduled for {publish_request.scheduled_time}"
                    )
            else:
                # Publish immediately to LinkedIn
                oauth_service = LinkedInOAuthService()
                linkedin_service = LinkedInAPIService(session, oauth_service)
                
                try:
                    # Create LinkedIn post
                    linkedin_response = await linkedin_service.create_post(
                        user=current_user,
                        content=draft.content,
                        visibility="PUBLIC"
                    )
                    
                    # Extract LinkedIn post ID and URL
                    linkedin_post_id = linkedin_response.get("id")
                    linkedin_post_url = f"https://www.linkedin.com/feed/update/{linkedin_post_id}" if linkedin_post_id else None
                    
                    # Mark draft as published
                    published_draft = await draft_repo.mark_as_published(
                        draft_id=draft_id,
                        linkedin_post_id=linkedin_post_id,
                        linkedin_post_url=linkedin_post_url
                    )
                    
                    if published_draft:
                        return PublishResponse(
                            draft_id=str(draft_id),
                            status="published",
                            linkedin_post_id=linkedin_post_id,
                            linkedin_post_url=linkedin_post_url,
                            message="Post published successfully to LinkedIn"
                        )
                
                except Exception as linkedin_error:
                    logger.error(f"LinkedIn publishing failed for draft {draft_id}: {linkedin_error}")
                    await draft_repo.update(draft_id, status=DraftStatus.FAILED)
                    
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to publish to LinkedIn: {str(linkedin_error)}"
                    )
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to publish draft {draft_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to publish draft: {str(e)}"
            )


@router.delete("/{draft_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_draft(
    draft_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> Response:
    """Delete a post draft."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        draft = await draft_repo.get_by_id(draft_id)

        if not draft:
            raise ContentNotFoundError(f"Draft {draft_id} not found")

        if draft.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        try:
            # Assuming BaseRepository.delete takes id and returns bool or raises
            deleted = await draft_repo.delete(id=draft_id)
            # if not deleted:
            #     raise ContentNotFoundError(f"Draft {draft_id} could not be deleted or was already deleted.")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Failed to delete draft {draft_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete draft: {str(e)}"
            )


@router.post("/{draft_id}/regenerate", response_model=PostDraftResponse)
async def regenerate_draft_endpoint(
    draft_id: UUID,
    style: Optional[str] = Query("professional_thought_leader", description="Style for regeneration (e.g., professional_thought_leader, storytelling, educational, thought_provoking)"), # Updated default and description
    preserve_hashtags: bool = Query(False, description="Preserve existing hashtags"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    """Regenerate a post draft with new content."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        draft = await draft_repo.get_by_id(draft_id)

        if not draft:
            raise ContentNotFoundError(f"Draft {draft_id} not found")

        if draft.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        try:
            content_generator = ContentGenerator(session) # Corrected class name
            regenerated_draft = await content_generator.regenerate_post_draft(
                draft_id=draft_id,
                user_id=current_user.id, # Pass user_id
                style=style,
                preserve_hashtags=preserve_hashtags
            )

            if regenerated_draft:
                return PostDraftResponse.model_validate(regenerated_draft)
            else:
                # This case might indicate an issue within regenerate_post_draft if it can return None
                logger.error(f"Regeneration returned None for draft {draft_id}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to regenerate draft")
        except Exception as e:
            logger.error(f"Failed to regenerate draft {draft_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to regenerate draft: {str(e)}"
            )


@router.get("/stats/summary", response_model=DraftStatsResponse)
async def get_draft_stats(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> DraftStatsResponse:
    """Get draft statistics summary for user."""
    async with db_session_cm as session:
        try:
            draft_repo = PostDraftRepository(session)
            stats = await draft_repo.get_user_drafts_summary(current_user.id)
            return DraftStatsResponse(**stats)
        except Exception as e:
            logger.error(f"Failed to get draft stats for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get draft stats: {str(e)}"
            )


@router.post("/batch-generate", response_model=List[PostDraftResponse])
async def batch_generate_drafts_endpoint(
    max_posts: int = Query(5, ge=1, le=10, description="Maximum posts to generate"),
    min_relevance_score: int = Query(70, ge=0, le=100, description="Minimum relevance score"),
    # Add style parameter to the endpoint
    style: Optional[str] = Query("professional_thought_leader", description="Style for batch generation (e.g., professional_thought_leader, storytelling)"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[PostDraftResponse]:
    """Generate multiple drafts from high-relevance content."""
    async with db_session_cm as session:
        try:
            content_generator = ContentGenerator(session) # Corrected class name
            drafts = await content_generator.batch_generate_posts(
                user_id=current_user.id,
                max_posts=max_posts,
                min_relevance_score=min_relevance_score,
                style=style # Pass the style
            )
            return [PostDraftResponse.model_validate(draft) for draft in drafts]
        except Exception as e:
            logger.error(f"Failed to batch generate drafts for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to batch generate drafts: {str(e)}"
            )
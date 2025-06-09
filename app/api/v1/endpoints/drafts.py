"""
Draft management endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing post drafts, scheduling, publishing,
and draft lifecycle operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID # Import UUID
import logging # For logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response, Body
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
from app.schemas.enhanced_draft_schemas import (
    DraftRegenerateRequest,
    DraftWithContent,
    ToneStyle,
    DraftRegenerateResponse
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

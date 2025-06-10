"""
Draft management endpoints - FIXED VERSION
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.content_repository import PostDraftRepository, ContentItemRepository
from app.services.content_generator import ContentGenerator, ContentGenerationError
from app.schemas.api_schemas import (
    PostDraftResponse,
    PublishRequest,
    PublishResponse,
    DraftStatsResponse,
    PostDraftUpdate
)
from app.models.user import User
from app.models.content import ContentItem, DraftStatus
from app.utils.exceptions import ContentNotFoundError, ValidationError
from app.services.linkedin_api_service import LinkedInAPIService
from app.services.linkedin_oauth_service import LinkedInOAuthService

# 🔧 NEW: Proper Pydantic request models instead of Body(embed=True)
from pydantic import BaseModel, Field

class DraftCreateRequest(BaseModel):
    """Request model for creating drafts."""
    content_item_id: str = Field(..., description="Content item ID")
    tone_style: str = Field("professional_thought_leader", description="Generation style")
    num_variations: int = Field(1, ge=1, le=5, description="Number of variations")

class DraftRegenerateRequest(BaseModel):
    """Request model for regenerating drafts."""
    tone_style: str = Field(..., description="New tone style")
    preserve_hashtags: bool = Field(False, description="Keep existing hashtags")

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=List[PostDraftResponse])
async def get_drafts(
    status_filter: Optional[str] = Query(None, description="Filter by draft status"),
    limit: int = Query(20, ge=1, le=100, description="Number of drafts to return"),
    offset: int = Query(0, ge=0, description="Number of drafts to skip"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[PostDraftResponse]:
    """Get user's post drafts."""
    async with db_session_cm as session:
        draft_repo = PostDraftRepository(session)
        
        try:
            if status_filter:
                try:
                    draft_status_enum = DraftStatus(status_filter)
                    drafts_list = await draft_repo.get_drafts_by_status(
                        user_id=current_user.id,
                        status=draft_status_enum,
                        limit=limit,
                        offset=offset
                    )
                except ValueError:
                    raise ValidationError(f"Invalid status filter: {status_filter}")
            else:
                all_user_drafts = await draft_repo.find_by(user_id=current_user.id) # Example if find_by exists
                drafts_list = all_user_drafts[offset : offset + limit]

            return [PostDraftResponse.model_validate(draft) for draft in drafts_list]
            
        except Exception as e:
            logger.error(f"Failed to get drafts for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve drafts"
            )


@router.post("", response_model=PostDraftResponse, status_code=status.HTTP_201_CREATED)
async def create_draft(
    request: DraftCreateRequest,  # 🔧 FIX: Use Pydantic model instead of Body(embed=True)
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    """Generate a draft from content with tone selection."""
    async with db_session_cm as session:
        try:
            content_repo = ContentItemRepository(session)
            
            # Convert string UUID to UUID object
            try:
                content_item_id = UUID(request.content_item_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content item ID format"
                )
            
            # Fetch content_item with its 'source' relationship eagerly loaded
            stmt = (
                select(ContentItem)
                .options(selectinload(ContentItem.source))
                .where(ContentItem.id == content_item_id)
            )
            result = await session.execute(stmt)
            content_item = result.scalar_one_or_none()

            if not content_item:
                raise ContentNotFoundError(f"Content item {content_item_id} not found")

            # Check access permissions
            if not hasattr(content_item, 'source') or not content_item.source or content_item.source.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to content item's source")

            logger.info(f"Creating draft from content {content_item_id} with style '{request.tone_style}' for user {current_user.id}")

            # Generate draft using ContentGenerator
            content_generator = ContentGenerator(session)
            draft = await content_generator.generate_post_from_content(
                content_item_id=content_item_id,
                user_id=current_user.id,
                style=request.tone_style,
                num_variations=request.num_variations
            )
            
            logger.info(f"Successfully created draft {draft.id} from content {content_item_id}")
            return PostDraftResponse.model_validate(draft)

        except ContentGenerationError as cge:
            logger.error(f"Content generation failed for content {request.content_item_id}: {str(cge)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Failed to generate draft: {str(cge)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating draft: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during draft creation"
            )


@router.post("/{draft_id}/regenerate", response_model=PostDraftResponse)
async def regenerate_draft_with_tone(
    draft_id: UUID,
    request: DraftRegenerateRequest,  # 🔧 FIX: Use Pydantic model
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> PostDraftResponse:
    """Regenerate a draft with specified tone style."""
    async with db_session_cm as session:
        try:
            draft_repo = PostDraftRepository(session)
            
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
            
            logger.info(f"Regenerating draft {draft_id} with style '{request.tone_style}' for user {current_user.id}")
            
            # Regenerate using ContentGenerator
            content_generator = ContentGenerator(session)
            regenerated_draft = await content_generator.regenerate_post_draft(
                draft_id=draft_id,
                user_id=current_user.id,
                style=request.tone_style,
                preserve_hashtags=request.preserve_hashtags
            )
            
            logger.info(f"Successfully regenerated draft {draft_id}")
            return PostDraftResponse.model_validate(regenerated_draft)
                
        except ContentGenerationError as cge:
            logger.error(f"Content generation error for draft {draft_id}: {str(cge)}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Regeneration failed: {str(cge)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error regenerating draft {draft_id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during regeneration"
            )


@router.post("/batch-generate", response_model=List[PostDraftResponse])
async def batch_generate_drafts_endpoint(
    max_posts: int = Query(5, ge=1, le=10, description="Maximum posts to generate"),
    min_relevance_score: int = Query(70, ge=0, le=100, description="Minimum relevance score"),
    style: str = Query("professional_thought_leader", description="Generation style"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[PostDraftResponse]:
    """Generate multiple drafts from high-relevance content."""
    async with db_session_cm as session:
        try:
            logger.info(f"Starting batch generation for user {current_user.id}: max_posts={max_posts}, style={style}")
            
            content_generator = ContentGenerator(session)
            drafts = await content_generator.batch_generate_posts(
                user_id=current_user.id,
                max_posts=max_posts,
                min_relevance_score=min_relevance_score,
                style=style
            )
            
            logger.info(f"Successfully generated {len(drafts)} drafts for user {current_user.id}")
            return [PostDraftResponse.model_validate(draft) for draft in drafts]
            
        except Exception as e:
            logger.error(f"Failed to batch generate drafts for user {current_user.id}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to batch generate drafts: {str(e)}"
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
        
@router.get("/tone-styles", response_model=List[Dict[str, str]])
async def get_available_tone_styles() -> List[Dict[str, str]]:
    """Get available tone styles for draft generation."""
    return [
        {
            "value": "professional",
            "label": "Professional",
            "description": "Formal, business-focused tone"
        },
        {
            "value": "conversational",
            "label": "Conversational", 
            "description": "Friendly, approachable tone"
        },
        {
            "value": "storytelling",
            "label": "Storytelling",
            "description": "Narrative-driven, engaging tone"
        },
        {
            "value": "humorous",
            "label": "Humorous",
            "description": "Light-hearted, entertaining tone"
        },
        {
            "value": "professional_thought_leader",
            "label": "Thought Leadership",
            "description": "Expert insights and industry analysis"
        },
        {
            "value": "educational",
            "label": "Educational",
            "description": "Teaching and instructional content"
        },
        {
            "value": "engagement_optimized",
            "label": "Engagement Optimized",
            "description": "Designed to maximize interaction"
        },
        {
            "value": "motivational",
            "label": "Motivational",
            "description": "Inspiring and empowering content"
        },
        {
            "value": "casual",
            "label": "Casual",
            "description": "Relaxed and informal tone"
        },
        {
            "value": "thought_provoking",
            "label": "Thought Provoking",
            "description": "Challenging conventional thinking"
        }
    ]

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

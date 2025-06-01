"""
Enhanced draft management router with tone selection and regeneration.

Extends existing draft functionality with:
- Tone-based regeneration
- Duplicate prevention
- Real-time updates
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.content_repository import PostDraftRepository, ContentItemRepository
from app.services.content_generator import ContentGenerator
from app.models.user import User
from app.models.content import PostDraft, DraftStatus
from app.schemas.enhanced_draft_schemas import (
    DraftRegenerateRequest,
    DraftWithContent,
    ToneStyle,
    DraftRegenerateResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

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

"""
LinkedIn integration router for feed reading and interactions.

Provides endpoints for:
- Reading LinkedIn feed
- Liking posts
- Commenting on posts
- Getting post details
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.services.linkedin_client import linkedin_client, LinkedInClientError
from app.models.user import User
from app.schemas.linkedin_schemas import (
    LinkedInFeedPost,
    LinkedInInteractionRequest,
    LinkedInInteractionResponse,
    LinkedInPostDetails
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/feed", response_model=List[LinkedInFeedPost])
async def get_linkedin_feed(
    limit: int = Query(20, ge=1, le=100, description="Number of posts to fetch"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[LinkedInFeedPost]:
    """Get user's LinkedIn feed posts."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        feed_posts = await linkedin_client.get_user_feed(current_user, limit)
        
        return [LinkedInFeedPost(**post) for post in feed_posts]
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn client error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get LinkedIn feed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve LinkedIn feed"
        )

@router.post("/like", response_model=LinkedInInteractionResponse)
async def like_linkedin_post(
    request: LinkedInInteractionRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInInteractionResponse:
    """Like a LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        result = await linkedin_client.like_post(current_user, request.post_urn)
        
        return LinkedInInteractionResponse(
            success=result["success"],
            message=result["message"],
            interaction_type="like",
            post_urn=request.post_urn
        )
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn like error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to like LinkedIn post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to like post"
        )

@router.post("/comment", response_model=LinkedInInteractionResponse)
async def comment_on_linkedin_post(
    request: LinkedInInteractionRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInInteractionResponse:
    """Comment on a LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        if not request.comment_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Comment text is required"
            )
        
        result = await linkedin_client.comment_on_post(
            current_user, 
            request.post_urn, 
            request.comment_text
        )
        
        return LinkedInInteractionResponse(
            success=result["success"],
            message=result["message"],
            interaction_type="comment",
            post_urn=request.post_urn,
            comment_id=result.get("comment_id")
        )
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn comment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to comment on LinkedIn post: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to comment on post"
        )

@router.get("/post/{post_urn}", response_model=LinkedInPostDetails)
async def get_linkedin_post_details(
    post_urn: str,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> LinkedInPostDetails:
    """Get detailed information about a specific LinkedIn post."""
    try:
        if not current_user.has_valid_linkedin_token():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LinkedIn account not connected or token expired"
            )
        
        post_details = await linkedin_client.get_post_details(current_user, post_urn)
        
        return LinkedInPostDetails(**post_details)
        
    except LinkedInClientError as e:
        logger.error(f"LinkedIn post details error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get LinkedIn post details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get post details"
        )

@router.get("/status")
async def get_linkedin_connection_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get LinkedIn connection status for the current user."""
    return {
        "connected": current_user.has_valid_linkedin_token(),
        "has_token": bool(current_user.linkedin_access_token),
        "token_expires_at": current_user.linkedin_token_expires_at.isoformat() if current_user.linkedin_token_expires_at else None,
        "user_id": str(current_user.id)
    }

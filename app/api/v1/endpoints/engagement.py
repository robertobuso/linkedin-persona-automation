"""
Engagement endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing engagement opportunities, commenting,
and engagement analytics.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session
from app.repositories.engagement_repository import EngagementRepository
from app.schemas.api_schemas import (
    EngagementOpportunityResponse,
    CommentRequest,
    CommentResponse,
    EngagementStatsResponse
)
from app.services.ai_service import AIService
from app.schemas.ai_schemas import CommentGenerationRequest, ToneProfile
from app.models.user import User
from app.models.engagement import EngagementType, EngagementStatus
from app.utils.exceptions import ContentNotFoundError, ValidationError

router = APIRouter()


@router.get("/opportunities", response_model=List[EngagementOpportunityResponse])
async def get_engagement_opportunities(
    limit: int = Query(20, ge=1, le=100, description="Number of opportunities to return"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    engagement_type: Optional[str] = Query(None, description="Filter by engagement type"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get engagement opportunities for user.
    
    Args:
        limit: Number of opportunities to return
        priority: Optional priority filter
        engagement_type: Optional engagement type filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of engagement opportunities
    """
    engagement_repo = EngagementRepository(db)
    
    try:
        if engagement_type:
            # Validate engagement type
            try:
                eng_type = EngagementType(engagement_type)
                opportunities = await engagement_repo.get_opportunities_by_type(
                    user_id=current_user.id,
                    engagement_type=eng_type,
                    status=EngagementStatus.PENDING,
                    limit=limit
                )
            except ValueError:
                raise ValidationError(f"Invalid engagement type: {engagement_type}")
        else:
            # Get pending opportunities with optional priority filter
            from app.models.engagement import EngagementPriority
            priority_filter = None
            if priority:
                try:
                    priority_filter = EngagementPriority(priority)
                except ValueError:
                    raise ValidationError(f"Invalid priority: {priority}")
            
            opportunities = await engagement_repo.get_pending_opportunities(
                user_id=current_user.id,
                limit=limit,
                priority=priority_filter
            )
        
        return [
            EngagementOpportunityResponse.from_orm(opp) 
            for opp in opportunities
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement opportunities: {str(e)}"
        )


@router.post("/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_request: CommentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Generate and create a comment for an engagement opportunity.
    
    Args:
        comment_request: Comment creation request
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Generated comment response
        
    Raises:
        HTTPException: If opportunity not found or comment generation fails
    """
    engagement_repo = EngagementRepository(db)
    
    # Get the engagement opportunity
    opportunity = await engagement_repo.get_by_id(comment_request.opportunity_id)
    
    if not opportunity:
        raise ContentNotFoundError(f"Engagement opportunity {comment_request.opportunity_id} not found")
    
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Extract user tone profile
        tone_profile = ToneProfile(
            writing_style=current_user.tone_profile.get("writing_style", "professional"),
            tone=current_user.tone_profile.get("tone", "informative"),
            personality_traits=current_user.tone_profile.get("personality_traits", []),
            industry_focus=current_user.tone_profile.get("industry_focus", []),
            expertise_areas=current_user.tone_profile.get("expertise_areas", []),
            communication_preferences=current_user.tone_profile.get("communication_preferences", {})
        )
        
        # Generate comment using AI service
        ai_service = AIService()
        comment_gen_request = CommentGenerationRequest(
            post_content=opportunity.target_content or "LinkedIn post",
            post_author=opportunity.target_author,
            tone_profile=tone_profile,
            engagement_type="thoughtful",
            max_length=150
        )
        
        comment_response = await ai_service.generate_comment_draft(comment_gen_request)
        
        # Use provided comment text if available, otherwise use AI-generated
        final_comment = comment_request.comment_text or comment_response.comment
        
        # Mark opportunity as completed
        await engagement_repo.mark_as_completed(
            opportunity_id=comment_request.opportunity_id,
            execution_result={
                "comment_posted": final_comment,
                "ai_generated": comment_request.comment_text is None,
                "engagement_type": comment_response.engagement_type,
                "confidence_score": comment_response.confidence_score
            }
        )
        
        return CommentResponse(
            opportunity_id=comment_request.opportunity_id,
            comment_text=final_comment,
            status="posted",
            ai_generated=comment_request.comment_text is None,
            confidence_score=comment_response.confidence_score,
            alternative_comments=comment_response.alternative_comments
        )
        
    except Exception as e:
        # Mark opportunity as failed
        await engagement_repo.mark_as_failed(
            opportunity_id=comment_request.opportunity_id,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create comment: {str(e)}"
        )


@router.get("/opportunities/{opportunity_id}", response_model=EngagementOpportunityResponse)
async def get_engagement_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get a specific engagement opportunity.
    
    Args:
        opportunity_id: Engagement opportunity ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Engagement opportunity details
        
    Raises:
        HTTPException: If opportunity not found or access denied
    """
    engagement_repo = EngagementRepository(db)
    opportunity = await engagement_repo.get_by_id(opportunity_id)
    
    if not opportunity:
        raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
    
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return EngagementOpportunityResponse.from_orm(opportunity)


@router.post("/opportunities/{opportunity_id}/skip")
async def skip_engagement_opportunity(
    opportunity_id: str,
    reason: Optional[str] = Query(None, description="Reason for skipping"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Skip an engagement opportunity.
    
    Args:
        opportunity_id: Engagement opportunity ID
        reason: Optional reason for skipping
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If opportunity not found or access denied
    """
    engagement_repo = EngagementRepository(db)
    opportunity = await engagement_repo.get_by_id(opportunity_id)
    
    if not opportunity:
        raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
    
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        await engagement_repo.skip_opportunity(
            opportunity_id=opportunity_id,
            reason=reason
        )
        
        return {"message": "Engagement opportunity skipped successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip opportunity: {str(e)}"
        )


@router.post("/opportunities/{opportunity_id}/feedback")
async def record_engagement_feedback(
    opportunity_id: str,
    feedback: str = Query(..., description="Feedback (positive, negative, neutral)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Record user feedback on an engagement opportunity.
    
    Args:
        opportunity_id: Engagement opportunity ID
        feedback: User feedback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If opportunity not found or access denied
    """
    if feedback not in ["positive", "negative", "neutral"]:
        raise ValidationError("Feedback must be 'positive', 'negative', or 'neutral'")
    
    engagement_repo = EngagementRepository(db)
    opportunity = await engagement_repo.get_by_id(opportunity_id)
    
    if not opportunity:
        raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
    
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        await engagement_repo.record_user_feedback(
            opportunity_id=opportunity_id,
            feedback=feedback
        )
        
        return {"message": "Feedback recorded successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )


@router.get("/stats", response_model=EngagementStatsResponse)
async def get_engagement_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get engagement statistics for user.
    
    Args:
        days: Number of days to analyze
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Engagement statistics
    """
    try:
        engagement_repo = EngagementRepository(db)
        stats = await engagement_repo.get_engagement_stats(current_user.id, days)
        
        return EngagementStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement stats: {str(e)}"
        )


@router.get("/opportunities/high-priority", response_model=List[EngagementOpportunityResponse])
async def get_high_priority_opportunities(
    limit: int = Query(10, ge=1, le=50, description="Number of opportunities to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get high-priority engagement opportunities.
    
    Args:
        limit: Number of opportunities to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of high-priority engagement opportunities
    """
    try:
        engagement_repo = EngagementRepository(db)
        opportunities = await engagement_repo.get_high_priority_opportunities(
            user_id=current_user.id,
            limit=limit
        )
        
        return [
            EngagementOpportunityResponse.from_orm(opp) 
            for opp in opportunities
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get high-priority opportunities: {str(e)}"
        )


@router.post("/opportunities/{opportunity_id}/schedule")
async def schedule_engagement_opportunity(
    opportunity_id: str,
    scheduled_time: Optional[str] = Query(None, description="ISO datetime for scheduling"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Schedule an engagement opportunity for later execution.
    
    Args:
        opportunity_id: Engagement opportunity ID
        scheduled_time: Optional scheduled time (ISO format)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If opportunity not found or access denied
    """
    engagement_repo = EngagementRepository(db)
    opportunity = await engagement_repo.get_by_id(opportunity_id)
    
    if not opportunity:
        raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
    
    if opportunity.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        from datetime import datetime
        scheduled_datetime = None
        if scheduled_time:
            try:
                scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            except ValueError:
                raise ValidationError("Invalid datetime format. Use ISO format.")
        
        await engagement_repo.schedule_opportunity(
            opportunity_id=opportunity_id,
            scheduled_time=scheduled_datetime
        )
        
        message = "Engagement opportunity scheduled successfully"
        if scheduled_datetime:
            message += f" for {scheduled_datetime}"
        
        return {"message": message}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule opportunity: {str(e)}"
        )
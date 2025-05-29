"""
Engagement endpoints for LinkedIn Presence Automation Application.

Provides endpoints for managing engagement opportunities, commenting,
and engagement analytics.
"""

from typing import Any, List, Optional
from uuid import UUID # Import UUID
from datetime import datetime # For schedule_engagement_opportunity
import logging # For logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user # Ensure this is correctly defined
from app.database.connection import get_db_session, AsyncSessionContextManager # Your @asynccontextmanager decorated dependency
from app.repositories.engagement_repository import EngagementRepository
from app.schemas.api_schemas import ( # Ensure these schemas are correctly defined
    EngagementOpportunityResponse,
    CommentRequest,
    CommentResponse,
    EngagementStatsResponse
)
# Assuming AIService is correctly implemented and can be instantiated simply
# or you have a dependency injector for it.
from app.services.ai_service import AIService
from app.schemas.ai_schemas import CommentGenerationRequest, ToneProfile # Ensure these are defined
from app.models.user import User
from app.models.engagement import EngagementType, EngagementStatus, EngagementPriority # Ensure these Enums are defined
from app.utils.exceptions import ContentNotFoundError, ValidationError # Ensure these are defined

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/opportunities", response_model=List[EngagementOpportunityResponse])
async def get_engagement_opportunities(
    limit: int = Query(20, ge=1, le=100, description="Number of opportunities to return"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    engagement_type: Optional[str] = Query(None, description="Filter by engagement type"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> List[EngagementOpportunityResponse]: # Specific return type
    """Get engagement opportunities for user."""
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        opportunities_list: List[Any]

        try:
            if engagement_type:
                try:
                    eng_type_enum = EngagementType(engagement_type)
                    opportunities_list = await engagement_repo.get_opportunities_by_type(
                        user_id=current_user.id,
                        engagement_type=eng_type_enum,
                        status=EngagementStatus.PENDING,
                        limit=limit
                    )
                except ValueError:
                    raise ValidationError(f"Invalid engagement type: {engagement_type}")
            else:
                priority_filter_enum: Optional[EngagementPriority] = None
                if priority:
                    try:
                        priority_filter_enum = EngagementPriority(priority)
                    except ValueError:
                        raise ValidationError(f"Invalid priority: {priority}")
                
                opportunities_list = await engagement_repo.get_pending_opportunities(
                    user_id=current_user.id,
                    limit=limit,
                    priority=priority_filter_enum
                )
            
            # Use model_validate for Pydantic v2
            return [EngagementOpportunityResponse.model_validate(opp) for opp in opportunities_list]
            
        except ValidationError: # Re-raise ValidationError to be handled by its specific handler
            raise
        except Exception as e:
            logger.error(f"Failed to get engagement opportunities for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get engagement opportunities: {str(e)}"
            )


@router.post("/comment", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_request: CommentRequest,
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> CommentResponse: # Specific return type
    """Generate and create/simulate posting a comment for an engagement opportunity."""
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        
        opportunity_id_uuid = UUID(str(comment_request.opportunity_id)) # Ensure UUID if repo expects it
        opportunity = await engagement_repo.get_by_id(opportunity_id_uuid)
        
        if not opportunity:
            raise ContentNotFoundError(f"Engagement opportunity {comment_request.opportunity_id} not found")
        
        if opportunity.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        try:
            tone_profile_data = current_user.tone_profile or {}
            tone_profile = ToneProfile(
                writing_style=tone_profile_data.get("writing_style", "professional"),
                tone=tone_profile_data.get("tone", "informative"),
                personality_traits=tone_profile_data.get("personality_traits", []),
                industry_focus=tone_profile_data.get("industry_focus", []),
                expertise_areas=tone_profile_data.get("expertise_areas", []),
                communication_preferences=tone_profile_data.get("communication_preferences", {})
            )
            
            # AIService might need the session if it interacts with DB for style examples etc.
            # If AIService is purely for LLM calls, it might not need the session.
            # Adjust instantiation based on AIService's __init__
            ai_service = AIService() # Or AIService(session) if needed

            comment_gen_request = CommentGenerationRequest(
                post_content=opportunity.target_content or "LinkedIn post",
                post_author=opportunity.target_author,
                tone_profile=tone_profile,
                # Assuming engagement_type in CommentGenerationRequest is an Enum or str
                engagement_type=EngagementTypeEnum.THOUGHTFUL, # Default or from request
                max_length=150
            )
            
            ai_comment_response = await ai_service.generate_comment_draft(comment_gen_request)
            final_comment = comment_request.comment_text or ai_comment_response.comment
            
            # Simulate posting or call actual LinkedIn service
            # For MVP, we might just mark it as completed/posted in our DB
            await engagement_repo.mark_as_completed(
                opportunity_id=opportunity_id_uuid,
                execution_result={
                    "comment_posted": final_comment,
                    "ai_generated": comment_request.comment_text is None,
                    "engagement_type_used": ai_comment_response.engagement_type.value, # Use .value for enum
                    "confidence_score": ai_comment_response.confidence_score
                }
            )
            
            return CommentResponse(
                opportunity_id=str(comment_request.opportunity_id), # Ensure schema expects str
                comment_text=final_comment,
                status="posted", # This status is for the comment itself
                ai_generated=comment_request.comment_text is None,
                confidence_score=ai_comment_response.confidence_score,
                alternative_comments=ai_comment_response.alternative_comments
            )
            
        except Exception as e:
            logger.error(f"Failed to create comment for opportunity {opportunity.id}: {e}", exc_info=True)
            await engagement_repo.mark_as_failed(
                opportunity_id=opportunity_id_uuid,
                error_message=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create comment: {str(e)}"
            )


@router.get("/opportunities/{opportunity_id}", response_model=EngagementOpportunityResponse)
async def get_engagement_opportunity(
    opportunity_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> EngagementOpportunityResponse: # Specific return type
    """Get a specific engagement opportunity."""
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        opportunity = await engagement_repo.get_by_id(opportunity_id)
        
        if not opportunity:
            raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
        
        if opportunity.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        return EngagementOpportunityResponse.model_validate(opportunity)


@router.post("/opportunities/{opportunity_id}/skip", response_model=dict) # Or a MessageResponse
async def skip_engagement_opportunity(
    opportunity_id: UUID, # Changed to UUID
    reason: Optional[str] = Query(None, description="Reason for skipping"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> dict: # Specific return type
    """Skip an engagement opportunity."""
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        opportunity = await engagement_repo.get_by_id(opportunity_id)
        
        if not opportunity:
            raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
        
        if opportunity.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        try:
            await engagement_repo.skip_opportunity(
                opportunity_id=opportunity_id,
                reason=reason
            )
            return {"message": "Engagement opportunity skipped successfully"}
        except Exception as e:
            logger.error(f"Failed to skip opportunity {opportunity_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to skip opportunity: {str(e)}"
            )


@router.post("/opportunities/{opportunity_id}/feedback", response_model=dict) # Or a MessageResponse
async def record_engagement_feedback(
    opportunity_id: UUID, # Changed to UUID
    feedback: str = Query(..., description="Feedback (positive, negative, neutral)"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> dict: # Specific return type
    """Record user feedback on an engagement opportunity."""
    if feedback not in ["positive", "negative", "neutral"]:
        raise ValidationError("Feedback must be 'positive', 'negative', or 'neutral'")
    
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        opportunity = await engagement_repo.get_by_id(opportunity_id)
        
        if not opportunity:
            raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
        
        if opportunity.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        try:
            await engagement_repo.record_user_feedback(
                opportunity_id=opportunity_id,
                feedback=feedback
            )
            return {"message": "Feedback recorded successfully"}
        except Exception as e:
            logger.error(f"Failed to record feedback for opportunity {opportunity_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record feedback: {str(e)}"
            )


@router.get("/stats", response_model=EngagementStatsResponse)
async def get_engagement_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> EngagementStatsResponse: # Specific return type
    """Get engagement statistics for user."""
    async with db_session_cm as session: # Use async with
        try:
            engagement_repo = EngagementRepository(session) # Pass actual session
            stats = await engagement_repo.get_engagement_stats(current_user.id, days)
            return EngagementStatsResponse(**stats) # Assuming stats is a dict compatible with the schema
        except Exception as e:
            logger.error(f"Failed to get engagement stats for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get engagement stats: {str(e)}"
            )


@router.get("/opportunities/high-priority", response_model=List[EngagementOpportunityResponse])
async def get_high_priority_opportunities(
    limit: int = Query(10, ge=1, le=50, description="Number of opportunities to return"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> List[EngagementOpportunityResponse]: # Specific return type
    """Get high-priority engagement opportunities."""
    async with db_session_cm as session: # Use async with
        try:
            engagement_repo = EngagementRepository(session) # Pass actual session
            opportunities = await engagement_repo.get_high_priority_opportunities(
                user_id=current_user.id,
                limit=limit
            )
            return [EngagementOpportunityResponse.model_validate(opp) for opp in opportunities]
        except Exception as e:
            logger.error(f"Failed to get high-priority opportunities for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get high-priority opportunities: {str(e)}"
            )


@router.post("/opportunities/{opportunity_id}/schedule", response_model=dict) # Or a MessageResponse
async def schedule_engagement_opportunity_endpoint( # Renamed to avoid conflict
    opportunity_id: UUID, # Changed to UUID
    scheduled_time_str: Optional[str] = Query(None, alias="scheduled_time", description="ISO datetime for scheduling"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session) # Renamed
) -> dict: # Specific return type
    """Schedule an engagement opportunity for later execution."""
    async with db_session_cm as session: # Use async with
        engagement_repo = EngagementRepository(session) # Pass actual session
        opportunity = await engagement_repo.get_by_id(opportunity_id)
        
        if not opportunity:
            raise ContentNotFoundError(f"Engagement opportunity {opportunity_id} not found")
        
        if opportunity.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        try:
            scheduled_datetime_obj: Optional[datetime] = None
            if scheduled_time_str:
                try:
                    # Ensure timezone info is handled correctly if present (e.g., 'Z' for UTC)
                    if scheduled_time_str.endswith('Z'):
                        scheduled_datetime_obj = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                    else:
                        scheduled_datetime_obj = datetime.fromisoformat(scheduled_time_str)
                except ValueError:
                    raise ValidationError("Invalid datetime format. Use ISO format (e.g., YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+00:00).")
            
            await engagement_repo.schedule_opportunity(
                opportunity_id=opportunity_id,
                scheduled_time=scheduled_datetime_obj
            )
            
            message = "Engagement opportunity scheduled successfully"
            if scheduled_datetime_obj:
                message += f" for {scheduled_datetime_obj.isoformat()}"
            
            return {"message": message}
            
        except ValidationError: # Re-raise ValidationError
            raise
        except Exception as e:
            logger.error(f"Failed to schedule opportunity {opportunity_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to schedule opportunity: {str(e)}"
            )
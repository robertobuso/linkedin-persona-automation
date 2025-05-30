"""
Extended Engagement endpoints for LinkedIn Presence Automation Application.

Phase 2: Extends existing engagement endpoints to support LinkedIn post
discovery and comment management while following established patterns.
"""

from typing import Any, List, Optional
from uuid import UUID
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session, AsyncSessionContextManager
from app.repositories.engagement_repository import EngagementRepository
from app.schemas.api_schemas import (
    EngagementOpportunityResponse,
    CommentRequest,
    CommentResponse,
    EngagementStatsResponse
)
from app.services.linkedin_post_discovery import LinkedInPostDiscoveryService
from app.services.smart_commenting_service import SmartCommentingService
from app.models.user import User
from app.models.engagement import EngagementType, EngagementStatus, EngagementPriority
from app.utils.exceptions import ContentNotFoundError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter()

# Import existing endpoints and add new ones
from app.api.v1.endpoints.engagement import (
    get_engagement_opportunities,
    create_comment,
    get_engagement_opportunity,
    skip_engagement_opportunity,
    record_engagement_feedback,
    get_engagement_stats,
    get_high_priority_opportunities,
    schedule_engagement_opportunity_endpoint
)

# NEW: LinkedIn Comment Discovery Endpoints

@router.post("/discover-posts", response_model=dict)
async def discover_linkedin_posts(
    max_posts: int = Query(50, ge=10, le=100, description="Maximum posts to discover"),
    sources: List[str] = Query(["feed"], description="Discovery sources"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Discover LinkedIn posts for commenting opportunities.
    
    Integrates with existing content discovery patterns.
    """
    async with db_session_cm as session:
        try:
            discovery_service = LinkedInPostDiscoveryService(session)
            
            # Configure discovery based on parameters
            discovery_config = {
                'sources': sources,
                'max_posts': max_posts,
                'min_relevance_score': 0.6,
                'min_engagement_potential': 0.5
            }
            
            # Run discovery
            result = await discovery_service.discover_posts_for_commenting(
                current_user.id, discovery_config
            )
            
            return {
                "message": "LinkedIn post discovery completed",
                "posts_found": result.posts_found,
                "opportunities_created": result.opportunities_created,
                "processing_time": result.processing_time,
                "discovery_metadata": result.discovery_metadata
            }
            
        except Exception as e:
            logger.error(f"LinkedIn post discovery failed for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Discovery failed: {str(e)}"
            )


@router.get("/comment-opportunities", response_model=List[EngagementOpportunityResponse])
async def get_comment_opportunities(
    limit: int = Query(20, ge=1, le=100, description="Number of opportunities to return"),
    priority: Optional[str] = Query(None, description="Filter by priority level"),
    status: Optional[str] = Query("pending", description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[EngagementOpportunityResponse]:
    """
    Get comment-specific engagement opportunities.
    
    Extends existing opportunity retrieval with comment filtering.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            
            # Build filters for comment opportunities
            filters = {
                'user_id': current_user.id,
                'engagement_type': EngagementType.COMMENT
            }
            
            if status:
                try:
                    filters['status'] = EngagementStatus(status)
                except ValueError:
                    raise ValidationError(f"Invalid status: {status}")
            
            if priority:
                try:
                    filters['priority'] = EngagementPriority(priority)
                except ValueError:
                    raise ValidationError(f"Invalid priority: {priority}")
            
            # Get opportunities using existing repository patterns
            if priority:
                opportunities = await engagement_repo.get_opportunities_by_type(
                    user_id=current_user.id,
                    engagement_type=EngagementType.COMMENT,
                    status=filters.get('status', EngagementStatus.PENDING),
                    limit=limit
                )
                # Filter by priority
                opportunities = [opp for opp in opportunities if opp.priority == filters['priority']]
            else:
                opportunities = await engagement_repo.get_opportunities_by_type(
                    user_id=current_user.id,
                    engagement_type=EngagementType.COMMENT,
                    status=filters.get('status', EngagementStatus.PENDING),
                    limit=limit
                )
            
            return [EngagementOpportunityResponse.model_validate(opp) for opp in opportunities]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get comment opportunities for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get comment opportunities: {str(e)}"
            )


@router.post("/comment-opportunities/{opportunity_id}/generate-comment", response_model=dict)
async def generate_comment_for_opportunity(
    opportunity_id: UUID,
    comment_approach: str = Query("thoughtful", description="Comment approach style"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Generate AI comment for specific opportunity.
    
    Uses existing AI service patterns for comment generation.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            commenting_service = SmartCommentingService(session)
            
            # Get opportunity
            opportunity = await engagement_repo.get_by_id(opportunity_id)
            if not opportunity:
                raise ContentNotFoundError(f"Opportunity {opportunity_id} not found")
            
            if opportunity.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Generate comment using existing AI patterns
            comment_response = await commenting_service.generate_personalized_comment(
                opportunity, current_user, comment_approach
            )
            
            # Update opportunity with generated comment
            await engagement_repo.update(
                opportunity_id,
                suggested_comment=comment_response.comment,
                ai_analysis={
                    **(opportunity.ai_analysis or {}),
                    "generated_comment": comment_response.comment,
                    "confidence_score": comment_response.confidence_score,
                    "comment_approach": comment_approach,
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "message": "Comment generated successfully",
                "comment_text": comment_response.comment,
                "confidence_score": comment_response.confidence_score,
                "alternative_comments": comment_response.alternative_comments,
                "approach_used": comment_approach
            }
            
        except ValidationError:
            raise
        except ContentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate comment for opportunity {opportunity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate comment: {str(e)}"
            )


@router.post("/comment-opportunities/{opportunity_id}/execute", response_model=dict)
async def execute_comment_opportunity(
    opportunity_id: UUID,
    override_approval: bool = Query(False, description="Override manual approval requirement"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Execute comment opportunity (generate and post comment).
    
    Uses existing execution patterns with safety checks.
    """
    async with db_session_cm as session:
        try:
            commenting_service = SmartCommentingService(session)
            
            # Execute comment opportunity using existing service patterns
            result = await commenting_service.execute_comment_opportunity(
                opportunity_id, current_user.id, override_approval
            )
            
            return {
                "message": "Comment execution completed",
                "success": result.success,
                "comment_text": result.comment_text,
                "linkedin_comment_id": result.linkedin_comment_id,
                "confidence_score": result.confidence_score,
                "reasoning": result.reasoning,
                "error_message": result.error_message,
                "alternative_comments": result.alternative_comments
            }
            
        except Exception as e:
            logger.error(f"Failed to execute comment opportunity {opportunity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute comment: {str(e)}"
            )


@router.post("/comment-opportunities/{opportunity_id}/schedule", response_model=dict)
async def schedule_comment_opportunity(
    opportunity_id: UUID,
    scheduled_time: Optional[datetime] = Body(None, description="When to execute comment"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Schedule comment opportunity for later execution.
    
    Uses existing scheduling patterns with optimal timing.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            commenting_service = SmartCommentingService(session)
            
            # Get opportunity
            opportunity = await engagement_repo.get_by_id(opportunity_id)
            if not opportunity:
                raise ContentNotFoundError(f"Opportunity {opportunity_id} not found")
            
            if opportunity.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Calculate optimal timing if not provided
            if not scheduled_time:
                scheduled_time = await commenting_service.get_optimal_timing(
                    opportunity, current_user
                )
            
            # Schedule using existing repository patterns
            updated_opportunity = await engagement_repo.schedule_opportunity(
                opportunity_id, scheduled_time
            )
            
            if not updated_opportunity:
                raise ContentNotFoundError("Failed to schedule opportunity")
            
            return {
                "message": "Comment opportunity scheduled successfully",
                "opportunity_id": str(opportunity_id),
                "scheduled_time": scheduled_time.isoformat(),
                "optimal_timing_used": scheduled_time != datetime.utcnow()
            }
            
        except ValidationError:
            raise
        except ContentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to schedule comment opportunity {opportunity_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to schedule comment: {str(e)}"
            )


@router.get("/comment-queue", response_model=List[EngagementOpportunityResponse])
async def get_comment_queue(
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> List[EngagementOpportunityResponse]:
    """
    Get comment queue (all comment opportunities with status).
    
    Provides comprehensive view for comment management interface.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            
            # Get comment opportunities with various statuses
            if status_filter:
                try:
                    status_enum = EngagementStatus(status_filter)
                    opportunities = await engagement_repo.get_opportunities_by_type(
                        user_id=current_user.id,
                        engagement_type=EngagementType.COMMENT,
                        status=status_enum,
                        limit=limit
                    )
                except ValueError:
                    raise ValidationError(f"Invalid status: {status_filter}")
            else:
                # Get all comment opportunities regardless of status
                all_opportunities = await engagement_repo.find_by(
                    user_id=current_user.id,
                    engagement_type=EngagementType.COMMENT
                )
                # Sort by priority and created date
                opportunities = sorted(
                    all_opportunities,
                    key=lambda x: (
                        x.priority == EngagementPriority.URGENT,
                        x.priority == EngagementPriority.HIGH,
                        x.created_at
                    ),
                    reverse=True
                )[:limit]
            
            return [EngagementOpportunityResponse.model_validate(opp) for opp in opportunities]
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to get comment queue for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get comment queue: {str(e)}"
            )


@router.get("/comment-analytics", response_model=dict)
async def get_comment_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Get comment analytics and performance metrics.
    
    Extends existing analytics patterns for comment-specific metrics.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            
            # Get comment-specific stats using existing patterns
            comment_stats = await engagement_repo.get_engagement_stats(current_user.id, days)
            
            # Filter for comment-specific metrics
            comment_analytics = {
                "total_comment_opportunities": comment_stats.get("total_opportunities", 0),
                "comments_posted": comment_stats.get("status_breakdown", {}).get("completed", 0),
                "comments_pending": comment_stats.get("status_breakdown", {}).get("pending", 0),
                "comments_scheduled": comment_stats.get("status_breakdown", {}).get("scheduled", 0),
                "comments_failed": comment_stats.get("status_breakdown", {}).get("failed", 0),
                "comments_skipped": comment_stats.get("status_breakdown", {}).get("skipped", 0),
                "success_rate": 0.0,
                "period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Calculate success rate
            total_attempted = (
                comment_analytics["comments_posted"] + 
                comment_analytics["comments_failed"]
            )
            if total_attempted > 0:
                comment_analytics["success_rate"] = (
                    comment_analytics["comments_posted"] / total_attempted * 100
                )
            
            # Add discovery metrics
            discovery_stats = await _get_discovery_metrics(engagement_repo, current_user.id, days)
            comment_analytics.update(discovery_stats)
            
            return comment_analytics
            
        except Exception as e:
            logger.error(f"Failed to get comment analytics for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get comment analytics: {str(e)}"
            )


@router.post("/bulk-comment-actions", response_model=dict)
async def bulk_comment_actions(
    opportunity_ids: List[UUID] = Body(..., description="List of opportunity IDs"),
    action: str = Body(..., description="Action to perform (schedule, skip, execute)"),
    scheduled_time: Optional[datetime] = Body(None, description="Schedule time for schedule action"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
) -> dict:
    """
    Perform bulk actions on comment opportunities.
    
    Follows existing bulk operation patterns.
    """
    async with db_session_cm as session:
        try:
            engagement_repo = EngagementRepository(session)
            commenting_service = SmartCommentingService(session)
            
            results = {
                "total_processed": len(opportunity_ids),
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for opp_id in opportunity_ids:
                try:
                    # Verify ownership
                    opportunity = await engagement_repo.get_by_id(opp_id)
                    if not opportunity or opportunity.user_id != current_user.id:
                        results["errors"].append(f"Opportunity {opp_id} not found or access denied")
                        results["failed"] += 1
                        continue
                    
                    # Perform action
                    if action == "schedule":
                        if not scheduled_time:
                            scheduled_time = await commenting_service.get_optimal_timing(
                                opportunity, current_user
                            )
                        await engagement_repo.schedule_opportunity(opp_id, scheduled_time)
                        
                    elif action == "skip":
                        await engagement_repo.skip_opportunity(opp_id, "Bulk skip action")
                        
                    elif action == "execute":
                        result = await commenting_service.execute_comment_opportunity(
                            opp_id, current_user.id
                        )
                        if not result.success:
                            results["errors"].append(f"Execution failed for {opp_id}: {result.error_message}")
                            results["failed"] += 1
                            continue
                    
                    else:
                        raise ValidationError(f"Invalid action: {action}")
                    
                    results["successful"] += 1
                    
                except Exception as e:
                    results["errors"].append(f"Error processing {opp_id}: {str(e)}")
                    results["failed"] += 1
                    continue
            
            return {
                "message": f"Bulk {action} action completed",
                "results": results
            }
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Bulk comment action failed for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Bulk action failed: {str(e)}"
            )


# Helper function for discovery metrics
async def _get_discovery_metrics(
    engagement_repo: EngagementRepository,
    user_id: UUID,
    days: int
) -> dict:
    """Get discovery-specific metrics."""
    try:
        # Count opportunities by discovery source
        all_opportunities = await engagement_repo.find_by(
            user_id=user_id,
            engagement_type=EngagementType.COMMENT
        )
        
        # Filter recent opportunities
        since_date = datetime.utcnow() - timedelta(days=days)
        recent_opportunities = [
            opp for opp in all_opportunities 
            if opp.created_at and opp.created_at >= since_date
        ]
        
        # Group by discovery source
        discovery_sources = {}
        for opp in recent_opportunities:
            source = opp.discovery_source or "unknown"
            discovery_sources[source] = discovery_sources.get(source, 0) + 1
        
        return {
            "discovery_metrics": {
                "total_discovered": len(recent_opportunities),
                "sources_breakdown": discovery_sources,
                "avg_opportunities_per_day": len(recent_opportunities) / max(days, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get discovery metrics: {str(e)}")
        return {"discovery_metrics": {"error": str(e)}}
"""
Analytics endpoints for LinkedIn Presence Automation Application.

Provides endpoints for analytics dashboards, performance metrics,
and recommendation insights.
"""

from typing import Any, Optional, List
from uuid import UUID # Import UUID for type hinting if your IDs are UUIDs
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging # For logging errors

# Assuming your logger is configured
logger = logging.getLogger(__name__)

from app.core.security import get_current_active_user # Ensure this dependency is correctly defined
from app.database.connection import get_db_session # Your @asynccontextmanager decorated dependency
from app.services.analytics_service import AnalyticsService # Ensure this service is correctly implemented
from app.services.recommendation_service import RecommendationService # Ensure this service is correctly implemented
from app.schemas.api_schemas import ( # Ensure these schemas are correctly defined and ORM compatible where needed
    DashboardResponse,
    RecommendationsResponse,
    PerformanceMetricsResponse,
    WeeklyReportResponse
)
# Assuming EngagementPrediction is defined in recommendation_schemas
from app.schemas.recommendation_schemas import RecommendationRequest, EngagementPrediction, OptimalTimingResponse
from app.models.user import User

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_analytics_dashboard(
    period: Optional[str] = Query("30", description="Period in days (7, 30, 90)"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> DashboardResponse: # Changed Any to specific response model
    """
    Get analytics dashboard data.
    """
    async with db_session_cm as session: # Use async with
        try:
            if period not in ["7", "30", "90"]:
                period = "30"
            period_days = int(period)
            
            analytics_service = AnalyticsService(session) # Pass actual session
            
            performance_metrics = await analytics_service.calculate_performance_metrics(
                user_id=current_user.id,
                period_days=period_days
            )
            
            content_trends = await analytics_service.analyze_content_trends(
                user_id=current_user.id,
                period_days=period_days
            )
            
            engagement_history = await analytics_service.get_user_engagement_history(
                user_id=current_user.id,
                days=period_days
            )
            
            # Ensure the Pydantic models can handle the structure from services
            return DashboardResponse(
                metrics=performance_metrics.model_dump() if hasattr(performance_metrics, 'model_dump') else performance_metrics,
                trends=content_trends.model_dump() if hasattr(content_trends, 'model_dump') else content_trends,
                engagement_history=engagement_history, # Assuming this is already a dict
                period_days=period_days,
                user_id=str(current_user.id)
            )
        except Exception as e:
            logger.error(f"Failed to get dashboard data for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get dashboard data: {str(e)}"
            )


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum score filter"),
    content_types: Optional[str] = Query(None, description="Comma-separated content types"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> RecommendationsResponse: # Changed Any to specific response model
    """
    Get content recommendations for user.
    """
    async with db_session_cm as session: # Use async with
        try:
            # Assuming RecommendationService is correctly initialized in your DI or factory
            # If it needs repositories, they should be initialized with 'session'
            # For example:
            # from app.repositories.draft_repository import DraftRepository
            # from app.repositories.analytics_repository import AnalyticsRepository
            # from app.repositories.content_repository import ContentItemRepository
            # from app.services.style_analyzer import StyleAnalyzer
            # from app.utils.timing_optimizer import TimingOptimizer

            # draft_repo = DraftRepository(session)
            # analytics_repo = AnalyticsRepository(session) # Assuming this exists
            # content_repo = ContentItemRepository(session)
            # style_analyzer = StyleAnalyzer(session) # Assuming this exists
            # timing_optimizer = TimingOptimizer(session) # Assuming this exists

            # recommendation_service = RecommendationService(
            #     draft_repo, analytics_repo, content_repo, style_analyzer, timing_optimizer
            # )
            # OR if RecommendationService only takes session:
            recommendation_service = RecommendationService(session) # Pass actual session

            content_type_list = [ct.strip() for ct in content_types.split(",")] if content_types else None
            
            request_data = RecommendationRequest(
                user_id=current_user.id,
                limit=limit,
                min_score=min_score,
                content_types=content_type_list
            )
            
            recommendations_result = await recommendation_service.get_content_recommendations(request_data)
            
            # Ensure recommendations_result.recommendations are Pydantic models or dicts
            # And recommendations_result.optimal_times are also structured correctly
            return RecommendationsResponse(
                user_id=recommendations_result.user_id, # Assuming result has user_id
                recommendations=[rec.model_dump() if hasattr(rec, 'model_dump') else rec for rec in recommendations_result.recommendations],
                optimal_times=[time.model_dump() if hasattr(time, 'model_dump') else time for time in recommendations_result.optimal_times],
                total_count=len(recommendations_result.recommendations), # Or result.total_count if available
                generated_at=recommendations_result.generated_at
            )
            
        except Exception as e:
            logger.error(f"Failed to get recommendations for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get recommendations: {str(e)}"
            )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> PerformanceMetricsResponse: # Changed Any to specific response model
    """
    Get detailed performance metrics.
    """
    async with db_session_cm as session: # Use async with
        try:
            analytics_service = AnalyticsService(session) # Pass actual session
            
            metrics = await analytics_service.calculate_performance_metrics(
                user_id=current_user.id,
                period_days=period_days
            )
            
            # Ensure metrics object matches PerformanceMetricsResponse schema
            return PerformanceMetricsResponse(
                **metrics.model_dump() if hasattr(metrics, 'model_dump') else metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get performance metrics: {str(e)}"
            )


@router.get("/weekly-report", response_model=WeeklyReportResponse)
async def get_weekly_report(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> WeeklyReportResponse: # Changed Any to specific response model
    """
    Get weekly performance report.
    """
    async with db_session_cm as session: # Use async with
        try:
            analytics_service = AnalyticsService(session) # Pass actual session
            report = await analytics_service.generate_weekly_report(current_user.id)
            
            return WeeklyReportResponse(
                 **report.model_dump() if hasattr(report, 'model_dump') else report
            )
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate weekly report: {str(e)}"
            )


@router.get("/trends", response_model=Any) # Use a more specific schema if TrendAnalysis is defined
async def get_content_trends(
    period_days: int = Query(90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> Any: # Change to TrendAnalysis schema if available
    """
    Get content performance trends analysis.
    """
    async with db_session_cm as session: # Use async with
        try:
            analytics_service = AnalyticsService(session) # Pass actual session
            trends = await analytics_service.analyze_content_trends(
                user_id=current_user.id,
                period_days=period_days
            )
            return trends.model_dump() if hasattr(trends, 'model_dump') else trends
        except Exception as e:
            logger.error(f"Failed to get content trends for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get content trends: {str(e)}"
            )


@router.get("/optimal-times", response_model=List[OptimalTimingResponse]) # Changed to more specific model
async def get_optimal_posting_times(
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> List[OptimalTimingResponse]: # Changed Any to specific response model
    """
    Get optimal posting times for user.
    """
    async with db_session_cm as session: # Use async with
        try:
            # Assuming RecommendationService can be initialized with just a session
            # or you'll need to pass its dependencies initialized with 'session'
            recommendation_service = RecommendationService(session) # Pass actual session
            
            optimal_times = await recommendation_service.get_optimal_posting_times(current_user.id)
            
            # Ensure each item in optimal_times can be validated by OptimalTimingResponse
            return [OptimalTimingResponse(**time_data) if isinstance(time_data, dict) else time_data for time_data in optimal_times]
            
        except Exception as e:
            logger.error(f"Failed to get optimal posting times for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get optimal posting times: {str(e)}"
            )


@router.post("/track-performance/{post_id}", response_model=dict) # Or a MessageResponse schema
async def track_post_performance(
    post_id: UUID, # Changed to UUID
    metrics: dict, # This should ideally be a Pydantic model for validation
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> dict: # Change to MessageResponse schema if defined
    """
    Track performance metrics for a published post.
    """
    async with db_session_cm as session: # Use async with
        try:
            analytics_service = AnalyticsService(session) # Pass actual session
            
            await analytics_service.track_post_performance(
                post_id=post_id, # Pass UUID directly
                metrics=metrics
            )
            
            return {"message": "Performance metrics tracked successfully"}
            
        except Exception as e:
            logger.error(f"Failed to track performance for post {post_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to track performance: {str(e)}"
            )


@router.get("/engagement-prediction/{draft_id}", response_model=EngagementPrediction) # Use specific schema
async def get_engagement_prediction(
    draft_id: UUID, # Changed to UUID
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> EngagementPrediction: # Changed Any to specific response model
    """
    Get engagement prediction for a draft.
    """
    async with db_session_cm as session: # Use async with
        try:
            from app.services.engagement_predictor import EngagementPredictor
            # from app.repositories.content_repository import PostDraftRepository # Not needed if predictor takes session

            # Get the draft (handled by EngagementPredictor if it takes draft_id)
            # draft_repo = PostDraftRepository(session) # Initialize repo with actual session
            # draft = await draft_repo.get_by_id(draft_id)
            # if not draft:
            #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
            # if draft.user_id != current_user.id:
            #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            
            predictor = EngagementPredictor(session) # Pass actual session
            # Assuming predict_engagement needs draft_id and current_user object
            # If it needs the draft object, you need to fetch it first
            prediction = await predictor.predict_engagement_by_id(draft_id, current_user) # Assuming such a method or adapt
            
            return EngagementPrediction(**prediction.model_dump() if hasattr(prediction, 'model_dump') else prediction)
            
        except Exception as e:
            logger.error(f"Failed to get engagement prediction for draft {draft_id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get engagement prediction: {str(e)}"
            )


@router.get("/insights", response_model=List[Any]) # Use a more specific schema like List[AnalyticsInsight]
async def get_analytics_insights(
    period_days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db_session_cm: AsyncSession = Depends(get_db_session) # Changed variable name
) -> List[Any]: # Change to List[AnalyticsInsight] if schema defined
    """
    Get analytics insights and recommendations.
    """
    async with db_session_cm as session: # Use async with
        try:
            analytics_service = AnalyticsService(session) # Pass actual session
            report = await analytics_service.generate_weekly_report(current_user.id) # Or a more generic insights function
            
            insights = []
            # Ensure report.insights exists and items are serializable
            if hasattr(report, 'insights') and report.insights:
                for insight in report.insights:
                    insights.append(insight.model_dump() if hasattr(insight, 'model_dump') else insight)
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to get analytics insights for user {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analytics insights: {str(e)}"
            )
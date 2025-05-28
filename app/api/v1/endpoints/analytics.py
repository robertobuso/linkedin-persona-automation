"""
Analytics endpoints for LinkedIn Presence Automation Application.

Provides endpoints for analytics dashboards, performance metrics,
and recommendation insights.
"""

from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.database.connection import get_db_session
from app.services.analytics_service import AnalyticsService
from app.services.recommendation_service import RecommendationService
from app.schemas.api_schemas import (
    DashboardResponse,
    RecommendationsResponse,
    PerformanceMetricsResponse,
    WeeklyReportResponse
)
from app.schemas.recommendation_schemas import RecommendationRequest
from app.models.user import User

router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_analytics_dashboard(
    period: Optional[str] = Query("30", description="Period in days (7, 30, 90)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get analytics dashboard data.
    
    Args:
        period: Analysis period in days
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Dashboard analytics data including metrics and trends
    """
    try:
        # Validate period
        if period not in ["7", "30", "90"]:
            period = "30"
        
        period_days = int(period)
        
        analytics_service = AnalyticsService(db)
        
        # Get performance metrics
        performance_metrics = await analytics_service.calculate_performance_metrics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        # Get content trends
        content_trends = await analytics_service.analyze_content_trends(
            user_id=current_user.id,
            period_days=period_days
        )
        
        # Get engagement history
        engagement_history = await analytics_service.get_user_engagement_history(
            user_id=current_user.id,
            days=period_days
        )
        
        return DashboardResponse(
            metrics=performance_metrics.dict(),
            trends=content_trends.dict(),
            engagement_history=engagement_history,
            period_days=period_days,
            user_id=str(current_user.id)
        )
        
    except Exception as e:
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
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get content recommendations for user.
    
    Args:
        limit: Number of recommendations to return
        min_score: Minimum score filter
        content_types: Optional content type filters
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Content recommendations with scores and optimal timing
    """
    try:
        recommendation_service = RecommendationService(db)
        
        # Parse content types
        content_type_list = None
        if content_types:
            content_type_list = [ct.strip() for ct in content_types.split(",")]
        
        # Create recommendation request
        request = RecommendationRequest(
            user_id=current_user.id,
            limit=limit,
            min_score=min_score,
            content_types=content_type_list
        )
        
        # Get recommendations
        recommendations = await recommendation_service.get_content_recommendations(request)
        
        return RecommendationsResponse(
            recommendations=[rec.dict() for rec in recommendations.recommendations],
            optimal_times=[time.dict() for time in recommendations.optimal_times],
            total_count=len(recommendations.recommendations),
            generated_at=recommendations.generated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get detailed performance metrics.
    
    Args:
        period_days: Analysis period in days
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Detailed performance metrics and analysis
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Get performance metrics
        metrics = await analytics_service.calculate_performance_metrics(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return PerformanceMetricsResponse(
            **metrics.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/weekly-report", response_model=WeeklyReportResponse)
async def get_weekly_report(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get weekly performance report.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Weekly performance report with insights and recommendations
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Generate weekly report
        report = await analytics_service.generate_weekly_report(current_user.id)
        
        return WeeklyReportResponse(
            **report.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate weekly report: {str(e)}"
        )


@router.get("/trends", response_model=dict)
async def get_content_trends(
    period_days: int = Query(90, ge=30, le=365, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get content performance trends analysis.
    
    Args:
        period_days: Analysis period in days
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Content trends analysis with insights
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Get content trends
        trends = await analytics_service.analyze_content_trends(
            user_id=current_user.id,
            period_days=period_days
        )
        
        return trends.dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get content trends: {str(e)}"
        )


@router.get("/optimal-times", response_model=List[dict])
async def get_optimal_posting_times(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get optimal posting times for user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of optimal posting time slots
    """
    try:
        recommendation_service = RecommendationService(db)
        
        # Get optimal posting times
        optimal_times = await recommendation_service.get_optimal_posting_times(current_user.id)
        
        return optimal_times
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimal posting times: {str(e)}"
        )


@router.post("/track-performance/{post_id}")
async def track_post_performance(
    post_id: str,
    metrics: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Track performance metrics for a published post.
    
    Args:
        post_id: Post ID to track
        metrics: Performance metrics data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Track post performance
        await analytics_service.track_post_performance(
            post_id=post_id,
            metrics=metrics
        )
        
        return {"message": "Performance metrics tracked successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track performance: {str(e)}"
        )


@router.get("/engagement-prediction/{draft_id}", response_model=dict)
async def get_engagement_prediction(
    draft_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get engagement prediction for a draft.
    
    Args:
        draft_id: Draft ID to predict engagement for
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Engagement prediction with confidence score
    """
    try:
        from app.services.engagement_predictor import EngagementPredictor
        from app.repositories.content_repository import PostDraftRepository
        
        # Get the draft
        draft_repo = PostDraftRepository(db)
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
        
        # Get engagement prediction
        predictor = EngagementPredictor(db)
        prediction = await predictor.predict_engagement(draft, current_user)
        
        return prediction.dict()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement prediction: {str(e)}"
        )


@router.get("/insights", response_model=List[dict])
async def get_analytics_insights(
    period_days: int = Query(30, ge=7, le=90, description="Analysis period in days"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get analytics insights and recommendations.
    
    Args:
        period_days: Analysis period in days
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of analytics insights with actionable recommendations
    """
    try:
        analytics_service = AnalyticsService(db)
        
        # Generate weekly report to get insights
        report = await analytics_service.generate_weekly_report(current_user.id)
        
        # Format insights for response
        insights = []
        for insight in report.insights:
            insights.append(insight.dict())
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics insights: {str(e)}"
        )
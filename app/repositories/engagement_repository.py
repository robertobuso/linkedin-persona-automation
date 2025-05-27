"""
Engagement repository for LinkedIn Presence Automation Application.

Provides specialized database operations for EngagementOpportunity model
including opportunity discovery, scheduling, and execution tracking.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.engagement import EngagementOpportunity, EngagementType, EngagementStatus, EngagementPriority
from app.repositories.base import BaseRepository, NotFoundError


class EngagementRepository(BaseRepository[EngagementOpportunity]):
    """
    Repository for EngagementOpportunity model with engagement management operations.
    
    Provides specialized database operations for managing LinkedIn engagement
    opportunities including discovery, scheduling, execution, and performance tracking.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize EngagementRepository with database session."""
        super().__init__(EngagementOpportunity, session)
    
    async def get_pending_opportunities(
        self, 
        user_id: UUID,
        limit: int = 20,
        priority: Optional[EngagementPriority] = None
    ) -> List[EngagementOpportunity]:
        """
        Get pending engagement opportunities for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of opportunities
            priority: Optional priority filter
            
        Returns:
            List of pending EngagementOpportunity instances
        """
        conditions = [
            EngagementOpportunity.user_id == user_id,
            EngagementOpportunity.status == EngagementStatus.PENDING,
            or_(
                EngagementOpportunity.expires_at.is_(None),
                EngagementOpportunity.expires_at > datetime.utcnow()
            )
        ]
        
        if priority:
            conditions.append(EngagementOpportunity.priority == priority)
        
        stmt = (
            select(EngagementOpportunity)
            .where(and_(*conditions))
            .order_by(
                EngagementOpportunity.priority.desc(),
                EngagementOpportunity.relevance_score.desc().nullslast(),
                EngagementOpportunity.created_at.asc()
            )
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_scheduled_opportunities(
        self, 
        before_time: Optional[datetime] = None
    ) -> List[EngagementOpportunity]:
        """
        Get engagement opportunities scheduled for execution.
        
        Args:
            before_time: Get opportunities scheduled before this time (default: now)
            
        Returns:
            List of EngagementOpportunity instances ready for execution
        """
        if before_time is None:
            before_time = datetime.utcnow()
        
        stmt = (
            select(EngagementOpportunity)
            .where(
                and_(
                    EngagementOpportunity.status == EngagementStatus.SCHEDULED,
                    or_(
                        EngagementOpportunity.scheduled_for.is_(None),
                        EngagementOpportunity.scheduled_for <= before_time
                    ),
                    or_(
                        EngagementOpportunity.expires_at.is_(None),
                        EngagementOpportunity.expires_at > before_time
                    )
                )
            )
            .order_by(EngagementOpportunity.scheduled_for.asc().nullsfirst())
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_opportunity(
        self,
        user_id: UUID,
        target_type: str,
        target_url: str,
        engagement_type: EngagementType,
        target_id: Optional[str] = None,
        target_author: Optional[str] = None,
        target_title: Optional[str] = None,
        target_content: Optional[str] = None,
        target_company: Optional[str] = None,
        priority: EngagementPriority = EngagementPriority.MEDIUM,
        suggested_comment: Optional[str] = None,
        suggested_message: Optional[str] = None,
        engagement_reason: Optional[str] = None,
        context_tags: Optional[List[str]] = None,
        relevance_score: Optional[int] = None,
        engagement_potential: Optional[int] = None,
        ai_analysis: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None,
        discovery_source: Optional[str] = None,
        discovery_metadata: Optional[Dict[str, Any]] = None
    ) -> EngagementOpportunity:
        """
        Create a new engagement opportunity.
        
        Args:
            user_id: User ID
            target_type: Type of engagement target
            target_url: LinkedIn URL of the target
            engagement_type: Type of engagement to perform
            target_id: Optional LinkedIn ID of the target
            target_author: Optional author/owner of the target
            target_title: Optional title of the target content
            target_content: Optional content text
            target_company: Optional company associated with target
            priority: Priority level
            suggested_comment: AI-generated comment suggestion
            suggested_message: AI-generated message suggestion
            engagement_reason: Explanation of why this engagement is recommended
            context_tags: Tags describing the context
            relevance_score: AI-calculated relevance score
            engagement_potential: Predicted engagement potential
            ai_analysis: Detailed AI analysis
            expires_at: Expiration time for the opportunity
            discovery_source: How the opportunity was discovered
            discovery_metadata: Additional discovery metadata
            
        Returns:
            Created EngagementOpportunity instance
        """
        return await self.create(
            user_id=user_id,
            target_type=target_type,
            target_url=target_url,
            target_id=target_id,
            target_author=target_author,
            target_title=target_title,
            target_content=target_content,
            target_company=target_company,
            engagement_type=engagement_type,
            priority=priority,
            suggested_comment=suggested_comment,
            suggested_message=suggested_message,
            engagement_reason=engagement_reason,
            context_tags=context_tags or [],
            relevance_score=relevance_score,
            engagement_potential=engagement_potential,
            ai_analysis=ai_analysis,
            expires_at=expires_at,
            discovery_source=discovery_source,
            discovery_metadata=discovery_metadata
        )
    
    async def schedule_opportunity(
        self,
        opportunity_id: UUID,
        scheduled_time: Optional[datetime] = None
    ) -> Optional[EngagementOpportunity]:
        """
        Schedule an engagement opportunity for execution.
        
        Args:
            opportunity_id: Opportunity ID
            scheduled_time: When to execute (None for immediate)
            
        Returns:
            Updated EngagementOpportunity instance or None if not found
        """
        return await self.update(
            opportunity_id,
            status=EngagementStatus.SCHEDULED,
            scheduled_for=scheduled_time
        )
    
    async def mark_as_completed(
        self,
        opportunity_id: UUID,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> Optional[EngagementOpportunity]:
        """
        Mark an engagement opportunity as completed.
        
        Args:
            opportunity_id: Opportunity ID
            execution_result: Results and metadata from execution
            
        Returns:
            Updated EngagementOpportunity instance or None if not found
        """
        opportunity = await self.get_by_id(opportunity_id)
        if not opportunity:
            return None
        
        return await self.update(
            opportunity_id,
            status=EngagementStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            attempted_at=datetime.utcnow(),
            attempts_count=opportunity.attempts_count + 1,
            execution_result=execution_result,
            last_error_message=None
        )
    
    async def mark_as_failed(
        self,
        opportunity_id: UUID,
        error_message: str,
        execution_result: Optional[Dict[str, Any]] = None
    ) -> Optional[EngagementOpportunity]:
        """
        Mark an engagement opportunity as failed.
        
        Args:
            opportunity_id: Opportunity ID
            error_message: Error message
            execution_result: Results and metadata from failed execution
            
        Returns:
            Updated EngagementOpportunity instance or None if not found
        """
        opportunity = await self.get_by_id(opportunity_id)
        if not opportunity:
            return None
        
        return await self.update(
            opportunity_id,
            status=EngagementStatus.FAILED,
            attempted_at=datetime.utcnow(),
            attempts_count=opportunity.attempts_count + 1,
            last_error_message=error_message,
            execution_result=execution_result
        )
    
    async def skip_opportunity(
        self,
        opportunity_id: UUID,
        reason: Optional[str] = None
    ) -> Optional[EngagementOpportunity]:
        """
        Skip an engagement opportunity.
        
        Args:
            opportunity_id: Opportunity ID
            reason: Optional reason for skipping
            
        Returns:
            Updated EngagementOpportunity instance or None if not found
        """
        execution_result = {"skipped_reason": reason} if reason else None
        
        return await self.update(
            opportunity_id,
            status=EngagementStatus.SKIPPED,
            execution_result=execution_result
        )
    
    async def expire_old_opportunities(self, before_time: Optional[datetime] = None) -> int:
        """
        Mark expired opportunities as expired.
        
        Args:
            before_time: Mark opportunities expired before this time (default: now)
            
        Returns:
            Number of opportunities marked as expired
        """
        if before_time is None:
            before_time = datetime.utcnow()
        
        # Find opportunities that have expired
        stmt = select(EngagementOpportunity).where(
            and_(
                EngagementOpportunity.status.in_([
                    EngagementStatus.PENDING,
                    EngagementStatus.SCHEDULED
                ]),
                EngagementOpportunity.expires_at.isnot(None),
                EngagementOpportunity.expires_at <= before_time
            )
        )
        
        result = await self.session.execute(stmt)
        expired_opportunities = list(result.scalars().all())
        
        # Update their status
        count = 0
        for opportunity in expired_opportunities:
            await self.update(opportunity.id, status=EngagementStatus.EXPIRED)
            count += 1
        
        return count
    
    async def get_opportunities_by_type(
        self,
        user_id: UUID,
        engagement_type: EngagementType,
        status: Optional[EngagementStatus] = None,
        limit: int = 20
    ) -> List[EngagementOpportunity]:
        """
        Get engagement opportunities by type.
        
        Args:
            user_id: User ID
            engagement_type: Type of engagement
            status: Optional status filter
            limit: Maximum number of opportunities
            
        Returns:
            List of EngagementOpportunity instances
        """
        conditions = [
            EngagementOpportunity.user_id == user_id,
            EngagementOpportunity.engagement_type == engagement_type
        ]
        
        if status:
            conditions.append(EngagementOpportunity.status == status)
        
        stmt = (
            select(EngagementOpportunity)
            .where(and_(*conditions))
            .order_by(EngagementOpportunity.created_at.desc())
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_high_priority_opportunities(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[EngagementOpportunity]:
        """
        Get high-priority engagement opportunities.
        
        Args:
            user_id: User ID
            limit: Maximum number of opportunities
            
        Returns:
            List of high-priority EngagementOpportunity instances
        """
        stmt = (
            select(EngagementOpportunity)
            .where(
                and_(
                    EngagementOpportunity.user_id == user_id,
                    EngagementOpportunity.status.in_([
                        EngagementStatus.PENDING,
                        EngagementStatus.SCHEDULED
                    ]),
                    EngagementOpportunity.priority.in_([
                        EngagementPriority.HIGH,
                        EngagementPriority.URGENT
                    ]),
                    or_(
                        EngagementOpportunity.expires_at.is_(None),
                        EngagementOpportunity.expires_at > datetime.utcnow()
                    )
                )
            )
            .order_by(
                EngagementOpportunity.priority.desc(),
                EngagementOpportunity.relevance_score.desc().nullslast()
            )
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def record_user_feedback(
        self,
        opportunity_id: UUID,
        feedback: str
    ) -> Optional[EngagementOpportunity]:
        """
        Record user feedback on an engagement opportunity.
        
        Args:
            opportunity_id: Opportunity ID
            feedback: User feedback (positive, negative, neutral)
            
        Returns:
            Updated EngagementOpportunity instance or None if not found
        """
        return await self.update(opportunity_id, user_feedback=feedback)
    
    async def get_engagement_stats(self, user_id: UUID, days: int = 30) -> Dict[str, Any]:
        """
        Get engagement statistics for a user.
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary with engagement statistics
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get status counts
        status_stmt = (
            select(EngagementOpportunity.status, func.count(EngagementOpportunity.id))
            .where(
                and_(
                    EngagementOpportunity.user_id == user_id,
                    EngagementOpportunity.created_at >= since_date
                )
            )
            .group_by(EngagementOpportunity.status)
        )
        
        status_result = await self.session.execute(status_stmt)
        status_counts = dict(status_result.all())
        
        # Get type counts
        type_stmt = (
            select(EngagementOpportunity.engagement_type, func.count(EngagementOpportunity.id))
            .where(
                and_(
                    EngagementOpportunity.user_id == user_id,
                    EngagementOpportunity.created_at >= since_date
                )
            )
            .group_by(EngagementOpportunity.engagement_type)
        )
        
        type_result = await self.session.execute(type_stmt)
        type_counts = dict(type_result.all())
        
        total_opportunities = sum(status_counts.values())
        completed_count = status_counts.get(EngagementStatus.COMPLETED, 0)
        
        return {
            "total_opportunities": total_opportunities,
            "completion_rate": (completed_count / total_opportunities * 100) if total_opportunities > 0 else 0,
            "status_breakdown": {
                "pending": status_counts.get(EngagementStatus.PENDING, 0),
                "scheduled": status_counts.get(EngagementStatus.SCHEDULED, 0),
                "completed": completed_count,
                "failed": status_counts.get(EngagementStatus.FAILED, 0),
                "skipped": status_counts.get(EngagementStatus.SKIPPED, 0),
                "expired": status_counts.get(EngagementStatus.EXPIRED, 0),
            },
            "type_breakdown": {
                "likes": type_counts.get(EngagementType.LIKE, 0),
                "comments": type_counts.get(EngagementType.COMMENT, 0),
                "shares": type_counts.get(EngagementType.SHARE, 0),
                "follows": type_counts.get(EngagementType.FOLLOW, 0),
                "connects": type_counts.get(EngagementType.CONNECT, 0),
                "messages": type_counts.get(EngagementType.MESSAGE, 0),
            },
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
"""
Engagement models for LinkedIn Presence Automation Application.

Defines EngagementOpportunity entity for tracking and managing LinkedIn
engagement activities like commenting, liking, and sharing.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class EngagementType(str, Enum):
    """Enumeration of LinkedIn engagement types."""
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"
    FOLLOW = "follow"
    CONNECT = "connect"
    MESSAGE = "message"


class EngagementStatus(str, Enum):
    """Enumeration of engagement opportunity statuses."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    EXPIRED = "expired"


class EngagementPriority(str, Enum):
    """Enumeration of engagement priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EngagementOpportunity(Base):
    """
    Engagement opportunity model representing potential LinkedIn engagement actions.
    
    Stores information about posts, profiles, or content that the user should
    engage with to build their LinkedIn presence and network.
    """
    
    __tablename__ = "engagement_opportunities"
    
    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Unique engagement opportunity identifier"
    )
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who should perform this engagement"
    )
    
    # Engagement target information
    target_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of target (post, profile, company, etc.)"
    )
    
    target_url = Column(
        String(1000),
        nullable=False,
        doc="LinkedIn URL of the engagement target"
    )
    
    target_id = Column(
        String(255),
        nullable=True,
        doc="LinkedIn ID of the target (post ID, profile ID, etc.)"
    )
    
    # Target metadata
    target_author = Column(
        String(255),
        nullable=True,
        doc="Author or owner of the target content/profile"
    )
    
    target_title = Column(
        String(500),
        nullable=True,
        doc="Title or headline of the target content"
    )
    
    target_content = Column(
        Text,
        nullable=True,
        doc="Content text or description of the target"
    )
    
    target_company = Column(
        String(255),
        nullable=True,
        doc="Company associated with the target"
    )
    
    # Engagement configuration
    engagement_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Type of engagement to perform"
    )
    
    priority = Column(
        String(20),
        default=EngagementPriority.MEDIUM,
        nullable=False,
        index=True,
        doc="Priority level of this engagement opportunity"
    )
    
    # AI-generated engagement content
    suggested_comment = Column(
        Text,
        nullable=True,
        doc="AI-generated comment suggestion"
    )
    
    suggested_message = Column(
        Text,
        nullable=True,
        doc="AI-generated message suggestion for connections"
    )
    
    # Engagement reasoning and context
    engagement_reason = Column(
        Text,
        nullable=True,
        doc="AI explanation of why this engagement is recommended"
    )
    
    context_tags = Column(
        JSONB,
        nullable=False,
        default=list,
        doc="Tags describing the context or category of this opportunity"
    )
    
    # AI analysis and scoring
    relevance_score = Column(
        Integer,
        nullable=True,
        index=True,
        doc="AI-calculated relevance score (0-100)"
    )
    
    engagement_potential = Column(
        Integer,
        nullable=True,
        doc="Predicted engagement potential score (0-100)"
    )
    
    ai_analysis = Column(
        JSONB,
        nullable=True,
        doc="Detailed AI analysis of the engagement opportunity"
    )
    
    # Status and scheduling
    status = Column(
        String(50),
        default=EngagementStatus.PENDING,
        nullable=False,
        index=True,
        doc="Current status of the engagement opportunity"
    )
    
    scheduled_for = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Scheduled time for engagement execution"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Expiration time for this opportunity"
    )
    
    # Execution tracking
    attempted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When engagement was attempted"
    )
    
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="When engagement was successfully completed"
    )
    
    attempts_count = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of execution attempts"
    )
    
    # Results and feedback
    execution_result = Column(
        JSONB,
        nullable=True,
        doc="Results and metadata from engagement execution"
    )
    
    user_feedback = Column(
        String(20),
        nullable=True,
        doc="User feedback on the engagement suggestion (positive, negative, neutral)"
    )
    
    # Error tracking
    last_error_message = Column(
        Text,
        nullable=True,
        doc="Last error message from failed engagement attempt"
    )
    
    # Source tracking
    discovery_source = Column(
        String(100),
        nullable=True,
        doc="How this opportunity was discovered (feed_scan, network_analysis, etc.)"
    )
    
    discovery_metadata = Column(
        JSONB,
        nullable=True,
        doc="Additional metadata about opportunity discovery"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Opportunity creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Last opportunity update timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="engagement_opportunities",
        doc="User who should perform this engagement"
    )
    
    def __repr__(self) -> str:
        """String representation of EngagementOpportunity instance."""
        return (
            f"<EngagementOpportunity(id={self.id}, type='{self.engagement_type}', "
            f"status='{self.status}', priority='{self.priority}')>"
        )
    
    def is_expired(self) -> bool:
        """
        Check if the engagement opportunity has expired.
        
        Returns:
            True if the opportunity has passed its expiration time
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_ready_for_execution(self) -> bool:
        """
        Check if the engagement is ready for execution.
        
        Returns:
            True if the engagement is scheduled and ready to execute
        """
        if self.status != EngagementStatus.SCHEDULED:
            return False
        
        if self.scheduled_for is None:
            return True  # Execute immediately if no schedule
        
        return datetime.utcnow() >= self.scheduled_for
    
    def can_retry(self, max_attempts: int = 3) -> bool:
        """
        Check if the engagement can be retried.
        
        Args:
            max_attempts: Maximum number of retry attempts allowed
            
        Returns:
            True if the engagement can be retried
        """
        return (
            self.status == EngagementStatus.FAILED and
            self.attempts_count < max_attempts and
            not self.is_expired()
        )
    
    def update_execution_result(
        self, 
        success: bool, 
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update the engagement opportunity with execution results.
        
        Args:
            success: Whether the engagement was successful
            result_data: Additional result data and metadata
            error_message: Error message if execution failed
        """
        self.attempts_count += 1
        self.attempted_at = datetime.utcnow()
        
        if success:
            self.status = EngagementStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            self.last_error_message = None
        else:
            self.status = EngagementStatus.FAILED
            self.last_error_message = error_message
        
        if result_data:
            self.execution_result = result_data
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert EngagementOpportunity instance to dictionary.
        
        Returns:
            Dict containing engagement opportunity data
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "target_type": self.target_type,
            "target_url": self.target_url,
            "target_id": self.target_id,
            "target_author": self.target_author,
            "target_title": self.target_title,
            "target_company": self.target_company,
            "engagement_type": self.engagement_type,
            "priority": self.priority,
            "suggested_comment": self.suggested_comment,
            "suggested_message": self.suggested_message,
            "engagement_reason": self.engagement_reason,
            "context_tags": self.context_tags,
            "relevance_score": self.relevance_score,
            "engagement_potential": self.engagement_potential,
            "status": self.status,
            "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "attempts_count": self.attempts_count,
            "user_feedback": self.user_feedback,
            "discovery_source": self.discovery_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
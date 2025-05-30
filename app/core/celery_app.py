"""
Extended Celery configuration for LinkedIn Presence Automation Application.

Phase 1: Extends existing Celery infrastructure to add LinkedIn discovery
queue and commenting tasks while maintaining existing patterns.
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Queue
import asyncio
from celery.signals import worker_process_init
from app.database.connection import db_manager, get_database_url
import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Create Celery instance (using existing instance)
celery_app = Celery("linkedin_automation")

# EXTENDED Configuration - maintains existing settings and adds new ones
celery_app.conf.update(
    # Broker settings (unchanged)
    broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    
    # Task settings (unchanged)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # EXTENDED Task routing - adds new LinkedIn discovery routes
    task_routes={
        # Existing content tasks
        "app.tasks.content_tasks.discover_content_task": {"queue": "content_discovery"},
        "app.tasks.content_tasks.process_source_task": {"queue": "content_processing"},
        "app.tasks.content_tasks.process_content_item_task": {"queue": "content_processing"},
        "app.tasks.content_tasks.cleanup_expired_content_task": {"queue": "maintenance"},
        
        # NEW: LinkedIn discovery and commenting tasks
        "app.tasks.linkedin_tasks.discover_linkedin_posts_task": {"queue": "linkedin_discovery"},
        "app.tasks.linkedin_tasks.process_comment_opportunity_task": {"queue": "linkedin_commenting"},
        "app.tasks.linkedin_tasks.execute_scheduled_comments_task": {"queue": "linkedin_commenting"},
        "app.tasks.linkedin_tasks.cleanup_expired_opportunities_task": {"queue": "maintenance"},
        "app.tasks.linkedin_tasks.update_comment_performance_task": {"queue": "analytics"},
    },
    
    # EXTENDED Queue configuration - adds new LinkedIn queues
    task_default_queue="default",
    task_queues=(
        # Existing queues
        Queue("default"),
        Queue("content_discovery"),
        Queue("content_processing"),
        Queue("maintenance"),
        
        # NEW: LinkedIn-specific queues
        Queue("linkedin_discovery"),
        Queue("linkedin_commenting"),
        Queue("analytics"),
    ),
    
    # Worker settings (unchanged)
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings (unchanged)
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # EXTENDED Beat schedule - adds new LinkedIn discovery tasks
    beat_schedule={
        # Existing content discovery tasks
        "discover-content-every-2-hours": {
            "task": "app.tasks.content_tasks.discover_content_task",
            "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
            "options": {"queue": "content_discovery"},
        },
        "cleanup-expired-content-daily": {
            "task": "app.tasks.content_tasks.cleanup_expired_content_task",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "options": {"queue": "maintenance"},
        },
        
        # NEW: LinkedIn discovery tasks
        "discover-linkedin-posts-every-4-hours": {
            "task": "app.tasks.linkedin_tasks.discover_linkedin_posts_task",
            "schedule": crontab(minute=30, hour="*/4"),  # Every 4 hours at :30
            "options": {"queue": "linkedin_discovery"},
        },
        "execute-scheduled-comments-every-30-minutes": {
            "task": "app.tasks.linkedin_tasks.execute_scheduled_comments_task",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "options": {"queue": "linkedin_commenting"},
        },
        "cleanup-expired-opportunities-daily": {
            "task": "app.tasks.linkedin_tasks.cleanup_expired_opportunities_task",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
            "options": {"queue": "maintenance"},
        },
        "update-comment-performance-hourly": {
            "task": "app.tasks.linkedin_tasks.update_comment_performance_task",
            "schedule": crontab(minute=15),  # Every hour at :15
            "options": {"queue": "analytics"},
        },
    },
)

# EXTENDED Auto-discover tasks - adds new LinkedIn tasks
celery_app.autodiscover_tasks([
    "app.tasks.content_tasks",  # Existing
    "app.tasks.linkedin_tasks",  # NEW
])

# Existing debug task (unchanged)
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f"Request: {self.request!r}")
    return "Celery is working!"

# Existing task failure handler (unchanged)
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures with logging and notifications."""
    print(f"Task {task_id} failed: {error}")
    print(f"Traceback: {traceback}")
    # Here you could add notification logic (email, Slack, etc.)

# Configure error handling (unchanged)
celery_app.conf.task_annotations = {
    "*": {
        "on_failure": task_failure_handler,
    }
}

# Existing worker process init (unchanged)
@worker_process_init.connect
def init_db_on_worker_start(**kwargs):
    """Initialize database connection when a Celery worker process starts."""
    logger.info("Celery worker process starting, initializing database manager...")
    try:
        database_url = get_database_url()
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        echo_db = os.getenv("DEBUG", "False").lower() == "true" and os.getenv("CELERY_DB_ECHO", "False").lower() == "true"

        if not db_manager._initialized:
            db_manager.initialize(
                database_url=database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                echo=echo_db
            )
            logger.info("Database manager initialized for Celery worker.")
        else:
            logger.info("Database manager already initialized for Celery worker.")
    except Exception as e:
        logger.error(f"Error initializing database for Celery worker: {e}", exc_info=True)


# NEW: LinkedIn Task Definitions
"""
LinkedIn task definitions that integrate with existing infrastructure.
File: app/tasks/linkedin_tasks.py
"""

# LinkedIn Tasks Implementation (would be in separate file)
LINKEDIN_TASKS_CODE = '''
"""
LinkedIn tasks for automated discovery and commenting.

Integrates with existing Celery infrastructure and follows established patterns.
"""

import asyncio
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from celery import shared_task
from app.database.connection import get_db_session
from app.services.linkedin_post_discovery import LinkedInPostDiscoveryService
from app.services.smart_commenting_service import SmartCommentingService
from app.repositories.engagement_repository import EngagementRepository
from app.repositories.user_repository import UserRepository
from app.models.engagement import EngagementStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def discover_linkedin_posts_task(self, user_ids: Optional[List[str]] = None):
    """
    Discover LinkedIn posts for commenting opportunities.
    
    Args:
        user_ids: Optional list of user IDs to process. If None, processes all active users.
    """
    try:
        logger.info("Starting LinkedIn post discovery task")
        
        # Run async function in sync context
        result = asyncio.run(_discover_posts_async(user_ids))
        
        logger.info(f"LinkedIn post discovery completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"LinkedIn post discovery task failed: {str(e)}")
        raise self.retry(countdown=300, exc=e)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=2)
def process_comment_opportunity_task(self, opportunity_id: str, user_id: str):
    """
    Process a single comment opportunity.
    
    Args:
        opportunity_id: Engagement opportunity ID
        user_id: User ID
    """
    try:
        logger.info(f"Processing comment opportunity {opportunity_id}")
        
        result = asyncio.run(_process_comment_async(opportunity_id, user_id))
        
        logger.info(f"Comment opportunity processed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Comment opportunity processing failed: {str(e)}")
        raise self.retry(countdown=600, exc=e)  # Retry after 10 minutes


@shared_task(bind=True)
def execute_scheduled_comments_task(self):
    """
    Execute comments that are scheduled for now.
    """
    try:
        logger.info("Starting scheduled comments execution")
        
        result = asyncio.run(_execute_scheduled_comments_async())
        
        logger.info(f"Scheduled comments execution completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Scheduled comments execution failed: {str(e)}")
        return {"error": str(e)}


@shared_task(bind=True)
def cleanup_expired_opportunities_task(self):
    """
    Cleanup expired engagement opportunities.
    """
    try:
        logger.info("Starting expired opportunities cleanup")
        
        result = asyncio.run(_cleanup_expired_opportunities_async())
        
        logger.info(f"Cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {"error": str(e)}


@shared_task(bind=True)
def update_comment_performance_task(self):
    """
    Update comment performance metrics for analytics.
    """
    try:
        logger.info("Starting comment performance update")
        
        result = asyncio.run(_update_comment_performance_async())
        
        logger.info(f"Performance update completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Performance update failed: {str(e)}")
        return {"error": str(e)}


async def _discover_posts_async(user_ids: Optional[List[str]]):
    """Async function for post discovery."""
    async with get_db_session() as session:
        discovery_service = LinkedInPostDiscoveryService(session)
        user_repo = UserRepository(session)
        
        total_posts = 0
        total_opportunities = 0
        processed_users = 0
        
        # Get users to process
        if user_ids:
            users = []
            for user_id_str in user_ids:
                user = await user_repo.get_by_id(UUID(user_id_str))
                if user and user.has_valid_linkedin_token():
                    users.append(user)
        else:
            # Get all active users with LinkedIn tokens
            all_users = await user_repo.find_by(is_active=True)
            users = [u for u in all_users if u.has_valid_linkedin_token()]
        
        # Process each user
        for user in users:
            try:
                result = await discovery_service.discover_posts_for_commenting(user.id)
                total_posts += result.posts_found
                total_opportunities += result.opportunities_created
                processed_users += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to discover posts for user {user.id}: {str(e)}")
                continue
        
        return {
            "processed_users": processed_users,
            "total_posts_found": total_posts,
            "total_opportunities_created": total_opportunities,
            "completed_at": datetime.utcnow().isoformat()
        }


async def _process_comment_async(opportunity_id: str, user_id: str):
    """Async function for processing comment opportunity."""
    async with get_db_session() as session:
        commenting_service = SmartCommentingService(session)
        
        result = await commenting_service.execute_comment_opportunity(
            UUID(opportunity_id), UUID(user_id)
        )
        
        return {
            "opportunity_id": opportunity_id,
            "success": result.success,
            "comment_posted": result.comment_text is not None,
            "error": result.error_message
        }


async def _execute_scheduled_comments_async():
    """Async function for executing scheduled comments."""
    async with get_db_session() as session:
        engagement_repo = EngagementRepository(session)
        commenting_service = SmartCommentingService(session)
        
        # Get scheduled opportunities ready for execution
        scheduled_opportunities = await engagement_repo.get_scheduled_opportunities(
            before_time=datetime.utcnow()
        )
        
        executed_count = 0
        failed_count = 0
        
        for opportunity in scheduled_opportunities:
            try:
                result = await commenting_service.execute_comment_opportunity(
                    opportunity.id, opportunity.user_id
                )
                
                if result.success:
                    executed_count += 1
                else:
                    failed_count += 1
                
                # Small delay between executions
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to execute opportunity {opportunity.id}: {str(e)}")
                failed_count += 1
                continue
        
        return {
            "total_scheduled": len(scheduled_opportunities),
            "executed": executed_count,
            "failed": failed_count,
            "completed_at": datetime.utcnow().isoformat()
        }


async def _cleanup_expired_opportunities_async():
    """Async function for cleaning up expired opportunities."""
    async with get_db_session() as session:
        engagement_repo = EngagementRepository(session)
        
        expired_count = await engagement_repo.expire_old_opportunities()
        
        return {
            "expired_opportunities": expired_count,
            "completed_at": datetime.utcnow().isoformat()
        }


async def _update_comment_performance_async():
    """Async function for updating comment performance."""
    async with get_db_session() as session:
        # This would integrate with existing analytics service
        # For now, just return success
        return {
            "performance_updates": 0,
            "completed_at": datetime.utcnow().isoformat()
        }
'''

# Queue monitoring and health check functions
def get_queue_status():
    """
    Get status of all Celery queues for monitoring.
    
    Returns:
        Dictionary with queue statistics
    """
    try:
        from celery import current_app
        
        inspect = current_app.control.inspect()
        
        # Get queue lengths
        active_queues = inspect.active_queues() or {}
        
        # Get active tasks
        active_tasks = inspect.active() or {}
        
        # Get scheduled tasks
        scheduled_tasks = inspect.scheduled() or {}
        
        return {
            "queues": {
                "content_discovery": len(active_queues.get("content_discovery", [])),
                "content_processing": len(active_queues.get("content_processing", [])),
                "linkedin_discovery": len(active_queues.get("linkedin_discovery", [])),
                "linkedin_commenting": len(active_queues.get("linkedin_commenting", [])),
                "analytics": len(active_queues.get("analytics", [])),
                "maintenance": len(active_queues.get("maintenance", [])),
            },
            "active_tasks": sum(len(tasks) for tasks in active_tasks.values()),
            "scheduled_tasks": sum(len(tasks) for tasks in scheduled_tasks.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        return {"error": str(e)}


def trigger_linkedin_discovery(user_ids: Optional[List[str]] = None):
    """
    Manually trigger LinkedIn post discovery.
    
    Args:
        user_ids: Optional list of user IDs to process
    """
    from app.tasks.linkedin_tasks import discover_linkedin_posts_task
    
    return discover_linkedin_posts_task.delay(user_ids)


def trigger_comment_execution():
    """Manually trigger execution of scheduled comments."""
    from app.tasks.linkedin_tasks import execute_scheduled_comments_task
    
    return execute_scheduled_comments_task.delay()
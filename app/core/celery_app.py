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

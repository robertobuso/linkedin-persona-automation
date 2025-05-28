"""
Celery application configuration for LinkedIn Presence Automation Application.

Configures Celery with Redis broker for background task processing including
content ingestion, processing, and scheduled discovery jobs.
"""

from celery import Celery
from celery.schedules import crontab
from kombu import Queue
import asyncio
from celery.signals import worker_process_init
from app.database.connection import db_manager, get_database_url # Import db_manager and config getter
import os # For getenv if used directly in init
import logging # For logging within the signal handler

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery("linkedin_automation")

# Configuration
celery_app.conf.update(
    # Broker settings
    broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "app.tasks.content_tasks.discover_content_task": {"queue": "content_discovery"},
        "app.tasks.content_tasks.process_source_task": {"queue": "content_processing"},
        "app.tasks.content_tasks.process_content_item_task": {"queue": "content_processing"},
        "app.tasks.content_tasks.cleanup_expired_content_task": {"queue": "maintenance"},
    },
    
    # Queue configuration
    task_default_queue="default",
    task_queues=(
        Queue("default"),
        Queue("content_discovery"),
        Queue("content_processing"),
        Queue("maintenance"),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Beat schedule for periodic tasks
    beat_schedule={
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
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.tasks.content_tasks",
])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f"Request: {self.request!r}")
    return "Celery is working!"


# Task failure handler
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures with logging and notifications."""
    print(f"Task {task_id} failed: {error}")
    print(f"Traceback: {traceback}")
    # Here you could add notification logic (email, Slack, etc.)


# Configure error handling
celery_app.conf.task_annotations = {
    "*": {
        "on_failure": task_failure_handler,
    }
}

@worker_process_init.connect
def init_db_on_worker_start(**kwargs):
    """Initialize database connection when a Celery worker process starts."""
    logger.info("Celery worker process starting, initializing database manager...")
    try:
        # Get database URL and other params as your db_manager.initialize expects
        # This logic should mirror how you get params for db_manager.initialize in your main app startup
        database_url = get_database_url() # Assuming this function correctly gets the URL
        pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
        max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
        # Celery workers typically don't need SQL echoing like a dev FastAPI server might
        echo_db = os.getenv("DEBUG", "False").lower() == "true" and os.getenv("CELERY_DB_ECHO", "False").lower() == "true"

        if not db_manager._initialized: # Check if already initialized in this process
            db_manager.initialize(
                database_url=database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                echo=echo_db # Control echoing for celery separately if needed
            )
            logger.info("Database manager initialized for Celery worker.")
        else:
            logger.info("Database manager already initialized for Celery worker.")
    except Exception as e:
        logger.error(f"Error initializing database for Celery worker: {e}", exc_info=True)
        # Depending on severity, you might want to raise an error to stop the worker
        # For now, we'll log and let it continue, but tasks might fail if DB isn't up.
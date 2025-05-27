"""
Celery tasks for content ingestion and processing.

Defines background tasks for content discovery, processing, and maintenance
with proper error handling and retry logic.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from celery import Task
from celery.exceptions import Retry

from app.core.celery_app import celery_app
from app.database.connection import get_db_session
from app.services.content_ingestion import ContentIngestionService
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.models.content import ContentStatus

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Base task class with callback support and error handling."""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Exception info: {einfo}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    retry_backoff=True,
    retry_jitter=True
)
def discover_content_task(self, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Periodic task to discover content from all active sources.
    
    Args:
        user_id: Optional user ID to process sources for specific user
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Starting content discovery task (user_id: {user_id})")
        
        # Run async content ingestion
        result = asyncio.run(_run_content_ingestion(user_id))
        
        logger.info(f"Content discovery completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Content discovery task failed: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 60  # 1min, 2min, 4min
            logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown, exc=exc)
        
        # Max retries reached
        return {
            "success": False,
            "error": str(exc),
            "retries": self.request.retries
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 30},
    retry_backoff=True
)
def process_source_task(self, source_id: str) -> Dict[str, Any]:
    """
    Process content from a specific source.
    
    Args:
        source_id: UUID string of the content source to process
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Starting source processing task for source: {source_id}")
        
        # Convert string to UUID
        source_uuid = UUID(source_id)
        
        # Run async source processing
        result = asyncio.run(_run_source_processing(source_uuid))
        
        logger.info(f"Source processing completed: {result}")
        return result
        
    except ValueError as exc:
        logger.error(f"Invalid source ID format: {source_id}")
        return {
            "success": False,
            "error": f"Invalid source ID: {str(exc)}"
        }
    except Exception as exc:
        logger.error(f"Source processing task failed: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 30  # 30s, 1min, 2min
            logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown, exc=exc)
        
        return {
            "success": False,
            "error": str(exc),
            "retries": self.request.retries
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 120}
)
def process_content_item_task(self, content_item_id: str) -> Dict[str, Any]:
    """
    Process a specific content item with AI analysis.
    
    Args:
        content_item_id: UUID string of the content item to process
        
    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Starting content item processing task for item: {content_item_id}")
        
        # Convert string to UUID
        item_uuid = UUID(content_item_id)
        
        # Run async content item processing
        result = asyncio.run(_run_content_item_processing(item_uuid))
        
        logger.info(f"Content item processing completed: {result}")
        return result
        
    except ValueError as exc:
        logger.error(f"Invalid content item ID format: {content_item_id}")
        return {
            "success": False,
            "error": f"Invalid content item ID: {str(exc)}"
        }
    except Exception as exc:
        logger.error(f"Content item processing task failed: {str(exc)}")
        
        # Retry with longer delay for AI processing
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries * 120  # 2min, 4min
            logger.info(f"Retrying in {countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=countdown, exc=exc)
        
        return {
            "success": False,
            "error": str(exc),
            "retries": self.request.retries
        }


@celery_app.task(
    bind=True,
    base=CallbackTask,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 1, 'countdown': 300}
)
def cleanup_expired_content_task(self) -> Dict[str, Any]:
    """
    Cleanup expired and old content items.
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Starting content cleanup task")
        
        # Run async cleanup
        result = asyncio.run(_run_content_cleanup())
        
        logger.info(f"Content cleanup completed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Content cleanup task failed: {str(exc)}")
        
        # Single retry for cleanup tasks
        if self.request.retries < self.max_retries:
            logger.info("Retrying cleanup task in 5 minutes")
            raise self.retry(countdown=300, exc=exc)
        
        return {
            "success": False,
            "error": str(exc),
            "retries": self.request.retries
        }


@celery_app.task(
    bind=True,
    base=CallbackTask
)
def batch_process_sources_task(self, source_ids: List[str]) -> Dict[str, Any]:
    """
    Process multiple sources in batch.
    
    Args:
        source_ids: List of source UUID strings to process
        
    Returns:
        Dictionary with batch processing results
    """
    try:
        logger.info(f"Starting batch source processing for {len(source_ids)} sources")
        
        results = []
        for source_id in source_ids:
            try:
                # Process each source individually
                result = process_source_task.apply(args=[source_id])
                results.append({
                    "source_id": source_id,
                    "success": result.successful(),
                    "result": result.result if result.successful() else str(result.info)
                })
            except Exception as exc:
                logger.error(f"Failed to process source {source_id}: {str(exc)}")
                results.append({
                    "source_id": source_id,
                    "success": False,
                    "result": str(exc)
                })
        
        # Calculate summary
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        summary = {
            "total_sources": len(source_ids),
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / len(source_ids) * 100) if source_ids else 0,
            "results": results
        }
        
        logger.info(f"Batch processing completed: {summary}")
        return summary
        
    except Exception as exc:
        logger.error(f"Batch processing task failed: {str(exc)}")
        return {
            "success": False,
            "error": str(exc)
        }


# Async helper functions
async def _run_content_ingestion(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run content ingestion asynchronously.
    
    Args:
        user_id: Optional user ID string
        
    Returns:
        Processing results dictionary
    """
    async with get_db_session() as session:
        ingestion_service = ContentIngestionService(session)
        
        # Convert user_id to UUID if provided
        user_uuid = UUID(user_id) if user_id else None
        
        # Process all sources
        result = await ingestion_service.process_all_sources(user_uuid)
        
        return {
            "success": True,
            "processed_count": result.processed_count,
            "error_count": result.error_count,
            "skipped_count": result.skipped_count,
            "sources_processed": len(result.sources_processed),
            "errors": result.errors[:10],  # Limit error details
            "timestamp": datetime.utcnow().isoformat()
        }


async def _run_source_processing(source_id: UUID) -> Dict[str, Any]:
    """
    Run source processing asynchronously.
    
    Args:
        source_id: Source UUID to process
        
    Returns:
        Processing results dictionary
    """
    async with get_db_session() as session:
        ingestion_service = ContentIngestionService(session)
        
        # Process specific source
        result = await ingestion_service.process_source_by_id(source_id)
        
        return {
            "success": result.error_count == 0,
            "source_id": str(source_id),
            "processed_count": result.processed_count,
            "error_count": result.error_count,
            "skipped_count": result.skipped_count,
            "errors": result.errors,
            "timestamp": datetime.utcnow().isoformat()
        }


async def _run_content_item_processing(item_id: UUID) -> Dict[str, Any]:
    """
    Run content item processing asynchronously.
    
    Args:
        item_id: Content item UUID to process
        
    Returns:
        Processing results dictionary
    """
    async with get_db_session() as session:
        content_repo = ContentItemRepository(session)
        
        # Get content item
        content_item = await content_repo.get_by_id(item_id)
        if not content_item:
            return {
                "success": False,
                "error": "Content item not found"
            }
        
        try:
            # Update status to processing
            await content_repo.update_processing_status(
                item_id,
                ContentStatus.PROCESSING
            )
            
            # Here you would add AI processing logic
            # For now, just mark as processed with basic analysis
            ai_analysis = {
                "word_count": len(content_item.content.split()),
                "char_count": len(content_item.content),
                "processed_at": datetime.utcnow().isoformat(),
                "processing_version": "1.0"
            }
            
            # Calculate basic relevance score
            relevance_score = min(100, max(0, len(content_item.content) // 10))
            
            # Update with processed status
            await content_repo.update_processing_status(
                item_id,
                ContentStatus.PROCESSED,
                ai_analysis=ai_analysis,
                relevance_score=relevance_score
            )
            
            return {
                "success": True,
                "item_id": str(item_id),
                "relevance_score": relevance_score,
                "word_count": ai_analysis["word_count"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as exc:
            # Update with failed status
            await content_repo.update_processing_status(
                item_id,
                ContentStatus.FAILED,
                error_message=str(exc)
            )
            
            return {
                "success": False,
                "item_id": str(item_id),
                "error": str(exc)
            }


async def _run_content_cleanup() -> Dict[str, Any]:
    """
    Run content cleanup asynchronously.
    
    Returns:
        Cleanup results dictionary
    """
    async with get_db_session() as session:
        content_repo = ContentItemRepository(session)
        
        # Define cleanup criteria
        cutoff_date = datetime.utcnow() - timedelta(days=90)  # 90 days old
        
        try:
            # Get old content items
            old_items = await content_repo.find_by(
                status=ContentStatus.PROCESSED
            )
            
            # Filter by date
            items_to_cleanup = [
                item for item in old_items 
                if item.created_at < cutoff_date
            ]
            
            # Archive old items (update status instead of deleting)
            archived_count = 0
            for item in items_to_cleanup:
                await content_repo.update_processing_status(
                    item.id,
                    ContentStatus.SKIPPED  # Use SKIPPED as archived status
                )
                archived_count += 1
            
            # Clean up failed items older than 30 days
            failed_cutoff = datetime.utcnow() - timedelta(days=30)
            failed_items = await content_repo.find_by(
                status=ContentStatus.FAILED
            )
            
            failed_cleanup_count = 0
            for item in failed_items:
                if item.created_at < failed_cutoff:
                    await content_repo.delete(item.id)
                    failed_cleanup_count += 1
            
            return {
                "success": True,
                "archived_items": archived_count,
                "deleted_failed_items": failed_cleanup_count,
                "cutoff_date": cutoff_date.isoformat(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as exc:
            logger.error(f"Content cleanup failed: {str(exc)}")
            return {
                "success": False,
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }


# Task monitoring and management
@celery_app.task(bind=True)
def get_task_status(self, task_id: str) -> Dict[str, Any]:
    """
    Get status of a specific task.
    
    Args:
        task_id: Task ID to check
        
    Returns:
        Task status information
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result,
            "traceback": result.traceback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task
def health_check_task() -> Dict[str, Any]:
    """
    Health check task for monitoring.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker_id": health_check_task.request.hostname,
        "queue": health_check_task.request.delivery_info.get("routing_key", "unknown")
    }
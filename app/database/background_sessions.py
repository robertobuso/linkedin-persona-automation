"""
Database session helper utilities for background tasks and proper async context management.

This module provides utilities to create database sessions in background contexts
where the normal FastAPI dependency injection isn't available.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os

logger = logging.getLogger(__name__)

# Background task database engine and session maker
_background_engine = None
_background_session_maker = None


def get_background_database_url() -> str:
    """Get database URL for background tasks."""
    return os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://user:password@localhost/linkedin_automation"
    )


def initialize_background_database():
    """Initialize database engine and session maker for background tasks."""
    global _background_engine, _background_session_maker
    
    if _background_engine is None:
        database_url = get_background_database_url()
        
        _background_engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for debugging
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        
        _background_session_maker = async_sessionmaker(
            bind=_background_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        logger.info("Initialized background database engine and session maker")


@asynccontextmanager
async def get_db_session_directly() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session directly for use in background tasks.
    
    This function creates a new database session that can be used in background
    tasks where the normal FastAPI dependency injection isn't available.
    
    Yields:
        AsyncSession: Database session for background tasks
    """
    # Initialize background database if not already done
    if _background_session_maker is None:
        initialize_background_database()
    
    session = _background_session_maker()
    try:
        yield session
        # Auto-commit if no explicit transaction management
        await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error in background session: {str(e)}")
        await session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error in background session: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager  
async def get_db_session_for_background_task() -> AsyncGenerator[AsyncSession, None]:
    """
    Alternative name for get_db_session_directly for clarity.
    
    Yields:
        AsyncSession: Database session for background tasks
    """
    async with get_db_session_directly() as session:
        yield session


async def test_background_database_connection() -> bool:
    """
    Test the background database connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with get_db_session_directly() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Background database connection test failed: {str(e)}")
        return False


async def cleanup_background_database():
    """Clean up background database resources."""
    global _background_engine, _background_session_maker
    
    if _background_engine:
        await _background_engine.dispose()
        _background_engine = None
        _background_session_maker = None
        logger.info("Cleaned up background database resources")


# Content-specific database utilities
class DatabaseOperationError(Exception):
    """Base exception for database operations in background tasks."""
    pass


class BackgroundDatabaseManager:
    """
    Manager for database operations in background tasks.
    
    Provides a high-level interface for common database operations
    in background tasks with proper error handling.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with automatic error handling."""
        try:
            async with get_db_session_directly() as session:
                yield session
        except SQLAlchemyError as e:
            self.logger.error(f"Database operation failed: {str(e)}")
            raise DatabaseOperationError(f"Database operation failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error in database operation: {str(e)}")
            raise DatabaseOperationError(f"Unexpected database error: {str(e)}")
    
    async def execute_with_retry(self, operation, max_retries: int = 3):
        """
        Execute a database operation with retry logic.
        
        Args:
            operation: Async function that takes a session parameter
            max_retries: Maximum number of retry attempts
            
        Returns:
            Result of the operation
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                async with self.get_session() as session:
                    return await operation(session)
                    
            except DatabaseOperationError as e:
                last_error = e
                self.logger.warning(f"Database operation attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import asyncio
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    break
            except Exception as e:
                last_error = e
                self.logger.error(f"Non-retryable error in database operation: {str(e)}")
                break
        
        # If we get here, all retries failed
        raise DatabaseOperationError(f"Database operation failed after {max_retries} attempts: {str(last_error)}")


# Global instance for background tasks
background_db_manager = BackgroundDatabaseManager()


# Utility functions for content processing
async def safe_create_content_item(session: AsyncSession, **item_data) -> bool:
    """
    Safely create a content item with proper error handling and field validation.
    
    Args:
        session: Database session
        **item_data: Content item data
        
    Returns:
        bool: True if created successfully, False otherwise
    """
    try:
        from app.repositories.content_repository import ContentItemRepository
        from app.repositories.base import DataValidationError, DuplicateError
        
        content_repo = ContentItemRepository(session)
        
        # Create the content item with automatic validation
        await content_repo.create(**item_data)
        
        logger.debug(f"Successfully created content item: {item_data.get('title', 'Unknown')[:50]}...")
        return True
        
    except DuplicateError:
        logger.debug(f"Skipping duplicate content item: {item_data.get('url', 'Unknown URL')}")
        return False
        
    except DataValidationError as e:
        logger.warning(f"Data validation failed for content item: {str(e)}")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error creating content item: {str(e)}")
        return False


async def update_source_stats(session: AsyncSession, source_id, items_found: int = 0, success: bool = True, error_message: str = None):
    """
    Update content source statistics safely.
    
    Args:
        session: Database session
        source_id: Source ID to update
        items_found: Number of items found
        success: Whether the operation was successful
        error_message: Error message if operation failed
    """
    try:
        from app.repositories.content_repository import ContentSourceRepository
        
        source_repo = ContentSourceRepository(session)
        await source_repo.update_check_status(
            source_id=source_id,
            success=success,
            items_found=items_found,
            error_message=error_message
        )
        
        logger.debug(f"Updated stats for source {source_id}: {items_found} items, success={success}")
        
    except Exception as e:
        logger.error(f"Failed to update source stats for {source_id}: {str(e)}")
        # Don't raise - stats update failure shouldn't break the main operation


# Initialize background database on module import
try:
    initialize_background_database()
except Exception as e:
    logger.warning(f"Failed to initialize background database on import: {str(e)}")
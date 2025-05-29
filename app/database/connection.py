"""
Database connection and session management for LinkedIn Presence Automation Application.

This module provides async SQLAlchemy engine configuration, session factory,
and database connection utilities with proper connection pooling and cleanup.
"""

import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import MetaData, text
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# SQLAlchemy declarative base for all models
Base = declarative_base()

# Naming convention for constraints to ensure consistent migration naming
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

Base.metadata = MetaData(naming_convention=convention)


class DatabaseManager:
    """
    Manages database connections, sessions, and engine lifecycle.
    
    Provides async SQLAlchemy engine with connection pooling and session factory
    for the LinkedIn automation application.
    """
    
    def __init__(self):
        self.engine: Optional[create_async_engine] = None # Corrected type hint
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None # Corrected type hint
        self._initialized = False
    
    def initialize(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 20,
        max_overflow: int = 30,
        echo: bool = False
    ) -> None:
        """
        Initialize the database engine and session factory.
        
        Args:
            database_url: PostgreSQL connection URL. If None, reads from DATABASE_URL env var
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum number of connections that can overflow the pool
            echo: Whether to log all SQL statements
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return
        
        if database_url is None:
            database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Configure connection pooling based on environment
        if "sqlite" in database_url.lower():
            # SQLite doesn't support connection pooling
            poolclass = NullPool
            pool_size = 0
            max_overflow = 0
        else:
            poolclass = QueuePool
        
        # Create async engine with connection pooling
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=poolclass,
            pool_size=pool_size if poolclass == QueuePool else 0,
            max_overflow=max_overflow if poolclass == QueuePool else 0,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False, # Typically False for async sessions unless you need specific autoflush behavior
            autocommit=False
        )
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
    @asynccontextmanager
    async def get_session_directly(self) -> AsyncGenerator[AsyncSession, None]:
        if not self._initialized or not self.session_factory: # Check session_factory too
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        session: AsyncSession = self.session_factory() # Create a session
        try:
            yield session
            await session.commit() # Commit at the end of the 'with' block if no exceptions
        except Exception:
            await session.rollback() # Rollback on any exception
            raise
        finally:
            await session.close() # Ensure session is closed

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")
        self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get a database session.
    It yields the session, and FastAPI handles the context management.
    """
    if not db_manager._initialized or not db_manager.session_factory:
        # Ensure db_manager is initialized (e.g., in FastAPI lifespan)
        # This might happen if a worker/process didn't run the full init.
        # However, init_database() should be called by the main app and workers.
        logger.error("get_db_session called but DatabaseManager not initialized!")
        raise RuntimeError("Database manager not initialized. Call initialize() first.")

    session: AsyncSession = db_manager.session_factory()
    try:
        yield session
        await session.commit() # Commit if no exceptions within the route handler's use of session
    except Exception:
        await session.rollback() # Rollback on any exception
        raise
    finally:
        await session.close() # Always close the session


def get_database_url() -> str:
    """
    Get database URL from environment variables with validation.
    
    Returns:
        str: Database connection URL
        
    Raises:
        ValueError: If DATABASE_URL is not set
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return database_url


async def init_database() -> None:
    """
    Initialize database connection with environment configuration.
    
    Reads configuration from environment variables:
    - DATABASE_URL: PostgreSQL connection string
    - DATABASE_POOL_SIZE: Connection pool size (default: 20)
    - DATABASE_MAX_OVERFLOW: Max overflow connections (default: 30)
    - DEBUG: Enable SQL query logging (default: False)
    """
    logger.info("Initializing database manager for FastAPI app...")
    database_url = get_database_url()
    pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
    echo_db = os.getenv("DEBUG", "False").lower() == "true" # For FastAPI, echo if DEBUG is true
    
    db_manager.initialize(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo_db
    )

    # Optional: Test the connection after initialization
    try:
                # For a simpler test of the factory:
        test_session = db_manager.session_factory()
        await test_session.execute(text("SELECT 1"))
        await test_session.commit()
        await test_session.close()
        logger.info("Database session factory test successful during init.")
    except Exception as e:
        logger.error(f"Database session factory test failed during init: {e}", exc_info=True)
        raise


async def close_database() -> None:
    """Close database connections and cleanup resources."""
    await db_manager.close()


async def run_migrations(): # If you still want this function for some reason
    logger.info("Database migrations are expected to be handled by the entrypoint script.")
    # You could add a check here if needed, e.g., verify alembic_version table
    pass
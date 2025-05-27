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
from sqlalchemy import MetaData
import logging

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
        self.engine: Optional[object] = None
        self.session_factory: Optional[async_sessionmaker] = None
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
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with proper cleanup.
        
        Yields:
            AsyncSession: Database session for executing queries
            
        Raises:
            RuntimeError: If database manager is not initialized
        """
        if not self._initialized or self.session_factory is None:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine and cleanup resources."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")
        
        self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session for dependency injection.
    
    Yields:
        AsyncSession: Database session for executing queries
    """
    async with db_manager.get_session() as session:
        yield session


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
    database_url = get_database_url()
    pool_size = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
    echo = os.getenv("DEBUG", "False").lower() == "true"
    
    db_manager.initialize(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo
    )


async def close_database() -> None:
    """Close database connections and cleanup resources."""
    await db_manager.close()
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


class AsyncSessionContextManager:
    """
    Async context manager for database sessions that works with FastAPI dependencies.
    
    This allows you to use `async with db_session_cm as session:` in your endpoints
    without needing to refactor all your existing code.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self) -> AsyncSession:
        """Enter the async context and return a database session."""
        self.session = self.session_factory()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context, handling commit/rollback and cleanup."""
        if self.session:
            try:
                if exc_type is None:
                    # No exception occurred, commit the transaction
                    await self.session.commit()
                else:
                    # Exception occurred, rollback the transaction
                    await self.session.rollback()
            finally:
                # Always close the session
                await self.session.close()
                self.session = None


class DatabaseManager:
    """
    Manages database connections, sessions, and engine lifecycle.
    
    Provides async SQLAlchemy engine with connection pooling and session factory
    for the LinkedIn automation application.
    """
    
    def __init__(self):
        self.engine: Optional[create_async_engine] = None
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
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
            autoflush=False,
            autocommit=False
        )
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
    @asynccontextmanager
    async def get_session_context(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session with proper context management.
        
        This is for manual use when you need a direct context manager.
        """
        if not self._initialized or not self.session_factory:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def get_session_cm(self) -> AsyncSessionContextManager:
        """
        Get an async context manager for database sessions.
        
        This returns a context manager that can be used with `async with`
        and is compatible with FastAPI dependencies.
        """
        if not self._initialized or not self.session_factory:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        
        return AsyncSessionContextManager(self.session_factory)

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            logger.info("Database engine closed")
        self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()



def get_db_session() -> AsyncSessionContextManager:
    """
    FastAPI dependency to get a database session context manager.
    
    This returns an AsyncSessionContextManager that can be used with `async with`
    in your endpoints, allowing you to keep your existing code structure:
    
    ```python
    async def my_endpoint(
        db_session_cm: AsyncSessionContextManager = Depends(get_db_session)
    ):
        async with db_session_cm as session:
            # Your existing code works unchanged!
            repo = SomeRepository(session)
            return await repo.some_method()
    ```
    """
    if not db_manager._initialized or not db_manager.session_factory:
        logger.error("get_db_session called but DatabaseManager not initialized!")
        raise RuntimeError("Database manager not initialized. Call initialize() first.")

    return db_manager.get_session_cm()


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
    echo_db = os.getenv("DEBUG", "False").lower() == "true"
    
    db_manager.initialize(
        database_url=database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo_db
    )

    # Test the connection after initialization
    try:
        async with db_manager.get_session_context() as test_session:
            await test_session.execute(text("SELECT 1"))
        logger.info("Database connection test successful during init.")
    except Exception as e:
        logger.error(f"Database connection test failed during init: {e}", exc_info=True)
        raise


async def close_database() -> None:
    """Close database connections and cleanup resources."""
    await db_manager.close()


async def run_migrations():
    """Database migrations are expected to be handled by the entrypoint script."""
    logger.info("Database migrations are expected to be handled by the entrypoint script.")
    pass


# Independent background session maker
_background_engine = None
_background_session_maker = None

def _get_database_url():
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/db_name")

def _initialize_background_engine():
    """Initialize background database engine if not already done."""
    global _background_engine, _background_session_maker
    
    if _background_engine is None:
        database_url = _get_database_url()
        
        _background_engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        
        _background_session_maker = async_sessionmaker(
            bind=_background_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info("Initialized independent background database engine")

@asynccontextmanager
async def get_db_session_directly() -> AsyncGenerator[AsyncSession, None]:
    """
    Create an independent database session for background tasks.
    
    This doesn't depend on the main app's db_manager and creates its own connection.
    """
    # Initialize if needed
    _initialize_background_engine()
    
    session = _background_session_maker()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Background session error: {str(e)}")
        await session.rollback()
        raise
    finally:
        await session.close()


# Alternative: Use the existing engine if available
@asynccontextmanager  
async def get_db_session_from_existing() -> AsyncGenerator[AsyncSession, None]:
    """
    Try to use existing database setup, fallback to independent session.
    """
    try:
        # Try to use the existing database setup
        from app.database.connection import db_manager
        
        # Check if db_manager has a usable method
        if hasattr(db_manager, 'engine'):
            # Create session directly from engine
            async with AsyncSession(db_manager.engine) as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        else:
            # Fallback to independent session
            async with get_db_session_directly() as session:
                yield session
                
    except Exception as e:
        logger.warning(f"Could not use existing db_manager: {str(e)}, using independent session")
        # Final fallback
        async with get_db_session_directly() as session:
            yield session
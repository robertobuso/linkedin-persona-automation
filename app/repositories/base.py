"""
Base repository pattern implementation for LinkedIn Presence Automation Application.

Fixed version with single combined pagination method that supports both filtering and ordering.
"""

import logging
from typing import TypeVar, Generic, List, Optional, Dict, Any, Type, Union
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError, DataError
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager

from app.database.connection import Base

ModelType = TypeVar("ModelType", bound=Base)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database operations."""
    pass


class DuplicateError(DatabaseError):
    """Exception raised when attempting to create duplicate records."""
    pass


class NotFoundError(DatabaseError):
    """Exception raised when a requested record is not found."""
    pass


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass


class DataValidationError(DatabaseError):
    """Exception raised when data validation fails."""
    pass


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing generic CRUD operations for SQLAlchemy models.
    
    This class implements the repository pattern with async SQLAlchemy,
    providing common database operations that can be extended by specific
    model repositories.
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize the repository with a model class and database session.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    def _validate_string_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and truncate string fields based on model constraints.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            Dictionary with validated/truncated values
        """
        validated_data = data.copy()
        
        # Get model column information
        for column_name, column in self.model.__table__.columns.items():
            if column_name in validated_data and hasattr(column.type, 'length'):
                value = validated_data[column_name]
                if isinstance(value, str) and column.type.length:
                    max_length = column.type.length
                    if len(value) > max_length:
                        # Truncate with ellipsis if too long
                        if max_length > 3:
                            validated_data[column_name] = value[:max_length-3] + "..."
                        else:
                            validated_data[column_name] = value[:max_length]
                        
                        logger.warning(
                            f"Truncated {column_name} from {len(value)} to {max_length} chars "
                            f"for {self.model.__name__}"
                        )
        
        return validated_data
    
    async def get_by_id(self, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """Get a single record by its primary key."""
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
            
        except OperationalError as e:
            logger.error(f"Database connection failed getting {self.model.__name__} {id}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model.__name__} by ID {id}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def get_by_ids(self, ids: List[Union[UUID, str, int]]) -> List[ModelType]:
        """
        Get multiple records by their primary keys.
        
        Args:
            ids: List of primary key values
            
        Returns:
            List of model instances
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = select(self.model).where(self.model.id.in_(ids))
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except OperationalError as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record with proper validation and error handling.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
            
        Raises:
            DuplicateError: If record violates unique constraints
            DataValidationError: If data validation fails
            ConnectionError: If database connection fails
        """
        try:
            # Validate and truncate string fields
            validated_kwargs = self._validate_string_fields(kwargs)
            
            # Add ID if not provided
            if 'id' not in validated_kwargs:
                validated_kwargs['id'] = uuid4()
            
            # Add timestamps
            now = datetime.utcnow()
            if hasattr(self.model, 'created_at') and 'created_at' not in validated_kwargs:
                validated_kwargs['created_at'] = now
            if hasattr(self.model, 'updated_at') and 'updated_at' not in validated_kwargs:
                validated_kwargs['updated_at'] = now
            
            # Use model's create_safe method if available (for ContentItem)
            if hasattr(self.model, 'create_safe'):
                instance = self.model.create_safe(**validated_kwargs)
            else:
                instance = self.model(**validated_kwargs)
            
            # Add to session and flush to get ID
            self.session.add(instance)
            await self.session.flush()
            
            # Refresh to get all database-generated fields
            await self.session.refresh(instance)
            
            logger.debug(f"Created {self.model.__name__} with ID: {instance.id}")
            return instance
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity constraint violation creating {self.model.__name__}: {str(e)}")
            raise DuplicateError(f"Record violates unique constraints: {str(e)}")
            
        except DataError as e:
            await self.session.rollback()
            logger.error(f"Data validation error creating {self.model.__name__}: {str(e)}")
            raise DataValidationError(f"Data validation failed: {str(e)}")
            
        except OperationalError as e:
            await self.session.rollback()
            logger.error(f"Database connection failed creating {self.model.__name__}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
        
    async def update(self, id: Union[UUID, str, int], **kwargs) -> Optional[ModelType]:
        """
        Update an existing record by ID with proper validation.
        
        Args:
            id: Primary key of record to update
            **kwargs: Field values to update
            
        Returns:
            Updated model instance or None if not found
        """
        try:
            # Validate and truncate string fields
            validated_kwargs = self._validate_string_fields(kwargs)
            
            # Add updated timestamp
            if hasattr(self.model, 'updated_at'):
                validated_kwargs['updated_at'] = datetime.utcnow()
            
            # Use update with returning to get the updated instance
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**validated_kwargs)
                .returning(self.model)
            )
            
            result = await self.session.execute(stmt)
            updated_instance = result.scalar_one_or_none()
            
            if updated_instance:
                await self.session.refresh(updated_instance)
                logger.debug(f"Updated {self.model.__name__} with ID: {id}")
            
            return updated_instance
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity constraint violation updating {self.model.__name__} {id}: {str(e)}")
            raise DuplicateError(f"Update violates unique constraints: {str(e)}")
            
        except DataError as e:
            await self.session.rollback()
            logger.error(f"Data validation error updating {self.model.__name__} {id}: {str(e)}")
            raise DataValidationError(f"Data validation failed: {str(e)}")
            
        except OperationalError as e:
            await self.session.rollback()
            logger.error(f"Database connection failed updating {self.model.__name__} {id}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error updating {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def delete(self, id: Union[UUID, str, int]) -> bool:
        """Delete a record by ID."""
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            
            deleted = result.rowcount > 0
            if deleted:
                logger.debug(f"Deleted {self.model.__name__} with ID: {id}")
            
            return deleted
            
        except OperationalError as e:
            await self.session.rollback()
            logger.error(f"Database connection failed deleting {self.model.__name__} {id}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error deleting {self.model.__name__} {id}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """List all records with optional pagination."""
        try:
            stmt = select(self.model).offset(offset)
            
            if limit is not None:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except OperationalError as e:
            logger.error(f"Database connection failed listing {self.model.__name__}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def list_with_pagination(
        self, 
        page: int = 1, 
        page_size: int = 20,
        order_by: Optional[str] = None,
        order_desc: bool = False,
        **filters
    ) -> Dict[str, Any]:
        """
        List records with pagination, filtering, and ordering.
        
        COMBINED METHOD - supports both filtering and ordering capabilities.
        
        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: Field name to order by (optional)
            order_desc: Whether to order in descending order
            **filters: Filter conditions (field_name=value)
            
        Returns:
            Dictionary with items, total_count, page, page_size, total_pages, has_next, has_prev
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build base query
            stmt = select(self.model)
            
            # Apply filters if provided
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        conditions.append(getattr(self.model, key) == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            # Add ordering if specified
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    stmt = stmt.order_by(order_field.desc())
                else:
                    stmt = stmt.order_by(order_field)
            
            # Add pagination
            paginated_stmt = stmt.offset(offset).limit(page_size)
            
            # Execute paginated query
            result = await self.session.execute(paginated_stmt)
            items = list(result.scalars().all())
            
            # Get total count with same filters
            count_stmt = select(func.count(self.model.id))
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        conditions.append(getattr(self.model, key) == value)
                
                if conditions:
                    count_stmt = count_stmt.where(and_(*conditions))
            
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
            
            return {
                "items": items,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
            
        except OperationalError as e:
            logger.error(f"Database connection failed in pagination for {self.model.__name__}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in pagination for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def count(self, **filters) -> int:
        """Count records matching the given filters."""
        try:
            stmt = select(func.count(self.model.id))
            
            # Apply filters
            if filters:
                conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        conditions.append(getattr(self.model, key) == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except OperationalError as e:
            logger.error(f"Database connection failed counting {self.model.__name__}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error counting {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def exists(self, **filters) -> bool:
        """Check if any records exist matching the given filters."""
        count = await self.count(**filters)
        return count > 0

    async def bulk_create(self, instances_data: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple instances in batch with validation."""
        try:
            instances = []
            now = datetime.utcnow()
            
            for data in instances_data:
                # Validate and truncate string fields
                validated_data = self._validate_string_fields(data)
                
                # Add ID if not provided
                if 'id' not in validated_data:
                    validated_data['id'] = uuid4()
                
                # Add timestamps
                if hasattr(self.model, 'created_at') and 'created_at' not in validated_data:
                    validated_data['created_at'] = now
                if hasattr(self.model, 'updated_at') and 'updated_at' not in validated_data:
                    validated_data['updated_at'] = now
                
                # Use model's create_safe method if available
                if hasattr(self.model, 'create_safe'):
                    instance = self.model.create_safe(**validated_data)
                else:
                    instance = self.model(**validated_data)
                
                instances.append(instance)
            
            # Add all instances to session
            self.session.add_all(instances)
            await self.session.flush()
            
            # Refresh all instances
            for instance in instances:
                await self.session.refresh(instance)
            
            logger.debug(f"Bulk created {len(instances)} {self.model.__name__} instances")
            return instances
            
        except (IntegrityError, DataError, OperationalError) as e:
            await self.session.rollback()
            logger.error(f"Bulk create failed for {self.model.__name__}: {str(e)}")
            raise
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Bulk create failed for {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in a single transaction.
        
        Args:
            updates: List of dictionaries with 'id' and field values to update
            
        Returns:
            Number of records updated
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            updated_count = 0
            
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                record_id = update_data.pop('id')
                
                # Validate and truncate string fields
                validated_data = self._validate_string_fields(update_data)
                
                stmt = (
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**validated_data)
                )
                result = await self.session.execute(stmt)
                updated_count += result.rowcount
            
            return updated_count
            
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def find_by(self, **filters) -> List[ModelType]:
        """Find records matching the given filters."""
        try:
            stmt = select(self.model)
            
            # Apply filters
            conditions = []
            for key, value in filters.items():
                if hasattr(self.model, key):
                    conditions.append(getattr(self.model, key) == value)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
            
        except OperationalError as e:
            logger.error(f"Database connection failed finding {self.model.__name__}: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error finding {self.model.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    async def find_one_by(self, **filters) -> Optional[ModelType]:
        """Find a single record matching the given filters."""
        results = await self.find_by(**filters)
        return results[0] if results else None
    
    @asynccontextmanager
    async def transaction(self):
        """Context manager for explicit transaction handling."""
        try:
            yield self.session
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
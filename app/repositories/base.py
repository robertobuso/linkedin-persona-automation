"""
Base repository pattern implementation for LinkedIn Presence Automation Application.

Provides generic CRUD operations and common database patterns that can be
extended by specific model repositories.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any, Type, Union
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, OperationalError
from app.database.connection import Base

# Type variable for model classes
ModelType = TypeVar("ModelType", bound=Base)


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
    
    async def get_by_id(self, id: Union[UUID, str, int]) -> Optional[ModelType]:
        """
        Get a single record by its primary key.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = select(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except OperationalError as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
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
        Create a new record.
        
        Args:
            **kwargs: Field values for the new record
            
        Returns:
            Created model instance
            
        Raises:
            DuplicateError: If record violates unique constraints
            ConnectionError: If database connection fails
        """
        try:
            instance = self.model(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicateError(f"Record already exists: {str(e)}")
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def update(self, id: Union[UUID, str, int], **kwargs) -> Optional[ModelType]:
        """
        Update an existing record by ID.
        
        Args:
            id: Primary key of record to update
            **kwargs: Field values to update
            
        Returns:
            Updated model instance or None if not found
            
        Raises:
            DuplicateError: If update violates unique constraints
            ConnectionError: If database connection fails
        """
        try:
            stmt = (
                update(self.model)
                .where(self.model.id == id)
                .values(**kwargs)
                .returning(self.model)
            )
            result = await self.session.execute(stmt)
            updated_instance = result.scalar_one_or_none()
            
            if updated_instance:
                await self.session.refresh(updated_instance)
            
            return updated_instance
        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicateError(f"Update violates constraints: {str(e)}")
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def delete(self, id: Union[UUID, str, int]) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: Primary key of record to delete
            
        Returns:
            True if record was deleted, False if not found
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = delete(self.model).where(self.model.id == id)
            result = await self.session.execute(stmt)
            return result.rowcount > 0
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def list_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        List all records with optional pagination.
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = select(self.model).offset(offset)
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except OperationalError as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def list_with_pagination(
        self, 
        page: int = 1, 
        page_size: int = 20,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> Dict[str, Any]:
        """
        List records with pagination and optional ordering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: Field name to order by
            order_desc: Whether to order in descending order
            
        Returns:
            Dictionary with items, total_count, page, page_size, total_pages
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Build base query
            stmt = select(self.model)
            
            # Add ordering if specified
            if order_by and hasattr(self.model, order_by):
                order_field = getattr(self.model, order_by)
                if order_desc:
                    stmt = stmt.order_by(order_field.desc())
                else:
                    stmt = stmt.order_by(order_field)
            
            # Add pagination
            paginated_stmt = stmt.offset(offset).limit(page_size)
            
            # Execute queries
            result = await self.session.execute(paginated_stmt)
            items = list(result.scalars().all())
            
            # Get total count
            count_stmt = select(func.count(self.model.id))
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar()
            
            # Calculate total pages
            total_pages = (total_count + page_size - 1) // page_size
            
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
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def count(self, **filters) -> int:
        """
        Count records matching the given filters.
        
        Args:
            **filters: Field filters for counting
            
        Returns:
            Number of matching records
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = select(func.count(self.model.id))
            
            # Apply filters
            if filters:
                conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        conditions.append(getattr(self.model, field) == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return result.scalar()
        except OperationalError as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def exists(self, **filters) -> bool:
        """
        Check if any records exist matching the given filters.
        
        Args:
            **filters: Field filters for existence check
            
        Returns:
            True if matching records exist
            
        Raises:
            ConnectionError: If database connection fails
        """
        count = await self.count(**filters)
        return count > 0
    
    async def find_by(self, **filters) -> List[ModelType]:
        """
        Find records matching the given filters.
        
        Args:
            **filters: Field filters for search
            
        Returns:
            List of matching model instances
            
        Raises:
            ConnectionError: If database connection fails
        """
        try:
            stmt = select(self.model)
            
            # Apply filters
            if filters:
                conditions = []
                for field, value in filters.items():
                    if hasattr(self.model, field):
                        if isinstance(value, list):
                            conditions.append(getattr(self.model, field).in_(value))
                        else:
                            conditions.append(getattr(self.model, field) == value)
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except OperationalError as e:
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
    async def find_one_by(self, **filters) -> Optional[ModelType]:
        """
        Find a single record matching the given filters.
        
        Args:
            **filters: Field filters for search
            
        Returns:
            Model instance or None if not found
            
        Raises:
            ConnectionError: If database connection fails
        """
        results = await self.find_by(**filters)
        return results[0] if results else None
    
    async def bulk_create(self, records: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            records: List of dictionaries containing field values
            
        Returns:
            List of created model instances
            
        Raises:
            DuplicateError: If any record violates unique constraints
            ConnectionError: If database connection fails
        """
        try:
            instances = [self.model(**record) for record in records]
            self.session.add_all(instances)
            await self.session.flush()
            
            # Refresh all instances to get generated IDs
            for instance in instances:
                await self.session.refresh(instance)
            
            return instances
        except IntegrityError as e:
            await self.session.rollback()
            raise DuplicateError(f"Bulk create failed due to duplicates: {str(e)}")
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
    
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
                stmt = (
                    update(self.model)
                    .where(self.model.id == record_id)
                    .values(**update_data)
                )
                result = await self.session.execute(stmt)
                updated_count += result.rowcount
            
            return updated_count
        except OperationalError as e:
            await self.session.rollback()
            raise ConnectionError(f"Database connection failed: {str(e)}")
"""
Repository for user content preferences with versioning and caching support.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_content_preferences import UserContentPreferences
from app.repositories.base import BaseRepository, NotFoundError, DuplicateError

logger = logging.getLogger(__name__)


class UserContentPreferencesRepository(BaseRepository[UserContentPreferences]):
    """
    Repository for UserContentPreferences with specialized operations for 
    preference management, versioning, and performance optimization.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize UserContentPreferencesRepository with database session."""
        super().__init__(UserContentPreferences, session)
    
    async def get_active_preferences_for_user(self, user_id: UUID) -> Optional[UserContentPreferences]:
        """
        Get the active content preferences for a user.
        
        Args:
            user_id: User ID to get preferences for
            
        Returns:
            Active UserContentPreferences instance or None
        """
        stmt = select(UserContentPreferences).where(
            and_(
                UserContentPreferences.user_id == user_id,
                UserContentPreferences.is_active == True
            )
        ).order_by(desc(UserContentPreferences.created_at))
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_preferences_for_user(
        self, 
        user_id: UUID, 
        preferences_data: Dict[str, Any]
    ) -> UserContentPreferences:
        """
        Create new content preferences for a user, deactivating any existing ones.
        
        Args:
            user_id: User ID to create preferences for
            preferences_data: Dictionary of preference values
            
        Returns:
            Created UserContentPreferences instance
        """
        try:
            # First, deactivate any existing active preferences
            await self._deactivate_existing_preferences(user_id)
            
            # Create new preferences
            preferences_data['user_id'] = user_id
            preferences_data['is_active'] = True
            preferences_data['preferences_version'] = await self._get_next_version(user_id)
            
            new_preferences = await self.create(**preferences_data)
            
            logger.info(f"Created new content preferences for user {user_id}, version {new_preferences.preferences_version}")
            return new_preferences
            
        except Exception as e:
            logger.error(f"Failed to create preferences for user {user_id}: {str(e)}")
            raise
    
    async def update_preferences_for_user(
        self, 
        user_id: UUID, 
        preferences_updates: Dict[str, Any]
    ) -> UserContentPreferences:
        """
        Update content preferences for a user by creating a new version.
        
        Args:
            user_id: User ID to update preferences for
            preferences_updates: Dictionary of preference updates
            
        Returns:
            Updated UserContentPreferences instance
        """
        try:
            # Get current active preferences
            current_prefs = await self.get_active_preferences_for_user(user_id)
            
            if current_prefs:
                # Create new version with updates
                current_data = current_prefs.to_dict()
                # Remove fields that shouldn't be copied
                for field in ['id', 'created_at', 'updated_at']:
                    current_data.pop(field, None)
                
                # Apply updates
                current_data.update(preferences_updates)
                
                # Create new version
                return await self.create_preferences_for_user(user_id, current_data)
            else:
                # No existing preferences, create new ones
                return await self.create_preferences_for_user(user_id, preferences_updates)
                
        except Exception as e:
            logger.error(f"Failed to update preferences for user {user_id}: {str(e)}")
            raise
    
    async def get_preferences_history(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[UserContentPreferences]:
        """
        Get the preference history for a user.
        
        Args:
            user_id: User ID to get history for
            limit: Maximum number of records to return
            
        Returns:
            List of UserContentPreferences ordered by creation date (newest first)
        """
        stmt = select(UserContentPreferences).where(
            UserContentPreferences.user_id == user_id
        ).order_by(desc(UserContentPreferences.created_at)).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def restore_preferences_version(
        self, 
        user_id: UUID, 
        preferences_id: UUID
    ) -> UserContentPreferences:
        """
        Restore a previous version of preferences by making it active.
        
        Args:
            user_id: User ID
            preferences_id: ID of preferences version to restore
            
        Returns:
            Restored UserContentPreferences instance
            
        Raises:
            NotFoundError: If preferences not found or don't belong to user
        """
        try:
            # Get the preferences to restore
            prefs_to_restore = await self.get_by_id(preferences_id)
            if not prefs_to_restore or prefs_to_restore.user_id != user_id:
                raise NotFoundError(f"Preferences {preferences_id} not found for user {user_id}")
            
            # Deactivate current active preferences
            await self._deactivate_existing_preferences(user_id)
            
            # Create new version based on the one to restore
            restore_data = prefs_to_restore.to_dict()
            # Remove fields that shouldn't be copied
            for field in ['id', 'created_at', 'updated_at']:
                restore_data.pop(field, None)
            
            # Create as new version
            return await self.create_preferences_for_user(user_id, restore_data)
            
        except Exception as e:
            logger.error(f"Failed to restore preferences {preferences_id} for user {user_id}: {str(e)}")
            raise
    
    async def get_users_with_preferences(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get users who have active content preferences.
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of dictionaries with user_id and preference summary
        """
        try:
            stmt = select(UserContentPreferences).where(
                UserContentPreferences.is_active == True
            ).offset(offset)
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.session.execute(stmt)
            preferences_list = list(result.scalars().all())
            
            return [
                {
                    "user_id": str(prefs.user_id),
                    "preferences_version": prefs.preferences_version,
                    "primary_interests": prefs.primary_interests,
                    "min_relevance_score": prefs.min_relevance_score,
                    "max_articles_per_day": prefs.max_articles_per_day,
                    "created_at": prefs.created_at.isoformat(),
                    "updated_at": prefs.updated_at.isoformat()
                }
                for prefs in preferences_list
            ]
            
        except Exception as e:
            logger.error(f"Failed to get users with preferences: {str(e)}")
            raise
    
    async def bulk_update_preference_field(
        self, 
        field_name: str, 
        old_value: Any, 
        new_value: Any
    ) -> int:
        """
        Bulk update a specific preference field across all active preferences.
        Useful for system-wide updates or migrations.
        
        Args:
            field_name: Name of the field to update
            old_value: Current value to match
            new_value: New value to set
            
        Returns:
            Number of preferences updated
        """
        try:
            if not hasattr(UserContentPreferences, field_name):
                raise ValueError(f"Field {field_name} does not exist on UserContentPreferences")
            
            field = getattr(UserContentPreferences, field_name)
            
            # For JSONB fields, we need different handling
            if field_name in ['primary_interests', 'secondary_interests', 'topics_to_avoid', 
                             'content_types', 'companies_to_follow', 'authors_to_follow', 'sources_to_prioritize']:
                # This would require more complex JSONB operations
                logger.warning(f"Bulk update of JSONB field {field_name} not implemented")
                return 0
            
            # For simple fields
            stmt = select(UserContentPreferences).where(
                and_(
                    UserContentPreferences.is_active == True,
                    field == old_value
                )
            )
            
            result = await self.session.execute(stmt)
            preferences_to_update = list(result.scalars().all())
            
            updated_count = 0
            for prefs in preferences_to_update:
                setattr(prefs, field_name, new_value)
                updated_count += 1
            
            logger.info(f"Bulk updated {updated_count} preferences: {field_name} from {old_value} to {new_value}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update preference field {field_name}: {str(e)}")
            raise
    
    async def get_preference_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics about preference usage and trends.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with preference analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all active preferences
            stmt = select(UserContentPreferences).where(
                UserContentPreferences.is_active == True
            )
            result = await self.session.execute(stmt)
            active_prefs = list(result.scalars().all())
            
            # Get recent preferences
            recent_stmt = select(UserContentPreferences).where(
                UserContentPreferences.created_at >= since_date
            )
            recent_result = await self.session.execute(recent_stmt)
            recent_prefs = list(recent_result.scalars().all())
            
            # Analyze interests
            all_primary_interests = []
            all_secondary_interests = []
            for prefs in active_prefs:
                all_primary_interests.extend(prefs.primary_interests or [])
                all_secondary_interests.extend(prefs.secondary_interests or [])
            
            from collections import Counter
            
            return {
                "total_active_preferences": len(active_prefs),
                "preferences_created_recently": len(recent_prefs),
                "most_common_primary_interests": Counter(all_primary_interests).most_common(10),
                "most_common_secondary_interests": Counter(all_secondary_interests).most_common(10),
                "avg_relevance_threshold": sum(p.min_relevance_score for p in active_prefs) / len(active_prefs) if active_prefs else 0,
                "avg_max_articles": sum(p.max_articles_per_day for p in active_prefs) / len(active_prefs) if active_prefs else 0,
                "content_style_distribution": Counter(p.content_style_preferences for p in active_prefs),
                "experience_level_distribution": Counter(p.experience_level for p in active_prefs),
                "analysis_period_days": days,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get preference analytics: {str(e)}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _deactivate_existing_preferences(self, user_id: UUID) -> None:
        """Deactivate all existing active preferences for a user."""
        stmt = select(UserContentPreferences).where(
            and_(
                UserContentPreferences.user_id == user_id,
                UserContentPreferences.is_active == True
            )
        )
        
        result = await self.session.execute(stmt)
        existing_prefs = list(result.scalars().all())
        
        for prefs in existing_prefs:
            prefs.is_active = False
            
        logger.debug(f"Deactivated {len(existing_prefs)} existing preferences for user {user_id}")
    
    async def _get_next_version(self, user_id: UUID) -> int:
        """Get the next version number for user preferences."""
        stmt = select(func.max(UserContentPreferences.preferences_version)).where(
            UserContentPreferences.user_id == user_id
        )
        
        result = await self.session.execute(stmt)
        max_version = result.scalar()
        
        return (max_version or 0) + 1
"""
LinkedIn API service for posting, commenting, and content discovery (2025 Updated).
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.linkedin_oauth_service import LinkedInOAuthService

logger = logging.getLogger(__name__)

class LinkedInAPIService:
    """Service for LinkedIn API operations (posting, commenting, discovery) - 2025 Updated."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.api_base = "https://api.linkedin.com/v2"

    async def _get_valid_token(self, user: User) -> str:
        """Get valid access token for user."""
        if not user.linkedin_access_token:
            raise ValueError("User has no LinkedIn access token")
        
        # For now, just return the token (you can add refresh logic later)
        return user.linkedin_access_token

    async def create_post(
        self,
        user: User,
        content: str,
        visibility: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """Create a LinkedIn post using OpenID Connect subject ID."""
        access_token = await self._get_valid_token(user)
        
        # Get the LinkedIn person URN using userinfo endpoint
        person_urn = await self._get_person_urn_from_userinfo(access_token)
        
        # Updated post format for 2025 LinkedIn API
        post_data = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202210",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/ugcPosts",
                json=post_data,
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"LinkedIn post creation failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"LinkedIn post created: {result.get('id')}")
            return result

    async def create_comment(
        self,
        user: User,
        post_urn: str,
        comment_text: str
    ) -> Dict[str, Any]:
        """Create a comment on a LinkedIn post."""
        access_token = await self._get_valid_token(user)
        person_urn = await self._get_person_urn(access_token)
        
        comment_data = {
            "actor": person_urn,
            "object": post_urn,
            "message": {
                "text": comment_text
            }
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202210",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/socialActions/{post_urn}/comments",
                json=comment_data,
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"LinkedIn comment creation failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"LinkedIn comment created: {result.get('id')}")
            return result

    async def get_user_posts(
        self,
        user: User,
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user's LinkedIn posts."""
        access_token = await self._get_valid_token(user)
        person_urn = await self._get_person_urn(access_token)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": "202210",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        params = {
            "authors": person_urn,
            "count": count,
            "sortBy": "LAST_MODIFIED"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base}/ugcPosts",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn posts fetch failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            return result.get("elements", [])

    async def _get_person_urn_from_userinfo(self, access_token: str) -> str:
        """
        Get LinkedIn person URN using the OpenID Connect userinfo endpoint.
        This avoids the permissions issue with /v2/people/~
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"LinkedIn userinfo fetch failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            # The 'sub' field contains the LinkedIn ID we need
            linkedin_id = result.get('sub')
            if not linkedin_id:
                raise ValueError("Could not get LinkedIn ID from userinfo")
                
            return f"urn:li:person:{linkedin_id}"

    async def _get_person_urn(self, access_token: str) -> str:
        """
        Get LinkedIn person URN for the authenticated user.
        Still needed for posting APIs in 2025.
        """
        return await self.oauth_service.get_user_urn_from_profile(access_token)

    async def like_post(
        self,
        user: User,
        post_urn: str
    ) -> Dict[str, Any]:
        """Like a LinkedIn post."""
        access_token = await self._get_valid_token(user)
        person_urn = await self._get_person_urn(access_token)
        
        like_data = {
            "actor": person_urn,
            "object": post_urn
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202210",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/socialActions/{post_urn}/likes",
                json=like_data,
                headers=headers
            )
            
            if response.status_code not in [200, 201]:
                logger.error(f"LinkedIn like failed: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            logger.info(f"LinkedIn post liked: {post_urn}")
            return result
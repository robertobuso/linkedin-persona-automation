"""
LinkedIn API client for reading feeds and interacting with posts.

Provides capabilities for:
- Reading user's LinkedIn feed
- Liking posts
- Commenting on posts
- Getting post details
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from playwright.async_api import async_playwright, Browser, Page

from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class LinkedInClientError(Exception):
    """Base exception for LinkedIn client errors."""
    pass

class LinkedInClient:
    """
    LinkedIn API and web scraping client.
    
    Handles both official API calls and web scraping for features
    not available through the official API.
    """
    
    def __init__(self):
        self.api_base_url = "https://api.linkedin.com/v2"
        self.browser: Optional[Browser] = None
        
    async def get_user_feed(self, user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's LinkedIn feed posts.
        
        Args:
            user: User with LinkedIn credentials
            limit: Number of posts to fetch
            
        Returns:
            List of feed post dictionaries
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            # Try API first, fall back to web scraping
            try:
                return await self._get_feed_via_api(user, limit)
            except Exception as api_error:
                logger.warning(f"API method failed, trying web scraping: {api_error}")
                return await self._get_feed_via_scraping(user, limit)
                
        except Exception as e:
            logger.error(f"Failed to get user feed: {str(e)}")
            raise LinkedInClientError(f"Failed to get feed: {str(e)}")
    
    async def like_post(self, user: User, post_urn: str) -> Dict[str, Any]:
        """
        Like a LinkedIn post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            
        Returns:
            Response from like action
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn API endpoint for likes
            url = f"{self.api_base_url}/socialActions/{post_urn}/likes"
            
            like_data = {
                "actor": f"urn:li:person:{user.id}",
                "object": post_urn
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=like_data, headers=headers) as response:
                    if response.status == 201:
                        return {"success": True, "message": "Post liked successfully"}
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to like post: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to like post: {str(e)}")
            raise LinkedInClientError(f"Failed to like post: {str(e)}")
    
    async def comment_on_post(self, user: User, post_urn: str, comment_text: str) -> Dict[str, Any]:
        """
        Comment on a LinkedIn post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            comment_text: Comment content
            
        Returns:
            Response from comment action
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # LinkedIn API endpoint for comments
            url = f"{self.api_base_url}/socialActions/{post_urn}/comments"
            
            comment_data = {
                "actor": f"urn:li:person:{user.id}",
                "object": post_urn,
                "message": {
                    "text": comment_text
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=comment_data, headers=headers) as response:
                    if response.status == 201:
                        response_data = await response.json()
                        return {
                            "success": True,
                            "comment_id": response_data.get("id"),
                            "message": "Comment posted successfully"
                        }
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to comment: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to comment on post: {str(e)}")
            raise LinkedInClientError(f"Failed to comment: {str(e)}")
    
    async def get_post_details(self, user: User, post_urn: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific post.
        
        Args:
            user: User with LinkedIn credentials
            post_urn: LinkedIn post URN
            
        Returns:
            Post details dictionary
        """
        try:
            if not user.has_valid_linkedin_token():
                raise LinkedInClientError("User does not have valid LinkedIn token")
            
            headers = {
                "Authorization": f"Bearer {user.linkedin_access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Get post data
            url = f"{self.api_base_url}/shares/{post_urn}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise LinkedInClientError(f"Failed to get post details: {error_text}")
                        
        except Exception as e:
            logger.error(f"Failed to get post details: {str(e)}")
            raise LinkedInClientError(f"Failed to get post details: {str(e)}")
    
    async def _get_feed_via_api(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get feed using LinkedIn API."""
        headers = {
            "Authorization": f"Bearer {user.linkedin_access_token}",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        # LinkedIn API endpoint for feed
        url = f"{self.api_base_url}/shares"
        params = {
            "q": "owners",
            "owners": f"urn:li:person:{user.id}",
            "count": limit,
            "projection": "(elements*(id,activity,commentary,content,created,edited,lastModified,owner,resharedShare,socialCounts))"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._format_api_feed_response(data)
                else:
                    error_text = await response.text()
                    raise LinkedInClientError(f"API request failed: {error_text}")
    
    async def _get_feed_via_scraping(self, user: User, limit: int) -> List[Dict[str, Any]]:
        """Get feed using web scraping as fallback."""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=True)
        
        context = await self.browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to LinkedIn
            await page.goto("https://www.linkedin.com/login")
            
            # Note: In production, you'd need to handle LinkedIn authentication
            # This is a simplified example
            await page.fill("#username", user.email)
            await page.fill("#password", "user_password")  # You'd need to securely store this
            await page.click("[type='submit']")
            
            # Wait for redirect to feed
            await page.wait_for_url("**/feed/**")
            
            # Scrape feed posts
            posts = await page.query_selector_all('[data-id^="urn:li:activity"]')
            
            feed_posts = []
            for i, post in enumerate(posts[:limit]):
                try:
                    post_data = await self._extract_post_data(page, post)
                    if post_data:
                        feed_posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Failed to extract post {i}: {str(e)}")
                    continue
            
            return feed_posts
            
        finally:
            await context.close()
    
    def _format_api_feed_response(self, api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format API response into standardized feed post format."""
        posts = []
        
        for element in api_response.get("elements", []):
            try:
                post = {
                    "id": element.get("id"),
                    "urn": element.get("id"),
                    "author": self._extract_author_info(element),
                    "content": self._extract_content_text(element),
                    "created_time": element.get("created", {}).get("time"),
                    "social_counts": element.get("socialCounts", {}),
                    "type": "feed_post",
                    "platform": "linkedin"
                }
                posts.append(post)
                
            except Exception as e:
                logger.warning(f"Failed to format post: {str(e)}")
                continue
        
        return posts
    
    async def _extract_post_data(self, page: Page, post_element) -> Optional[Dict[str, Any]]:
        """Extract post data from scraped element."""
        try:
            # Extract post URN
            post_id = await post_element.get_attribute("data-id")
            
            # Extract author info
            author_element = await post_element.query_selector(".feed-shared-actor__name")
            author_name = await author_element.inner_text() if author_element else "Unknown"
            
            # Extract content
            content_element = await post_element.query_selector(".feed-shared-text")
            content_text = await content_element.inner_text() if content_element else ""
            
            # Extract engagement counts
            likes_element = await post_element.query_selector("[aria-label*='reaction']")
            likes_text = await likes_element.inner_text() if likes_element else "0"
            
            return {
                "id": post_id,
                "urn": post_id,
                "author": {"name": author_name},
                "content": content_text,
                "created_time": datetime.utcnow().timestamp() * 1000,  # Approximate
                "social_counts": {
                    "numLikes": self._parse_engagement_count(likes_text)
                },
                "type": "feed_post",
                "platform": "linkedin"
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract post data: {str(e)}")
            return None
    
    def _extract_author_info(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Extract author information from API response element."""
        owner = element.get("owner", {})
        return {
            "id": owner.get("id"),
            "name": owner.get("localizedName", "Unknown")
        }
    
    def _extract_content_text(self, element: Dict[str, Any]) -> str:
        """Extract content text from API response element."""
        commentary = element.get("commentary", {})
        return commentary.get("text", "")
    
    def _parse_engagement_count(self, count_text: str) -> int:
        """Parse engagement count from text."""
        try:
            # Handle formats like "123", "1.2K", "1.2M"
            count_text = count_text.strip().replace(",", "")
            
            if "K" in count_text:
                return int(float(count_text.replace("K", "")) * 1000)
            elif "M" in count_text:
                return int(float(count_text.replace("M", "")) * 1000000)
            else:
                return int(count_text) if count_text.isdigit() else 0
                
        except (ValueError, AttributeError):
            return 0
    
    async def close(self):
        """Close browser resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

# Singleton instance
linkedin_client = LinkedInClient()

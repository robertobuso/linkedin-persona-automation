"""
LinkedIn scraper service for LinkedIn Presence Automation Application.

Handles LinkedIn content scraping using Playwright with session management,
rate limiting, and robust error handling.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import random
import json
import os
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)


@dataclass
class LinkedInPost:
    """Data class for LinkedIn post content."""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    engagement_metrics: Optional[Dict[str, int]] = None


class LinkedInScraper:
    """
    LinkedIn content scraper using Playwright with session management.
    
    Implements rate limiting, session persistence, and robust error handling
    for scraping LinkedIn profiles and company pages.
    """
    
    def __init__(self):
        """Initialize LinkedIn scraper."""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.session_file = "linkedin_session.json"
        self.rate_limit_delay = (2, 5)  # Random delay between 2-5 seconds
        self.max_posts_per_profile = 20
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _initialize_browser(self):
        """Initialize Playwright browser and context."""
        try:
            playwright = await async_playwright().start()
            
            # Launch browser in headless mode
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                ]
            )
            
            # Create browser context with realistic settings
            self.context = await self.browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ),
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Load saved session if available
            await self._load_session()
            
            logger.info("LinkedIn scraper browser initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def _cleanup(self):
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("LinkedIn scraper browser cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def _load_session(self):
        """Load saved session cookies."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Add cookies to context
                if 'cookies' in session_data:
                    await self.context.add_cookies(session_data['cookies'])
                    logger.info("Loaded saved LinkedIn session")
            
        except Exception as e:
            logger.warning(f"Failed to load session: {str(e)}")
    
    async def _save_session(self, page: Page):
        """Save current session cookies."""
        try:
            cookies = await page.context.cookies()
            session_data = {
                'cookies': cookies,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            
            logger.info("Saved LinkedIn session")
            
        except Exception as e:
            logger.warning(f"Failed to save session: {str(e)}")
    
    async def scrape_profile_posts(self, profile_url: str) -> List[LinkedInPost]:
        """
        Scrape posts from a LinkedIn profile.
        
        Args:
            profile_url: LinkedIn profile URL to scrape
            
        Returns:
            List of LinkedInPost objects
        """
        if not self.context:
            await self._initialize_browser()
        
        posts = []
        page = None
        
        try:
            logger.info(f"Scraping LinkedIn profile: {profile_url}")
            
            # Create new page
            page = await self.context.new_page()
            
            # Set up request interception to block unnecessary resources
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", 
                           lambda route: route.abort())
            
            # Navigate to profile
            await page.goto(profile_url, wait_until='networkidle', timeout=30000)
            
            # Check if we need to login
            if await self._check_login_required(page):
                logger.warning("LinkedIn login required - cannot scrape without authentication")
                return []
            
            # Wait for posts to load
            await page.wait_for_selector('.feed-shared-update-v2', timeout=10000)
            
            # Scroll to load more posts
            await self._scroll_to_load_posts(page)
            
            # Extract posts
            post_elements = await page.query_selector_all('.feed-shared-update-v2')
            
            for i, post_element in enumerate(post_elements[:self.max_posts_per_profile]):
                try:
                    post = await self._extract_post_content(post_element, profile_url)
                    if post and len(post.content) > 100:  # Minimum content length
                        posts.append(post)
                    
                    # Rate limiting
                    if i < len(post_elements) - 1:
                        delay = random.uniform(*self.rate_limit_delay)
                        await asyncio.sleep(delay)
                        
                except Exception as e:
                    logger.error(f"Error extracting post {i}: {str(e)}")
                    continue
            
            # Save session for future use
            await self._save_session(page)
            
            logger.info(f"Successfully scraped {len(posts)} posts from {profile_url}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to scrape profile {profile_url}: {str(e)}")
            return []
        
        finally:
            if page:
                await page.close()
    
    async def _check_login_required(self, page: Page) -> bool:
        """
        Check if LinkedIn login is required.
        
        Args:
            page: Playwright page object
            
        Returns:
            True if login is required
        """
        try:
            # Check for login indicators
            login_selectors = [
                '.login-form',
                '.sign-in-form',
                '[data-test-id="sign-in-form"]',
                'input[name="session_key"]'
            ]
            
            for selector in login_selectors:
                if await page.query_selector(selector):
                    return True
            
            # Check URL for login redirect
            current_url = page.url
            if 'linkedin.com/login' in current_url or 'linkedin.com/uas/login' in current_url:
                return True
            
            return False
            
        except Exception:
            return True  # Assume login required if check fails
    
    async def _scroll_to_load_posts(self, page: Page):
        """
        Scroll page to load more posts.
        
        Args:
            page: Playwright page object
        """
        try:
            # Scroll down multiple times to load more content
            for _ in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                
                # Check if "Show more" button exists and click it
                show_more_button = await page.query_selector('.pv-profile-section__see-more-inline')
                if show_more_button:
                    await show_more_button.click()
                    await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"Error during scrolling: {str(e)}")
    
    async def _extract_post_content(self, post_element, profile_url: str) -> Optional[LinkedInPost]:
        """
        Extract content from a single post element.
        
        Args:
            post_element: Playwright element for the post
            profile_url: Original profile URL
            
        Returns:
            LinkedInPost object or None
        """
        try:
            # Extract post text content
            content_element = await post_element.query_selector('.feed-shared-text')
            if not content_element:
                content_element = await post_element.query_selector('.feed-shared-update-v2__description')
            
            if not content_element:
                return None
            
            content = await content_element.inner_text()
            content = content.strip()
            
            if len(content) < 50:  # Skip very short posts
                return None
            
            # Extract post URL
            post_url = await self._extract_post_url(post_element, profile_url)
            
            # Extract author information
            author = await self._extract_author_info(post_element)
            
            # Extract published date
            published_at = await self._extract_published_date(post_element)
            
            # Extract engagement metrics
            engagement_metrics = await self._extract_engagement_metrics(post_element)
            
            # Generate title from content (first sentence or first 100 chars)
            title = self._generate_title_from_content(content)
            
            # Extract hashtags as tags
            tags = self._extract_hashtags(content)
            
            return LinkedInPost(
                title=title,
                content=content,
                url=post_url,
                author=author,
                published_at=published_at,
                tags=tags,
                engagement_metrics=engagement_metrics
            )
            
        except Exception as e:
            logger.error(f"Error extracting post content: {str(e)}")
            return None
    
    async def _extract_post_url(self, post_element, profile_url: str) -> str:
        """Extract post URL from post element."""
        try:
            # Look for permalink in post
            permalink_element = await post_element.query_selector('a[href*="/posts/"]')
            if permalink_element:
                href = await permalink_element.get_attribute('href')
                if href:
                    return urljoin('https://linkedin.com', href)
            
            # Fallback to profile URL with timestamp
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            return f"{profile_url}#post-{timestamp}"
            
        except Exception:
            # Ultimate fallback
            return f"{profile_url}#post-{random.randint(1000, 9999)}"
    
    async def _extract_author_info(self, post_element) -> Optional[str]:
        """Extract author information from post."""
        try:
            # Try different author selectors
            author_selectors = [
                '.feed-shared-actor__name',
                '.feed-shared-actor__title',
                '.update-components-actor__name'
            ]
            
            for selector in author_selectors:
                author_element = await post_element.query_selector(selector)
                if author_element:
                    author = await author_element.inner_text()
                    return author.strip()
            
            return None
            
        except Exception:
            return None
    
    async def _extract_published_date(self, post_element) -> Optional[datetime]:
        """Extract published date from post."""
        try:
            # Look for time element
            time_element = await post_element.query_selector('time')
            if time_element:
                datetime_attr = await time_element.get_attribute('datetime')
                if datetime_attr:
                    try:
                        return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                    except ValueError:
                        pass
            
            # Look for relative time text
            time_text_element = await post_element.query_selector('.feed-shared-actor__sub-description')
            if time_text_element:
                time_text = await time_text_element.inner_text()
                # Parse relative time (e.g., "2h", "1d", "3w")
                return self._parse_relative_time(time_text)
            
            return None
            
        except Exception:
            return None
    
    def _parse_relative_time(self, time_text: str) -> Optional[datetime]:
        """Parse relative time text to datetime."""
        try:
            import re
            
            # Extract number and unit
            match = re.search(r'(\d+)([hdwmy])', time_text.lower())
            if not match:
                return None
            
            number = int(match.group(1))
            unit = match.group(2)
            
            now = datetime.utcnow()
            
            if unit == 'h':  # hours
                return now - timedelta(hours=number)
            elif unit == 'd':  # days
                return now - timedelta(days=number)
            elif unit == 'w':  # weeks
                return now - timedelta(weeks=number)
            elif unit == 'm':  # months (approximate)
                return now - timedelta(days=number * 30)
            elif unit == 'y':  # years (approximate)
                return now - timedelta(days=number * 365)
            
            return None
            
        except Exception:
            return None
    
    async def _extract_engagement_metrics(self, post_element) -> Dict[str, int]:
        """Extract engagement metrics from post."""
        try:
            metrics = {
                'likes': 0,
                'comments': 0,
                'shares': 0
            }
            
            # Extract likes
            likes_element = await post_element.query_selector('.social-counts-reactions__count')
            if likes_element:
                likes_text = await likes_element.inner_text()
                metrics['likes'] = self._parse_count_text(likes_text)
            
            # Extract comments
            comments_element = await post_element.query_selector('.social-counts-comments__count')
            if comments_element:
                comments_text = await comments_element.inner_text()
                metrics['comments'] = self._parse_count_text(comments_text)
            
            # Extract shares
            shares_element = await post_element.query_selector('.social-counts-shares__count')
            if shares_element:
                shares_text = await shares_element.inner_text()
                metrics['shares'] = self._parse_count_text(shares_text)
            
            return metrics
            
        except Exception:
            return {'likes': 0, 'comments': 0, 'shares': 0}
    
    def _parse_count_text(self, count_text: str) -> int:
        """Parse count text (e.g., '1.2K', '500') to integer."""
        try:
            count_text = count_text.strip().replace(',', '')
            
            if 'K' in count_text:
                return int(float(count_text.replace('K', '')) * 1000)
            elif 'M' in count_text:
                return int(float(count_text.replace('M', '')) * 1000000)
            else:
                return int(count_text)
                
        except (ValueError, AttributeError):
            return 0
    
    def _generate_title_from_content(self, content: str) -> str:
        """Generate title from post content."""
        try:
            # Use first sentence or first 100 characters
            sentences = content.split('.')
            if sentences and len(sentences[0]) > 10:
                title = sentences[0].strip()
                if len(title) > 100:
                    title = title[:97] + '...'
                return title
            
            # Fallback to first 100 characters
            if len(content) > 100:
                return content[:97] + '...'
            
            return content
            
        except Exception:
            return "LinkedIn Post"
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content."""
        try:
            import re
            hashtags = re.findall(r'#\w+', content)
            return [tag.lower() for tag in hashtags]
        except Exception:
            return []
    
    async def validate_profile_url(self, profile_url: str) -> Dict[str, Any]:
        """
        Validate LinkedIn profile URL.
        
        Args:
            profile_url: LinkedIn profile URL to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Basic URL validation
            parsed = urlparse(profile_url)
            if 'linkedin.com' not in parsed.netloc:
                return {
                    "valid": False,
                    "error": "Not a LinkedIn URL"
                }
            
            if not self.context:
                await self._initialize_browser()
            
            page = await self.context.new_page()
            
            try:
                # Try to access the profile
                await page.goto(profile_url, wait_until='networkidle', timeout=15000)
                
                # Check if profile exists and is accessible
                if await self._check_login_required(page):
                    return {
                        "valid": False,
                        "error": "Login required to access profile"
                    }
                
                # Check for profile indicators
                profile_indicators = [
                    '.pv-top-card',
                    '.profile-photo-edit',
                    '.pv-text-details__left-panel'
                ]
                
                profile_found = False
                for selector in profile_indicators:
                    if await page.query_selector(selector):
                        profile_found = True
                        break
                
                if not profile_found:
                    return {
                        "valid": False,
                        "error": "Profile not found or not accessible"
                    }
                
                # Extract basic profile info
                name_element = await page.query_selector('.text-heading-xlarge')
                name = await name_element.inner_text() if name_element else "Unknown"
                
                return {
                    "valid": True,
                    "profile_name": name,
                    "url": profile_url
                }
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Profile validation failed for {profile_url}: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
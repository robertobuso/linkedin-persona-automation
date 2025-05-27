"""
Content extraction utilities for LinkedIn Presence Automation Application.

Provides utilities for extracting full article content from URLs using
Playwright and BeautifulSoup with intelligent content detection.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import re
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup, Comment
from readability import Document

logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    Content extraction service for fetching full article content from URLs.
    
    Uses Playwright for JavaScript-rendered content and BeautifulSoup for
    HTML parsing with intelligent content detection and cleaning.
    """
    
    def __init__(self):
        """Initialize content extractor."""
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.timeout = 30000  # 30 seconds
        
        # Common content selectors (ordered by priority)
        self.content_selectors = [
            'article',
            '.post-content',
            '.entry-content',
            '.article-content',
            '.content',
            '.main-content',
            '.story-body',
            '.article-body',
            '.post-body',
            '[role="main"]',
            'main',
            '.container .content',
            '#content',
            '#main-content'
        ]
        
        # Elements to remove
        self.remove_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.sidebar', '.navigation', '.menu',
            '.advertisement', '.ads', '.ad',
            '.social-share', '.share-buttons',
            '.comments', '.comment-section',
            '.related-posts', '.recommended',
            '.newsletter-signup', '.subscription',
            'script', 'style', 'noscript'
        ]
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup()
    
    async def _initialize_browser(self):
        """Initialize Playwright browser."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            self.context = await self.browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )
            )
            logger.info("Content extractor browser initialized")
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
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    async def extract_full_content(self, url: str) -> Optional[str]:
        """
        Extract full article content from URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted content text or None if failed
        """
        try:
            logger.info(f"Extracting content from: {url}")
            
            # Try different extraction methods
            content = await self._extract_with_playwright(url)
            if not content or len(content) < 200:
                content = await self._extract_with_requests(url)
            
            if content and len(content) >= 200:
                # Clean and process content
                cleaned_content = self._clean_content(content)
                logger.info(f"Successfully extracted {len(cleaned_content)} characters from {url}")
                return cleaned_content
            
            logger.warning(f"Could not extract sufficient content from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {str(e)}")
            return None
    
    async def _extract_with_playwright(self, url: str) -> Optional[str]:
        """
        Extract content using Playwright for JavaScript-rendered pages.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted content or None
        """
        if not self.context:
            await self._initialize_browser()
        
        page = None
        try:
            page = await self.context.new_page()
            
            # Block unnecessary resources
            await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,mp4,mp3}", 
                           lambda route: route.abort())
            
            # Navigate to page
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            
            # Wait for content to load
            await page.wait_for_timeout(2000)
            
            # Get page HTML
            html = await page.content()
            
            # Extract content using BeautifulSoup
            return self._extract_content_from_html(html, url)
            
        except Exception as e:
            logger.warning(f"Playwright extraction failed for {url}: {str(e)}")
            return None
        finally:
            if page:
                await page.close()
    
    async def _extract_with_requests(self, url: str) -> Optional[str]:
        """
        Extract content using requests for static pages.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted content or None
        """
        try:
            import requests
            
            headers = {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(url, headers=headers, timeout=30)
            )
            
            response.raise_for_status()
            
            # Extract content from HTML
            return self._extract_content_from_html(response.text, url)
            
        except Exception as e:
            logger.warning(f"Requests extraction failed for {url}: {str(e)}")
            return None
    
    def _extract_content_from_html(self, html: str, url: str) -> Optional[str]:
        """
        Extract main content from HTML using multiple strategies.
        
        Args:
            html: HTML content
            url: Original URL for context
            
        Returns:
            Extracted content text
        """
        try:
            # Try readability first
            content = self._extract_with_readability(html)
            if content and len(content) > 200:
                return content
            
            # Fall back to manual extraction
            return self._extract_with_selectors(html)
            
        except Exception as e:
            logger.error(f"HTML content extraction failed: {str(e)}")
            return None
    
    def _extract_with_readability(self, html: str) -> Optional[str]:
        """
        Extract content using python-readability.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted content text
        """
        try:
            doc = Document(html)
            content_html = doc.summary()
            
            # Convert to text
            soup = BeautifulSoup(content_html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text if len(text) > 100 else None
            
        except Exception as e:
            logger.warning(f"Readability extraction failed: {str(e)}")
            return None
    
    def _extract_with_selectors(self, html: str) -> Optional[str]:
        """
        Extract content using CSS selectors.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted content text
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove unwanted elements
            for selector in self.remove_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Remove comments
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Try content selectors in order
            for selector in self.content_selectors:
                content_elements = soup.select(selector)
                if content_elements:
                    # Use the largest content element
                    largest_element = max(content_elements, key=lambda e: len(e.get_text()))
                    text = largest_element.get_text(separator=' ', strip=True)
                    
                    if len(text) > 200:
                        # Clean whitespace
                        text = re.sub(r'\s+', ' ', text).strip()
                        return text
            
            # Last resort: use body content
            body = soup.find('body')
            if body:
                text = body.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                return text if len(text) > 200 else None
            
            return None
            
        except Exception as e:
            logger.error(f"Selector-based extraction failed: {str(e)}")
            return None
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and normalize extracted content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Cleaned content
        """
        try:
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content).strip()
            
            # Remove common unwanted patterns
            patterns_to_remove = [
                r'Share on Facebook.*?Share on Twitter.*?Share on LinkedIn',
                r'Follow us on.*?(?:Facebook|Twitter|LinkedIn|Instagram)',
                r'Subscribe to.*?newsletter',
                r'Click here to.*?(?:read more|subscribe|download)',
                r'Advertisement\s*',
                r'Sponsored content\s*',
                r'Related articles?:.*?(?:\n|$)',
                r'Tags?:.*?(?:\n|$)',
                r'Categories?:.*?(?:\n|$)',
            ]
            
            for pattern in patterns_to_remove:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            
            # Remove URLs
            content = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', content)
            
            # Clean up punctuation
            content = re.sub(r'\.{3,}', '...', content)
            content = re.sub(r'-{3,}', '---', content)
            
            # Remove excessive line breaks
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Final whitespace cleanup
            content = re.sub(r'\s+', ' ', content).strip()
            
            return content
            
        except Exception as e:
            logger.error(f"Content cleaning failed: {str(e)}")
            return content
    
    def extract_metadata(self, html: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary with extracted metadata
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            metadata = {}
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                metadata['description'] = meta_desc.get('content', '').strip()
            
            # Extract Open Graph data
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            if og_title:
                metadata['og_title'] = og_title.get('content', '').strip()
            
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                metadata['og_description'] = og_desc.get('content', '').strip()
            
            # Extract author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta:
                metadata['author'] = author_meta.get('content', '').strip()
            
            # Extract keywords
            keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_meta:
                keywords = keywords_meta.get('content', '').strip()
                metadata['keywords'] = [k.strip() for k in keywords.split(',') if k.strip()]
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {}
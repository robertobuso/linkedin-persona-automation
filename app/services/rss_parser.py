"""
RSS feed parser service for LinkedIn Presence Automation Application.

Handles parsing of RSS/Atom feeds with robust error handling, retry logic,
and content extraction capabilities.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin, urlparse
import time
import random

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """Data class for parsed content items."""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class RSSParser:
    """
    RSS/Atom feed parser with robust error handling and retry logic.
    
    Supports various feed formats, handles encoding issues, and implements
    exponential backoff for failed requests.
    """
    
    def __init__(self):
        """Initialize RSS parser with session configuration."""
        self.session = self._create_session()
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
    
    def _create_session(self) -> requests.Session:
        """
        Create requests session with retry strategy.
        
        Returns:
            Configured requests session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        
        return session
    
    async def parse_feed(self, url: str) -> List[ContentItem]:
        """
        Parse RSS/Atom feed from URL.
        
        Args:
            url: RSS feed URL to parse
            
        Returns:
            List of ContentItem objects
        """
        try:
            logger.info(f"Parsing RSS feed: {url}")
            
            # Add random delay to avoid rate limiting
            await asyncio.sleep(random.uniform(1, 3))
            
            # Fetch feed content
            response = await self._fetch_feed(url)
            if not response:
                return []
            
            # Parse feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")
            
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in feed: {url}")
                return []
            
            # Convert entries to ContentItem objects
            items = []
            for entry in feed.entries:
                try:
                    item = await self._parse_entry(entry, feed)
                    if item:
                        items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing entry from {url}: {str(e)}")
                    continue
            
            logger.info(f"Successfully parsed {len(items)} items from {url}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to parse RSS feed {url}: {str(e)}")
            return []
    
    async def _fetch_feed(self, url: str) -> Optional[requests.Response]:
        """
        Fetch feed content with error handling.
        
        Args:
            url: Feed URL to fetch
            
        Returns:
            Response object or None if failed
        """
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(url, timeout=30)
            )
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error fetching feed {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching feed {url}: {str(e)}")
            return None
    
    async def _parse_entry(self, entry: Any, feed: Any) -> Optional[ContentItem]:
        """
        Parse individual feed entry into ContentItem.
        
        Args:
            entry: Feed entry object
            feed: Parent feed object
            
        Returns:
            ContentItem or None if parsing failed
        """
        try:
            # Extract title
            title = self._get_entry_text(entry, 'title', 'Untitled')
            
            # Extract content
            content = self._extract_entry_content(entry)
            if not content:
                logger.warning(f"No content found for entry: {title}")
                return None
            
            # Extract URL
            url = self._get_entry_link(entry)
            if not url:
                logger.warning(f"No URL found for entry: {title}")
                return None
            
            # Extract author
            author = self._extract_author(entry, feed)
            
            # Extract published date
            published_at = self._extract_published_date(entry)
            
            # Extract category/tags
            category, tags = self._extract_categories_and_tags(entry)
            
            return ContentItem(
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                category=category,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error parsing entry: {str(e)}")
            return None
    
    def _get_entry_text(self, entry: Any, field: str, default: str = "") -> str:
        """
        Safely extract text from entry field.
        
        Args:
            entry: Feed entry object
            field: Field name to extract
            default: Default value if field not found
            
        Returns:
            Extracted text or default
        """
        try:
            value = getattr(entry, field, None)
            if value:
                if isinstance(value, str):
                    return value.strip()
                elif hasattr(value, 'value'):
                    return value.value.strip()
                elif isinstance(value, list) and value:
                    return str(value[0]).strip()
            return default
        except Exception:
            return default
    
    def _extract_entry_content(self, entry: Any) -> str:
        """
        Extract content from entry with fallback options.
        
        Args:
            entry: Feed entry object
            
        Returns:
            Extracted content text
        """
        # Try different content fields in order of preference
        content_fields = [
            'content',
            'description',
            'summary',
            'subtitle'
        ]
        
        for field in content_fields:
            content = self._get_entry_text(entry, field)
            if content and len(content) > 50:  # Minimum content length
                return self._clean_html_content(content)
        
        return ""
    
    def _clean_html_content(self, content: str) -> str:
        """
        Clean HTML content and extract plain text.
        
        Args:
            content: Raw content with potential HTML
            
        Returns:
            Cleaned plain text
        """
        try:
            from bs4 import BeautifulSoup
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean whitespace
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.warning(f"Error cleaning HTML content: {str(e)}")
            return content
    
    def _get_entry_link(self, entry: Any) -> Optional[str]:
        """
        Extract URL from entry.
        
        Args:
            entry: Feed entry object
            
        Returns:
            Entry URL or None
        """
        try:
            # Try different link fields
            if hasattr(entry, 'link') and entry.link:
                return entry.link
            
            if hasattr(entry, 'links') and entry.links:
                for link in entry.links:
                    if hasattr(link, 'href'):
                        return link.href
            
            if hasattr(entry, 'id') and entry.id:
                # Sometimes ID is the URL
                if entry.id.startswith('http'):
                    return entry.id
            
            return None
            
        except Exception:
            return None
    
    def _extract_author(self, entry: Any, feed: Any) -> Optional[str]:
        """
        Extract author information.
        
        Args:
            entry: Feed entry object
            feed: Parent feed object
            
        Returns:
            Author name or None
        """
        try:
            # Try entry-level author first
            author = self._get_entry_text(entry, 'author')
            if author:
                return author
            
            # Try author detail
            if hasattr(entry, 'author_detail') and entry.author_detail:
                if hasattr(entry.author_detail, 'name'):
                    return entry.author_detail.name
            
            # Fall back to feed-level author
            if hasattr(feed, 'feed'):
                feed_info = feed.feed
                author = self._get_entry_text(feed_info, 'author')
                if author:
                    return author
                
                # Try managingEditor
                author = self._get_entry_text(feed_info, 'managingEditor')
                if author:
                    return author
            
            return None
            
        except Exception:
            return None
    
    def _extract_published_date(self, entry: Any) -> Optional[datetime]:
        """
        Extract and parse published date.
        
        Args:
            entry: Feed entry object
            
        Returns:
            Parsed datetime or None
        """
        try:
            # Try different date fields
            date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
            
            for field in date_fields:
                date_tuple = getattr(entry, field, None)
                if date_tuple:
                    try:
                        return datetime(*date_tuple[:6])
                    except (ValueError, TypeError):
                        continue
            
            # Try string date fields
            string_fields = ['published', 'updated', 'created']
            for field in string_fields:
                date_str = self._get_entry_text(entry, field)
                if date_str:
                    try:
                        # Use feedparser's date parsing
                        import email.utils
                        timestamp = email.utils.parsedate_to_datetime(date_str)
                        return timestamp.replace(tzinfo=None)
                    except Exception:
                        continue
            
            return None
            
        except Exception:
            return None
    
    def _extract_categories_and_tags(self, entry: Any) -> tuple[Optional[str], Optional[List[str]]]:
        """
        Extract category and tags from entry.
        
        Args:
            entry: Feed entry object
            
        Returns:
            Tuple of (category, tags_list)
        """
        try:
            category = None
            tags = []
            
            # Extract tags/categories
            if hasattr(entry, 'tags') and entry.tags:
                for tag in entry.tags:
                    if hasattr(tag, 'term'):
                        tags.append(tag.term)
                    elif isinstance(tag, str):
                        tags.append(tag)
                
                # Use first tag as category
                if tags:
                    category = tags[0]
            
            # Try category field
            if not category:
                category = self._get_entry_text(entry, 'category')
            
            return category, tags if tags else None
            
        except Exception:
            return None, None
    
    async def validate_feed_url(self, url: str) -> Dict[str, Any]:
        """
        Validate RSS feed URL and return feed information.
        
        Args:
            url: Feed URL to validate
            
        Returns:
            Dictionary with validation results and feed info
        """
        try:
            logger.info(f"Validating RSS feed: {url}")
            
            # Fetch and parse feed
            response = await self._fetch_feed(url)
            if not response:
                return {
                    "valid": False,
                    "error": "Failed to fetch feed"
                }
            
            feed = feedparser.parse(response.content)
            
            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                return {
                    "valid": False,
                    "error": f"Feed parsing error: {feed.bozo_exception}"
                }
            
            # Check for entries
            if not hasattr(feed, 'entries'):
                return {
                    "valid": False,
                    "error": "No entries found in feed"
                }
            
            # Extract feed information
            feed_info = getattr(feed, 'feed', {})
            
            return {
                "valid": True,
                "title": getattr(feed_info, 'title', 'Unknown'),
                "description": getattr(feed_info, 'description', ''),
                "link": getattr(feed_info, 'link', ''),
                "language": getattr(feed_info, 'language', 'unknown'),
                "entry_count": len(feed.entries),
                "last_updated": getattr(feed_info, 'updated', None),
                "feed_type": feed.version or 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Feed validation failed for {url}: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
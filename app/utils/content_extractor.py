"""
Fixed content extraction utilities without hard-coded AI-only filtering.

Provides utilities for extracting full article content from URLs using
Playwright and BeautifulSoup with user-configurable content detection.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
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
    
    def check_content_relevance(
        self, 
        text: str, 
        user_interests: List[str], 
        custom_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check content relevance based on user interests instead of hard-coded AI filter.
        
        Args:
            text: Content text to analyze
            user_interests: List of user interest keywords/topics
            custom_filters: Optional additional filtering criteria
            
        Returns:
            Dictionary with relevance analysis
        """
        text_lower = text.lower()
        custom_filters = custom_filters or {}
        
        # Basic relevance scoring
        relevance_score = 0.0
        matching_interests = []
        
        # Check against user interests
        for interest in user_interests:
            interest_lower = interest.lower()
            if interest_lower in text_lower:
                relevance_score += 1.0
                matching_interests.append(interest)
                
                # Boost score for title matches
                title_section = text[:200].lower()
                if interest_lower in title_section:
                    relevance_score += 0.5
        
        # Normalize score
        if user_interests:
            relevance_score = min(1.0, relevance_score / len(user_interests))
        else:
            relevance_score = 0.5  # Default for users with no specified interests
        
        # Apply custom filters
        blocked_keywords = custom_filters.get("blocked_keywords", [])
        for blocked in blocked_keywords:
            if blocked.lower() in text_lower:
                relevance_score *= 0.1  # Heavily penalize blocked content
                break
        
        # Check for spam patterns
        spam_score = self._calculate_spam_score(text)
        relevance_score *= (1.0 - spam_score)
        
        return {
            "relevance_score": relevance_score,
            "matching_interests": matching_interests,
            "spam_score": spam_score,
            "blocked": relevance_score < 0.1,
            "reason": "User interests match" if matching_interests else "No specific interests matched"
        }
    
    def _calculate_spam_score(self, text: str) -> float:
        """Calculate spam probability score."""
        text_lower = text.lower()
        
        spam_indicators = [
            "click here", "buy now", "limited time", "act fast", "guaranteed",
            "make money", "earn $", "free trial", "subscribe now", "don't miss out",
            "urgent", "exclusive offer", "act now", "limited offer"
        ]
        
        spam_count = sum(1 for indicator in spam_indicators if indicator in text_lower)
        
        # Check for excessive promotional language
        promo_patterns = [
            r'\b\d+%\s+off\b',
            r'\$\d+',
            r'\bfree\b.*\b(trial|shipping|delivery)\b',
            r'\bbest\s+(deal|offer|price)\b'
        ]
        
        pattern_count = sum(1 for pattern in promo_patterns if re.search(pattern, text_lower))
        
        # Calculate spam score (0 = no spam, 1 = definitely spam)
        total_indicators = spam_count + pattern_count
        spam_score = min(1.0, total_indicators / 10.0)
        
        return spam_score

    async def extract_full_content(
        self, 
        url: str, 
        user_interests: Optional[List[str]] = None,
        custom_filters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract full article content from URL with user-based relevance filtering.
        
        Args:
            url: URL to extract content from
            user_interests: List of user interests for relevance checking
            custom_filters: Optional custom filtering criteria
            
        Returns:
            Dictionary with extracted content and metadata, or None if not relevant
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
                
                # Check relevance based on user interests (not hard-coded AI filter)
                relevance_analysis = self.check_content_relevance(
                    cleaned_content, 
                    user_interests or [], 
                    custom_filters
                )
                
                # Extract metadata
                metadata = self.extract_metadata_from_content(cleaned_content)
                
                result = {
                    "content": cleaned_content,
                    "relevance_analysis": relevance_analysis,
                    "metadata": metadata,
                    "word_count": len(cleaned_content.split()),
                    "character_count": len(cleaned_content),
                    "extraction_url": url,
                    "extraction_method": "playwright" if await self._extract_with_playwright(url) else "requests"
                }
                
                # Only filter out if explicitly blocked or spam
                if relevance_analysis["blocked"]:
                    logger.info(f"Content filtered out: {relevance_analysis['reason']} from {url}")
                    return None
                
                logger.info(f"Successfully extracted content from {url} (relevance: {relevance_analysis['relevance_score']:.2f})")
                return result
            
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
            
            # Block unnecessary resources to speed up loading
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
    
    def extract_metadata_from_content(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from content for better processing.
        
        Args:
            content: Cleaned content text
            
        Returns:
            Dictionary with content metadata
        """
        try:
            if not isinstance(content, str):
                logger.error(f"Expected string content but got {type(content).__name__}")
                return {
                    "word_count": 0,
                    "character_count": 0,
                    "summary": "",
                    "reading_time_minutes": 0,
                    "key_sentences": [],
                    "content_type": "unknown",
                    "complexity_score": 0.0
                }
        
            # Basic statistics
            word_count = len(content.split())
            char_count = len(content)
            
            # Extract first paragraph as summary
            paragraphs = content.split('\n\n')
            summary = paragraphs[0] if paragraphs else content[:200]
            
            # Estimate reading time (average 200 words per minute)
            reading_time_minutes = max(1, word_count // 200)
            
            # Extract potential key phrases (simple approach)
            sentences = content.split('. ')
            key_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 50]
            
            return {
                "word_count": word_count,
                "character_count": char_count,
                "summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "reading_time_minutes": reading_time_minutes,
                "key_sentences": key_sentences,
                "content_type": self._classify_content_type(content),
                "complexity_score": self._calculate_complexity_score(content)
            }
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {
                "word_count": len(content.split()),
                "character_count": len(content),
                "summary": content[:300],
                "reading_time_minutes": 1,
                "key_sentences": [],
                "content_type": "article",
                "complexity_score": 0.5
            }
    
    def _classify_content_type(self, content: str) -> str:
        """Classify content type based on patterns."""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ["tutorial", "how to", "step by step", "guide"]):
            return "tutorial"
        elif any(word in content_lower for word in ["analysis", "research", "study", "findings"]):
            return "analysis"
        elif any(word in content_lower for word in ["news", "announced", "today", "breaking"]):
            return "news"
        elif any(word in content_lower for word in ["opinion", "perspective", "think", "believe"]):
            return "opinion"
        else:
            return "article"
    
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate content complexity score (0-1)."""
        try:
            words = content.split()
            
            # Average word length
            avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Average sentence length
            sentences = content.split('. ')
            avg_sentence_length = len(words) / len(sentences) if sentences else 0
            
            # Technical terms (basic heuristic)
            technical_indicators = sum(1 for word in words if len(word) > 10)
            technical_ratio = technical_indicators / len(words) if words else 0
            
            # Combine metrics (normalize to 0-1)
            complexity = (
                min(1.0, avg_word_length / 10.0) * 0.3 +
                min(1.0, avg_sentence_length / 30.0) * 0.4 +
                min(1.0, technical_ratio * 10) * 0.3
            )
            
            return complexity
            
        except Exception:
            return 0.5
    
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
"""
Content deduplication utilities for LinkedIn Presence Automation Application.

Provides utilities for detecting and preventing duplicate content using
URL-based and content similarity detection methods.
"""

import hashlib
import logging
from typing import Optional, List, Dict, Any, Set
from difflib import SequenceMatcher
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)


class ContentDeduplicator:
    """
    Content deduplication service for detecting duplicate and similar content.
    
    Uses URL normalization, content hashing, and similarity detection
    to identify duplicate content items.
    """
    
    def __init__(self):
        """Initialize content deduplicator."""
        self.url_cache: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.similarity_threshold = 0.85  # 85% similarity threshold
        
        # URL parameters to ignore during normalization
        self.ignore_params = {
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'campaign',
            '_ga', '_gid', 'mc_cid', 'mc_eid',
            'timestamp', 'time', 't'
        }
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent duplicate detection.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL string
        """
        try:
            # Parse URL
            parsed = urlparse(url.lower().strip())
            
            # Remove fragment
            parsed = parsed._replace(fragment='')
            
            # Parse and filter query parameters
            query_params = parse_qs(parsed.query)
            filtered_params = {}
            
            for key, values in query_params.items():
                if key.lower() not in self.ignore_params:
                    # Keep only the first value for each parameter
                    filtered_params[key] = values[0] if values else ''
            
            # Rebuild query string
            if filtered_params:
                query_string = urlencode(sorted(filtered_params.items()))
                parsed = parsed._replace(query=query_string)
            else:
                parsed = parsed._replace(query='')
            
            # Remove trailing slash from path (except for root)
            path = parsed.path
            if path.endswith('/') and len(path) > 1:
                path = path.rstrip('/')
                parsed = parsed._replace(path=path)
            
            # Rebuild URL
            normalized_url = urlunparse(parsed)
            
            logger.debug(f"Normalized URL: {url} -> {normalized_url}")
            return normalized_url
            
        except Exception as e:
            logger.warning(f"URL normalization failed for {url}: {str(e)}")
            return url.lower().strip()
    
    def generate_content_hash(self, content: str) -> str:
        """
        Generate hash for content similarity detection.
        
        Args:
            content: Content text to hash
            
        Returns:
            Content hash string
        """
        try:
            # Normalize content for hashing
            normalized_content = self._normalize_content_for_hashing(content)
            
            # Generate SHA-256 hash
            content_hash = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
            
            return content_hash
            
        except Exception as e:
            logger.error(f"Content hashing failed: {str(e)}")
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _normalize_content_for_hashing(self, content: str) -> str:
        """
        Normalize content text for consistent hashing.
        
        Args:
            content: Raw content text
            
        Returns:
            Normalized content for hashing
        """
        try:
            # Convert to lowercase
            normalized = content.lower()
            
            # Remove extra whitespace
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            # Remove punctuation and special characters
            normalized = re.sub(r'[^\w\s]', '', normalized)
            
            # Remove common stop words that don't affect content meaning
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
                'her', 'us', 'them'
            }
            
            words = normalized.split()
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
            return ' '.join(filtered_words)
            
        except Exception as e:
            logger.warning(f"Content normalization failed: {str(e)}")
            return content.lower()
    
    def is_duplicate_url(self, url: str) -> bool:
        """
        Check if URL is a duplicate.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is duplicate
        """
        normalized_url = self.normalize_url(url)
        return normalized_url in self.url_cache
    
    def add_url(self, url: str) -> None:
        """
        Add URL to cache.
        
        Args:
            url: URL to add
        """
        normalized_url = self.normalize_url(url)
        self.url_cache.add(normalized_url)
    
    def is_duplicate_content(self, content: str) -> bool:
        """
        Check if content is a duplicate based on hash.
        
        Args:
            content: Content to check
            
        Returns:
            True if content is duplicate
        """
        content_hash = self.generate_content_hash(content)
        return content_hash in self.content_hashes
    
    def add_content_hash(self, content: str) -> str:
        """
        Add content hash to cache and return the hash.
        
        Args:
            content: Content to hash and add
            
        Returns:
            Generated content hash
        """
        content_hash = self.generate_content_hash(content)
        self.content_hashes.add(content_hash)
        return content_hash
    
    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        try:
            # Normalize both contents
            norm1 = self._normalize_content_for_hashing(content1)
            norm2 = self._normalize_content_for_hashing(content2)
            
            # Calculate similarity using SequenceMatcher
            similarity = SequenceMatcher(None, norm1, norm2).ratio()
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity calculation failed: {str(e)}")
            return 0.0
    
    def is_similar_content(self, content: str, existing_contents: List[str]) -> bool:
        """
        Check if content is similar to any existing content.
        
        Args:
            content: Content to check
            existing_contents: List of existing content strings
            
        Returns:
            True if content is similar to any existing content
        """
        try:
            for existing_content in existing_contents:
                similarity = self.calculate_content_similarity(content, existing_content)
                if similarity >= self.similarity_threshold:
                    logger.info(f"Similar content detected (similarity: {similarity:.2f})")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Similarity check failed: {str(e)}")
            return False
    
    def find_similar_content(self, content: str, existing_contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find all similar content items.
        
        Args:
            content: Content to check
            existing_contents: List of content dictionaries with 'content' and 'id' keys
            
        Returns:
            List of similar content items with similarity scores
        """
        similar_items = []
        
        try:
            for item in existing_contents:
                existing_content = item.get('content', '')
                similarity = self.calculate_content_similarity(content, existing_content)
                
                if similarity >= self.similarity_threshold:
                    similar_items.append({
                        'id': item.get('id'),
                        'content': existing_content,
                        'similarity': similarity
                    })
            
            # Sort by similarity (highest first)
            similar_items.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar_items
            
        except Exception as e:
            logger.error(f"Similar content search failed: {str(e)}")
            return []
    
    def extract_content_fingerprint(self, content: str) -> Dict[str, Any]:
        """
        Extract content fingerprint for advanced duplicate detection.
        
        Args:
            content: Content to fingerprint
            
        Returns:
            Dictionary with content fingerprint data
        """
        try:
            # Basic statistics
            word_count = len(content.split())
            char_count = len(content)
            
            # Extract key phrases (simple n-gram approach)
            words = self._normalize_content_for_hashing(content).split()
            
            # Generate 3-grams
            trigrams = []
            for i in range(len(words) - 2):
                trigram = ' '.join(words[i:i+3])
                trigrams.append(trigram)
            
            # Get most common trigrams
            from collections import Counter
            common_trigrams = Counter(trigrams).most_common(5)
            
            # Extract first and last sentences
            sentences = content.split('.')
            first_sentence = sentences[0].strip() if sentences else ''
            last_sentence = sentences[-1].strip() if len(sentences) > 1 else ''
            
            return {
                'word_count': word_count,
                'char_count': char_count,
                'content_hash': self.generate_content_hash(content),
                'common_trigrams': [trigram for trigram, count in common_trigrams],
                'first_sentence_hash': hashlib.md5(first_sentence.encode()).hexdigest(),
                'last_sentence_hash': hashlib.md5(last_sentence.encode()).hexdigest(),
                'length_bucket': self._get_length_bucket(char_count)
            }
            
        except Exception as e:
            logger.error(f"Fingerprint extraction failed: {str(e)}")
            return {
                'word_count': len(content.split()),
                'char_count': len(content),
                'content_hash': self.generate_content_hash(content),
                'common_trigrams': [],
                'first_sentence_hash': '',
                'last_sentence_hash': '',
                'length_bucket': 'unknown'
            }
    
    def _get_length_bucket(self, char_count: int) -> str:
        """
        Get length bucket for content categorization.
        
        Args:
            char_count: Character count
            
        Returns:
            Length bucket string
        """
        if char_count < 500:
            return 'short'
        elif char_count < 2000:
            return 'medium'
        elif char_count < 5000:
            return 'long'
        else:
            return 'very_long'
    
    def clear_cache(self) -> None:
        """Clear all cached URLs and content hashes."""
        self.url_cache.clear()
        self.content_hashes.clear()
        logger.info("Deduplication cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'cached_urls': len(self.url_cache),
            'cached_content_hashes': len(self.content_hashes),
            'similarity_threshold': self.similarity_threshold
        }
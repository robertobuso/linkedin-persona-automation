"""
Complete enhanced content ingestion service with robust JSON parsing.

This includes all the JSON parsing functions integrated into the service.
Replace your existing enhanced_content_ingestion.py with this version.
"""

import asyncio
import re
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import redis.asyncio as redis
from langchain.schema import BaseMessage, SystemMessage, HumanMessage

from app.models.content import ContentSource, ContentItem, ContentStatus
from app.models.user import User, ContentSelection
from app.models.user_content_preferences import UserContentPreferences
from app.repositories.content_repository import ContentSourceRepository, ContentItemRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_content_preferences_repository import UserContentPreferencesRepository
from app.services.rss_parser import RSSParser
from app.services.linkedin_scraper import LinkedInScraper
from app.utils.content_extractor import ContentExtractor
from app.utils.deduplication import ContentDeduplicator
from app.database.connection import get_db_session
from app.schemas.api_schemas import ContentStatsResponse

logger = logging.getLogger(__name__)


@dataclass
class ContentSelectionResult:
    """Result of LLM-based content selection."""
    selected_articles: List[Dict[str, Any]]
    selection_reasons: Dict[str, str]
    processing_details: Dict[str, Any]
    cache_key: str
    selection_timestamp: datetime


@dataclass
class ArticleCandidate:
    """Candidate article for LLM evaluation."""
    title: str
    url: str
    content: str
    source_id: Optional[UUID] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    source_name: str = ""
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "author": self.author,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "source_name": self.source_name,
            "source_id": str(self.source_id) if self.source_id else None,
            "word_count": self.word_count
        }


def clean_and_repair_json(json_text: str) -> str:
    """
    Clean and attempt to repair common JSON formatting issues from LLM responses.
    
    Args:
        json_text: Raw JSON text from LLM
        
    Returns:
        Cleaned JSON text
    """
    # Remove markdown code blocks
    json_text = re.sub(r'^```(?:json)?\s*', '', json_text.strip())
    json_text = re.sub(r'\s*```$', '', json_text.strip())
    
    # Remove any text before the first { or [
    match = re.search(r'[{\[]', json_text)
    if match:
        json_text = json_text[match.start():]
    
    # Remove any text after the last } or ]
    last_brace = json_text.rfind('}')
    last_bracket = json_text.rfind(']')
    last_pos = max(last_brace, last_bracket)
    
    if last_pos != -1:
        json_text = json_text[:last_pos + 1]
    
    # Fix common issues
    # Remove trailing commas before closing braces/brackets
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
    
    return json_text.strip()


def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM response with multiple fallback strategies.
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Parsed JSON dictionary
    """
    logger.debug(f"Attempting to parse JSON from response of length {len(response_text)}")
    
    # Strategy 1: Find JSON using regex with greedy matching
    json_patterns = [
        r'\{[\s\S]*\}',  # Match from first { to last }
        r'\[[\s\S]*\]',  # Match from first [ to last ]
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, response_text)
        for match in matches:
            try:
                cleaned = clean_and_repair_json(match)
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse failed for pattern {pattern}: {str(e)}")
                continue
    
    # Strategy 2: Try to find the JSON block more intelligently
    try:
        start_idx = response_text.find('{')
        if start_idx != -1:
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(response_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if brace_count == 0:  # Found balanced braces
                json_candidate = response_text[start_idx:end_idx]
                cleaned = clean_and_repair_json(json_candidate)
                return json.loads(cleaned)
                
    except json.JSONDecodeError as e:
        logger.warning(f"Balanced brace strategy failed: {str(e)}")
    
    # Strategy 3: Try to extract just the selections array
    try:
        # Look for "selections": [...]
        array_match = re.search(r'"selections":\s*\[([\s\S]*?)\](?:\s*,|\s*})', response_text)
        if array_match:
            selections_json = f'{{"selections": [{array_match.group(1)}]}}'
            cleaned = clean_and_repair_json(selections_json)
            return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning(f"Array extraction strategy failed: {str(e)}")
    
    # Strategy 4: Manual parsing for critical data
    try:
        selections = []
        
        # Extract individual selection objects with index-based format
        selection_pattern = r'\{\s*"index":\s*(\d+)\s*,\s*"score":\s*([0-9.]+)\s*,\s*"reason":\s*"([^"]*)"[^}]*\}'
        
        for match in re.finditer(selection_pattern, response_text):
            try:
                selection = {
                    "index": int(match.group(1)),
                    "score": float(match.group(2)),
                    "reason": match.group(3)
                }
                selections.append(selection)
            except (ValueError, IndexError) as e:
                logger.warning(f"Failed to parse individual selection: {str(e)}")
                continue
        
        if selections:
            logger.info(f"Manually extracted {len(selections)} selections from malformed JSON")
            return {"selections": selections}
            
    except Exception as e:
        logger.warning(f"Manual parsing strategy failed: {str(e)}")
    
    # If all strategies fail, raise an exception
    raise json.JSONDecodeError(f"Could not parse JSON from LLM response after trying multiple strategies", response_text, 0)


class EnhancedContentIngestionService:
    """
    Enhanced content ingestion service with robust LLM-based selection and JSON parsing.
    """
    
    def __init__(self, session: AsyncSession, redis_client: Optional[redis.Redis] = None):
        """
        Initialize the enhanced content ingestion service.
        
        Args:
            session: Database session for repository operations
            redis_client: Optional Redis client for caching
        """
        self.session = session
        self.redis_client = redis_client
        self.source_repo = ContentSourceRepository(session)
        self.content_repo = ContentItemRepository(session)
        self.user_repo = UserRepository(session)
        self.preferences_repo = UserContentPreferencesRepository(session)
        self.rss_parser = RSSParser()
        self.linkedin_scraper = LinkedInScraper()
        self.content_extractor = ContentExtractor()
        self.deduplicator = ContentDeduplicator()
        
        # Cache settings
        self.cache_ttl = 3600  # 1 hour
        self.max_articles_for_llm = 50  # Limit articles sent to LLM
    
    async def process_content_with_llm_selection(
        self, 
        user_id: UUID, 
        force_refresh: bool = False
    ) -> ContentSelectionResult:
        """
        Process content for a user using LLM-based selection.
        """
        try:
            logger.info(f"Processing content with LLM selection for user {user_id}")
            
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_result = await self._get_cached_selection(user_id)
                if cached_result:
                    logger.info(f"Returning cached selection for user {user_id}")
                    return cached_result
            
            # Get user and preferences
            stmt = (
                select(User)
                .options(selectinload(User.content_preferences_records))
                .where(User.id == user_id)
            )
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user_preferences = await self.preferences_repo.get_active_preferences_for_user(user_id)
            
            # Get user's content sources
            sources = await self.source_repo.get_active_sources_by_user(user_id)
            if not sources:
                logger.warning(f"No active sources found for user {user_id}")
                return self._empty_selection_result(user_id)
            
            # Gather candidate articles from all sources
            candidates = await self._gather_candidate_articles(sources, user, user_preferences)
            if not candidates:
                logger.warning(f"No candidate articles found for user {user_id}")
                return self._empty_selection_result(user_id)
            
            # Use LLM to select most relevant articles
            selection_result = await self._select_articles_with_llm(
                user_id, candidates, user, user_preferences
            )
            
            # Cache the results
            await self._cache_selection_result(selection_result)
            
            # Track selection in database
            await self._record_content_selection(
                user_id, len(candidates), len(selection_result.selected_articles), 
                selection_result.processing_details
            )
            
            logger.info(f"LLM selection completed for user {user_id}: {len(selection_result.selected_articles)} articles selected from {len(candidates)} candidates")
            return selection_result
            
        except Exception as e:
            logger.error(f"LLM content selection failed for user {user_id}: {str(e)}", exc_info=True)
            raise
    
    async def _gather_candidate_articles(
        self, 
        sources: List[ContentSource], 
        user: User,
        user_preferences: Optional[UserContentPreferences]
    ) -> List[ArticleCandidate]:
        """
        Gather candidate articles from ALL user sources.
        Fixed to process all sources and then limit candidates.
        """
        all_candidates = []
        articles_per_source = max(1, self.max_articles_for_llm // len(sources)) if sources else 50
        
        logger.info(f"Processing {len(sources)} sources, targeting ~{articles_per_source} articles per source")
        
        for source in sources:
            source_candidates = []
            
            try:
                logger.info(f"Gathering candidates from source: {source.name} ({source.source_type})")
                
                if source.source_type == "rss_feed":
                    items = await self.rss_parser.parse_feed(source.url)
                elif source.source_type == "linkedin":
                    items = await self.linkedin_scraper.scrape_profile_posts(source.url)
                else:
                    logger.warning(f"Unsupported source type: {source.source_type}")
                    continue
                
                logger.info(f"Found {len(items)} items from {source.name}")
                
                for item in items:
                    try:
                        # Duplicate checking
                        if await self.content_repo.check_duplicate_url(item.url):
                            logger.debug(f"Skipping duplicate URL: {item.url}")
                            continue
                        
                        # Create metadata
                        word_count = len(item.content.split()) if item.content else 0

                        candidate = ArticleCandidate(
                            title=item.title,
                            url=item.url,
                            content=item.content,
                            author=item.author,
                            published_at=item.published_at,
                            source_name=source.name,
                            source_id=source.id, 
                            word_count=word_count
                        )
                        source_candidates.append(candidate)
                        
                        # Limit per source to ensure fair distribution
                        if len(source_candidates) >= articles_per_source:
                            logger.info(f"Reached per-source limit of {articles_per_source} for {source.name}")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Error processing item from {source.name}: {str(e)}")
                        continue
                
                logger.info(f"Gathered {len(source_candidates)} candidates from {source.name}")
                all_candidates.extend(source_candidates)
                        
            except Exception as e:
                logger.error(f"Error gathering candidates from source {source.name}: {str(e)}")
                continue
        
        # Now limit total candidates if needed
        if len(all_candidates) > self.max_articles_for_llm:
            logger.info(f"Limiting candidates from {len(all_candidates)} to {self.max_articles_for_llm}")
            
            # Try to maintain balanced distribution across sources
            candidates_by_source = {}
            for candidate in all_candidates:
                source_name = candidate.source_name
                if source_name not in candidates_by_source:
                    candidates_by_source[source_name] = []
                candidates_by_source[source_name].append(candidate)
            
            # Select proportionally from each source
            final_candidates = []
            sources_count = len(candidates_by_source)
            candidates_per_source = self.max_articles_for_llm // sources_count
            remaining_slots = self.max_articles_for_llm % sources_count
            
            for i, (source_name, source_candidates) in enumerate(candidates_by_source.items()):
                # Give some sources one extra candidate if there are remaining slots
                limit = candidates_per_source + (1 if i < remaining_slots else 0)
                selected = source_candidates[:limit]
                final_candidates.extend(selected)
                logger.info(f"Selected {len(selected)} candidates from {source_name}")
            
            all_candidates = final_candidates
        
        logger.info(f"Final total: {len(all_candidates)} candidate articles for LLM selection")
        
        # Log source distribution
        source_counts = {}
        for candidate in all_candidates:
            source_name = candidate.source_name
            source_counts[source_name] = source_counts.get(source_name, 0) + 1
        
        logger.info(f"Source distribution: {source_counts}")
        
        return all_candidates
    
    async def _select_articles_with_llm(
        self,
        user_id: UUID,
        candidates: List[ArticleCandidate],
        user: User,
        user_preferences: Optional[UserContentPreferences]
    ) -> ContentSelectionResult:
        """Use LLM to select the most relevant articles from candidates."""
        try:
            start_time = datetime.utcnow()
            
            # Build LLM prompt
            user_context = self._build_user_context(user, user_preferences)
            selection_prompt = self._build_selection_prompt(candidates, user_context, user_preferences)
            
            # Call LLM for selection
            logger.debug(f"Calling LLM for article selection (user: {user_id})")
            llm_response = await self._invoke_llm_with_structured_output(selection_prompt)
            
            # Parse LLM response
            selected_articles, selection_reasons = self._parse_llm_selection_response(
                llm_response, candidates
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Build result
            cache_key = self._build_cache_key(user_id)
            result = ContentSelectionResult(
                selected_articles=selected_articles,
                selection_reasons=selection_reasons,
                processing_details={
                    "llm_model": "gpt-4",
                    "candidates_evaluated": len(candidates),
                    "articles_selected": len(selected_articles),
                    "processing_time_seconds": processing_time,
                    "user_context_used": user_context,
                    "selection_criteria": {
                        "min_relevance_score": user_preferences.min_relevance_score if user_preferences else 0.7,
                        "max_articles": user_preferences.max_articles_per_day if user_preferences else 15,
                        "content_types": user_preferences.content_types if user_preferences else ["articles"]
                    }
                },
                cache_key=cache_key,
                selection_timestamp=datetime.utcnow()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LLM article selection failed: {str(e)}")
            raise
    
    def _build_user_context(
        self, 
        user: User, 
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build user context string for LLM prompt."""
        if user_preferences:
            context_parts = []
            
            if user_preferences.job_role:
                context_parts.append(f"Job role: {user_preferences.job_role}")
            
            if user_preferences.industry:
                context_parts.append(f"Industry: {user_preferences.industry}")
            
            if user_preferences.primary_interests:
                context_parts.append(f"Primary interests: {', '.join(user_preferences.primary_interests)}")
            
            if user_preferences.secondary_interests:
                context_parts.append(f"Secondary interests: {', '.join(user_preferences.secondary_interests)}")
            
            if user_preferences.custom_prompt:
                context_parts.append(f"Custom instructions: {user_preferences.custom_prompt}")
            
            return ". ".join(context_parts)
        else:
            # Fallback to legacy preferences
            return getattr(user, 'get_interests_for_llm', lambda: "Professional interested in technology and business")()
    
    def _build_selection_prompt(
        self, 
        candidates: List[ArticleCandidate], 
        user_context: str,
        user_preferences: Optional[UserContentPreferences]
    ) -> str:
        """Build a more robust LLM prompt for article selection with simplified JSON format."""
        max_articles = user_preferences.max_articles_per_day if user_preferences else 15
        target_articles = min(max_articles, len(candidates), 15)  # Cap at 15 for now
        
        # Create simplified candidate list for the prompt
        simplified_candidates = []
        for i, candidate in enumerate(candidates):
            simplified_candidates.append({
                "index": i,
                "title": candidate.title,
                "url": candidate.url[:100] + "..." if len(candidate.url) > 100 else candidate.url,
                "author": candidate.author or "Unknown",
                "source": candidate.source_name,
                "word_count": candidate.word_count,
                "content_preview": candidate.content[:200] + "..." if len(candidate.content) > 200 else candidate.content
            })
        
        candidates_json = json.dumps(simplified_candidates, indent=2)
        
        prompt = f"""You are an expert content curator for LinkedIn professionals. Select the {target_articles} most relevant articles from the candidates below for a user with these preferences:

USER CONTEXT:
{user_context}

CANDIDATES (Total: {len(candidates)}):
{candidates_json}

SELECTION CRITERIA:
- Select exactly {target_articles} articles that would be most valuable for this user
- Prioritize articles that match the user's interests and professional context
- Consider content quality, relevance, and professional value
- Avoid duplicate or very similar topics
- Prefer recent, actionable content over old news

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no markdown, no explanations, no extra text
2. Keep selection_reason under 50 characters to avoid JSON issues
3. Use the article index numbers, not full URLs
4. Double-check your JSON syntax before responding

REQUIRED JSON FORMAT:
{{
    "selections": [
        {{
            "index": 0,
            "score": 0.95,
            "reason": "Highly relevant to AI interests"
        }},
        {{
            "index": 5,
            "score": 0.87,
            "reason": "Valuable industry insights"
        }}
    ]
}}

Select exactly {target_articles} articles by their index numbers. Respond with ONLY the JSON object above."""
        
        return prompt
    
    async def _invoke_llm_with_structured_output(self, prompt: str) -> Dict[str, Any]:
        """
        Invoke LLM with improved structured output parsing for article selection.
        """
        try:
            from app.services.ai_service import AIService
            
            ai_service = AIService()
            
            # Create a structured prompt for article selection
            system_prompt = """You are an expert content curator for LinkedIn professionals. 
            Analyze the provided articles and select the most relevant ones based on user preferences.
            
            CRITICAL: Your response must be valid JSON. Double-check your JSON syntax.
            
            Return your response as a JSON object with this exact structure:
            {
                "selections": [
                    {
                        "index": 0,
                        "score": 0.85,
                        "reason": "Brief explanation"
                    }
                ]
            }
            
            IMPORTANT JSON RULES:
            - Use double quotes for all strings
            - No trailing commas
            - Escape any quotes inside strings with backslashes
            - Keep reason brief (under 50 characters)
            - Ensure all objects are properly closed with }
            """
            
            # Use the AI service to get structured response
            langchain_messages: List[BaseMessage] = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response_text, metrics = await ai_service._invoke_llm_with_fallback(
                messages=langchain_messages,
                max_tokens=2000,
                temperature=0.1
            )
            
            logger.debug(f"Raw LLM response length: {len(response_text)} characters")
            
            # Use the robust JSON extraction
            try:
                parsed_json = extract_json_from_response(response_text)
                logger.info(f"Successfully parsed JSON with {len(parsed_json.get('selections', []))} selections")
                return parsed_json
                
            except json.JSONDecodeError as e:
                logger.error(f"All JSON parsing strategies failed. Response preview: {response_text[:500]}...")
                logger.error(f"JSON error: {str(e)}")
                
                # Save the problematic response for debugging
                try:
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(response_text)
                        logger.error(f"Saved problematic LLM response to: {f.name}")
                except Exception:
                    pass
                
                # Return fallback response
                return await self._fallback_selection_response()
                    
        except Exception as e:
            logger.error(f"LLM service failed: {str(e)}")
            return await self._fallback_selection_response()

    async def _fallback_selection_response(self) -> Dict[str, Any]:
        """Enhanced fallback response when LLM fails."""
        logger.warning("Using fallback selection due to LLM/JSON parsing failure")
        return {
            "selections": [],
            "error": "LLM service or JSON parsing failed - using fallback selection",
            "fallback": True
        }
    
    def _parse_llm_selection_response(
        self, 
        llm_response: Dict[str, Any], 
        candidates: List[ArticleCandidate]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """
        Parse the simplified LLM response format.
        """
        try:
            selected_articles = []
            selection_reasons = {}
            
            selections = llm_response.get("selections", [])
            
            # Process index-based selections
            for selection in selections:
                try:
                    index = selection.get("index")
                    if index is None:
                        continue
                        
                    if 0 <= index < len(candidates):
                        candidate = candidates[index]
                        
                        article_data = {
                            "title": candidate.title,
                            "url": candidate.url,
                            "content": candidate.content,
                            "author": candidate.author,
                            "published_at": candidate.published_at.isoformat() if candidate.published_at else None,
                            "source_name": candidate.source_name,
                            "source_id": str(candidate.source_id) if candidate.source_id else None,
                            "word_count": candidate.word_count,
                            "relevance_score": selection.get("score", 0.7),
                            "selection_reason": selection.get("reason", "Selected by AI")
                        }
                        
                        selected_articles.append(article_data)
                        selection_reasons[candidate.url] = selection.get("reason", "Selected by AI")
                    else:
                        logger.warning(f"Invalid article index: {index} (max: {len(candidates)-1})")
                        
                except Exception as e:
                    logger.warning(f"Error processing selection: {str(e)}")
                    continue
            
            if selected_articles:
                logger.info(f"Successfully parsed {len(selected_articles)} article selections")
                return selected_articles, selection_reasons
            else:
                logger.warning("No valid articles found in LLM response, using fallback")
                return self._create_fallback_selection(candidates)
                
        except Exception as e:
            logger.error(f"Error parsing LLM selection response: {str(e)}")
            return self._create_fallback_selection(candidates)

    def _create_fallback_selection(self, candidates: List[ArticleCandidate], max_articles: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        """Create a fallback selection when LLM parsing fails."""
        fallback_articles = []
        fallback_reasons = {}
        
        # Select first few candidates as fallback
        for i, candidate in enumerate(candidates[:max_articles]):
            article_data = {
                "title": candidate.title,
                "url": candidate.url,
                "content": candidate.content,
                "author": candidate.author,
                "published_at": candidate.published_at.isoformat() if candidate.published_at else None,
                "source_name": candidate.source_name,
                "source_id": str(candidate.source_id) if candidate.source_id else None,
                "word_count": candidate.word_count,
                "relevance_score": 0.6,
                "selection_reason": "Fallback selection due to LLM parsing error"
            }
            
            fallback_articles.append(article_data)
            fallback_reasons[candidate.url] = "Fallback selection due to LLM parsing error"
        
        logger.info(f"Created fallback selection with {len(fallback_articles)} articles")
        return fallback_articles, fallback_reasons
    
    async def _get_cached_selection(self, user_id: UUID) -> Optional[ContentSelectionResult]:
        """Get cached content selection for user."""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._build_cache_key(user_id)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return ContentSelectionResult(
                    selected_articles=data["selected_articles"],
                    selection_reasons=data["selection_reasons"],
                    processing_details=data["processing_details"],
                    cache_key=cache_key,
                    selection_timestamp=datetime.fromisoformat(data["selection_timestamp"])
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving cached selection for user {user_id}: {str(e)}")
            return None
    
    async def _cache_selection_result(self, result: ContentSelectionResult) -> None:
        """Cache the selection result in Redis."""
        if not self.redis_client:
            return
        
        try:
            cache_data = {
                "selected_articles": result.selected_articles,
                "selection_reasons": result.selection_reasons,
                "processing_details": result.processing_details,
                "selection_timestamp": result.selection_timestamp.isoformat()
            }
            
            await self.redis_client.setex(
                result.cache_key,
                self.cache_ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached selection result with key: {result.cache_key}")
            
        except Exception as e:
            logger.warning(f"Error caching selection result: {str(e)}")
    
    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate cached content selection for user."""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._build_cache_key(user_id)
            await self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Error invalidating cache for user {user_id}: {str(e)}")
    
    def _build_cache_key(self, user_id: UUID) -> str:
        """Build cache key for user content selection."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return f"content_selection:{user_id}:{today}"
    
    def _empty_selection_result(self, user_id: UUID) -> ContentSelectionResult:
        """Create empty selection result."""
        return ContentSelectionResult(
            selected_articles=[],
            selection_reasons={},
            processing_details={
                "candidates_evaluated": 0,
                "articles_selected": 0,
                "processing_time_seconds": 0.0,
                "error": "No candidates found"
            },
            cache_key=self._build_cache_key(user_id),
            selection_timestamp=datetime.utcnow()
        )
    
    async def _record_content_selection(
        self,
        user_id: UUID,
        candidates_count: int,
        selected_count: int,
        processing_details: Dict[str, Any]
    ) -> None:
        """Record content selection in database for analytics."""
        try:
            selection_record = ContentSelection(
                user_id=user_id,
                selection_date=datetime.utcnow(),
                selection_type="llm_selection",
                articles_considered=candidates_count,
                articles_selected=selected_count,
                llm_model_used=processing_details.get("llm_model", "unknown"),
                selection_criteria=processing_details.get("selection_criteria", {}),
                processing_time_seconds=processing_details.get("processing_time_seconds", 0.0),
                selected_article_ids=[],
                selection_scores={},
                selection_reasons={}
            )
            
            self.session.add(selection_record)
            await self.session.flush()
            
            logger.debug(f"Recorded content selection for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording content selection: {str(e)}")
    
    # Legacy methods for backward compatibility
    async def process_all_sources(self, user_id: Optional[UUID] = None):
        """Legacy method - redirects to new LLM-based processing."""
        if user_id:
            return await self.process_content_with_llm_selection(user_id)
        else:
            # Process for all users with preferences
            users_with_prefs = await self.preferences_repo.get_users_with_preferences()
            results = []
            
            for user_info in users_with_prefs:
                try:
                    user_uuid = UUID(user_info["user_id"])
                    result = await self.process_content_with_llm_selection(user_uuid)
                    results.append({
                        "user_id": user_info["user_id"],
                        "selected_articles": len(result.selected_articles),
                        "success": True
                    })
                except Exception as e:
                    logger.error(f"Failed to process content for user {user_info['user_id']}: {str(e)}")
                    results.append({
                        "user_id": user_info["user_id"],
                        "selected_articles": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            return {
                "users_processed": len(results),
                "total_successful": sum(1 for r in results if r["success"]),
                "total_failed": sum(1 for r in results if not r["success"]),
                "results": results
            }


# Factory function for dependency injection
async def get_enhanced_content_ingestion_service(
    redis_client: Optional[redis.Redis] = None
) -> EnhancedContentIngestionService:
    """
    Factory function to create EnhancedContentIngestionService with database session.
    
    Args:
        redis_client: Optional Redis client for caching
        
    Returns:
        EnhancedContentIngestionService instance
    """
    async with get_db_session() as session:
        return EnhancedContentIngestionService(session, redis_client)
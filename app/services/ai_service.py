"""
AI service for LinkedIn Presence Automation Application.

Provides unified interface for AI operations including content summarization,
post generation, and comment creation using LangChain with multiple LLM providers.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from uuid import UUID
from datetime import datetime
import json
import time
from dataclasses import dataclass

from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_community.callbacks.manager import get_openai_callback
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config.llm_config import get_llm_config, LLMProvider, LLMConfig
from app.schemas.ai_schemas import (
    SummaryRequest, SummaryResponse, PostGenerationRequest, PostGenerationResponse,
    CommentGenerationRequest, CommentGenerationResponse, ToneProfile
)
from app.utils.prompt_builder import PromptBuilder
from app.prompts.summarization_prompts import SummarizationPrompts
from app.prompts.post_generation_prompts import PostGenerationPrompts
from app.prompts.comment_prompts import CommentPrompts

logger = logging.getLogger(__name__)


@dataclass
class AIUsageMetrics:
    """Metrics for AI service usage tracking."""
    provider: str
    model: str
    tokens_used: int
    cost: float
    response_time: float
    success: bool
    error_message: Optional[str] = None


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class ProviderUnavailableError(AIServiceError):
    """Exception raised when all AI providers are unavailable."""
    pass


class TokenLimitExceededError(AIServiceError):
    """Exception raised when token limit is exceeded."""
    pass


class AIService:
    """
    Unified AI service for content processing and generation.

    Provides content summarization, post draft generation, and comment creation
    with automatic provider fallback and cost tracking.
    """

    def __init__(self):
        """Initialize AI service with LLM configurations."""
        self.config_manager = get_llm_config()
        self.prompt_builder = PromptBuilder()
        self.summarization_prompts = SummarizationPrompts()
        self.post_prompts = PostGenerationPrompts()
        self.comment_prompts = CommentPrompts()
        self.usage_metrics: List[AIUsageMetrics] = []

        # Cache for LLM instances
        self._llm_cache: Dict[str, Any] = {}

    def _get_llm_instance(self, provider: LLMProvider, config: LLMConfig):
        """
        Get or create LLM instance for provider.

        Args:
            provider: LLM provider
            config: LLM configuration

        Returns:
            LLM instance
        """
        cache_key = f"{provider.value}_{config.model_name}"

        if cache_key not in self._llm_cache:
            if provider == LLMProvider.OPENAI:
                self._llm_cache[cache_key] = ChatOpenAI(
                    model_name=config.model_name,
                    openai_api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    request_timeout=config.timeout
                )
            elif provider == LLMProvider.ANTHROPIC:
                self._llm_cache[cache_key] = ChatAnthropic(
                    model=config.model_name,
                    anthropic_api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens_to_sample=config.max_tokens,
                    timeout=config.timeout
                )
            else:
                raise AIServiceError(f"Unsupported provider: {provider}")

        return self._llm_cache[cache_key]

    async def _invoke_llm_with_fallback(
        self,
        messages: List[BaseMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> tuple[str, AIUsageMetrics]:
        """
        Invoke LLM with automatic fallback to secondary provider.

        Args:
            messages: List of messages to send to LLM
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation

        Returns:
            Tuple of (response_text, usage_metrics)

        Raises:
            ProviderUnavailableError: If all providers fail
        """
        providers_to_try = [
            (self.config_manager.primary_provider, self.config_manager.get_primary_config()),
            (self.config_manager.fallback_provider, self.config_manager.get_fallback_config())
        ]

        last_error = None

        for provider, config in providers_to_try:
            if not config:
                continue

            try:
                start_time = time.time()

                # Get LLM instance
                llm = self._get_llm_instance(provider, config)

                # Override config if parameters provided
                if max_tokens:
                    llm.max_tokens = min(max_tokens, config.max_tokens)
                if temperature is not None:
                    llm.temperature = temperature

                # Invoke LLM with callback for token tracking
                if provider == LLMProvider.OPENAI:
                    with get_openai_callback() as cb:
                        response = await llm.agenerate([messages])
                        tokens_used = cb.total_tokens
                        cost = cb.total_cost
                else:
                    # For Anthropic, estimate tokens and cost
                    response = await llm.agenerate([messages])
                    tokens_used = self._estimate_tokens(messages, response.generations[0][0].text)
                    cost = self.config_manager.get_cost_estimate(provider, tokens_used)

                response_time = time.time() - start_time
                response_text = response.generations[0][0].text

                # Record successful usage
                metrics = AIUsageMetrics(
                    provider=provider.value,
                    model=config.model_name,
                    tokens_used=tokens_used,
                    cost=cost,
                    response_time=response_time,
                    success=True
                )
                self.usage_metrics.append(metrics)

                logger.info(f"LLM invocation successful with {provider.value}: {tokens_used} tokens, ${cost:.4f}")
                return response_text, metrics

            except Exception as e:
                response_time = time.time() - start_time
                error_msg = str(e)

                # Record failed usage
                metrics = AIUsageMetrics(
                    provider=provider.value,
                    model=config.model_name if config else "unknown",
                    tokens_used=0,
                    cost=0.0,
                    response_time=response_time,
                    success=False,
                    error_message=error_msg
                )
                self.usage_metrics.append(metrics)

                logger.warning(f"LLM invocation failed with {provider.value}: {error_msg}")
                last_error = e
                continue

        # All providers failed
        raise ProviderUnavailableError(f"All LLM providers failed. Last error: {last_error}")

    def _estimate_tokens(self, messages: List[BaseMessage], response: str) -> int:
        """
        Estimate token count for non-OpenAI providers.

        Args:
            messages: Input messages
            response: Response text

        Returns:
            Estimated token count
        """
        # Simple estimation: ~4 characters per token
        input_text = " ".join([msg.content for msg in messages])
        total_chars = len(input_text) + len(response)
        return total_chars // 4

    async def summarize_content(self, request: SummaryRequest) -> SummaryResponse:
        """
        Summarize content with user tone matching.

        Args:
            request: Summary request with content and user tone profile

        Returns:
            Summary response with generated summary and key points
        """
        try:
            logger.info(f"Summarizing content: {len(request.content)} characters")

            # Build summarization prompt
            prompt = self.summarization_prompts.build_summarization_prompt(
                content=request.content,
                tone_profile=request.tone_profile,
                max_length=request.max_length or 200
            )

            messages = [
                SystemMessage(content=self.summarization_prompts.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            # Invoke LLM
            response_text, metrics = await self._invoke_llm_with_fallback(
                messages=messages,
                max_tokens=300,
                temperature=0.3
            )

            # Parse structured response
            summary_data = self._parse_summary_response(response_text)

            return SummaryResponse(
                summary=summary_data["summary"],
                key_points=summary_data["key_points"],
                word_count=len(summary_data["summary"].split()),
                processing_time=metrics.response_time,
                model_used=f"{metrics.provider}:{metrics.model}",
                tokens_used=metrics.tokens_used,
                cost=metrics.cost
            )

        except Exception as e:
            logger.error(f"Content summarization failed: {str(e)}")
            raise AIServiceError(f"Summarization failed: {str(e)}")

    async def generate_post_draft(self, request: PostGenerationRequest) -> PostGenerationResponse:
        """
        Generate LinkedIn post draft from content summary.

        Args:
            request: Post generation request with summary and user examples

        Returns:
            Post generation response with multiple draft variations
        """
        try:
            logger.info(f"Generating post draft. Style: {request.style}, Summary: {len(request.summary)} chars")

            variations = []
            # To store the metrics of the call that produced the "best" variation for overall reporting
            best_variation_metrics: Optional[AIUsageMetrics] = None 

            for i in range(request.num_variations or 1): # Ensure at least 1 variation
                try:
                    prompt_to_use: str
                    if request.custom_prompt_text: # Check if a pre-built prompt is provided
                        prompt_to_use = request.custom_prompt_text
                        logger.debug(f"Using custom_prompt_text for variation {i+1}")
                    else:
                        # Fallback to building prompt based on style if no override
                        # This assumes PostGenerationPrompts has methods matching the style names
                        # or a generic build_post_prompt that uses the style.
                        # For simplicity, let's assume build_post_prompt handles different styles.
                        prompt_to_use = self.post_prompts.build_post_prompt(
                            summary=request.summary,
                            user_examples=request.user_examples,
                            tone_profile=request.tone_profile,
                            style=request.style or "professional_thought_leader"
                        )
                        logger.debug(f"Built prompt using style '{request.style}' for variation {i+1}")
                    
                    messages = [
                        SystemMessage(content=self.post_prompts.get_system_prompt()),
                        HumanMessage(content=prompt_to_use)
                    ]

                    temperature = 0.7 + (i * 0.1) if (request.num_variations or 1) > 1 else 0.7
                    response_text, metrics = await self._invoke_llm_with_fallback(
                        messages=messages,
                        max_tokens=500, # Or request.max_tokens if you add it to PostGenerationRequest
                        temperature=temperature
                    )

                    post_data = self._parse_post_response(response_text)
                    # Store metrics with each variation if needed, or just for the best one later
                    post_data["metrics"] = metrics # Temporarily store metrics with variation
                    variations.append(post_data)
                    
                    await asyncio.sleep(0.5) # Small delay

                except Exception as e:
                    logger.warning(f"Failed to generate post variation {i+1}: {str(e)}")
                    continue
            
            if not variations:
                raise AIServiceError("Failed to generate any post variations after LLM calls.")

            best_variation_data = self._select_best_post_variation(variations, request.tone_profile)
            # Retrieve the metrics associated with the best variation
            best_variation_metrics = best_variation_data.pop("metrics", None) 
            # If metrics were not stored per variation, you might need to log the last 'metrics' object

            # Calculate aggregate metrics (if multiple variations were generated and tracked)
            # For simplicity, using metrics from the best (or last successful) variation.
            # If you generate multiple variations, you need to decide how to aggregate costs/tokens.
            # The current self.usage_metrics appends ALL calls, so we can sum the last N.
            num_successful_variations = len(variations)
            relevant_metrics = self.usage_metrics[-num_successful_variations:] if num_successful_variations > 0 else []
            
            final_metrics = best_variation_metrics or (relevant_metrics[-1] if relevant_metrics else AIUsageMetrics(
                provider="unknown", model="unknown", tokens_used=0, cost=0.0, response_time=0.0, success=False
            ))


            return PostGenerationResponse(
                content=best_variation_data["content"],
                hashtags=best_variation_data["hashtags"],
                variations=[var["content"] for var in variations], # Content of all generated variations
                engagement_hooks=best_variation_data.get("engagement_hooks", []),
                call_to_action=best_variation_data.get("call_to_action"),
                estimated_reach=self._estimate_post_reach(best_variation_data),
                processing_time=sum(m.response_time for m in relevant_metrics),
                model_used=f"{final_metrics.provider}:{final_metrics.model}",
                tokens_used=sum(m.tokens_used for m in relevant_metrics),
                cost=sum(m.cost for m in relevant_metrics)
            )

        except Exception as e:
            logger.error(f"Post generation failed: {str(e)}", exc_info=True)
            raise AIServiceError(f"Post generation failed: {str(e)}")

    async def generate_comment_draft(self, request: CommentGenerationRequest) -> CommentGenerationResponse:
        """
        Generate comment draft for LinkedIn engagement.

        Args:
            request: Comment generation request with post context and user tone

        Returns:
            Comment generation response with suggested comment
        """
        try:
            logger.info(f"Generating comment for post: {len(request.post_content)} characters")

            # Build comment generation prompt
            prompt = self.comment_prompts.build_comment_prompt(
                post_content=request.post_content,
                post_author=request.post_author,
                tone_profile=request.tone_profile,
                engagement_type=request.engagement_type or "thoughtful"
            )

            messages = [
                SystemMessage(content=self.comment_prompts.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            # Invoke LLM
            response_text, metrics = await self._invoke_llm_with_fallback(
                messages=messages,
                max_tokens=150,
                temperature=0.8
            )

            # Parse comment response
            comment_data = self._parse_comment_response(response_text)

            return CommentGenerationResponse(
                comment=comment_data["comment"],
                engagement_type=comment_data.get("engagement_type", "thoughtful"),
                confidence_score=comment_data.get("confidence_score", 0.8),
                alternative_comments=comment_data.get("alternatives", []),
                processing_time=metrics.response_time,
                model_used=f"{metrics.provider}:{metrics.model}",
                tokens_used=metrics.tokens_used,
                cost=metrics.cost
            )

        except Exception as e:
            logger.error(f"Comment generation failed: {str(e)}")
            raise AIServiceError(f"Comment generation failed: {str(e)}")

    def _parse_summary_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for summary generation."""
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)

            # Fallback to text parsing
            lines = response_text.strip().split('\n')
            summary = ""
            key_points = []

            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.lower().startswith('summary:'):
                    current_section = 'summary'
                    summary = line[8:].strip()
                elif line.lower().startswith('key points:'):
                    current_section = 'key_points'
                elif line.startswith('- ') or line.startswith('• '):
                    if current_section == 'key_points':
                        key_points.append(line[2:].strip())
                elif current_section == 'summary' and not summary:
                    summary = line
                elif current_section == 'key_points':
                    key_points.append(line)

            return {
                "summary": summary or response_text[:200],
                "key_points": key_points or [response_text[:100]]
            }

        except Exception as e:
            logger.warning(f"Failed to parse summary response: {str(e)}")
            return {
                "summary": response_text[:200],
                "key_points": [response_text[:100]]
            }

    def _parse_post_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for post generation."""
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)

            # Fallback to text parsing
            lines = response_text.strip().split('\n')
            content = ""
            hashtags = []
            engagement_hooks = []
            call_to_action = None

            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.lower().startswith('post:') or line.lower().startswith('content:'):
                    current_section = 'content'
                    content = line.split(':', 1)[1].strip() if ':' in line else ""
                elif line.lower().startswith('hashtags:'):
                    current_section = 'hashtags'
                elif line.lower().startswith('hooks:'):
                    current_section = 'hooks'
                elif line.lower().startswith('cta:') or line.lower().startswith('call to action:'):
                    call_to_action = line.split(':', 1)[1].strip()
                elif line.startswith('#'):
                    hashtags.extend([tag.strip() for tag in line.split() if tag.startswith('#')])
                elif current_section == 'content' and not content:
                    content = line
                elif current_section == 'content':
                    content += " " + line
                elif current_section == 'hooks':
                    engagement_hooks.append(line)

            # Extract hashtags from content if not found separately
            if not hashtags and '#' in content:
                import re
                hashtags = re.findall(r'#\w+', content)

            return {
                "content": content or response_text,
                "hashtags": hashtags,
                "engagement_hooks": engagement_hooks,
                "call_to_action": call_to_action
            }

        except Exception as e:
            logger.warning(f"Failed to parse post response: {str(e)}")
            return {
                "content": response_text,
                "hashtags": [],
                "engagement_hooks": [],
                "call_to_action": None
            }

    def _parse_comment_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for comment generation."""
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                return json.loads(response_text)

            # Fallback to text parsing
            return {
                "comment": response_text.strip(),
                "engagement_type": "thoughtful",
                "confidence_score": 0.8,
                "alternatives": []
            }

        except Exception as e:
            logger.warning(f"Failed to parse comment response: {str(e)}")
            return {
                "comment": response_text.strip(),
                "engagement_type": "thoughtful",
                "confidence_score": 0.5,
                "alternatives": []
            }

    def _select_best_post_variation(self, variations: List[Dict[str, Any]], tone_profile: ToneProfile) -> Dict[str, Any]:
        """Select best post variation based on tone profile and quality metrics."""
        if not variations:
            raise AIServiceError("No variations to select from")

        # Simple scoring based on content length and hashtag count
        best_variation = variations[0]
        best_score = 0

        for variation in variations:
            score = 0
            content = variation.get("content", "")
            hashtags = variation.get("hashtags", [])

            # Score based on content length (optimal range: 100-300 chars)
            content_length = len(content)
            if 100 <= content_length <= 300:
                score += 10
            elif content_length < 100:
                score += content_length / 10
            else:
                score += max(0, 10 - (content_length - 300) / 50)

            # Score based on hashtag count (optimal: 3-5 hashtags)
            hashtag_count = len(hashtags)
            if 3 <= hashtag_count <= 5:
                score += 5
            elif hashtag_count < 3:
                score += hashtag_count
            else:
                score += max(0, 5 - (hashtag_count - 5))

            # Score based on engagement hooks
            if variation.get("engagement_hooks"):
                score += 3

            # Score based on call to action
            if variation.get("call_to_action"):
                score += 2

            if score > best_score:
                best_score = score
                best_variation = variation

        return best_variation

    def _estimate_post_reach(self, post_data: Dict[str, Any]) -> Dict[str, int]:
        """Estimate potential reach for post based on content analysis."""
        content = post_data.get("content", "")
        hashtags = post_data.get("hashtags", [])

        # Simple reach estimation based on content characteristics
        base_reach = 100

        # Boost for optimal content length
        if 100 <= len(content) <= 300:
            base_reach *= 1.5

        # Boost for hashtags
        base_reach += len(hashtags) * 20

        # Boost for engagement hooks
        if post_data.get("engagement_hooks"):
            base_reach *= 1.3

        # Boost for call to action
        if post_data.get("call_to_action"):
            base_reach *= 1.2

        return {
            "estimated_views": int(base_reach),
            "estimated_likes": int(base_reach * 0.1),
            "estimated_comments": int(base_reach * 0.02),
            "estimated_shares": int(base_reach * 0.01)
        }

    def get_usage_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get AI service usage metrics for the specified time period.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary with usage statistics
        """
        cutoff_time = datetime.utcnow().timestamp() - (hours * 3600)
        recent_metrics = [
            m for m in self.usage_metrics 
            if (datetime.utcnow().timestamp() - m.response_time) <= (hours * 3600)
        ]

        if not recent_metrics:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0,
                "provider_breakdown": {},
                "period_hours": hours
            }

        successful = [m for m in recent_metrics if m.success]
        failed = [m for m in recent_metrics if not m.success]

        # Provider breakdown
        provider_stats = {}
        for metric in recent_metrics:
            provider = metric.provider
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "success_rate": 0.0
                }

            provider_stats[provider]["requests"] += 1
            provider_stats[provider]["tokens"] += metric.tokens_used
            provider_stats[provider]["cost"] += metric.cost

        # Calculate success rates
        for provider in provider_stats:
            provider_metrics = [m for m in recent_metrics if m.provider == provider]
            successful_count = len([m for m in provider_metrics if m.success])
            provider_stats[provider]["success_rate"] = (
                successful_count / len(provider_metrics) * 100 if provider_metrics else 0
            )

        return {
            "total_requests": len(recent_metrics),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(recent_metrics) * 100 if recent_metrics else 0,
            "total_tokens": sum(m.tokens_used for m in successful),
            "total_cost": sum(m.cost for m in successful),
            "average_response_time": sum(m.response_time for m in successful) / len(successful) if successful else 0,
            "provider_breakdown": provider_stats,
            "period_hours": hours,
            "generated_at": datetime.utcnow().isoformat()
        }

    def clear_usage_metrics(self):
        """Clear stored usage metrics."""
        self.usage_metrics.clear()
        logger.info("AI service usage metrics cleared")
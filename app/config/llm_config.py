"""
LLM configuration for LinkedIn Presence Automation Application.

Configures OpenAI GPT-4 and Anthropic Claude providers with fallback support,
token limits, cost tracking, and provider-specific settings.
"""

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Enumeration of supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    provider: LLMProvider
    model_name: str
    api_key: str
    max_tokens: int
    temperature: float
    timeout: int
    cost_per_token: float
    rate_limit_rpm: int
    rate_limit_tpm: int


class LLMConfigManager:
    """
    Manager for LLM provider configurations with fallback support.
    
    Handles configuration loading, provider selection, and cost tracking
    for OpenAI GPT-4 and Anthropic Claude models.
    """
    
    def __init__(self):
        """Initialize LLM configuration manager."""
        self.providers: Dict[LLMProvider, LLMConfig] = {}
        self.primary_provider = LLMProvider.OPENAI
        self.fallback_provider = LLMProvider.ANTHROPIC
        self._load_configurations()
    
    def _load_configurations(self):
        """Load LLM provider configurations from environment variables."""
        # OpenAI GPT-4 Configuration
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.providers[LLMProvider.OPENAI] = LLMConfig(
                provider=LLMProvider.OPENAI,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                api_key=openai_api_key,
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "60")),
                cost_per_token=float(os.getenv("OPENAI_COST_PER_TOKEN", "0.00003")),
                rate_limit_rpm=int(os.getenv("OPENAI_RATE_LIMIT_RPM", "500")),
                rate_limit_tpm=int(os.getenv("OPENAI_RATE_LIMIT_TPM", "30000"))
            )
            logger.info("OpenAI GPT-4 configuration loaded")
        
        # Anthropic Claude Configuration
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key:
            self.providers[LLMProvider.ANTHROPIC] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=anthropic_api_key,
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
                timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "60")),
                cost_per_token=float(os.getenv("ANTHROPIC_COST_PER_TOKEN", "0.000015")),
                rate_limit_rpm=int(os.getenv("ANTHROPIC_RATE_LIMIT_RPM", "300")),
                rate_limit_tpm=int(os.getenv("ANTHROPIC_RATE_LIMIT_TPM", "20000"))
            )
            logger.info("Anthropic Claude configuration loaded")
        
        if not self.providers:
            logger.warning("No LLM providers configured")
    
    def get_primary_config(self) -> Optional[LLMConfig]:
        """
        Get primary LLM provider configuration.
        
        Returns:
            Primary LLM configuration or None if not available
        """
        return self.providers.get(self.primary_provider)
    
    def get_fallback_config(self) -> Optional[LLMConfig]:
        """
        Get fallback LLM provider configuration.
        
        Returns:
            Fallback LLM configuration or None if not available
        """
        return self.providers.get(self.fallback_provider)
    
    def get_config(self, provider: LLMProvider) -> Optional[LLMConfig]:
        """
        Get configuration for specific provider.
        
        Args:
            provider: LLM provider to get configuration for
            
        Returns:
            LLM configuration or None if not available
        """
        return self.providers.get(provider)
    
    def get_available_providers(self) -> List[LLMProvider]:
        """
        Get list of available LLM providers.
        
        Returns:
            List of configured LLM providers
        """
        return list(self.providers.keys())
    
    def is_provider_available(self, provider: LLMProvider) -> bool:
        """
        Check if a provider is available.
        
        Args:
            provider: LLM provider to check
            
        Returns:
            True if provider is configured and available
        """
        return provider in self.providers
    
    def get_cost_estimate(self, provider: LLMProvider, token_count: int) -> float:
        """
        Estimate cost for token usage with specific provider.
        
        Args:
            provider: LLM provider
            token_count: Number of tokens
            
        Returns:
            Estimated cost in USD
        """
        config = self.get_config(provider)
        if not config:
            return 0.0
        
        return token_count * config.cost_per_token
    
    def get_model_limits(self, provider: LLMProvider) -> Dict[str, int]:
        """
        Get model limits for specific provider.
        
        Args:
            provider: LLM provider
            
        Returns:
            Dictionary with model limits
        """
        config = self.get_config(provider)
        if not config:
            return {}
        
        return {
            "max_tokens": config.max_tokens,
            "rate_limit_rpm": config.rate_limit_rpm,
            "rate_limit_tpm": config.rate_limit_tpm,
            "timeout": config.timeout
        }


# Global configuration manager instance
llm_config_manager = LLMConfigManager()


def get_llm_config() -> LLMConfigManager:
    """
    Get global LLM configuration manager instance.
    
    Returns:
        LLM configuration manager
    """
    return llm_config_manager


def validate_llm_configuration() -> Dict[str, Any]:
    """
    Validate LLM configuration and return status.
    
    Returns:
        Dictionary with validation results
    """
    config_manager = get_llm_config()
    available_providers = config_manager.get_available_providers()
    
    validation_result = {
        "valid": len(available_providers) > 0,
        "available_providers": [provider.value for provider in available_providers],
        "primary_provider": config_manager.primary_provider.value if config_manager.get_primary_config() else None,
        "fallback_provider": config_manager.fallback_provider.value if config_manager.get_fallback_config() else None,
        "errors": []
    }
    
    # Check primary provider
    if not config_manager.get_primary_config():
        validation_result["errors"].append(f"Primary provider {config_manager.primary_provider.value} not configured")
    
    # Check fallback provider
    if not config_manager.get_fallback_config():
        validation_result["errors"].append(f"Fallback provider {config_manager.fallback_provider.value} not configured")
    
    # Validate API keys
    for provider in available_providers:
        config = config_manager.get_config(provider)
        if not config.api_key:
            validation_result["errors"].append(f"API key missing for {provider.value}")
    
    return validation_result
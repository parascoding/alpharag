"""
Provider factory for creating data provider instances
"""

from typing import Dict, Optional, List, Any
import logging
from .base_provider import BaseDataProvider
from .mock_provider import MockProvider
from .yahoo_provider import YahooProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .upstox_provider import UpstoxProvider

logger = logging.getLogger(__name__)

class ProviderFactory:
    """
    Factory for creating data provider instances
    Supports configuration-driven provider selection and fallback chains
    """

    # Registry of available providers
    _providers = {
        'mock': MockProvider,
        'yahoo': YahooProvider,
        'alpha_vantage': AlphaVantageProvider,
        'upstox': UpstoxProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str, **kwargs) -> Optional[BaseDataProvider]:
        """
        Create a provider instance by name

        Args:
            provider_name: Name of the provider to create
            **kwargs: Configuration parameters for the provider

        Returns:
            Provider instance or None if not available
        """
        try:
            if provider_name not in cls._providers:
                logger.error(f"Unknown provider: {provider_name}")
                return None

            provider_class = cls._providers[provider_name]
            provider = provider_class(**kwargs)

            logger.info(f"Created provider: {provider_name}")
            return provider

        except Exception as e:
            logger.error(f"Error creating provider {provider_name}: {e}")
            return None

    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider names"""
        return list(cls._providers.keys())

    @classmethod
    def get_provider_with_fallback(cls, primary_provider: str, fallback_providers: List[str] = None, **kwargs) -> Optional[BaseDataProvider]:
        """
        Get a provider with fallback chain

        Args:
            primary_provider: Primary provider to try first
            fallback_providers: List of fallback providers to try if primary fails
            **kwargs: Configuration parameters

        Returns:
            First available provider or None if all fail
        """
        if fallback_providers is None:
            fallback_providers = ['mock']  # Always fallback to mock

        # Try primary provider first
        provider_chain = [primary_provider] + fallback_providers

        for provider_name in provider_chain:
            logger.info(f"Trying provider: {provider_name}")

            provider = cls.get_provider(provider_name, **kwargs)
            if provider and provider.is_available():
                if provider_name == 'mock':
                    logger.error(f"⚠️ FALLING BACK TO MOCK DATA: {provider_name} - Real APIs failed")
                else:
                    logger.info(f"✅ Using provider: {provider_name}")
                return provider
            else:
                logger.warning(f"⚠️  Provider {provider_name} not available, trying next...")

        logger.error("❌ No providers available in fallback chain")
        return None

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a new provider class

        Args:
            name: Provider name
            provider_class: Provider class that extends BaseDataProvider
        """
        if not issubclass(provider_class, BaseDataProvider):
            raise ValueError(f"Provider class must extend BaseDataProvider")

        cls._providers[name] = provider_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def health_check_all(cls) -> Dict[str, Any]:
        """
        Perform health check on all registered providers

        Returns:
            Dictionary with health status of all providers
        """
        health_status = {
            'timestamp': logger.handlers[0].format(logger.makeRecord(
                logger.name, logging.INFO, __file__, 0,
                '', (), None
            )) if logger.handlers else 'unknown',
            'providers': {}
        }

        for provider_name in cls._providers:
            try:
                provider = cls.get_provider(provider_name)
                if provider:
                    status = provider.health_check()
                else:
                    status = {
                        'provider': provider_name,
                        'healthy': False,
                        'error': 'Could not create provider instance'
                    }
                health_status['providers'][provider_name] = status

            except Exception as e:
                health_status['providers'][provider_name] = {
                    'provider': provider_name,
                    'healthy': False,
                    'error': str(e)
                }

        return health_status
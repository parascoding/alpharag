"""
Base data provider interface for financial data sources
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseDataProvider(ABC):
    """
    Abstract base class for all data providers
    Defines the interface that all data providers must implement
    """

    def __init__(self, name: str, **kwargs):
        self.name = name
        self.config = kwargs
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

    @abstractmethod
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a single symbol

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')

        Returns:
            Current price as float, None if not available
        """
        pass

    @abstractmethod
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to current prices
        """
        pass

    @abstractmethod
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data for a symbol

        Args:
            symbol: Stock symbol
            period: Time period (e.g., '1mo', '3mo', '1y')

        Returns:
            DataFrame with OHLCV data, None if not available
        """
        pass

    @abstractmethod
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get basic company information

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with company info, None if not available
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the data provider is currently available

        Returns:
            True if provider is available, False otherwise
        """
        pass

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about this provider

        Returns:
            Dictionary with provider metadata
        """
        return {
            'name': self.name,
            'class': self.__class__.__name__,
            'config': self.config,
            'available': self.is_available()
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider

        Returns:
            Dictionary with health status
        """
        try:
            available = self.is_available()
            return {
                'provider': self.name,
                'healthy': available,
                'timestamp': datetime.now().isoformat(),
                'error': None
            }
        except Exception as e:
            return {
                'provider': self.name,
                'healthy': False,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
"""
Enhanced Market Data Ingestion using the new provider system
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import time

from .data_providers import ProviderFactory, BaseDataProvider

logger = logging.getLogger(__name__)

class MarketDataIngestionV2:
    """
    Enhanced market data ingestion using pluggable data providers
    Supports multiple data sources with automatic fallback
    """
    
    def __init__(self, primary_provider: str = 'mock', fallback_providers: List[str] = None, **provider_kwargs):
        """
        Initialize with configurable data providers
        
        Args:
            primary_provider: Primary data provider to use
            fallback_providers: List of fallback providers
            **provider_kwargs: Configuration for providers
        """
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or ['mock']
        self.provider_kwargs = provider_kwargs
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
        # Initialize provider
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the data provider with fallback"""
        self.provider = ProviderFactory.get_provider_with_fallback(
            primary_provider=self.primary_provider,
            fallback_providers=self.fallback_providers,
            **self.provider_kwargs
        )
        
        if not self.provider:
            raise RuntimeError("Could not initialize any data provider")
        
        logger.info(f"✅ Initialized data ingestion with provider: {self.provider.name}")
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        try:
            logger.info(f"Fetching current prices for {len(symbols)} symbols using {self.provider.name}")
            
            # Check cache first
            cached_prices = self._get_cached_prices(symbols)
            uncached_symbols = [s for s in symbols if s not in cached_prices]
            
            if uncached_symbols:
                # Fetch new prices
                new_prices = self.provider.get_current_prices(uncached_symbols)
                
                # Cache the results
                self._cache_prices(new_prices)
                
                # Combine cached and new prices
                all_prices = {**cached_prices, **new_prices}
            else:
                all_prices = cached_prices
            
            successful = len([p for p in all_prices.values() if p > 0])
            logger.info(f"Successfully fetched {successful}/{len(symbols)} prices")
            
            return all_prices
            
        except Exception as e:
            logger.error(f"Error fetching prices: {e}")
            # Return zeros for all symbols as fallback
            return {symbol: 0.0 for symbol in symbols}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a single symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if not available
        """
        try:
            # Check cache first
            cache_key = f"price_{symbol}"
            if self._is_cached(cache_key):
                cached_price = self.cache[cache_key]['data']
                logger.info(f"Using cached price for {symbol}: ₹{cached_price:.2f}")
                return cached_price
            
            # Fetch from provider
            price = self.provider.get_current_price(symbol)
            
            # Cache the result
            if price is not None:
                self.cache[cache_key] = {
                    'data': price,
                    'timestamp': datetime.now()
                }
            
            return price
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol: Stock symbol
            period: Time period (e.g., '1mo', '3mo', '1y')
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(f"Fetching historical data for {symbol}, period: {period}")
            
            # Check cache
            cache_key = f"hist_{symbol}_{period}"
            if self._is_cached(cache_key):
                cached_data = self.cache[cache_key]['data']
                logger.info(f"Using cached historical data for {symbol}")
                return cached_data
            
            # Fetch from provider
            hist_data = self.provider.get_historical_data(symbol, period)
            
            # Cache the result
            if hist_data is not None:
                self.cache[cache_key] = {
                    'data': hist_data,
                    'timestamp': datetime.now()
                }
            
            return hist_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """
        Get company information for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            logger.info(f"Fetching company info for {symbol}")
            
            # Check cache (company info changes rarely)
            cache_key = f"info_{symbol}"
            if self._is_cached(cache_key, timeout=3600):  # 1 hour cache for company info
                cached_info = self.cache[cache_key]['data']
                logger.info(f"Using cached company info for {symbol}")
                return cached_info
            
            # Fetch from provider
            company_info = self.provider.get_company_info(symbol)
            
            # Cache the result
            if company_info is not None:
                self.cache[cache_key] = {
                    'data': company_info,
                    'timestamp': datetime.now()
                }
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error fetching company info for {symbol}: {e}")
            return None
    
    def get_market_summary(self, symbols: List[str]) -> Dict:
        """
        Get comprehensive market summary
        
        Args:
            symbols: List of symbols to include in summary
            
        Returns:
            Dictionary with market summary data
        """
        try:
            logger.info(f"Generating market summary for {len(symbols)} symbols")
            
            # Get current prices
            prices = self.get_current_prices(symbols)
            
            # Build summary
            summary = {
                'market_status': 'open',  # TODO: Implement market hours detection
                'timestamp': datetime.now().isoformat(),
                'provider': self.provider.name,
                'prices': prices,
                'symbols_count': len(symbols),
                'successful_prices': len([p for p in prices.values() if p > 0])
            }
            
            # Add technical indicators if available
            for symbol in symbols:
                hist_data = self.get_historical_data(symbol, "1mo")
                if hist_data is not None and not hist_data.empty:
                    tech_indicators = self._calculate_technical_indicators(hist_data)
                    summary[f"{symbol}_technical"] = tech_indicators
            
            logger.info(f"Market summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'provider': self.provider.name if self.provider else 'none'
            }
    
    def _calculate_technical_indicators(self, hist_data: pd.DataFrame) -> Dict:
        """Calculate basic technical indicators from historical data"""
        try:
            indicators = {}
            
            if 'Close' in hist_data.columns:
                close_prices = hist_data['Close']
                
                # Simple moving averages
                if len(close_prices) >= 5:
                    indicators['sma_5'] = float(close_prices.tail(5).mean())
                if len(close_prices) >= 20:
                    indicators['sma_20'] = float(close_prices.tail(20).mean())
                
                # RSI if available
                if 'RSI' in hist_data.columns:
                    indicators['rsi'] = float(hist_data['RSI'].iloc[-1])
                
                # Price range
                indicators['high_1mo'] = float(close_prices.max())
                indicators['low_1mo'] = float(close_prices.min())
                indicators['current'] = float(close_prices.iloc[-1])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def _get_cached_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get cached prices for symbols"""
        cached = {}
        for symbol in symbols:
            cache_key = f"price_{symbol}"
            if self._is_cached(cache_key):
                cached[symbol] = self.cache[cache_key]['data']
        return cached
    
    def _cache_prices(self, prices: Dict[str, float]):
        """Cache price data"""
        timestamp = datetime.now()
        for symbol, price in prices.items():
            if price > 0:  # Only cache valid prices
                cache_key = f"price_{symbol}"
                self.cache[cache_key] = {
                    'data': price,
                    'timestamp': timestamp
                }
    
    def _is_cached(self, key: str, timeout: int = None) -> bool:
        """Check if data is cached and still valid"""
        if timeout is None:
            timeout = self.cache_timeout
            
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < timeout:
                return True
        return False
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_provider_info(self) -> Dict:
        """Get information about the current provider"""
        if self.provider:
            return self.provider.get_provider_info()
        return {'error': 'No provider available'}
    
    def health_check(self) -> Dict:
        """Perform health check on the data ingestion system"""
        try:
            provider_health = self.provider.health_check() if self.provider else None
            
            return {
                'data_ingestion': {
                    'healthy': provider_health.get('healthy', False) if provider_health else False,
                    'provider': self.provider.name if self.provider else 'none',
                    'cache_size': len(self.cache),
                    'timestamp': datetime.now().isoformat()
                },
                'provider_health': provider_health
            }
            
        except Exception as e:
            return {
                'data_ingestion': {
                    'healthy': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            }
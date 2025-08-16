"""
Upstox data provider implementation for Indian stock market data
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
import logging
import json

from .base_provider import BaseDataProvider
from .upstox_instrument_mapper import upstox_mapper

logger = logging.getLogger(__name__)

class UpstoxProvider(BaseDataProvider):
    """
    Upstox implementation of the data provider interface
    Supports Indian stocks via NSE and BSE with real-time data
    """

    def __init__(self, access_token: str, **kwargs):
        super().__init__("upstox", **kwargs)
        self.access_token = access_token
        self.base_url = "https://api.upstox.com/v2"
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.1)  # 100ms between requests
        self.timeout = kwargs.get('timeout', 10)
        self.session = requests.Session()

        # Set default headers for all requests
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'User-Agent': 'AlphaRAG/1.0'
        })

        if not self.access_token:
            raise ValueError("Upstox access token is required")

    def _make_request(self, endpoint: str, params: Dict[str, str] = None) -> Optional[Dict]:
        """Make a request to Upstox API"""
        try:
            url = f"{self.base_url}{endpoint}"
            self.logger.debug(f"Making Upstox request: {url}")

            response = self.session.get(url, params=params, timeout=self.timeout)
            time.sleep(self.rate_limit_delay)  # Rate limiting

            if response.status_code == 200:
                data = response.json()

                # Check for API errors in response
                if data.get('status') == 'error':
                    self.logger.error(f"Upstox API error: {data.get('message', 'Unknown error')}")
                    self.logger.error(f"Full response: {data}")
                    return None

                return data
            else:
                self.logger.error(f"HTTP error {response.status_code}: {response.text[:200]}")
                self.logger.error(f"Request URL: {response.url}")
                return None

        except Exception as e:
            self.logger.error(f"Upstox request failed: {e}")
            return None

    def _convert_symbol_to_instrument_key(self, symbol: str) -> str:
        """
        Convert symbol format to Upstox instrument key
        RELIANCE.NS -> NSE_EQ|INE002A01018
        Uses the instrument mapper for accurate mapping
        """
        instrument_key = upstox_mapper.get_instrument_key(symbol)
        if instrument_key:
            return instrument_key

        # Fallback to simple pattern if mapper fails
        if symbol.endswith('.NS'):
            base_symbol = symbol.replace('.NS', '')
            return f"NSE_EQ|{base_symbol}"
        elif symbol.endswith('.BO'):
            base_symbol = symbol.replace('.BO', '')
            return f"BSE_EQ|{base_symbol}"
        else:
            return f"NSE_EQ|{symbol}"

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using Upstox quote API"""
        try:
            instrument_key = self._convert_symbol_to_instrument_key(symbol)
            self.logger.info(f"Fetching current price for {symbol} (instrument: {instrument_key})")

            params = {
                'instrument_key': instrument_key
            }

            data = self._make_request('/market-quote/quotes', params)

            if data and data.get('status') == 'success':
                quote_data = data.get('data', {})

                # The API returns keys in format like 'NSE_EQ:RELIANCE' instead of 'NSE_EQ|INE002A01018'
                # We need to find the matching entry by looking for symbol matches
                price = None

                # Extract the base symbol from our input
                if symbol.endswith('.NS') or symbol.endswith('.BO'):
                    base_symbol = symbol.split('.')[0]
                else:
                    base_symbol = symbol

                # Look for matching quote by symbol name
                for key, quote in quote_data.items():
                    # Check if this is the right symbol (e.g., 'NSE_EQ:RELIANCE' contains 'RELIANCE')
                    if f":{base_symbol}" in key or quote.get('symbol') == base_symbol:
                        price = quote.get('last_price')
                        self.logger.debug(f"Found {symbol} data in response key: {key}")
                        break

                # If not found by symbol match, try exact instrument key match
                if price is None and instrument_key in quote_data:
                    quote = quote_data[instrument_key]
                    price = quote.get('last_price')

                if price:
                    self.logger.info(f"✅ Current price for {symbol}: ₹{price:.2f}")
                    return float(price)

            self.logger.warning(f"No price data found for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}

        self.logger.info(f"Fetching prices for {len(symbols)} symbols")

        # Upstox supports batch requests for multiple instruments
        try:
            instrument_keys = [self._convert_symbol_to_instrument_key(symbol) for symbol in symbols]

            # Create comma-separated list of instrument keys
            params = {
                'instrument_key': ','.join(instrument_keys)
            }

            data = self._make_request('/market-quote/quotes', params)

            if data and data.get('status') == 'success':
                quote_data = data.get('data', {})

                for i, symbol in enumerate(symbols):
                    instrument_key = instrument_keys[i]

                    # Try to find price using flexible matching
                    price = None

                    # First try exact match
                    if instrument_key in quote_data:
                        price = quote_data[instrument_key].get('last_price')

                    # If not found, try symbol-based matching
                    if price is None:
                        # Extract the base symbol from our input
                        if symbol.endswith('.NS') or symbol.endswith('.BO'):
                            base_symbol = symbol.split('.')[0]
                        else:
                            base_symbol = symbol

                        # Look for matching quote by symbol name
                        for key, quote in quote_data.items():
                            # Check if this is the right symbol (e.g., 'NSE_EQ:RELIANCE' contains 'RELIANCE')
                            if f":{base_symbol}" in key or quote.get('symbol') == base_symbol:
                                price = quote.get('last_price')
                                self.logger.debug(f"Found {symbol} data in response key: {key}")
                                break

                    if price:
                        prices[symbol] = float(price)
                        self.logger.info(f"✅ {symbol}: ₹{price:.2f}")
                    else:
                        prices[symbol] = 0.0
                        self.logger.warning(f"⚠️ No price for {symbol}")

            # Fill in any missing symbols
            for symbol in symbols:
                if symbol not in prices:
                    prices[symbol] = 0.0

        except Exception as e:
            self.logger.error(f"Batch price fetch failed: {e}")
            # Fallback to individual requests
            for symbol in symbols:
                price = self.get_current_price(symbol)
                prices[symbol] = price if price is not None else 0.0
                time.sleep(self.rate_limit_delay)

        successful = len([p for p in prices.values() if p > 0])
        self.logger.info(f"Successfully fetched {successful}/{len(symbols)} prices from Upstox")
        return prices

    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical data using Upstox historical candle data API"""
        try:
            instrument_key = self._convert_symbol_to_instrument_key(symbol)
            self.logger.info(f"Fetching historical data for {symbol}, period: {period}")

            # Calculate date range
            end_date = datetime.now().strftime('%Y-%m-%d')

            if period == "1mo":
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                interval = "day"
            elif period == "3mo":
                start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                interval = "day"
            elif period == "1y":
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                interval = "day"
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                interval = "day"

            # Upstox historical candle API uses path parameters in format:
            # /historical-candle/{instrument_key}/{interval}/{to_date}/{from_date}
            # Note: to_date comes BEFORE from_date in the URL path
            endpoint = f'/historical-candle/{instrument_key}/{interval}/{end_date}/{start_date}'

            data = self._make_request(endpoint)

            if data and data.get('status') == 'success':
                candles = data.get('data', {}).get('candles', [])

                if candles:
                    # Create DataFrame from candle data
                    # Upstox format: [timestamp, open, high, low, close, volume, oi]
                    df_data = []
                    for candle in candles:
                        df_data.append({
                            'Date': pd.to_datetime(candle[0]),
                            'Open': float(candle[1]),
                            'High': float(candle[2]),
                            'Low': float(candle[3]),
                            'Close': float(candle[4]),
                            'Volume': int(candle[5]) if len(candle) > 5 else 0
                        })

                    hist_data = pd.DataFrame(df_data).set_index('Date').sort_index()

                    # Calculate technical indicators
                    if not hist_data.empty:
                        hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
                        hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
                        hist_data['RSI'] = self._calculate_rsi(hist_data['Close'])

                        self.logger.info(f"✅ Historical data for {symbol}: {len(hist_data)} days")
                        return hist_data

            self.logger.warning(f"No historical data found for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company information from Upstox
        Note: Upstox API may not have detailed company info like Alpha Vantage
        We'll extract what we can from market quote data
        """
        try:
            instrument_key = self._convert_symbol_to_instrument_key(symbol)
            self.logger.info(f"Fetching company info for {symbol}")

            # Get full market quote which may contain some company data
            params = {
                'instrument_key': instrument_key
            }

            data = self._make_request('/market-quote/quotes', params)

            if data and data.get('status') == 'success':
                quote_data = data.get('data', {})
                if instrument_key in quote_data:
                    quote = quote_data[instrument_key]

                    # Extract available information
                    company_info = {
                        'symbol': symbol,
                        'name': quote.get('instrument_name', symbol),
                        'exchange': 'NSE' if 'NSE' in instrument_key else 'BSE',
                        'sector': 'N/A',  # Not available in Upstox quote data
                        'industry': 'N/A',  # Not available in Upstox quote data
                        'market_cap': 0,  # Not available in Upstox quote data
                        'last_price': quote.get('last_price', 0),
                        'previous_close': quote.get('prev_close', 0),
                        'change': quote.get('net_change', 0),
                        'change_percent': quote.get('percent_change', 0),
                        'volume': quote.get('volume', 0),
                        'currency': 'INR',
                        'timestamp': datetime.now().isoformat()
                    }

                    self.logger.info(f"✅ Company info for {symbol}: {company_info['name']}")
                    return company_info

            self.logger.warning(f"No company info found for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {e}")
            return None

    def is_available(self) -> bool:
        """Check if Upstox API is available"""
        try:
            self.logger.info(f"Testing Upstox API with token: {self.access_token[:10]}...{self.access_token[-4:]}")

            # Test with a simple market quote request
            params = {
                'instrument_key': 'NSE_EQ|INE002A01018'  # Reliance Industries
            }

            data = self._make_request('/market-quote/quotes', params)

            if data is None:
                self.logger.error("Upstox returned None response - check logs above for details")
                return False

            available = data.get('status') == 'success'

            if not available:
                self.logger.error(f"Upstox API not available. Response: {data}")

            self.logger.info(f"Upstox availability check: {'✅ Available' if available else '❌ Not available'}")
            return available

        except Exception as e:
            self.logger.error(f"Upstox availability check failed: {e}")
            return False

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Upstox provider"""
        health_status = {
            'provider': self.name,
            'healthy': False,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }

        try:
            # Test API connectivity
            available = self.is_available()
            health_status['healthy'] = available
            health_status['details']['api_available'] = available

            if available:
                # Test basic functionality
                test_price = self.get_current_price('RELIANCE.NS')
                health_status['details']['price_fetch_working'] = test_price is not None
                health_status['details']['test_price'] = test_price

        except Exception as e:
            health_status['details']['error'] = str(e)

        return health_status
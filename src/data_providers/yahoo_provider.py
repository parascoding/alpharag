"""
Yahoo Finance provider using direct HTTP requests
Avoids yfinance library compatibility issues with Python 3.8
"""

import requests
import pandas as pd
import json
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
import logging

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)

class YahooProvider(BaseDataProvider):
    """
    Yahoo Finance implementation using direct HTTP requests
    Supports Indian stocks with .NS and .BO suffixes
    """

    def __init__(self, **kwargs):
        super().__init__("yahoo", **kwargs)
        self.base_url = "https://query1.finance.yahoo.com"
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.5)  # 500ms between requests
        self.timeout = kwargs.get('timeout', 10)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _make_request(self, endpoint: str, params: Dict[str, str]) -> Optional[Dict]:
        """Make a request to Yahoo Finance API"""
        try:
            url = f"{self.base_url}{endpoint}"
            self.logger.debug(f"Making Yahoo request: {url}")

            response = self.session.get(url, params=params, timeout=self.timeout)
            time.sleep(self.rate_limit_delay)  # Rate limiting

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"HTTP error {response.status_code}: {response.text[:200]}")
                return None

        except Exception as e:
            self.logger.error(f"Yahoo request failed: {e}")
            return None

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using Yahoo Finance quote API"""
        try:
            self.logger.info(f"Fetching current price for {symbol}")

            params = {
                'symbols': symbol,
                'fields': 'regularMarketPrice,currency'
            }

            data = self._make_request('/v7/finance/quote', params)

            if data and 'quoteResponse' in data:
                results = data['quoteResponse'].get('result', [])
                if results:
                    quote = results[0]
                    price = quote.get('regularMarketPrice')

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

        try:
            # Yahoo Finance supports batch requests
            symbols_str = ','.join(symbols)
            params = {
                'symbols': symbols_str,
                'fields': 'regularMarketPrice,currency'
            }

            data = self._make_request('/v7/finance/quote', params)

            if data and 'quoteResponse' in data:
                results = data['quoteResponse'].get('result', [])

                for quote in results:
                    symbol = quote.get('symbol')
                    price = quote.get('regularMarketPrice')

                    if symbol and price:
                        prices[symbol] = float(price)
                        self.logger.info(f"✅ {symbol}: ₹{price:.2f}")
                    elif symbol:
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
        self.logger.info(f"Successfully fetched {successful}/{len(symbols)} prices from Yahoo")
        return prices

    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Get historical data using Yahoo Finance history API"""
        try:
            self.logger.info(f"Fetching historical data for {symbol}, period: {period}")

            # Calculate date range
            end_timestamp = int(datetime.now().timestamp())

            if period == "1mo":
                start_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
            elif period == "3mo":
                start_timestamp = int((datetime.now() - timedelta(days=90)).timestamp())
            elif period == "1y":
                start_timestamp = int((datetime.now() - timedelta(days=365)).timestamp())
            else:
                start_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())

            params = {
                'symbol': symbol,
                'period1': start_timestamp,
                'period2': end_timestamp,
                'interval': '1d',
                'events': 'history'
            }

            data = self._make_request('/v8/finance/chart/' + symbol, params)

            if data and 'chart' in data:
                chart = data['chart']
                if chart.get('result'):
                    result = chart['result'][0]
                    timestamps = result.get('timestamp', [])
                    indicators = result.get('indicators', {})

                    if timestamps and indicators.get('quote'):
                        quote_data = indicators['quote'][0]

                        # Create DataFrame
                        hist_data = pd.DataFrame({
                            'Date': [datetime.fromtimestamp(ts) for ts in timestamps],
                            'Open': quote_data.get('open', []),
                            'High': quote_data.get('high', []),
                            'Low': quote_data.get('low', []),
                            'Close': quote_data.get('close', []),
                            'Volume': quote_data.get('volume', [])
                        })

                        hist_data = hist_data.set_index('Date').dropna()

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
        """Get company information from Yahoo Finance"""
        try:
            self.logger.info(f"Fetching company info for {symbol}")

            params = {
                'modules': 'summaryProfile,price,defaultKeyStatistics'
            }

            data = self._make_request(f'/v10/finance/quoteSummary/{symbol}', params)

            if data and 'quoteSummary' in data:
                result = data['quoteSummary'].get('result', [])
                if result:
                    modules = result[0]

                    profile = modules.get('summaryProfile', {})
                    price_info = modules.get('price', {})
                    key_stats = modules.get('defaultKeyStatistics', {})

                    company_info = {
                        'symbol': symbol,
                        'name': price_info.get('longName', 'N/A'),
                        'sector': profile.get('sector', 'N/A'),
                        'industry': profile.get('industry', 'N/A'),
                        'market_cap': self._extract_value(price_info.get('marketCap', {})),
                        'pe_ratio': self._extract_value(key_stats.get('trailingPE', {})),
                        'dividend_yield': self._extract_value(key_stats.get('dividendYield', {})),
                        'beta': self._extract_value(key_stats.get('beta', {})),
                        'fifty_two_week_high': self._extract_value(key_stats.get('fiftyTwoWeekHigh', {})),
                        'fifty_two_week_low': self._extract_value(key_stats.get('fiftyTwoWeekLow', {})),
                        'currency': price_info.get('currency', 'INR'),
                        'exchange': price_info.get('exchangeName', 'NSI'),
                        'country': profile.get('country', 'India'),
                        'website': profile.get('website', 'N/A'),
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
        """Check if Yahoo Finance API is available"""
        try:
            # Test with a reliable Indian stock
            test_symbol = "RELIANCE.NS"
            params = {
                'symbols': test_symbol,
                'fields': 'regularMarketPrice'
            }

            data = self._make_request('/v7/finance/quote', params)
            available = data is not None and 'quoteResponse' in data

            self.logger.info(f"Yahoo Finance availability check: {'✅ Available' if available else '❌ Not available'}")
            return available

        except Exception as e:
            self.logger.error(f"Yahoo Finance availability check failed: {e}")
            return False

    def _extract_value(self, field_data: Dict) -> float:
        """Extract numeric value from Yahoo Finance field data"""
        if isinstance(field_data, dict):
            return field_data.get('raw', 0.0)
        elif isinstance(field_data, (int, float)):
            return float(field_data)
        else:
            return 0.0

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
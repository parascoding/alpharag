"""
yfinance data provider implementation
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
import logging

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)

class YFinanceProvider(BaseDataProvider):
    """
    yfinance implementation of the data provider interface
    Best for Indian stocks with .NS suffix (NSE) and .BO suffix (BSE)
    """

    def __init__(self, **kwargs):
        super().__init__("yfinance", **kwargs)
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 0.1)  # 100ms between calls
        self.timeout = kwargs.get('timeout', 10)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a single symbol using yfinance
        """
        try:
            self.logger.info(f"Fetching current price for {symbol}")

            # Create yfinance ticker
            ticker = yf.Ticker(symbol)

            # Get current data
            data = ticker.history(period="1d", interval="1m")

            if not data.empty:
                current_price = data['Close'].iloc[-1]
                self.logger.info(f"✅ Current price for {symbol}: ₹{current_price:.2f}")
                return float(current_price)
            else:
                self.logger.warning(f"No price data found for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
            return None

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Get current prices for multiple symbols
        """
        prices = {}

        self.logger.info(f"Fetching prices for {len(symbols)} symbols")

        for symbol in symbols:
            price = self.get_current_price(symbol)
            prices[symbol] = price if price is not None else 0.0

            # Rate limiting
            time.sleep(self.rate_limit_delay)

        self.logger.info(f"Successfully fetched {len([p for p in prices.values() if p > 0])} prices")
        return prices

    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data for a symbol
        """
        try:
            self.logger.info(f"Fetching historical data for {symbol}, period: {period}")

            ticker = yf.Ticker(symbol)

            # Map period formats if needed
            period_map = {
                "1mo": "1mo",
                "3mo": "3mo",
                "6mo": "6mo",
                "1y": "1y",
                "2y": "2y",
                "5y": "5y"
            }

            yf_period = period_map.get(period, period)
            hist_data = ticker.history(period=yf_period)

            if not hist_data.empty:
                # Calculate some basic technical indicators
                hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
                hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
                hist_data['RSI'] = self._calculate_rsi(hist_data['Close'])

                self.logger.info(f"✅ Historical data for {symbol}: {len(hist_data)} days")
                return hist_data
            else:
                self.logger.warning(f"No historical data found for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get basic company information
        """
        try:
            self.logger.info(f"Fetching company info for {symbol}")

            ticker = yf.Ticker(symbol)
            info = ticker.info

            if info:
                # Extract key information
                company_info = {
                    'symbol': symbol,
                    'name': info.get('longName', 'N/A'),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                    'dividend_yield': info.get('dividendYield', 0),
                    'beta': info.get('beta', 0),
                    'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                    'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                    'currency': info.get('currency', 'INR'),
                    'exchange': info.get('exchange', 'NSI'),
                    'timestamp': datetime.now().isoformat()
                }

                self.logger.info(f"✅ Company info for {symbol}: {company_info['name']}")
                return company_info
            else:
                self.logger.warning(f"No company info found for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {e}")
            return None

    def is_available(self) -> bool:
        """
        Check if yfinance is available by testing with a known symbol
        """
        try:
            # Test with a reliable Indian stock
            test_symbol = "RELIANCE.NS"
            ticker = yf.Ticker(test_symbol)

            # Try to get minimal data with short timeout
            data = ticker.history(period="1d", interval="1d")

            available = not data.empty
            self.logger.info(f"yfinance availability check: {'✅ Available' if available else '❌ Not available'}")
            return available

        except Exception as e:
            self.logger.error(f"yfinance availability check failed: {e}")
            return False

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """
        Calculate RSI (Relative Strength Index)
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
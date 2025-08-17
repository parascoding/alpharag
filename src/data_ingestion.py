import requests
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time
import random

logger = logging.getLogger(__name__)

class MarketDataIngestion:
    def __init__(self, alpha_vantage_api_key: Optional[str] = None):
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes

    def _load_mock_market_data(self) -> Dict:
        """
        Load mock market data from JSON file
        """
        try:
            mock_data_path = Path(__file__).parent.parent / 'mock_data' / 'market_data.json'

            if not mock_data_path.exists():
                logger.warning(f"Mock market data file not found: {mock_data_path}")
                return self._get_fallback_market_data()

            with open(mock_data_path, 'r') as f:
                data = json.load(f)

            logger.info(f"Loaded mock market data from {mock_data_path}")
            return data['market_data']

        except Exception as e:
            logger.error(f"Error loading mock market data: {e}")
            return self._get_fallback_market_data()

    def _get_fallback_market_data(self) -> Dict:
        """
        Fallback market data if JSON file is not available
        """
        return {
            'stock_prices': {
                'RELIANCE.NS': {'current_price': 2847.65},
                'TCS.NS': {'current_price': 3687.45},
                'INFY.NS': {'current_price': 1532.25}
            },
            'technical_indicators': {
                'RELIANCE.NS': {'rsi': 52.4, 'sma_5': 2856.42, 'sma_20': 2821.75},
                'TCS.NS': {'rsi': 58.7, 'sma_5': 3698.84, 'sma_20': 3645.67},
                'INFY.NS': {'rsi': 46.8, 'sma_5': 1548.76, 'sma_20': 1521.43}
            },
            'market_status': 'open'
        }

    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        prices = {}

        for symbol in symbols:
            try:
                price = self._get_current_price_mock(symbol)
                if price is None and self.alpha_vantage_api_key:
                    price = self._get_current_price_alphavantage(symbol)

                prices[symbol] = price if price is not None else 0.0
                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                prices[symbol] = 0.0

        return prices

    def _get_current_price_mock(self, symbol: str) -> Optional[float]:
        """
        Get mock price from JSON data with slight randomization
        """
        mock_data = self._load_mock_market_data()
        stock_prices = mock_data.get('stock_prices', {})

        if symbol in stock_prices:
            base_price = stock_prices[symbol].get('current_price', 0)
            # Add slight random variation (±2%) to simulate real-time changes
            variation = base_price * random.uniform(-0.02, 0.02)
            price = base_price + variation
            logger.info(f"Mock price for {symbol}: ₹{price:.2f}")
            return float(price)

        logger.warning(f"No mock price data found for {symbol}")
        return None

    def _get_current_price_alphavantage(self, symbol: str) -> Optional[float]:
        try:
            # Remove .NS suffix for Alpha Vantage
            av_symbol = symbol.replace('.NS', '')

            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol,
                'apikey': self.alpha_vantage_api_key
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if 'Global Quote' in data:
                price = data['Global Quote'].get('05. price')
                if price:
                    logger.info(f"Fetched price from Alpha Vantage for {symbol}: {price}")
                    return float(price)

        except Exception as e:
            logger.error(f"Alpha Vantage error for {symbol}: {e}")

        return None

    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Generate mock historical data based on current price from JSON
        """
        try:
            mock_data = self._load_mock_market_data()
            stock_prices = mock_data.get('stock_prices', {})

            base_price = 1000  # fallback
            if symbol in stock_prices:
                base_price = stock_prices[symbol].get('current_price', 1000)

            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')

            # Generate mock OHLCV data
            data = []
            for i, date in enumerate(dates):
                # Create price trend around base price
                price_trend = base_price + (i - 15) * random.uniform(-2, 2)
                daily_volatility = base_price * 0.02  # 2% daily volatility

                open_price = price_trend + random.uniform(-daily_volatility, daily_volatility)
                high_price = open_price + random.uniform(0, daily_volatility)
                low_price = open_price - random.uniform(0, daily_volatility)
                close_price = open_price + random.uniform(-daily_volatility/2, daily_volatility/2)

                data.append({
                    'Date': date,
                    'Open': max(0, open_price),
                    'High': max(0, high_price),
                    'Low': max(0, low_price),
                    'Close': max(0, close_price),
                    'Volume': random.randint(1000000, 5000000)
                })

            hist_data = pd.DataFrame(data).set_index('Date')

            # Calculate basic technical indicators
            hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
            hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
            hist_data['RSI'] = self._calculate_rsi(hist_data['Close'])

            logger.info(f"Generated mock historical data for {symbol}: {len(hist_data)} days")
            return hist_data

        except Exception as e:
            logger.error(f"Error generating historical data for {symbol}: {e}")

        return None

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_market_summary(self, symbols: List[str]) -> Dict:
        """
        Get comprehensive market summary from JSON data
        """
        mock_data = self._load_mock_market_data()

        summary = {
            'market_status': mock_data.get('market_status', 'open'),
            'timestamp': datetime.now().isoformat(),
            'prices': {}
        }

        # Get current prices with slight randomization
        stock_prices = mock_data.get('stock_prices', {})
        technical_data = mock_data.get('technical_indicators', {})

        for symbol in symbols:
            if symbol in stock_prices:
                base_price = stock_prices[symbol].get('current_price', 0)
                variation = base_price * random.uniform(-0.02, 0.02)
                summary['prices'][symbol] = base_price + variation

            # Add technical indicators
            if symbol in technical_data:
                tech_info = technical_data[symbol].copy()
                # Add slight randomization to technical indicators
                for key, value in tech_info.items():
                    if isinstance(value, (int, float)):
                        variation = value * random.uniform(-0.01, 0.01)
                        tech_info[key] = value + variation

                summary[f"{symbol}_technical"] = tech_info

        return summary

    def _get_market_status(self) -> str:
        """
        Simple market hours check for NSE (9:15 AM - 3:30 PM IST)
        """
        try:
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)

            if current_time.weekday() >= 5:  # Weekend
                return "closed"

            market_open = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
            market_close = current_time.replace(hour=15, minute=30, second=0, microsecond=0)

            if market_open <= current_time <= market_close:
                return "open"
            else:
                return "closed"
        except ImportError:
            # If pytz is not available, assume market is open for testing
            return "open"

    def _is_cached(self, key: str) -> bool:
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return True
        return False
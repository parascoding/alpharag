import requests
import pandas as pd
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
        # Mock prices for testing - replace with real API later
        mock_prices = {
            'RELIANCE.NS': 2500.00 + random.uniform(-50, 50),
            'TCS.NS': 3700.00 + random.uniform(-100, 100),
            'INFY.NS': 1550.00 + random.uniform(-30, 30)
        }
        
        if symbol in mock_prices:
            price = mock_prices[symbol]
            logger.info(f"Mock price for {symbol}: {price}")
            return float(price)
        
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
        # Mock historical data for testing
        try:
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            base_price = {
                'RELIANCE.NS': 2500,
                'TCS.NS': 3700,
                'INFY.NS': 1550
            }.get(symbol, 1000)
            
            # Generate mock OHLCV data
            data = []
            for i, date in enumerate(dates):
                price = base_price + random.uniform(-100, 100)
                data.append({
                    'Date': date,
                    'Open': price + random.uniform(-10, 10),
                    'High': price + random.uniform(0, 20),
                    'Low': price - random.uniform(0, 20),
                    'Close': price,
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
        summary = {
            'prices': self.get_current_prices(symbols),
            'market_status': self._get_market_status(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add basic technical analysis
        for symbol in symbols:
            hist_data = self.get_historical_data(symbol, "1mo")
            if hist_data is not None and not hist_data.empty:
                latest = hist_data.iloc[-1]
                summary[f'{symbol}_technical'] = {
                    'current_price': float(latest['Close']),
                    'sma_5': float(latest['SMA_5']) if pd.notna(latest['SMA_5']) else None,
                    'sma_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None,
                    'rsi': float(latest['RSI']) if pd.notna(latest['RSI']) else None,
                    'volume': int(latest['Volume']),
                    'high_52w': float(hist_data['High'].max()),
                    'low_52w': float(hist_data['Low'].min())
                }
        
        return summary
    
    def _get_market_status(self) -> str:
        # Simple market hours check for NSE (9:15 AM - 3:30 PM IST)
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
    
    def _is_cached(self, key: str) -> bool:
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return True
        return False
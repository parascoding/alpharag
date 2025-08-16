"""
Mock data provider implementation - uses existing mock data
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import random
from datetime import datetime, timedelta
import logging

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)

class MockProvider(BaseDataProvider):
    """
    Mock implementation using existing JSON mock data
    This ensures we can test the provider architecture with known data
    """
    
    def __init__(self, **kwargs):
        super().__init__("mock", **kwargs)
        self.mock_data = self._load_mock_data()
        
    def _load_mock_data(self) -> Dict:
        """Load mock data from JSON file"""
        try:
            mock_data_path = Path(__file__).parent.parent.parent / 'mock_data' / 'market_data.json'
            
            if not mock_data_path.exists():
                self.logger.warning(f"Mock data file not found: {mock_data_path}")
                return self._get_fallback_data()
            
            with open(mock_data_path, 'r') as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded mock data from {mock_data_path}")
            return data['market_data']
            
        except Exception as e:
            self.logger.error(f"Error loading mock data: {e}")
            return self._get_fallback_data()
    
    def _get_fallback_data(self) -> Dict:
        """Fallback data if JSON is not available"""
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
            'company_info': {
                'RELIANCE.NS': {
                    'name': 'Reliance Industries Limited',
                    'sector': 'Energy',
                    'industry': 'Oil & Gas Refining & Marketing',
                    'market_cap': 1800000000000
                },
                'TCS.NS': {
                    'name': 'Tata Consultancy Services Limited',
                    'sector': 'Technology',
                    'industry': 'Information Technology Services',
                    'market_cap': 1400000000000
                },
                'INFY.NS': {
                    'name': 'Infosys Limited',
                    'sector': 'Technology', 
                    'industry': 'Information Technology Services',
                    'market_cap': 650000000000
                }
            }
        }
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price with slight randomization"""
        try:
            stock_prices = self.mock_data.get('stock_prices', {})
            
            if symbol in stock_prices:
                base_price = stock_prices[symbol].get('current_price', 0)
                # Add slight random variation (±2%) to simulate real-time changes
                variation = base_price * random.uniform(-0.02, 0.02)
                price = base_price + variation
                
                self.logger.info(f"Mock price for {symbol}: ₹{price:.2f}")
                return float(price)
            
            self.logger.warning(f"No price data found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols"""
        prices = {}
        
        self.logger.info(f"Fetching mock prices for {len(symbols)} symbols")
        
        for symbol in symbols:
            price = self.get_current_price(symbol)
            prices[symbol] = price if price is not None else 0.0
        
        successful = len([p for p in prices.values() if p > 0])
        self.logger.info(f"Successfully fetched {successful}/{len(symbols)} mock prices")
        return prices
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """Generate mock historical data"""
        try:
            # Get base price
            base_price = 1000  # fallback
            stock_prices = self.mock_data.get('stock_prices', {})
            if symbol in stock_prices:
                base_price = stock_prices[symbol].get('current_price', 1000)
            
            # Generate date range
            days = 30 if period == "1mo" else 90
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
            
            # Generate mock OHLCV data
            data = []
            for i, date in enumerate(dates):
                # Create price trend around base price
                price_trend = base_price + (i - days/2) * random.uniform(-2, 2)
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
            
            # Calculate technical indicators
            hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
            hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
            hist_data['RSI'] = self._calculate_rsi(hist_data['Close'])
            
            self.logger.info(f"Generated mock historical data for {symbol}: {len(hist_data)} days")
            return hist_data
            
        except Exception as e:
            self.logger.error(f"Error generating historical data for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get mock company information"""
        try:
            # Use fallback company data since it's not in the JSON
            fallback_data = self._get_fallback_data()
            company_data = fallback_data.get('company_info', {})
            
            if symbol in company_data:
                info = company_data[symbol].copy()
                info.update({
                    'symbol': symbol,
                    'pe_ratio': random.uniform(15, 30),
                    'dividend_yield': random.uniform(0.5, 3.0),
                    'beta': random.uniform(0.8, 1.5),
                    'currency': 'INR',
                    'exchange': 'NSI',
                    'timestamp': datetime.now().isoformat()
                })
                
                self.logger.info(f"Mock company info for {symbol}: {info['name']}")
                return info
            
            self.logger.warning(f"No company info found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting company info for {symbol}: {e}")
            return None
    
    def is_available(self) -> bool:
        """Mock provider is always available"""
        return True
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
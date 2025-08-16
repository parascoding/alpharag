"""
Alpha Vantage data provider implementation
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import time
from datetime import datetime, timedelta
import logging

from .base_provider import BaseDataProvider

logger = logging.getLogger(__name__)

class AlphaVantageProvider(BaseDataProvider):
    """
    Alpha Vantage implementation of the data provider interface
    Supports both US and international markets including Indian stocks
    """
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__("alpha_vantage", **kwargs)
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = kwargs.get('rate_limit_delay', 12)  # 5 calls per minute for free tier
        self.timeout = kwargs.get('timeout', 10)
        self.last_request_time = 0
        
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required")
    
    def _make_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """
        Make a rate-limited request to Alpha Vantage API
        """
        try:
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                self.logger.info(f"Rate limiting: sleeping for {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            # Add API key to params
            params['apikey'] = self.api_key
            
            self.logger.info(f"Making Alpha Vantage request: {params.get('function', 'unknown')}")
            response = requests.get(self.base_url, params=params, timeout=self.timeout)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    self.logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                    
                if 'Note' in data:
                    self.logger.warning(f"Alpha Vantage API note: {data['Note']}")
                    return None
                
                return data
            else:
                self.logger.error(f"HTTP error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Request failed: {e}")
            return None
    
    def _convert_symbol(self, symbol: str) -> str:
        """
        Convert symbol format for Alpha Vantage
        Indian stocks: RELIANCE.NS -> RELIANCE.BSE or handle specially
        """
        if symbol.endswith('.NS'):
            # For NSE stocks, we need to use different approach
            # Alpha Vantage has limited Indian stock coverage
            base_symbol = symbol.replace('.NS', '')
            return f"{base_symbol}.BSE"  # Try BSE format
        elif symbol.endswith('.BO'):
            return symbol  # Already in correct format
        else:
            return symbol  # US stocks or other formats
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a single symbol using Global Quote
        """
        try:
            av_symbol = self._convert_symbol(symbol)
            self.logger.info(f"Fetching current price for {symbol} (as {av_symbol})")
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': av_symbol
            }
            
            data = self._make_request(params)
            if data and 'Global Quote' in data:
                quote = data['Global Quote']
                price = quote.get('05. price')
                
                if price:
                    price_float = float(price)
                    self.logger.info(f"✅ Current price for {symbol}: ${price_float:.2f}")
                    
                    # For Indian stocks, convert USD to INR (approximate)
                    if symbol.endswith('.NS') or symbol.endswith('.BO'):
                        # Rough conversion - in production, you'd get real exchange rates
                        price_inr = price_float * 83  # Approximate USD to INR
                        self.logger.info(f"✅ Converted to INR: ₹{price_inr:.2f}")
                        return price_inr
                    
                    return price_float
                    
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
            
            # Rate limiting between requests
            if len(symbols) > 1:
                time.sleep(1)  # Additional delay for multiple requests
        
        successful = len([p for p in prices.values() if p > 0])
        self.logger.info(f"Successfully fetched {successful}/{len(symbols)} prices from Alpha Vantage")
        return prices
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical data using TIME_SERIES_DAILY
        """
        try:
            av_symbol = self._convert_symbol(symbol)
            self.logger.info(f"Fetching historical data for {symbol} (as {av_symbol}), period: {period}")
            
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': av_symbol,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            data = self._make_request(params)
            if data and 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                
                # Convert to DataFrame
                df_data = []
                for date_str, values in time_series.items():
                    df_data.append({
                        'Date': pd.to_datetime(date_str),
                        'Open': float(values['1. open']),
                        'High': float(values['2. high']),
                        'Low': float(values['3. low']),
                        'Close': float(values['4. close']),
                        'Volume': int(values['5. volume'])
                    })
                
                hist_data = pd.DataFrame(df_data).set_index('Date').sort_index()
                
                # For Indian stocks, convert to INR
                if symbol.endswith('.NS') or symbol.endswith('.BO'):
                    for col in ['Open', 'High', 'Low', 'Close']:
                        hist_data[col] = hist_data[col] * 83  # USD to INR conversion
                
                # Calculate technical indicators
                hist_data['SMA_5'] = hist_data['Close'].rolling(window=5).mean()
                hist_data['SMA_20'] = hist_data['Close'].rolling(window=20).mean()
                hist_data['RSI'] = self._calculate_rsi(hist_data['Close'])
                
                # Filter by period
                if period == "1mo":
                    cutoff_date = datetime.now() - timedelta(days=30)
                    hist_data = hist_data[hist_data.index >= cutoff_date]
                
                self.logger.info(f"✅ Historical data for {symbol}: {len(hist_data)} days")
                return hist_data
                
            self.logger.warning(f"No historical data found for {symbol}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company overview information
        """
        try:
            av_symbol = self._convert_symbol(symbol)
            self.logger.info(f"Fetching company info for {symbol} (as {av_symbol})")
            
            params = {
                'function': 'OVERVIEW',
                'symbol': av_symbol
            }
            
            data = self._make_request(params)
            if data and data.get('Symbol'):
                # Extract key information
                company_info = {
                    'symbol': symbol,
                    'name': data.get('Name', 'N/A'),
                    'sector': data.get('Sector', 'N/A'),
                    'industry': data.get('Industry', 'N/A'),
                    'market_cap': self._safe_float(data.get('MarketCapitalization', 0)),
                    'pe_ratio': self._safe_float(data.get('PERatio', 0)),
                    'dividend_yield': self._safe_float(data.get('DividendYield', 0)),
                    'beta': self._safe_float(data.get('Beta', 0)),
                    'fifty_two_week_high': self._safe_float(data.get('52WeekHigh', 0)),
                    'fifty_two_week_low': self._safe_float(data.get('52WeekLow', 0)),
                    'currency': data.get('Currency', 'USD'),
                    'exchange': data.get('Exchange', 'NASDAQ'),
                    'country': data.get('Country', 'N/A'),
                    'description': data.get('Description', 'N/A')[:200] + '...' if data.get('Description') else 'N/A',
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
        """
        Check if Alpha Vantage API is available
        """
        try:
            # Test with a simple request
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'AAPL'  # Use a reliable US stock for testing
            }
            
            data = self._make_request(params)
            available = data is not None and 'Global Quote' in data
            
            self.logger.info(f"Alpha Vantage availability check: {'✅ Available' if available else '❌ Not available'}")
            return available
            
        except Exception as e:
            self.logger.error(f"Alpha Vantage availability check failed: {e}")
            return False
    
    def _safe_float(self, value: str) -> float:
        """Safely convert string to float"""
        try:
            if value == 'None' or value == '-':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
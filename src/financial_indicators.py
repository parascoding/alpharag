#!/usr/bin/env python3
"""
Financial Indicators Module for AlphaRAG
Provides comprehensive fundamental analysis with mock-first approach and real API migration capability
"""

import requests
import random
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import time

logger = logging.getLogger(__name__)

class FinancialIndicatorsFetcher:
    def __init__(self, alpha_vantage_api_key: Optional[str] = None, use_real_apis: bool = False):
        """
        Initialize Financial Indicators Fetcher
        
        Args:
            alpha_vantage_api_key: API key for Alpha Vantage (optional)
            use_real_apis: Flag to switch between mock data and real APIs
        """
        self.alpha_vantage_api_key = alpha_vantage_api_key
        self.use_real_apis = use_real_apis
        self.cache = {}
        self.cache_timeout = 86400  # 24 hours for financial data
        
        # Log the mode
        mode = "REAL APIs" if use_real_apis and alpha_vantage_api_key else "MOCK data"
        logger.info(f"Financial Indicators initialized in {mode} mode")
    
    def get_financial_indicators(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get comprehensive financial indicators for given symbols
        
        Args:
            symbols: List of stock symbols (e.g., ['RELIANCE.NS', 'TCS.NS'])
            
        Returns:
            Dictionary mapping symbols to their financial indicators
        """
        financial_data = {}
        
        for symbol in symbols:
            try:
                if self.use_real_apis and self.alpha_vantage_api_key:
                    # Try real API first, fallback to mock if fails
                    indicators = self._get_real_financial_data(symbol)
                    if not indicators:
                        logger.error(f"Real API FAILED for {symbol} - FALLING BACK TO MOCK DATA - Alpha Vantage not working")
                        indicators = self._generate_mock_financial_data(symbol)
                else:
                    # Use mock data
                    logger.error(f"Using MOCK financial data for {symbol} - Real APIs not configured")
                    indicators = self._generate_mock_financial_data(symbol)
                
                if indicators:
                    indicators['symbol'] = symbol
                    indicators['last_updated'] = datetime.now().isoformat()
                    financial_data[symbol] = indicators
                    logger.info(f"Retrieved financial data for {symbol}")
                else:
                    logger.warning(f"No financial data available for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error getting financial indicators for {symbol}: {e}")
                continue
        
        return financial_data
    
    def _load_mock_data_from_json(self) -> Dict[str, Any]:
        """
        Load mock financial data from JSON file
        """
        try:
            mock_data_path = Path(__file__).parent.parent / 'mock_data' / 'financial_indicators.json'
            
            if not mock_data_path.exists():
                logger.warning(f"Mock data file not found: {mock_data_path}. Using fallback data.")
                return self._generate_fallback_mock_data()
            
            with open(mock_data_path, 'r') as f:
                data = json.load(f)
            
            logger.error(f"Using MOCK financial data from {mock_data_path} - Real APIs not available")
            return data['financial_indicators']
            
        except Exception as e:
            logger.error(f"Error loading mock data from JSON: {e}")
            return self._generate_fallback_mock_data()
    
    def _generate_fallback_mock_data(self) -> Dict[str, Any]:
        """
        Generate basic mock financial data as fallback
        """
        return {
            'RELIANCE.NS': {
                'sector': 'Oil & Gas',
                'market_cap_cr': 1950000,
                'pe_ratio': 22.4, 'pb_ratio': 1.8, 'roe': 12.8,
                'debt_to_equity': 0.65, 'current_ratio': 1.45,
                'revenue_growth_yoy': 8.4, 'dividend_yield': 0.8
            },
            'TCS.NS': {
                'sector': 'IT Services', 
                'market_cap_cr': 1350000,
                'pe_ratio': 28.5, 'pb_ratio': 12.4, 'roe': 42.8,
                'debt_to_equity': 0.01, 'current_ratio': 3.2,
                'revenue_growth_yoy': 16.8, 'dividend_yield': 2.1
            },
            'INFY.NS': {
                'sector': 'IT Services',
                'market_cap_cr': 750000, 
                'pe_ratio': 26.1, 'pb_ratio': 8.9, 'roe': 31.4,
                'debt_to_equity': 0.02, 'current_ratio': 2.8,
                'revenue_growth_yoy': 19.7, 'dividend_yield': 2.8
            }
        }
    
    def _generate_mock_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Generate mock financial data - now loads from JSON file
        """
        mock_data = self._load_mock_data_from_json()
        
        if symbol not in mock_data:
            logger.warning(f"No mock data found for {symbol}")
            return {}
        
        # Get base data from JSON
        base_data = mock_data[symbol].copy()
        
        # Flatten the nested structure from JSON
        financial_data = {
            'symbol': symbol,
            'sector': base_data.get('sector', 'Unknown'),
            'market_cap_cr': base_data.get('market_cap_cr', 0),
            'data_source': 'mock'
        }
        
        # Add all metrics from nested categories
        for category in ['valuation_metrics', 'profitability_metrics', 
                        'financial_health', 'growth_metrics', 
                        'dividend_metrics', 'efficiency_metrics']:
            if category in base_data:
                financial_data.update(base_data[category])
        
        # Add slight randomization to make data more realistic
        for key, value in financial_data.items():
            if isinstance(value, (int, float)) and key not in ['market_cap_cr', 'symbol']:
                # Add ±5% random variation
                variation = value * random.uniform(-0.05, 0.05)
                financial_data[key] = round(value + variation, 2)
        
        logger.error(f"Using MOCK financial data for {symbol} from JSON - Real APIs failed or not configured")
        return financial_data
    
    def _get_real_financial_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real financial data from Alpha Vantage API
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            
        Returns:
            Dictionary of financial indicators or None if failed
        """
        try:
            # Remove .NS suffix for Alpha Vantage API (they use different format)
            api_symbol = symbol.replace('.NS', '.BSE') if '.NS' in symbol else symbol
            
            # Try company overview first
            overview_url = f"https://www.alphavantage.co/query"
            overview_params = {
                'function': 'OVERVIEW',
                'symbol': api_symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = requests.get(overview_url, params=overview_params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Symbol' not in data or not data.get('Symbol'):
                logger.error(f"No data returned from Alpha Vantage for {symbol}")
                return None
            
            # Parse the financial data
            financial_data = {
                'symbol': symbol,
                'sector': data.get('Sector', 'Unknown'),
                'market_cap_cr': self._safe_float(data.get('MarketCapitalization', 0)) / 10000000,  # Convert to crores
                'pe_ratio': self._safe_float(data.get('PERatio')),
                'pb_ratio': self._safe_float(data.get('PriceToBookRatio')),
                'ps_ratio': self._safe_float(data.get('PriceToSalesRatioTTM')),
                'ev_ebitda': self._safe_float(data.get('EVToEBITDA')),
                'roe': self._safe_float(data.get('ReturnOnEquityTTM')) * 100,  # Convert to percentage
                'roa': self._safe_float(data.get('ReturnOnAssetsTTM')) * 100,
                'gross_margin': self._safe_float(data.get('GrossProfitTTM')),
                'operating_margin': self._safe_float(data.get('OperatingMarginTTM')) * 100,
                'net_profit_margin': self._safe_float(data.get('ProfitMargin')) * 100,
                'debt_to_equity': self._safe_float(data.get('DebtToEquity')),
                'current_ratio': self._safe_float(data.get('CurrentRatio')),
                'quick_ratio': self._safe_float(data.get('QuickRatio')),
                'revenue_growth_yoy': self._safe_float(data.get('QuarterlyRevenueGrowthYOY')) * 100,
                'earnings_growth_yoy': self._safe_float(data.get('QuarterlyEarningsGrowthYOY')) * 100,
                'dividend_yield': self._safe_float(data.get('DividendYield')) * 100,
                'dividend_payout_ratio': self._safe_float(data.get('PayoutRatio')) * 100,
                'data_source': 'alpha_vantage'
            }
            
            logger.info(f"Successfully fetched real financial data for {symbol}")
            return financial_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching financial data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing financial data for {symbol}: {e}")
            return None
    
    def _safe_float(self, value: Any) -> float:
        """
        Safely convert value to float, return 0 if conversion fails
        """
        try:
            if value is None or value == 'None' or value == '':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def calculate_financial_health_score(self, financial_data: Dict) -> Dict[str, Any]:
        """
        Calculate an overall financial health score based on key metrics
        """
        scores = {}
        
        # Valuation Score (lower P/E and P/B are generally better)
        pe_score = max(0, min(10, 10 - (financial_data.get('pe_ratio', 20) - 15) * 0.5))
        pb_score = max(0, min(10, 10 - (financial_data.get('pb_ratio', 3) - 2) * 2))
        scores['valuation_score'] = (pe_score + pb_score) / 2
        
        # Profitability Score (higher is better)
        roe_score = min(10, financial_data.get('roe', 0) * 0.4)
        margin_score = min(10, financial_data.get('net_profit_margin', 0) * 0.5)
        scores['profitability_score'] = (roe_score + margin_score) / 2
        
        # Financial Health Score (lower debt, higher ratios are better)
        debt_score = max(0, min(10, 10 - financial_data.get('debt_to_equity', 0) * 10))
        liquidity_score = min(10, financial_data.get('current_ratio', 1) * 4)
        scores['financial_health_score'] = (debt_score + liquidity_score) / 2
        
        # Growth Score (higher growth is better, but capped)
        revenue_growth_score = max(0, min(10, financial_data.get('revenue_growth_yoy', 0) * 0.3))
        earnings_growth_score = max(0, min(10, financial_data.get('earnings_growth_yoy', 0) * 0.25))
        scores['growth_score'] = (revenue_growth_score + earnings_growth_score) / 2
        
        # Overall Score (weighted average)
        overall_score = (
            scores['valuation_score'] * 0.25 +
            scores['profitability_score'] * 0.35 +
            scores['financial_health_score'] * 0.25 +
            scores['growth_score'] * 0.15
        )
        
        # Rating system
        if overall_score >= 8:
            rating = "EXCELLENT"
            rating_emoji = "🟢"
        elif overall_score >= 7:
            rating = "GOOD" 
            rating_emoji = "🟢"
        elif overall_score >= 6:
            rating = "FAIR"
            rating_emoji = "🟡"
        elif overall_score >= 4:
            rating = "POOR"
            rating_emoji = "🟠"
        else:
            rating = "VERY POOR"
            rating_emoji = "🔴"
        
        scores.update({
            'overall_score': round(overall_score, 1),
            'rating': rating,
            'rating_emoji': rating_emoji
        })
        
        return scores
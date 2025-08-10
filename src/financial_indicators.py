#!/usr/bin/env python3
"""
Financial Indicators Module for AlphaRAG
Provides comprehensive fundamental analysis with mock-first approach and real API migration capability
"""

import requests
import random
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
                        logger.warning(f"Real API failed for {symbol}, using mock data")
                        indicators = self._get_mock_financial_data(symbol)
                else:
                    # Use mock data
                    indicators = self._get_mock_financial_data(symbol)
                
                financial_data[symbol] = indicators
                time.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching financial data for {symbol}: {e}")
                # Always fallback to mock data on error
                financial_data[symbol] = self._get_mock_financial_data(symbol)
        
        return financial_data
    
    def _get_mock_financial_data(self, symbol: str) -> Dict[str, Any]:
        """
        Generate realistic mock financial data based on Indian market characteristics
        """
        # Base financial data by sector
        base_data = {
            'RELIANCE.NS': {
                # Oil & Gas sector characteristics
                'sector': 'Oil & Gas',
                'market_cap_cr': 1850000 + random.uniform(-50000, 100000),  # ~18.5 lakh crore
                'pe_ratio': 15.2 + random.uniform(-2, 2),
                'pb_ratio': 1.8 + random.uniform(-0.3, 0.3),
                'ps_ratio': 1.2 + random.uniform(-0.2, 0.3),
                'ev_ebitda': 8.5 + random.uniform(-1, 1.5),
                'peg_ratio': 1.1 + random.uniform(-0.2, 0.3),
                
                # Profitability ratios
                'roe': 12.5 + random.uniform(-2, 3),  # Return on Equity
                'roa': 6.8 + random.uniform(-1, 1.5),  # Return on Assets
                'roic': 9.2 + random.uniform(-1.5, 2),  # Return on Invested Capital
                'gross_margin': 45.2 + random.uniform(-3, 5),
                'operating_margin': 12.8 + random.uniform(-2, 3),
                'net_profit_margin': 8.2 + random.uniform(-1, 2),
                
                # Financial health
                'debt_to_equity': 0.45 + random.uniform(-0.05, 0.10),
                'current_ratio': 1.2 + random.uniform(-0.1, 0.2),
                'quick_ratio': 0.95 + random.uniform(-0.1, 0.15),
                'interest_coverage': 4.2 + random.uniform(-0.5, 1),
                'asset_turnover': 0.85 + random.uniform(-0.1, 0.2),
                
                # Growth indicators
                'revenue_growth_yoy': 8.5 + random.uniform(-3, 5),
                'earnings_growth_yoy': 12.1 + random.uniform(-4, 8),
                'book_value_growth_yoy': 6.8 + random.uniform(-2, 4),
                
                # Dividend metrics
                'dividend_yield': 0.5 + random.uniform(-0.1, 0.2),
                'dividend_payout_ratio': 6.5 + random.uniform(-1, 2),
                'dividend_coverage_ratio': 15.4 + random.uniform(-2, 4)
            },
            
            'TCS.NS': {
                # IT Services sector characteristics
                'sector': 'IT Services',
                'market_cap_cr': 1250000 + random.uniform(-30000, 80000),  # ~12.5 lakh crore
                'pe_ratio': 28.5 + random.uniform(-3, 4),
                'pb_ratio': 12.4 + random.uniform(-1.5, 2),
                'ps_ratio': 6.8 + random.uniform(-0.8, 1.2),
                'ev_ebitda': 18.2 + random.uniform(-2, 3),
                'peg_ratio': 1.8 + random.uniform(-0.3, 0.5),
                
                # Profitability ratios (IT services typically higher)
                'roe': 35.2 + random.uniform(-3, 5),
                'roa': 28.5 + random.uniform(-2, 4),
                'roic': 42.1 + random.uniform(-4, 6),
                'gross_margin': 68.5 + random.uniform(-2, 4),
                'operating_margin': 25.8 + random.uniform(-2, 3),
                'net_profit_margin': 21.8 + random.uniform(-2, 3),
                
                # Financial health (IT services typically very healthy)
                'debt_to_equity': 0.05 + random.uniform(0, 0.05),  # Very low debt
                'current_ratio': 2.1 + random.uniform(-0.2, 0.4),
                'quick_ratio': 1.95 + random.uniform(-0.2, 0.3),
                'interest_coverage': 45.2 + random.uniform(-5, 10),  # Very high
                'asset_turnover': 1.35 + random.uniform(-0.15, 0.25),
                
                # Growth indicators
                'revenue_growth_yoy': 12.1 + random.uniform(-2, 6),
                'earnings_growth_yoy': 15.8 + random.uniform(-3, 8),
                'book_value_growth_yoy': 18.2 + random.uniform(-2, 6),
                
                # Dividend metrics
                'dividend_yield': 3.2 + random.uniform(-0.3, 0.5),
                'dividend_payout_ratio': 35.8 + random.uniform(-3, 5),
                'dividend_coverage_ratio': 2.8 + random.uniform(-0.3, 0.5)
            },
            
            'INFY.NS': {
                # IT Services sector (similar to TCS but with variations)
                'sector': 'IT Services',
                'market_cap_cr': 650000 + random.uniform(-20000, 50000),  # ~6.5 lakh crore
                'pe_ratio': 24.8 + random.uniform(-2, 3),
                'pb_ratio': 8.9 + random.uniform(-1, 1.5),
                'ps_ratio': 5.2 + random.uniform(-0.5, 0.8),
                'ev_ebitda': 16.8 + random.uniform(-1.5, 2.5),
                'peg_ratio': 1.5 + random.uniform(-0.2, 0.4),
                
                # Profitability ratios
                'roe': 28.9 + random.uniform(-2, 4),
                'roa': 25.2 + random.uniform(-2, 3),
                'roic': 38.5 + random.uniform(-3, 5),
                'gross_margin': 65.8 + random.uniform(-2, 4),
                'operating_margin': 22.5 + random.uniform(-1.5, 2.5),
                'net_profit_margin': 19.5 + random.uniform(-1.5, 2.5),
                
                # Financial health
                'debt_to_equity': 0.08 + random.uniform(0, 0.07),
                'current_ratio': 3.2 + random.uniform(-0.3, 0.5),
                'quick_ratio': 2.95 + random.uniform(-0.2, 0.4),
                'interest_coverage': 52.1 + random.uniform(-5, 12),
                'asset_turnover': 1.28 + random.uniform(-0.12, 0.20),
                
                # Growth indicators
                'revenue_growth_yoy': 15.2 + random.uniform(-3, 7),
                'earnings_growth_yoy': 18.5 + random.uniform(-4, 9),
                'book_value_growth_yoy': 16.8 + random.uniform(-2, 5),
                
                # Dividend metrics
                'dividend_yield': 2.8 + random.uniform(-0.2, 0.4),
                'dividend_payout_ratio': 28.5 + random.uniform(-2, 4),
                'dividend_coverage_ratio': 3.5 + random.uniform(-0.4, 0.6)
            }
        }
        
        # Get base data for symbol, or create generic data if not found
        if symbol in base_data:
            data = base_data[symbol].copy()
        else:
            # Generic company data for unknown symbols
            data = {
                'sector': 'Unknown',
                'market_cap_cr': 50000 + random.uniform(-10000, 20000),
                'pe_ratio': 20.0 + random.uniform(-5, 8),
                'pb_ratio': 3.5 + random.uniform(-1, 2),
                'ps_ratio': 2.8 + random.uniform(-0.5, 1),
                'ev_ebitda': 12.0 + random.uniform(-2, 4),
                'peg_ratio': 1.5 + random.uniform(-0.5, 0.8),
                'roe': 18.0 + random.uniform(-5, 8),
                'roa': 12.0 + random.uniform(-3, 5),
                'roic': 15.0 + random.uniform(-4, 6),
                'gross_margin': 40.0 + random.uniform(-5, 10),
                'operating_margin': 15.0 + random.uniform(-3, 5),
                'net_profit_margin': 12.0 + random.uniform(-2, 4),
                'debt_to_equity': 0.6 + random.uniform(-0.2, 0.4),
                'current_ratio': 1.5 + random.uniform(-0.3, 0.5),
                'quick_ratio': 1.2 + random.uniform(-0.2, 0.3),
                'interest_coverage': 8.0 + random.uniform(-2, 4),
                'asset_turnover': 1.0 + random.uniform(-0.2, 0.3),
                'revenue_growth_yoy': 10.0 + random.uniform(-5, 10),
                'earnings_growth_yoy': 12.0 + random.uniform(-6, 12),
                'book_value_growth_yoy': 8.0 + random.uniform(-3, 6),
                'dividend_yield': 2.0 + random.uniform(-0.5, 1),
                'dividend_payout_ratio': 25.0 + random.uniform(-5, 10),
                'dividend_coverage_ratio': 4.0 + random.uniform(-1, 2)
            }
        
        # Add metadata
        data.update({
            'symbol': symbol,
            'data_source': 'mock',
            'last_updated': datetime.now().isoformat(),
            'currency': 'INR'
        })
        
        logger.info(f"Generated mock financial data for {symbol} ({data.get('sector', 'Unknown')} sector)")
        return data
    
    def _get_real_financial_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch real financial data from Alpha Vantage API
        This method is prepared for future implementation
        """
        try:
            # Check cache first
            cache_key = f"financial_{symbol}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            # Remove .NS suffix for Alpha Vantage
            av_symbol = symbol.replace('.NS', '')
            
            # Alpha Vantage Overview endpoint
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': av_symbol,
                'apikey': self.alpha_vantage_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'Symbol' in data and data['Symbol']:
                # Parse Alpha Vantage data into our format
                financial_data = self._parse_alpha_vantage_data(data, symbol)
                
                # Cache the result
                self.cache[cache_key] = {
                    'data': financial_data,
                    'timestamp': datetime.now()
                }
                
                logger.info(f"Fetched real financial data for {symbol} from Alpha Vantage")
                return financial_data
            else:
                logger.warning(f"No data returned from Alpha Vantage for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching real financial data for {symbol}: {e}")
            return None
    
    def _parse_alpha_vantage_data(self, av_data: Dict, symbol: str) -> Dict[str, Any]:
        """
        Parse Alpha Vantage API response into our standardized format
        """
        def safe_float(value, default=0.0):
            try:
                return float(value) if value and value != 'None' and value != '-' else default
            except (ValueError, TypeError):
                return default
        
        def safe_percentage(value, default=0.0):
            try:
                if value and value != 'None' and value != '-':
                    # Remove % sign if present and convert
                    clean_value = str(value).replace('%', '')
                    return float(clean_value)
                return default
            except (ValueError, TypeError):
                return default
        
        return {
            'symbol': symbol,
            'sector': av_data.get('Sector', 'Unknown'),
            'market_cap_cr': safe_float(av_data.get('MarketCapitalization', 0)) / 10000000,  # Convert to crores
            
            # Valuation ratios
            'pe_ratio': safe_float(av_data.get('PERatio')),
            'pb_ratio': safe_float(av_data.get('PriceToBookRatio')),
            'ps_ratio': safe_float(av_data.get('PriceToSalesRatioTTM')),
            'ev_ebitda': safe_float(av_data.get('EVToEBITDA')),
            'peg_ratio': safe_float(av_data.get('PEGRatio')),
            
            # Profitability ratios
            'roe': safe_percentage(av_data.get('ReturnOnEquityTTM')),
            'roa': safe_percentage(av_data.get('ReturnOnAssetsTTM')),
            'gross_margin': safe_percentage(av_data.get('GrossProfitTTM')),
            'operating_margin': safe_percentage(av_data.get('OperatingMarginTTM')),
            'net_profit_margin': safe_percentage(av_data.get('ProfitMargin')),
            
            # Financial health
            'debt_to_equity': safe_float(av_data.get('DebtToEquity')),
            'current_ratio': safe_float(av_data.get('CurrentRatio')),
            'quick_ratio': safe_float(av_data.get('QuickRatio')),
            
            # Growth
            'revenue_growth_yoy': safe_percentage(av_data.get('QuarterlyRevenueGrowthYOY')),
            'earnings_growth_yoy': safe_percentage(av_data.get('QuarterlyEarningsGrowthYOY')),
            
            # Dividend
            'dividend_yield': safe_percentage(av_data.get('DividendYield')),
            
            # Metadata
            'data_source': 'alpha_vantage',
            'last_updated': datetime.now().isoformat(),
            'currency': 'INR'
        }
    
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
        
        # Growth Score (higher growth is better, but cap at reasonable levels)
        revenue_growth_score = min(10, max(0, financial_data.get('revenue_growth_yoy', 0) * 0.5))
        earnings_growth_score = min(10, max(0, financial_data.get('earnings_growth_yoy', 0) * 0.4))
        scores['growth_score'] = (revenue_growth_score + earnings_growth_score) / 2
        
        # Overall Score
        overall_score = (
            scores['valuation_score'] * 0.25 +
            scores['profitability_score'] * 0.3 +
            scores['financial_health_score'] * 0.25 +
            scores['growth_score'] * 0.2
        )
        
        scores['overall_score'] = round(overall_score, 1)
        
        # Add interpretation
        if overall_score >= 8.0:
            scores['rating'] = 'EXCELLENT'
            scores['rating_emoji'] = '🌟'
        elif overall_score >= 6.5:
            scores['rating'] = 'GOOD'
            scores['rating_emoji'] = '👍'
        elif overall_score >= 5.0:
            scores['rating'] = 'FAIR'
            scores['rating_emoji'] = '👌'
        elif overall_score >= 3.0:
            scores['rating'] = 'POOR'
            scores['rating_emoji'] = '⚠️'
        else:
            scores['rating'] = 'VERY POOR'
            scores['rating_emoji'] = '🚨'
        
        return scores
    
    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and not expired"""
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return True
        return False
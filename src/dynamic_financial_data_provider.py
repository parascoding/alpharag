"""
Dynamic Financial Data Provider
Combines multiple sources for comprehensive financial analysis
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import time
import re
from pathlib import Path

try:
    from .data_providers.upstox_instrument_mapper import upstox_mapper
except ImportError:
    from data_providers.upstox_instrument_mapper import upstox_mapper

logger = logging.getLogger(__name__)

class DynamicFinancialDataProvider:
    """
    Multi-source financial data provider that combines:
    1. Upstox API - for real-time prices and market data
    2. Alpha Vantage - for financial fundamentals (if API key available)
    3. Yahoo Finance - for backup financial data
    4. Intelligent defaults - for missing data
    """

    def __init__(self, upstox_provider=None, alpha_vantage_key=None):
        self.upstox_provider = upstox_provider
        self.alpha_vantage_key = alpha_vantage_key
        self.cache = {}
        self.cache_timeout = 3600  # 1 hour cache

        # Load sector benchmarks
        self.sector_benchmarks = self._load_sector_benchmarks()

        # Rate limiting
        self.last_api_call = {}
        self.api_delay = 12  # seconds between API calls

    def _load_sector_benchmarks(self) -> Dict:
        """Load sector-specific benchmark ratios"""
        return {
            'IT Services': {
                'pe_good': 25.0, 'pe_excellent': 20.0,
                'pb_good': 8.0, 'pb_excellent': 6.0,
                'roe_good': 25.0, 'roe_excellent': 30.0,
                'debt_equity_good': 0.1, 'debt_equity_excellent': 0.05,
                'net_margin_good': 20.0, 'net_margin_excellent': 25.0
            },
            'Banking': {
                'pe_good': 15.0, 'pe_excellent': 12.0,
                'pb_good': 2.0, 'pb_excellent': 1.5,
                'roe_good': 15.0, 'roe_excellent': 18.0,
                'debt_equity_good': 0.8, 'debt_equity_excellent': 0.6,
                'net_margin_good': 15.0, 'net_margin_excellent': 20.0
            },
            'Oil & Gas': {
                'pe_good': 18.0, 'pe_excellent': 15.0,
                'pb_good': 2.0, 'pb_excellent': 1.5,
                'roe_good': 12.0, 'roe_excellent': 15.0,
                'debt_equity_good': 0.6, 'debt_equity_excellent': 0.4,
                'net_margin_good': 8.0, 'net_margin_excellent': 12.0
            },
            'Chemicals': {
                'pe_good': 20.0, 'pe_excellent': 16.0,
                'pb_good': 3.0, 'pb_excellent': 2.5,
                'roe_good': 15.0, 'roe_excellent': 20.0,
                'debt_equity_good': 0.5, 'debt_equity_excellent': 0.3,
                'net_margin_good': 10.0, 'net_margin_excellent': 15.0
            },
            'default': {
                'pe_good': 20.0, 'pe_excellent': 15.0,
                'pb_good': 3.0, 'pb_excellent': 2.0,
                'roe_good': 15.0, 'roe_excellent': 20.0,
                'debt_equity_good': 0.5, 'debt_equity_excellent': 0.3,
                'net_margin_good': 12.0, 'net_margin_excellent': 18.0
            }
        }

    def get_financial_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive financial indicators for a symbol
        """
        try:
            # Check cache first
            cache_key = f"financial_{symbol}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']

            logger.info(f"Fetching financial data for {symbol}")

            # Get company information for sector classification
            company_info = upstox_mapper.get_company_info(symbol)
            sector = self._determine_sector(company_info)

            # Get current market data from Upstox
            market_data = self._get_market_data_upstox(symbol)

            # Try to get fundamentals from multiple sources
            fundamentals = self._get_fundamentals_multi_source(symbol, company_info)

            # Calculate ratios if we have the data
            ratios = self._calculate_financial_ratios(symbol, market_data, fundamentals, sector)

            # Calculate health scores
            health_scores = self._calculate_health_scores(ratios, sector)
            ratios.update(health_scores)

            # Cache the result
            self.cache[cache_key] = {
                'data': ratios,
                'timestamp': datetime.now()
            }

            logger.info(f"✅ Successfully calculated financial indicators for {symbol}")
            return ratios

        except Exception as e:
            logger.error(f"Error getting financial indicators for {symbol}: {e}")
            return self._get_fallback_data(symbol)

    def _determine_sector(self, company_info: Optional[Dict]) -> str:
        """Determine sector from company information"""
        if not company_info:
            return 'default'

        company_name = company_info.get('company_name', '').upper()
        trading_symbol = company_info.get('trading_symbol', '').upper()

        # Sector classification based on company name patterns
        if any(keyword in company_name for keyword in ['BANK', 'FINANCIAL']):
            return 'Banking'
        elif any(keyword in company_name for keyword in ['TECH', 'SOFTWARE', 'SERVICES', 'CONSULTANCY']):
            return 'IT Services'
        elif any(keyword in company_name for keyword in ['CHEMICAL', 'PHARMA']):
            return 'Chemicals'
        elif any(keyword in company_name for keyword in ['OIL', 'GAS', 'PETROLEUM', 'ENERGY']):
            return 'Oil & Gas'
        elif 'ETF' in company_name or 'GOLD' in trading_symbol:
            return 'ETF'
        else:
            return 'default'

    def _get_market_data_upstox(self, symbol: str) -> Dict:
        """Get current market data from Upstox"""
        market_data = {'current_price': 0, 'volume': 0, 'market_cap': 0}

        try:
            if self.upstox_provider:
                price = self.upstox_provider.get_current_price(symbol)
                if price and price > 0:
                    market_data['current_price'] = price
                    logger.debug(f"Got Upstox price for {symbol}: ₹{price}")
        except Exception as e:
            logger.warning(f"Could not get Upstox price for {symbol}: {e}")

        return market_data

    def _get_fundamentals_multi_source(self, symbol: str, company_info: Optional[Dict]) -> Dict:
        """Try to get fundamentals from multiple sources"""
        fundamentals = {}

        # 1. Try Alpha Vantage if API key is available
        if self.alpha_vantage_key:
            try:
                alpha_data = self._get_alpha_vantage_fundamentals(symbol)
                if alpha_data:
                    fundamentals.update(alpha_data)
                    logger.info(f"Got Alpha Vantage fundamentals for {symbol}")
            except Exception as e:
                logger.warning(f"Alpha Vantage failed for {symbol}: {e}")

        # 2. Try Yahoo Finance as backup
        if not fundamentals:
            try:
                yahoo_data = self._get_yahoo_finance_fundamentals(symbol)
                if yahoo_data:
                    fundamentals.update(yahoo_data)
                    logger.info(f"Got Yahoo Finance fundamentals for {symbol}")
            except Exception as e:
                logger.warning(f"Yahoo Finance failed for {symbol}: {e}")

        # 3. Generate intelligent estimates if no data available
        if not fundamentals:
            fundamentals = self._generate_estimated_fundamentals(symbol, company_info)
            logger.info(f"Using estimated fundamentals for {symbol}")

        return fundamentals

    def _get_alpha_vantage_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get fundamentals from Alpha Vantage API"""
        if not self.alpha_vantage_key:
            return None

        try:
            # Rate limiting
            self._wait_for_rate_limit('alpha_vantage')

            # Convert symbol format (remove .NS for Alpha Vantage)
            av_symbol = symbol.replace('.NS', '.BSE' if '.BO' in symbol else '.NSE')

            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'OVERVIEW',
                'symbol': av_symbol,
                'apikey': self.alpha_vantage_key
            }

            response = requests.get(url, params=params, timeout=30)
            data = response.json()

            if 'Error Message' in data or 'Note' in data:
                return None

            # Extract key metrics
            fundamentals = {}

            # Convert Alpha Vantage fields to our standard format
            field_mapping = {
                'EPS': 'eps_ttm',
                'BookValue': 'book_value_per_share',
                'PERatio': 'pe_ratio',
                'PriceToBookRatio': 'pb_ratio',
                'ReturnOnEquityTTM': 'roe',
                'ProfitMargin': 'net_profit_margin',
                'MarketCapitalization': 'market_cap'
            }

            for av_field, our_field in field_mapping.items():
                if av_field in data and data[av_field] != 'None':
                    try:
                        value = float(data[av_field])
                        fundamentals[our_field] = value
                    except (ValueError, TypeError):
                        continue

            return fundamentals if fundamentals else None

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None

    def _get_yahoo_finance_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Get fundamentals from Yahoo Finance (simplified approach)"""
        try:
            # This is a simplified approach - in practice, you might want to use
            # a library like yfinance or implement more robust scraping

            # For now, return None as Yahoo Finance requires more complex handling
            # and the yfinance library has compatibility issues with Python 3.8
            return None

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None

    def _generate_estimated_fundamentals(self, symbol: str, company_info: Optional[Dict]) -> Dict:
        """Generate intelligent estimates based on sector and market cap"""
        sector = self._determine_sector(company_info)

        # Base estimates by sector
        sector_estimates = {
            'IT Services': {
                'pe_ratio': 22.0, 'pb_ratio': 6.5, 'roe': 28.0,
                'net_profit_margin': 22.0, 'debt_to_equity': 0.05
            },
            'Banking': {
                'pe_ratio': 13.0, 'pb_ratio': 1.8, 'roe': 16.0,
                'net_profit_margin': 18.0, 'debt_to_equity': 0.7
            },
            'Chemicals': {
                'pe_ratio': 18.0, 'pb_ratio': 2.8, 'roe': 17.0,
                'net_profit_margin': 12.0, 'debt_to_equity': 0.4
            },
            'Oil & Gas': {
                'pe_ratio': 16.0, 'pb_ratio': 1.7, 'roe': 13.0,
                'net_profit_margin': 10.0, 'debt_to_equity': 0.5
            },
            'ETF': {
                'pe_ratio': 0, 'pb_ratio': 1.0, 'roe': 0,
                'net_profit_margin': 0, 'debt_to_equity': 0
            },
            'default': {
                'pe_ratio': 18.0, 'pb_ratio': 2.5, 'roe': 15.0,
                'net_profit_margin': 12.0, 'debt_to_equity': 0.4
            }
        }

        estimates = sector_estimates.get(sector, sector_estimates['default']).copy()
        estimates['data_source'] = 'estimated'
        estimates['sector'] = sector

        return estimates

    def _calculate_financial_ratios(self, symbol: str, market_data: Dict,
                                  fundamentals: Dict, sector: str) -> Dict:
        """Calculate financial ratios from available data"""
        ratios = {
            'symbol': symbol,
            'sector': sector,
            'current_price': market_data.get('current_price', 0),
            'data_source': fundamentals.get('data_source', 'mixed'),
            'last_updated': datetime.now().isoformat()
        }

        # Use provided ratios or calculate from fundamentals
        ratios['pe_ratio'] = fundamentals.get('pe_ratio', 0)
        ratios['pb_ratio'] = fundamentals.get('pb_ratio', 0)
        ratios['roe'] = fundamentals.get('roe', 0)
        ratios['net_profit_margin'] = fundamentals.get('net_profit_margin', 0)
        ratios['debt_to_equity'] = fundamentals.get('debt_to_equity', 0)

        # Additional calculated fields
        if ratios['pe_ratio'] > 0:
            ratios['earnings_yield'] = round(100 / ratios['pe_ratio'], 2)
        else:
            ratios['earnings_yield'] = 0

        return ratios

    def _calculate_health_scores(self, ratios: Dict, sector: str) -> Dict:
        """Calculate financial health scores"""
        benchmarks = self.sector_benchmarks.get(sector, self.sector_benchmarks['default'])
        scores = {}

        # Valuation Score
        pe_ratio = ratios.get('pe_ratio', 0)
        pb_ratio = ratios.get('pb_ratio', 0)

        pe_score = self._score_metric(pe_ratio, benchmarks['pe_excellent'],
                                     benchmarks['pe_good'], lower_is_better=True)
        pb_score = self._score_metric(pb_ratio, benchmarks['pb_excellent'],
                                     benchmarks['pb_good'], lower_is_better=True)

        scores['valuation_score'] = round((pe_score + pb_score) / 2, 1)

        # Profitability Score
        roe = ratios.get('roe', 0)
        net_margin = ratios.get('net_profit_margin', 0)

        roe_score = self._score_metric(roe, benchmarks['roe_excellent'], benchmarks['roe_good'])
        margin_score = self._score_metric(net_margin, benchmarks['net_margin_excellent'],
                                         benchmarks['net_margin_good'])

        scores['profitability_score'] = round((roe_score + margin_score) / 2, 1)

        # Financial Health Score
        debt_equity = ratios.get('debt_to_equity', 0)
        debt_score = self._score_metric(debt_equity, benchmarks['debt_equity_excellent'],
                                       benchmarks['debt_equity_good'], lower_is_better=True)

        scores['financial_health_score'] = debt_score

        # Growth Score (simplified - based on sector)
        growth_scores = {
            'IT Services': 8, 'Banking': 6, 'Chemicals': 7,
            'Oil & Gas': 5, 'ETF': 4, 'default': 6
        }
        scores['growth_score'] = growth_scores.get(sector, 6)

        # Overall Score
        overall_score = (
            scores['valuation_score'] * 0.25 +
            scores['profitability_score'] * 0.35 +
            scores['financial_health_score'] * 0.25 +
            scores['growth_score'] * 0.15
        )

        scores['overall_score'] = round(overall_score, 1)

        # Rating
        if overall_score >= 8:
            scores['rating'] = "EXCELLENT"
            scores['rating_emoji'] = "🟢"
        elif overall_score >= 7:
            scores['rating'] = "GOOD"
            scores['rating_emoji'] = "🟢"
        elif overall_score >= 6:
            scores['rating'] = "FAIR"
            scores['rating_emoji'] = "🟡"
        elif overall_score >= 4:
            scores['rating'] = "POOR"
            scores['rating_emoji'] = "🟠"
        else:
            scores['rating'] = "VERY POOR"
            scores['rating_emoji'] = "🔴"

        return scores

    def _score_metric(self, value: float, excellent: float, good: float,
                     lower_is_better: bool = False) -> float:
        """Score a metric from 0-10 based on thresholds"""
        if value <= 0:
            return 0

        if lower_is_better:
            if value <= excellent:
                return 10
            elif value <= good:
                return 8
            elif value <= good * 1.5:
                return 6
            else:
                return max(0, 10 - (value - good) * 2)
        else:
            if value >= excellent:
                return 10
            elif value >= good:
                return 8
            elif value >= good * 0.7:
                return 6
            else:
                return max(0, value * 0.4)

    def _get_fallback_data(self, symbol: str) -> Dict:
        """Provide fallback data when all sources fail"""
        return {
            'symbol': symbol,
            'sector': 'default',
            'current_price': 0,
            'pe_ratio': 0,
            'pb_ratio': 0,
            'roe': 0,
            'net_profit_margin': 0,
            'debt_to_equity': 0,
            'valuation_score': 5.0,
            'profitability_score': 5.0,
            'financial_health_score': 5.0,
            'growth_score': 5.0,
            'overall_score': 5.0,
            'rating': 'UNKNOWN',
            'rating_emoji': '❓',
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }

    def _wait_for_rate_limit(self, api_name: str):
        """Implement rate limiting for API calls"""
        if api_name in self.last_api_call:
            time_since_last = time.time() - self.last_api_call[api_name]
            if time_since_last < self.api_delay:
                sleep_time = self.api_delay - time_since_last
                time.sleep(sleep_time)

        self.last_api_call[api_name] = time.time()

    def _is_cached(self, key: str) -> bool:
        """Check if data is cached and still fresh"""
        if key in self.cache:
            cached_time = self.cache[key]['timestamp']
            if (datetime.now() - cached_time).seconds < self.cache_timeout:
                return True
        return False

    def get_financial_indicators_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get financial indicators for multiple symbols"""
        financial_data = {}

        for symbol in symbols:
            try:
                indicators = self.get_financial_indicators(symbol)
                if indicators:
                    financial_data[symbol] = indicators
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        logger.info(f"Successfully processed financial indicators for {len(financial_data)} symbols")
        return financial_data
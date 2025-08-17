#!/usr/bin/env python3
"""
Upstox-Based Financial Calculator
Calculates basic financial ratios using Upstox market data + publicly available financial info
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import time

logger = logging.getLogger(__name__)

class UpstoxFinancialCalculator:
    """
    Calculate financial ratios using Upstox market data combined with
    publicly available Indian stock fundamentals
    """

    def __init__(self, upstox_provider=None):
        """
        Initialize with an existing Upstox provider
        """
        self.upstox_provider = upstox_provider

        # Basic financial data for major Indian stocks (publicly available)
        # This data can be updated periodically from annual reports or financial websites
        self.stock_fundamentals = {
            'RELIANCE.NS': {
                'sector': 'Oil & Gas',
                'eps_ttm': 95.50,  # Trailing twelve months EPS
                'book_value_per_share': 1520.0,
                'total_equity': 675000,  # in crores
                'total_debt': 350000,   # in crores
                'net_profit_margin': 8.5,  # percentage
                'revenue_ttm': 875000,  # in crores
                'net_income_ttm': 64500,  # in crores
                'outstanding_shares': 676,  # in crores
                'market_cap_cr': 1850000,  # in crores (approx)
                'last_updated': '2025-08-17'
            },
            'TCS.NS': {
                'sector': 'IT Services',
                'eps_ttm': 162.0,
                'book_value_per_share': 405.0,
                'total_equity': 155000,
                'total_debt': 2500,
                'net_profit_margin': 25.8,
                'revenue_ttm': 253500,
                'net_income_ttm': 65450,
                'outstanding_shares': 365,
                'market_cap_cr': 1320000,
                'last_updated': '2025-08-17'
            },
            'INFY.NS': {
                'sector': 'IT Services',
                'eps_ttm': 74.50,
                'book_value_per_share': 285.0,
                'total_equity': 125000,
                'total_debt': 1800,
                'net_profit_margin': 22.5,
                'revenue_ttm': 183500,
                'net_income_ttm': 41285,
                'outstanding_shares': 416,
                'market_cap_cr': 750000,
                'last_updated': '2025-08-17'
            }
        }

        # Sector benchmarks for scoring
        self.sector_benchmarks = {
            'IT Services': {
                'pe_good': 25.0, 'pe_excellent': 20.0,
                'pb_good': 8.0, 'pb_excellent': 6.0,
                'roe_good': 25.0, 'roe_excellent': 30.0,
                'debt_equity_good': 0.1, 'debt_equity_excellent': 0.05
            },
            'Oil & Gas': {
                'pe_good': 18.0, 'pe_excellent': 15.0,
                'pb_good': 2.0, 'pb_excellent': 1.5,
                'roe_good': 12.0, 'roe_excellent': 15.0,
                'debt_equity_good': 0.6, 'debt_equity_excellent': 0.4
            },
            'default': {
                'pe_good': 20.0, 'pe_excellent': 15.0,
                'pb_good': 3.0, 'pb_excellent': 2.0,
                'roe_good': 15.0, 'roe_excellent': 20.0,
                'debt_equity_good': 0.5, 'debt_equity_excellent': 0.3
            }
        }

    def get_current_market_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get current market data from Upstox
        """
        market_data = {}

        if not self.upstox_provider:
            logger.error("No Upstox provider available")
            return market_data

        try:
            # Get current prices
            prices = self.upstox_provider.get_current_prices(symbols)

            for symbol in symbols:
                if symbol in prices and prices[symbol] > 0:
                    # Get additional market data
                    company_info = self.upstox_provider.get_company_info(symbol)

                    market_data[symbol] = {
                        'current_price': prices[symbol],
                        'previous_close': company_info.get('previous_close', 0) if company_info else 0,
                        'volume': company_info.get('volume', 0) if company_info else 0,
                        'change': company_info.get('change', 0) if company_info else 0,
                        'change_percent': company_info.get('change_percent', 0) if company_info else 0
                    }

            logger.info(f"Retrieved market data for {len(market_data)} symbols")
            return market_data

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return market_data

    def calculate_basic_ratios(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate basic financial ratios for a given symbol
        """
        try:
            # Get fundamental data
            if symbol not in self.stock_fundamentals:
                logger.warning(f"No fundamental data available for {symbol}")
                return {}

            fundamentals = self.stock_fundamentals[symbol]

            # Get current market price from Upstox
            current_price = 0
            if self.upstox_provider:
                price = self.upstox_provider.get_current_price(symbol)
                current_price = price if price else 0

            if current_price <= 0:
                logger.error(f"No valid current price for {symbol}")
                return {}

            # Calculate ratios
            ratios = {
                'symbol': symbol,
                'current_price': current_price,
                'sector': fundamentals['sector'],
                'data_source': 'upstox_calculated',
                'last_updated': datetime.now().isoformat()
            }

            # 1. Price-to-Earnings (PE) Ratio
            if fundamentals['eps_ttm'] > 0:
                ratios['pe_ratio'] = round(current_price / fundamentals['eps_ttm'], 2)
            else:
                ratios['pe_ratio'] = 0

            # 2. Price-to-Book (PB) Ratio
            if fundamentals['book_value_per_share'] > 0:
                ratios['pb_ratio'] = round(current_price / fundamentals['book_value_per_share'], 2)
            else:
                ratios['pb_ratio'] = 0

            # 3. Return on Equity (ROE)
            if fundamentals['total_equity'] > 0:
                ratios['roe'] = round((fundamentals['net_income_ttm'] / fundamentals['total_equity']) * 100, 2)
            else:
                ratios['roe'] = 0

            # 4. Debt-to-Equity Ratio
            if fundamentals['total_equity'] > 0:
                ratios['debt_to_equity'] = round(fundamentals['total_debt'] / fundamentals['total_equity'], 2)
            else:
                ratios['debt_to_equity'] = 0

            # 5. Net Profit Margin (already available)
            ratios['net_profit_margin'] = fundamentals['net_profit_margin']

            # 6. Market Cap (updated with current price)
            ratios['market_cap_cr'] = round(current_price * fundamentals['outstanding_shares'], 0)

            # 7. Earnings Per Share
            ratios['eps_ttm'] = fundamentals['eps_ttm']

            # 8. Book Value Per Share
            ratios['book_value_per_share'] = fundamentals['book_value_per_share']

            # Additional calculated metrics
            ratios['price_to_sales'] = round(ratios['market_cap_cr'] / fundamentals['revenue_ttm'], 2)
            ratios['earnings_yield'] = round(100 / ratios['pe_ratio'], 2) if ratios['pe_ratio'] > 0 else 0

            logger.info(f"✅ Calculated ratios for {symbol}: PE={ratios['pe_ratio']}, PB={ratios['pb_ratio']}, ROE={ratios['roe']}%")
            return ratios

        except Exception as e:
            logger.error(f"Error calculating ratios for {symbol}: {e}")
            return {}

    def get_financial_indicators_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get financial indicators for multiple symbols
        """
        financial_data = {}

        for symbol in symbols:
            try:
                ratios = self.calculate_basic_ratios(symbol)
                if ratios:
                    # Calculate financial health scores
                    health_scores = self.calculate_financial_health_score(ratios)
                    ratios.update(health_scores)
                    financial_data[symbol] = ratios

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        logger.info(f"Successfully calculated financial indicators for {len(financial_data)} symbols")
        return financial_data

    def calculate_financial_health_score(self, ratios: Dict) -> Dict[str, Any]:
        """
        Calculate financial health score based on calculated ratios
        """
        sector = ratios.get('sector', 'default')
        benchmarks = self.sector_benchmarks.get(sector, self.sector_benchmarks['default'])

        scores = {}

        # Valuation Score (lower PE and PB are generally better)
        pe_ratio = ratios.get('pe_ratio', 0)
        pb_ratio = ratios.get('pb_ratio', 0)

        if pe_ratio > 0:
            if pe_ratio <= benchmarks['pe_excellent']:
                pe_score = 10
            elif pe_ratio <= benchmarks['pe_good']:
                pe_score = 8
            elif pe_ratio <= benchmarks['pe_good'] * 1.5:
                pe_score = 6
            else:
                pe_score = max(0, 10 - (pe_ratio - benchmarks['pe_good']) * 0.2)
        else:
            pe_score = 0

        if pb_ratio > 0:
            if pb_ratio <= benchmarks['pb_excellent']:
                pb_score = 10
            elif pb_ratio <= benchmarks['pb_good']:
                pb_score = 8
            elif pb_ratio <= benchmarks['pb_good'] * 1.5:
                pb_score = 6
            else:
                pb_score = max(0, 10 - (pb_ratio - benchmarks['pb_good']) * 0.5)
        else:
            pb_score = 0

        scores['valuation_score'] = round((pe_score + pb_score) / 2, 1)

        # Profitability Score (higher ROE and margins are better)
        roe = ratios.get('roe', 0)
        net_margin = ratios.get('net_profit_margin', 0)

        if roe >= benchmarks['roe_excellent']:
            roe_score = 10
        elif roe >= benchmarks['roe_good']:
            roe_score = 8
        elif roe >= benchmarks['roe_good'] * 0.7:
            roe_score = 6
        else:
            roe_score = max(0, roe * 0.3)

        margin_score = min(10, net_margin * 0.4)
        scores['profitability_score'] = round((roe_score + margin_score) / 2, 1)

        # Financial Health Score (lower debt is better)
        debt_equity = ratios.get('debt_to_equity', 0)

        if debt_equity <= benchmarks['debt_equity_excellent']:
            debt_score = 10
        elif debt_equity <= benchmarks['debt_equity_good']:
            debt_score = 8
        elif debt_equity <= benchmarks['debt_equity_good'] * 1.5:
            debt_score = 6
        else:
            debt_score = max(0, 10 - debt_equity * 5)

        # Simple liquidity proxy (assume healthy if low debt)
        liquidity_score = debt_score
        scores['financial_health_score'] = round((debt_score + liquidity_score) / 2, 1)

        # Growth Score (placeholder - would need historical data)
        # For now, use sector-based estimate
        if sector == 'IT Services':
            growth_score = 8  # High growth sector
        elif sector == 'Oil & Gas':
            growth_score = 5  # Moderate growth sector
        else:
            growth_score = 6  # Default

        scores['growth_score'] = growth_score

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

    def update_fundamental_data(self, symbol: str, fundamental_data: Dict) -> bool:
        """
        Update fundamental data for a symbol (for future use with data scraping)
        """
        try:
            if symbol not in self.stock_fundamentals:
                self.stock_fundamentals[symbol] = {}

            self.stock_fundamentals[symbol].update(fundamental_data)
            self.stock_fundamentals[symbol]['last_updated'] = datetime.now().strftime('%Y-%m-%d')

            logger.info(f"Updated fundamental data for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error updating fundamental data for {symbol}: {e}")
            return False

    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols with available fundamental data
        """
        return list(self.stock_fundamentals.keys())

    def get_data_freshness(self, symbol: str) -> str:
        """
        Check how fresh the fundamental data is for a symbol
        """
        if symbol not in self.stock_fundamentals:
            return "No data available"

        last_updated = self.stock_fundamentals[symbol].get('last_updated', '2025-01-01')

        try:
            update_date = datetime.strptime(last_updated, '%Y-%m-%d')
            days_old = (datetime.now() - update_date).days

            if days_old == 0:
                return "Today"
            elif days_old < 7:
                return f"{days_old} days ago"
            elif days_old < 30:
                return f"{days_old // 7} weeks ago"
            else:
                return f"{days_old // 30} months ago"

        except:
            return "Unknown"
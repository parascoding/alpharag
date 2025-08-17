#!/usr/bin/env python3
"""
Base LLM Provider Interface
Abstract interface for all LLM providers (Gemini, GPT, Claude)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from src.prompt_manager import PromptManager

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers
    """

    def __init__(self, name: str, api_key: str, **kwargs):
        """
        Initialize LLM provider

        Args:
            name: Provider name (gemini, gpt, claude)
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.name = name
        self.api_key = api_key
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager()

        # Common configuration
        self.max_tokens = kwargs.get('max_tokens', 20000)
        self.temperature = kwargs.get('temperature', 0.2)
        self.timeout = kwargs.get('timeout', 50)

        self.logger.info(f"Initialized {name} LLM provider")

    @abstractmethod
    def generate_predictions(self, rag_context: str, portfolio_data: Dict,
                           market_data: Dict, sentiment_data: Dict,
                           financial_data: Optional[Dict] = None,
                           available_cash: float = 0.0) -> Dict:
        """
        Generate investment predictions and analysis

        Args:
            rag_context: Context retrieved from RAG engine
            portfolio_data: Portfolio information and holdings
            market_data: Current market prices and technical data
            sentiment_data: News sentiment analysis results
            financial_data: Financial indicators and ratios

        Returns:
            Dictionary containing predictions and analysis
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available and working

        Returns:
            True if provider is available, False otherwise
        """
        pass

    def _build_analysis_prompt(self, rag_context: str, portfolio_data: Dict,
                              market_data: Dict, sentiment_data: Dict,
                              financial_data: Optional[Dict] = None,
                              available_cash: float = 0.0) -> str:
        """
        Build the analysis prompt using the external prompt manager
        This allows easy modification of prompts without touching code
        """
        try:
            # Use prompt manager to get customizable prompt
            prompt = self.prompt_manager.get_analysis_prompt(
                portfolio_data, market_data, sentiment_data, available_cash
            )
            
            self.logger.info("Using external prompt template")
            return prompt
            
        except Exception as e:
            self.logger.warning(f"Failed to load external prompt template: {e}")
            # Fallback to original hardcoded prompt
            return self._build_fallback_prompt(portfolio_data, market_data, sentiment_data, available_cash)
    
    def _build_fallback_prompt(self, portfolio_data: Dict, market_data: Dict, 
                              sentiment_data: Dict, available_cash: float = 0.0) -> str:
        """
        Fallback prompt if external template loading fails
        """
        prompt = f"""Expert analysis for Indian equity portfolio.

PORTFOLIO: Investment ₹{portfolio_data['summary']['total_investment']:,.0f}, Current ₹{portfolio_data['summary']['total_current_value']:,.0f}, P&L {portfolio_data['summary']['total_pnl_percent']:.1f}%

HOLDINGS:
{self._format_portfolio_data(portfolio_data)}

{self._format_market_data(market_data)}

{self._format_sentiment_data(sentiment_data)}

Provide concise analysis:

1. NEW STOCK PURCHASE RECOMMENDATIONS:
Available Cash: ₹{available_cash:.2f}
Suggest 3-5 new stocks to buy with available liquid funds:
- Stock Symbol: BSE/NSE symbol  
- Recommended Amount: How much to invest (₹)
- Current Price: Market price
- Target Price: 30-day target
- Sector: Stock sector/industry
- Investment Thesis: Why to buy this stock (brief)
- Risk Level: LOW/MEDIUM/HIGH
- Confidence: 1-10 scale

2. INDIVIDUAL STOCK RECOMMENDATIONS:
For each stock in the portfolio, provide concise analysis:
- Recommendation: BUY/SELL/HOLD with confidence level (1-10)
- Current Status: Brief assessment  
- Key Factors: Main drivers (brief)
- Risk Level: LOW/MEDIUM/HIGH

3. PORTFOLIO OVERVIEW:
- Overall Performance Assessment
- Portfolio Risk Analysis  
- Overall Market Outlook

4. ACTION ITEMS:
- Immediate actions for existing positions
- New stock purchases with liquid funds
- Risk management suggestions

Format your response as clear, structured text that can be easily parsed and included in an email report.
Use bullet points and clear headings for readability."""

        return prompt

    def _format_portfolio_data(self, portfolio_data: Dict) -> str:
        """Format portfolio data for the prompt"""
        summary = portfolio_data['summary']
        holdings = portfolio_data['holdings']

        lines = [
            f"Total Investment: ₹{summary['total_investment']:,.2f}",
            f"Current Value: ₹{summary['total_current_value']:,.2f}",
            f"Total P&L: ₹{summary['total_pnl']:,.2f} ({summary['total_pnl_percent']:.2f}%)",
            "",
            "Individual Holdings:"
        ]

        for holding in holdings:
            lines.append(
                f"- {holding['symbol']}: {holding['quantity']} shares @ ₹{holding['buy_price']:.2f} "
                f"(Current: ₹{holding['current_price']:.2f}, P&L: {holding['pnl_percent']:.2f}%)"
            )

        return "\n".join(lines)

    def _format_market_data(self, market_data: Dict) -> str:
        """Format market data for the prompt (condensed)"""
        lines = ["Current Prices:"]

        prices = market_data.get('prices', {})
        for symbol, price in prices.items():
            tech_key = f"{symbol}_technical"
            if tech_key in market_data:
                tech = market_data[tech_key]
                rsi = tech.get('rsi', 0)
                lines.append(f"- {symbol}: ₹{price:.2f} (RSI: {rsi:.0f})")
            else:
                lines.append(f"- {symbol}: ₹{price:.2f}")

        return "\n".join(lines)

    def _format_sentiment_data(self, sentiment_data: Dict) -> str:
        """Format sentiment data for the prompt (condensed)"""
        lines = [
            f"Market Sentiment: {sentiment_data['overall_sentiment']['label']} ({sentiment_data['total_articles']} articles)"
        ]

        # Only include stocks with significant sentiment
        for symbol, data in sentiment_data['individual_sentiment'].items():
            if abs(data['sentiment_score']) > 0.1:  # Only show notable sentiment
                lines.append(f"- {symbol}: {data['sentiment_label']} ({data['sentiment_score']:.2f})")

        return "\n".join(lines)

    def _format_financial_data(self, financial_data: Dict) -> str:
        """Format comprehensive financial data for analysis"""
        if not financial_data:
            return "No financial indicators data available."

        lines = ["FINANCIAL FUNDAMENTALS ANALYSIS:"]

        for symbol, data in financial_data.items():
            health_score = data.get('health_score', {})
            lines.extend([
                f"\n{symbol} ({data.get('sector', 'Unknown')} Sector):",
                f"Market Cap: ₹{data.get('market_cap_cr', 0):,.0f} crores",
                "",
                "VALUATION METRICS:",
                f"  P/E Ratio: {data.get('pe_ratio', 0):.1f}x",
                f"  P/B Ratio: {data.get('pb_ratio', 0):.1f}x",
                f"  P/S Ratio: {data.get('ps_ratio', 0):.1f}x",
                f"  EV/EBITDA: {data.get('ev_ebitda', 0):.1f}x",
                "",
                "PROFITABILITY METRICS:",
                f"  ROE: {data.get('roe', 0):.1f}% (Return on Equity)",
                f"  ROA: {data.get('roa', 0):.1f}% (Return on Assets)",
                f"  ROIC: {data.get('roic', 0):.1f}% (Return on Invested Capital)",
                f"  Gross Margin: {data.get('gross_margin', 0):.1f}%",
                f"  Operating Margin: {data.get('operating_margin', 0):.1f}%",
                f"  Net Profit Margin: {data.get('net_profit_margin', 0):.1f}%",
                "",
                "FINANCIAL HEALTH:",
                f"  Debt-to-Equity: {data.get('debt_to_equity', 0):.2f}",
                f"  Current Ratio: {data.get('current_ratio', 0):.2f}",
                f"  Quick Ratio: {data.get('quick_ratio', 0):.2f}",
                f"  Interest Coverage: {data.get('interest_coverage', 0):.1f}x",
                "",
                "GROWTH INDICATORS:",
                f"  Revenue Growth (YoY): {data.get('revenue_growth_yoy', 0):+.1f}%",
                f"  Earnings Growth (YoY): {data.get('earnings_growth_yoy', 0):+.1f}%",
                f"  Book Value Growth (YoY): {data.get('book_value_growth_yoy', 0):+.1f}%",
                "",
                "DIVIDEND METRICS:",
                f"  Dividend Yield: {data.get('dividend_yield', 0):.1f}%",
                f"  Payout Ratio: {data.get('dividend_payout_ratio', 0):.1f}%",
                f"  Coverage Ratio: {data.get('dividend_coverage_ratio', 0):.1f}x",
                "",
                f"FINANCIAL HEALTH SCORE: {health_score.get('overall_score', 0):.1f}/10 ({health_score.get('rating', 'Unknown')})",
                f"  - Valuation: {health_score.get('valuation_score', 0):.1f}/10",
                f"  - Profitability: {health_score.get('profitability_score', 0):.1f}/10",
                f"  - Financial Health: {health_score.get('financial_health_score', 0):.1f}/10",
                f"  - Growth: {health_score.get('growth_score', 0):.1f}/10",
                ""
            ])

        return "\n".join(lines)

    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict,
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None,
                                     available_cash: float = 0.0) -> Dict:
        """Generate rule-based predictions if API fails"""
        self.logger.error(f"{self.name} API FAILED - Using FALLBACK PREDICTIONS with rule-based analysis")

        predictions = {
            'individual_recommendations': {},
            'new_stock_recommendations': {},
            'portfolio_analysis': f'Analysis generated using fallback rules due to {self.name} API error.',
            'action_items': ['Monitor API connectivity', 'Review market conditions manually'],
            'market_insights': 'Manual analysis required - API unavailable',
            'timestamp': datetime.now().isoformat(),
            'fallback_mode': True,
            'provider': self.name,
            'available_cash': available_cash
        }

        # Enhanced rule-based recommendations using financial data
        for holding in portfolio_data['holdings']:
            symbol = holding['symbol']
            pnl_percent = holding['pnl_percent']

            sentiment_score = sentiment_data['individual_sentiment'].get(symbol, {}).get('sentiment_score', 0)

            # Get financial health score if available
            financial_score = 5  # Default
            financial_reasoning = ""
            if financial_data and symbol in financial_data:
                fin_data = financial_data[symbol]
                health_score = fin_data.get('health_score', {})
                financial_score = health_score.get('overall_score', 5)

                financial_reasoning = f", Financial Score: {financial_score:.1f}/10"

                # Enhanced rules considering financials
                if financial_score >= 7 and pnl_percent < -10 and sentiment_score >= -0.1:
                    recommendation = 'BUY'
                    confidence = 8
                    reasoning = f'Strong financials + oversold + neutral sentiment{financial_reasoning}'
                elif financial_score <= 4 and pnl_percent > 15:
                    recommendation = 'SELL'
                    confidence = 7
                    reasoning = f'Weak financials + overvalued{financial_reasoning}'
                elif pnl_percent > 10 and sentiment_score < -0.2:
                    recommendation = 'SELL'
                    confidence = 6
                    reasoning = f'Rule-based: P&L {pnl_percent:.2f}%, Sentiment {sentiment_score:.3f}{financial_reasoning}'
                elif pnl_percent < -5 and sentiment_score > 0.2 and financial_score >= 6:
                    recommendation = 'BUY'
                    confidence = 6
                    reasoning = f'Rule-based: P&L {pnl_percent:.2f}%, Sentiment {sentiment_score:.3f}{financial_reasoning}'
                else:
                    recommendation = 'HOLD'
                    confidence = 5
                    reasoning = f'Rule-based: P&L {pnl_percent:.2f}%, Sentiment {sentiment_score:.3f}{financial_reasoning}'
            else:
                # Original logic for backward compatibility
                if pnl_percent > 10 and sentiment_score < -0.2:
                    recommendation = 'SELL'
                    confidence = 7
                elif pnl_percent < -5 and sentiment_score > 0.2:
                    recommendation = 'BUY'
                    confidence = 6
                else:
                    recommendation = 'HOLD'
                    confidence = 5
                reasoning = f'Rule-based: P&L {pnl_percent:.2f}%, Sentiment {sentiment_score:.3f}'

            predictions['individual_recommendations'][symbol] = {
                'recommendation': recommendation,
                'confidence': confidence,
                'reasoning': reasoning
            }

        return predictions

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the LLM provider"""
        health_status = {
            'provider': self.name,
            'healthy': False,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }

        try:
            available = self.is_available()
            health_status['healthy'] = available
            health_status['details']['api_available'] = available

        except Exception as e:
            health_status['details']['error'] = str(e)

        return health_status
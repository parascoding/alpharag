#!/usr/bin/env python3
"""
Prompt Manager for LLM Analysis
Loads and manages prompt templates from external files
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Manages prompt templates loaded from external files
    Allows easy modification of prompts without touching code
    """
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.cached_prompts = {}
        
    def load_prompt_template(self, template_name: str) -> Optional[str]:
        """
        Load a prompt template from file
        
        Args:
            template_name: Name of the template file (without .txt extension)
            
        Returns:
            Prompt template string or None if not found
        """
        try:
            template_file = self.prompts_dir / f"{template_name}.txt"
            
            if not template_file.exists():
                logger.warning(f"Prompt template not found: {template_file}")
                return None
                
            # Read and cache the template
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract the actual prompt (skip comments and metadata)
            prompt_lines = []
            in_prompt = False
            
            for line in content.split('\n'):
                line_stripped = line.strip()
                
                # Skip comments and empty lines
                if line_stripped.startswith('#') or not line_stripped:
                    continue
                    
                # Look for the prompt template section
                if 'PROMPT TEMPLATE:' in line:
                    in_prompt = True
                    continue
                elif line_stripped.startswith('# VARIABLES AVAILABLE'):
                    in_prompt = False
                    break
                    
                if in_prompt:
                    prompt_lines.append(line)
                    
            if prompt_lines:
                template = '\n'.join(prompt_lines)
                self.cached_prompts[template_name] = template
                logger.info(f"Loaded prompt template: {template_name}")
                return template
            else:
                logger.error(f"No prompt template found in {template_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading prompt template {template_name}: {e}")
            return None
    
    def get_analysis_prompt(self, portfolio_data: Dict, market_data: Dict, 
                           sentiment_data: Dict, available_cash: float = 0.0) -> str:
        """
        Get the formatted analysis prompt for LLM providers
        
        Args:
            portfolio_data: Portfolio information and holdings
            market_data: Current market prices and technical data  
            sentiment_data: News sentiment analysis results
            available_cash: Available cash for new investments
            
        Returns:
            Formatted prompt string
        """
        # Try to load custom template first
        template = self.load_prompt_template("llm_analysis_prompt")
        
        # Fall back to default template if file not found
        if not template:
            template = self._get_default_template()
            logger.info("Using default prompt template")
        
        # Format the template with data
        try:
            return template.format(
                total_investment=portfolio_data['summary']['total_investment'],
                total_current_value=portfolio_data['summary']['total_current_value'],
                total_pnl_percent=portfolio_data['summary']['total_pnl_percent'],
                portfolio_holdings=self._format_portfolio_data(portfolio_data),
                market_data=self._format_market_data(market_data),
                sentiment_data=self._format_sentiment_data(sentiment_data),
                available_cash=available_cash
            )
        except KeyError as e:
            logger.error(f"Template formatting error - missing key: {e}")
            return self._get_fallback_prompt(portfolio_data, market_data, sentiment_data, available_cash)
    
    def _get_default_template(self) -> str:
        """Default prompt template (fallback)"""
        return """Expert analysis for Indian equity portfolio.

PORTFOLIO: Investment ₹{total_investment:,.0f}, Current ₹{total_current_value:,.0f}, P&L {total_pnl_percent:.1f}%

HOLDINGS:
{portfolio_holdings}

{market_data}

{sentiment_data}

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

    def _get_fallback_prompt(self, portfolio_data: Dict, market_data: Dict, 
                           sentiment_data: Dict, available_cash: float) -> str:
        """Minimal fallback prompt if all else fails"""
        return f"""Analyze this Indian equity portfolio:

Portfolio Value: ₹{portfolio_data['summary']['total_current_value']:,.2f}
P&L: {portfolio_data['summary']['total_pnl_percent']:.1f}%
Available Cash: ₹{available_cash:.2f}

Holdings: {len(portfolio_data['holdings'])} stocks
Market Sentiment: {sentiment_data['overall_sentiment']['label']}

Provide BUY/SELL/HOLD recommendations for each stock and suggest new stock purchases."""

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
    
    def reload_templates(self):
        """Clear cached templates to force reload from files"""
        self.cached_prompts.clear()
        logger.info("Cleared prompt template cache")
import anthropic
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import json
import re

logger = logging.getLogger(__name__)

class ClaudePredictionEngine:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_tokens = 4000
        self.model = "claude-3-sonnet-20240229"
    
    def generate_predictions(self, rag_context: str, portfolio_data: Dict, 
                           market_data: Dict, sentiment_data: Dict, 
                           financial_data: Optional[Dict] = None) -> Dict:
        try:
            # Prepare the analysis prompt
            prompt = self._build_analysis_prompt(rag_context, portfolio_data, market_data, sentiment_data, financial_data)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse Claude's response
            analysis_text = response.content[0].text
            predictions = self._parse_predictions(analysis_text)
            
            logger.info("Generated predictions successfully using Claude API")
            return predictions
            
        except Exception as e:
            logger.error(f"Error generating predictions with Claude: {e}")
            return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
    
    def _build_analysis_prompt(self, rag_context: str, portfolio_data: Dict, 
                              market_data: Dict, sentiment_data: Dict, 
                              financial_data: Optional[Dict] = None) -> str:
        prompt = f"""You are an expert financial analyst specializing in Indian equity markets. 
        
Analyze the following portfolio and market data to provide investment recommendations.

PORTFOLIO INFORMATION:
{self._format_portfolio_data(portfolio_data)}

MARKET DATA:
{self._format_market_data(market_data)}

{self._format_financial_data(financial_data) if financial_data else "FINANCIAL FUNDAMENTALS: Not available"}

NEWS SENTIMENT ANALYSIS:
{self._format_sentiment_data(sentiment_data)}

RELEVANT CONTEXT (RAG Retrieved):
{rag_context}

Please provide a comprehensive analysis with the following structure:

1. INDIVIDUAL STOCK RECOMMENDATIONS:
For each stock in the portfolio, provide:
- Current Status: Brief assessment of current position
- Recommendation: BUY/SELL/HOLD with confidence level (1-10)
- Target Price: Expected price in next 30 days
- Key Factors: Main drivers for the recommendation
- Risk Level: LOW/MEDIUM/HIGH

2. PORTFOLIO OVERVIEW:
- Overall Performance Assessment
- Portfolio Risk Analysis
- Sector Diversification Comments
- Overall Market Outlook

3. ACTION ITEMS:
- Immediate actions to take
- Stocks to watch
- Risk management suggestions

4. MARKET INSIGHTS:
- Key market trends affecting the portfolio
- Economic factors to monitor
- Sector-specific insights

Format your response as clear, structured text that can be easily parsed and included in an email report.
Use bullet points and clear headings for readability."""

        return prompt
    
    def _format_financial_data(self, financial_data: Dict) -> str:
        """Format comprehensive financial data for Claude analysis"""
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

    def _format_portfolio_data(self, portfolio_data: Dict) -> str:
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
        lines = [
            f"Market Status: {market_data.get('market_status', 'Unknown')}",
            f"Data Timestamp: {market_data.get('timestamp', 'Unknown')}",
            "",
            "Current Prices and Technical Analysis:"
        ]
        
        prices = market_data.get('prices', {})
        for symbol, price in prices.items():
            lines.append(f"- {symbol}: ₹{price:.2f}")
            
            tech_key = f"{symbol}_technical"
            if tech_key in market_data:
                tech = market_data[tech_key]
                lines.append(f"  Technical: SMA5={tech.get('sma_5', 'N/A')}, SMA20={tech.get('sma_20', 'N/A')}, RSI={tech.get('rsi', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_sentiment_data(self, sentiment_data: Dict) -> str:
        lines = [
            f"Overall Sentiment: {sentiment_data['overall_sentiment']['label']} (Score: {sentiment_data['overall_sentiment']['score']})",
            f"Total Articles Analyzed: {sentiment_data['total_articles']}",
            "",
            "Individual Stock Sentiment:"
        ]
        
        for symbol, data in sentiment_data['individual_sentiment'].items():
            lines.append(
                f"- {symbol}: {data['sentiment_label']} (Score: {data['sentiment_score']}, "
                f"Articles: {data['article_count']})"
            )
        
        return "\n".join(lines)
    
    def _parse_predictions(self, analysis_text: str) -> Dict:
        # Parse Claude's structured response
        predictions = {
            'individual_recommendations': {},
            'portfolio_analysis': '',
            'action_items': [],
            'market_insights': '',
            'timestamp': datetime.now().isoformat(),
            'raw_analysis': analysis_text
        }
        
        try:
            # Extract individual stock recommendations using regex
            stock_pattern = r'(\w+\.NS|RELIANCE\.NS|TCS\.NS|INFY\.NS):?\s*(?:\n|\r\n)?.*?Recommendation:\s*(BUY|SELL|HOLD).*?confidence.*?(\d+)'
            
            # Split by sections and parse
            sections = analysis_text.split('\n\n')
            
            current_section = ''
            for section in sections:
                section_lower = section.lower()
                
                if 'individual stock' in section_lower or 'recommendations' in section_lower:
                    current_section = 'recommendations'
                elif 'portfolio overview' in section_lower:
                    current_section = 'portfolio'
                    predictions['portfolio_analysis'] = section
                elif 'action items' in section_lower:
                    current_section = 'actions'
                elif 'market insights' in section_lower:
                    current_section = 'insights'
                    predictions['market_insights'] = section
                
                # Parse recommendations section
                if current_section == 'recommendations':
                    # Look for stock symbols and recommendations
                    for line in section.split('\n'):
                        if any(symbol in line for symbol in ['RELIANCE', 'TCS', 'INFY']):
                            # Extract recommendation from the line or subsequent lines
                            if 'BUY' in line.upper():
                                symbol = self._extract_symbol(line)
                                if symbol:
                                    predictions['individual_recommendations'][symbol] = {
                                        'recommendation': 'BUY',
                                        'confidence': self._extract_confidence(line),
                                        'reasoning': line.strip()
                                    }
                            elif 'SELL' in line.upper():
                                symbol = self._extract_symbol(line)
                                if symbol:
                                    predictions['individual_recommendations'][symbol] = {
                                        'recommendation': 'SELL',
                                        'confidence': self._extract_confidence(line),
                                        'reasoning': line.strip()
                                    }
                            elif 'HOLD' in line.upper():
                                symbol = self._extract_symbol(line)
                                if symbol:
                                    predictions['individual_recommendations'][symbol] = {
                                        'recommendation': 'HOLD',
                                        'confidence': self._extract_confidence(line),
                                        'reasoning': line.strip()
                                    }
                
                # Parse action items
                if current_section == 'actions':
                    for line in section.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('-') or line.startswith('•')):
                            predictions['action_items'].append(line[1:].strip())
            
        except Exception as e:
            logger.warning(f"Error parsing predictions: {e}")
            # Fallback: just use the raw text
            predictions['parsing_error'] = str(e)
        
        return predictions
    
    def _extract_symbol(self, text: str) -> Optional[str]:
        symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
        text_upper = text.upper()
        
        for symbol in symbols:
            if symbol in text_upper or symbol.replace('.NS', '') in text_upper:
                return symbol
        return None
    
    def _extract_confidence(self, text: str) -> int:
        # Look for numbers that could be confidence scores (1-10)
        numbers = re.findall(r'\b(\d+)\b', text)
        for num in numbers:
            if 1 <= int(num) <= 10:
                return int(num)
        return 5  # Default confidence
    
    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict, 
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None) -> Dict:
        """Generate simple rule-based predictions if Claude API fails"""
        predictions = {
            'individual_recommendations': {},
            'portfolio_analysis': 'Analysis generated using fallback rules due to API error.',
            'action_items': ['Monitor API connectivity', 'Review market conditions manually'],
            'market_insights': 'Manual analysis required - API unavailable',
            'timestamp': datetime.now().isoformat(),
            'fallback_mode': True
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
                
                # Create financial reasoning
                pe_ratio = fin_data.get('pe_ratio', 0)
                roe = fin_data.get('roe', 0)
                debt_equity = fin_data.get('debt_to_equity', 0)
                
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
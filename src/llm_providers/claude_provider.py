#!/usr/bin/env python3
"""
Anthropic Claude LLM Provider
Implementation for Anthropic Claude API
"""

import anthropic
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import re

from .base_llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class ClaudeProvider(BaseLLMProvider):
    """
    Anthropic Claude implementation of the LLM provider interface
    """

    def __init__(self, api_key: str, **kwargs):
        super().__init__("claude", api_key, **kwargs)

        # Claude-specific configuration
        self.model_name = kwargs.get('model_name', 'claude-3-sonnet-20240229')

        try:
            # Initialize Anthropic client
            self.client = anthropic.Anthropic(api_key=api_key)

            self.logger.info(f"✅ Claude client initialized: {self.model_name}")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Claude: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Claude API is available"""
        try:
            if not self.client:
                return False

            # Test with a simple message
            test_response = self.client.messages.create(
                model=self.model_name,
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello, respond with 'API Working'"}
                ]
            )

            if test_response and test_response.content and test_response.content[0].text:
                self.logger.info("✅ Claude API availability check: Available")
                return True
            else:
                self.logger.error("❌ Claude API returned empty response")
                return False

        except Exception as e:
            self.logger.error(f"❌ Claude availability check failed: {e}")
            return False

    def generate_predictions(self, rag_context: str, portfolio_data: Dict,
                           market_data: Dict, sentiment_data: Dict,
                           financial_data: Optional[Dict] = None,
                           available_cash: float = 0.0) -> Dict:
        """Generate predictions using Claude"""
        try:
            if not self.client:
                self.logger.error("Claude client not initialized")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            # Build the analysis prompt
            prompt = self._build_analysis_prompt(rag_context, portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            self.logger.info("🤖 Generating predictions with Claude...")

            # Generate content with Claude
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            if not response or not response.content or not response.content[0].text:
                self.logger.error("Claude returned empty response")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            # Parse Claude's response
            analysis_text = response.content[0].text
            predictions = self._parse_predictions(analysis_text)
            predictions['provider'] = 'claude'
            predictions['model'] = self.model_name
            predictions['usage'] = {
                'input_tokens': response.usage.input_tokens if response.usage else 0,
                'output_tokens': response.usage.output_tokens if response.usage else 0
            }

            self.logger.info("✅ Generated predictions successfully using Claude API")
            return predictions

        except Exception as e:
            self.logger.error(f"❌ Error generating predictions with Claude: {e}")
            return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

    def _parse_predictions(self, analysis_text: str) -> Dict:
        """Parse Claude's structured response"""
        predictions = {
            'individual_recommendations': {},
            'new_stock_recommendations': {},
            'portfolio_analysis': '',
            'action_items': [],
            'market_insights': '',
            'timestamp': datetime.now().isoformat(),
            'raw_analysis': analysis_text
        }

        try:
            # Split analysis into sections
            sections = analysis_text.split('\n\n')
            current_section = ''

            for section in sections:
                section_lower = section.lower()

                # Identify sections
                if any(keyword in section_lower for keyword in ['individual stock', 'recommendations', '1.']):
                    current_section = 'recommendations'
                elif any(keyword in section_lower for keyword in ['portfolio overview', '2.']):
                    current_section = 'portfolio'
                    predictions['portfolio_analysis'] = section
                elif any(keyword in section_lower for keyword in ['action items', '3.']):
                    current_section = 'actions'
                elif any(keyword in section_lower for keyword in ['market insights', '4.']):
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
            self.logger.warning(f"Error parsing Claude predictions: {e}")
            predictions['parsing_error'] = str(e)

        return predictions

    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract stock symbol from text"""
        symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
        text_upper = text.upper()

        for symbol in symbols:
            if symbol in text_upper or symbol.replace('.NS', '') in text_upper:
                return symbol
        return None

    def _extract_confidence(self, text: str) -> int:
        """Extract confidence score from text"""
        # Look for numbers that could be confidence scores (1-10)
        numbers = re.findall(r'\b(\d+)\b', text)
        for num in numbers:
            if 1 <= int(num) <= 10:
                return int(num)
        return 5  # Default confidence

    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict,
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None,
                                     available_cash: float = 0.0) -> Dict:
        """Generate fallback predictions when Claude fails"""
        predictions = super()._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)
        predictions['provider'] = 'claude_fallback'
        return predictions
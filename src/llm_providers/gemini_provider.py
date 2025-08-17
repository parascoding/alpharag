#!/usr/bin/env python3
"""
Google Gemini LLM Provider
Implementation for Google Gemini AI API using direct REST calls
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import re

from .base_llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini implementation using direct REST API calls
    """

    def __init__(self, api_key: str, **kwargs):
        super().__init__("gemini", api_key, **kwargs)

        # Gemini-specific configuration
        self.model_name = kwargs.get('model_name', 'gemini-2.5-flash')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        # Test API key format
        if not api_key or not api_key.startswith('AIzaSy'):
            self.logger.error("❌ Invalid Gemini API key format")
            self.client = None
        else:
            self.client = requests.Session()
            self.logger.info(f"✅ Gemini configured with model: {self.model_name}")

    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        try:
            if not self.client:
                return False

            # Test with a simple prompt using REST API
            url = f"{self.base_url}/models/{self.model_name}:generateContent"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": "Hello, respond with 'API Working'"
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 10
                }
            }

            response = self.client.post(
                f"{url}?key={self.api_key}",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'candidates' in data and data['candidates']:
                    self.logger.info("✅ Gemini API availability check: Available")
                    return True
                else:
                    self.logger.error("❌ Gemini API returned empty candidates")
                    return False
            else:
                self.logger.error(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Gemini availability check failed: {e}")
            return False

    def generate_predictions(self, rag_context: str, portfolio_data: Dict,
                           market_data: Dict, sentiment_data: Dict,
                           financial_data: Optional[Dict] = None) -> Dict:
        """Generate predictions using Gemini"""
        try:
            if not self.client:
                self.logger.error("Gemini client not initialized")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)

            # Build the analysis prompt
            prompt = self._build_analysis_prompt(rag_context, portfolio_data, market_data, sentiment_data, financial_data)

            self.logger.info("🤖 Generating predictions with Gemini...")

            # Generate content with Gemini using REST API
            url = f"{self.base_url}/models/{self.model_name}:generateContent"

            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens
                }
            }

            response = self.client.post(
                f"{url}?key={self.api_key}",
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                self.logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)

            data = response.json()

            if 'candidates' not in data or not data['candidates']:
                self.logger.error("Gemini returned no candidates")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)

            # Extract the generated text
            candidate = data['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                self.logger.error("Gemini returned malformed response")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)

            analysis_text = candidate['content']['parts'][0]['text']

            # Parse Gemini's response
            predictions = self._parse_predictions(analysis_text)
            predictions['provider'] = 'gemini'
            predictions['model'] = self.model_name

            self.logger.info("✅ Generated predictions successfully using Gemini API")
            return predictions

        except Exception as e:
            self.logger.error(f"❌ Error generating predictions with Gemini: {e}")
            return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)

    def _parse_predictions(self, analysis_text: str) -> Dict:
        """Parse Gemini's structured response"""
        predictions = {
            'individual_recommendations': {},
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
                    # Look for stock symbols and extract recommendations
                    lines = section.split('\n')
                    current_symbol = None

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        # Check if line contains a stock symbol
                        symbol = self._extract_symbol(line)
                        if symbol:
                            current_symbol = symbol

                        # Extract recommendation details
                        if current_symbol and any(rec in line.upper() for rec in ['BUY', 'SELL', 'HOLD']):
                            recommendation = self._extract_recommendation(line)
                            confidence = self._extract_confidence(line)

                            if recommendation:
                                predictions['individual_recommendations'][current_symbol] = {
                                    'recommendation': recommendation,
                                    'confidence': confidence,
                                    'reasoning': line
                                }

                # Parse action items
                if current_section == 'actions':
                    for line in section.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                            predictions['action_items'].append(line[1:].strip())

        except Exception as e:
            self.logger.warning(f"Error parsing Gemini predictions: {e}")
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

    def _extract_recommendation(self, text: str) -> Optional[str]:
        """Extract recommendation from text"""
        text_upper = text.upper()
        if 'BUY' in text_upper:
            return 'BUY'
        elif 'SELL' in text_upper:
            return 'SELL'
        elif 'HOLD' in text_upper:
            return 'HOLD'
        return None

    def _extract_confidence(self, text: str) -> int:
        """Extract confidence score from text"""
        # Look for patterns like "confidence: 8", "8/10", "(8)"
        patterns = [
            r'confidence[:\s]+(\d+)',
            r'(\d+)/10',
            r'\((\d+)\)',
            r'level[:\s]+(\d+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                conf = int(match)
                if 1 <= conf <= 10:
                    return conf

        return 5  # Default confidence

    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict,
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None) -> Dict:
        """Generate fallback predictions when Gemini fails"""
        predictions = super()._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
        predictions['provider'] = 'gemini_fallback'
        return predictions
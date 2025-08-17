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
        import re
        
        predictions = {
            'individual_recommendations': {},
            'portfolio_analysis': '',
            'action_items': [],
            'market_insights': '',
            'timestamp': datetime.now().isoformat(),
            'raw_analysis': analysis_text
        }

        try:
            # Extract overall portfolio analysis (first paragraph)
            lines = analysis_text.split('\n')
            portfolio_lines = []
            for line in lines[:10]:  # First 10 lines usually contain portfolio overview
                if line.strip() and not line.strip().startswith('*') and not line.strip().startswith('#'):
                    portfolio_lines.append(line.strip())
            predictions['portfolio_analysis'] = ' '.join(portfolio_lines)

            # Use regex to find individual stock analysis blocks
            # Pattern: **SYMBOL.NS (Sector)** followed by analysis block
            stock_patterns = [
                r'\*\s+\*\*([A-Z0-9]+\.NS)\s+\([^)]+\)\*\*\s*\n(.*?)(?=\*\s+\*\*[A-Z0-9]+\.NS|\Z)',  # **SYMBOL.NS (Sector)**
                r'\*\s+\*\*([A-Z0-9]+\.NS)\*\*\s*\n(.*?)(?=\*\s+\*\*[A-Z0-9]+\.NS|\Z)',               # **SYMBOL.NS**
                r'([A-Z0-9]+\.NS)\s+\([^)]+\)(.*?)(?=[A-Z0-9]+\.NS\s+\(|\Z)',                         # SYMBOL.NS (Sector)
            ]
            
            for pattern in stock_patterns:
                matches = re.findall(pattern, analysis_text, re.DOTALL)
                
                for symbol, analysis_block in matches:
                    # Extract recommendation from analysis block
                    recommendation = self._extract_recommendation(analysis_block)
                    confidence = self._extract_confidence(analysis_block)
                    
                    # Extract reasoning
                    reasoning = self._extract_reasoning(analysis_block)
                    
                    if recommendation:
                        predictions['individual_recommendations'][symbol] = {
                            'recommendation': recommendation,
                            'confidence': confidence,
                            'reasoning': reasoning
                        }
                        self.logger.info(f"Parsed {symbol}: {recommendation} (confidence: {confidence})")
                
                if predictions['individual_recommendations']:
                    break  # Stop if we found matches with this pattern

            # If no stocks found with the above patterns, try line-by-line parsing
            if not predictions['individual_recommendations']:
                self.logger.warning("No stocks found with primary patterns, trying line-by-line parsing...")
                
                current_symbol = None
                current_analysis = []
                
                lines = analysis_text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this line contains a stock symbol
                    symbol = self._extract_symbol(line)
                    if symbol:
                        # Process previous symbol if we have one
                        if current_symbol and current_analysis:
                            analysis_text_block = '\n'.join(current_analysis)
                            recommendation = self._extract_recommendation(analysis_text_block)
                            if recommendation:
                                confidence = self._extract_confidence(analysis_text_block)
                                reasoning = self._extract_reasoning(analysis_text_block)
                                predictions['individual_recommendations'][current_symbol] = {
                                    'recommendation': recommendation,
                                    'confidence': confidence,
                                    'reasoning': reasoning
                                }
                                self.logger.info(f"Line-parsed {current_symbol}: {recommendation} (confidence: {confidence})")
                        
                        # Start new symbol
                        current_symbol = symbol
                        current_analysis = [line]
                    elif current_symbol:
                        # Add to current analysis
                        current_analysis.append(line)
                        
                        # Check if we have enough lines for this symbol (max 10 lines per stock)
                        if len(current_analysis) > 10:
                            analysis_text_block = '\n'.join(current_analysis)
                            recommendation = self._extract_recommendation(analysis_text_block)
                            if recommendation:
                                confidence = self._extract_confidence(analysis_text_block)
                                reasoning = self._extract_reasoning(analysis_text_block)
                                predictions['individual_recommendations'][current_symbol] = {
                                    'recommendation': recommendation,
                                    'confidence': confidence,
                                    'reasoning': reasoning
                                }
                                self.logger.info(f"Line-parsed {current_symbol}: {recommendation} (confidence: {confidence})")
                            current_symbol = None
                            current_analysis = []
                
                # Process the last symbol
                if current_symbol and current_analysis:
                    analysis_text_block = '\n'.join(current_analysis)
                    recommendation = self._extract_recommendation(analysis_text_block)
                    if recommendation:
                        confidence = self._extract_confidence(analysis_text_block)
                        reasoning = self._extract_reasoning(analysis_text_block)
                        predictions['individual_recommendations'][current_symbol] = {
                            'recommendation': recommendation,
                            'confidence': confidence,
                            'reasoning': reasoning
                        }
                        self.logger.info(f"Line-parsed {current_symbol}: {recommendation} (confidence: {confidence})")

            self.logger.info(f"Successfully parsed {len(predictions['individual_recommendations'])} stock recommendations")

        except Exception as e:
            self.logger.error(f"Error parsing Gemini predictions: {e}")
            predictions['parsing_error'] = str(e)

        return predictions

    def _extract_symbol(self, text: str) -> Optional[str]:
        """Extract stock symbol from text"""
        # Common Indian stock symbols pattern
        import re
        text_upper = text.upper()
        
        # Look for patterns like "SYMBOL.NS" or "**SYMBOL.NS**" 
        symbol_patterns = [
            r'\*\*([A-Z0-9]+\.NS)\*\*',  # **SYMBOL.NS**
            r'([A-Z0-9]+\.NS)',          # SYMBOL.NS
            r'\*\s+\*\*([A-Z0-9]+\.NS)', # * **SYMBOL.NS
        ]
        
        for pattern in symbol_patterns:
            matches = re.findall(pattern, text_upper)
            if matches:
                return matches[0]
        
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
        import re
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

    def _extract_reasoning(self, analysis_block: str) -> str:
        """Extract reasoning from analysis block"""
        lines = analysis_block.split('\n')
        
        # Look for key factors or reasoning lines
        reasoning_lines = []
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['key factors:', 'factors:', 'reason:', 'because']):
                # Get the content after the colon
                if ':' in line:
                    reasoning_lines.append(line.split(':', 1)[1].strip())
                else:
                    reasoning_lines.append(line)
            elif line.startswith('*') and any(keyword in line.lower() for keyword in ['current status:', 'recommendation:']):
                reasoning_lines.append(line.replace('*', '').strip())
        
        # If no specific reasoning found, use first meaningful line
        if not reasoning_lines:
            for line in lines[:3]:
                line = line.strip()
                if line and not line.startswith('*') and len(line) > 20:
                    reasoning_lines.append(line)
                    break
        
        # Combine reasoning without truncation
        reasoning = ' '.join(reasoning_lines)
        
        return reasoning or "Analysis available in detailed report"

    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict,
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None) -> Dict:
        """Generate fallback predictions when Gemini fails"""
        predictions = super()._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
        predictions['provider'] = 'gemini_fallback'
        return predictions
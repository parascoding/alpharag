#!/usr/bin/env python3
"""
OpenAI GPT LLM Provider
Implementation for OpenAI GPT API
"""

from openai import OpenAI
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import json
import re

from .base_llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GPTProvider(BaseLLMProvider):
    """
    OpenAI GPT implementation of the LLM provider interface
    """
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__("gpt", api_key, **kwargs)
        
        # GPT-specific configuration
        self.model_name = kwargs.get('model_name', 'gpt-4o-mini')
        self.organization = kwargs.get('organization', None)
        
        try:
            # Initialize OpenAI client
            client_kwargs = {'api_key': api_key}
            if self.organization:
                client_kwargs['organization'] = self.organization
                
            self.client = OpenAI(**client_kwargs)
            
            self.logger.info(f"✅ GPT client initialized: {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize GPT: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if GPT API is available"""
        try:
            if not self.client:
                return False
                
            # Test with a simple completion
            test_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": "Hello, respond with 'API Working'"}
                ],
                max_tokens=10,
                timeout=10
            )
            
            if test_response and test_response.choices and test_response.choices[0].message.content:
                self.logger.info("✅ GPT API availability check: Available")
                return True
            else:
                self.logger.error("❌ GPT API returned empty response")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ GPT availability check failed: {e}")
            return False
    
    def generate_predictions(self, rag_context: str, portfolio_data: Dict,
                           market_data: Dict, sentiment_data: Dict,
                           financial_data: Optional[Dict] = None) -> Dict:
        """Generate predictions using GPT"""
        try:
            if not self.client:
                self.logger.error("GPT client not initialized")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
            
            # Build the analysis prompt
            prompt = self._build_analysis_prompt(rag_context, portfolio_data, market_data, sentiment_data, financial_data)
            
            self.logger.info("🤖 Generating predictions with GPT...")
            
            # Generate completion with GPT
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert financial analyst specializing in Indian equity markets. Provide detailed, structured investment analysis and recommendations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            if not response or not response.choices or not response.choices[0].message.content:
                self.logger.error("GPT returned empty response")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
            
            # Parse GPT's response
            analysis_text = response.choices[0].message.content
            predictions = self._parse_predictions(analysis_text)
            predictions['provider'] = 'gpt'
            predictions['model'] = self.model_name
            predictions['usage'] = {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0
            }
            
            self.logger.info("✅ Generated predictions successfully using GPT API")
            return predictions
            
        except Exception as e:
            self.logger.error(f"❌ Error generating predictions with GPT: {e}")
            return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
    
    def _parse_predictions(self, analysis_text: str) -> Dict:
        """Parse GPT's structured response"""
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
                
                # Identify sections by headers and numbering
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
                    self._parse_recommendations_section(section, predictions)
                
                # Parse action items
                if current_section == 'actions':
                    for line in section.split('\n'):
                        line = line.strip()
                        if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                            predictions['action_items'].append(line[1:].strip())

        except Exception as e:
            self.logger.warning(f"Error parsing GPT predictions: {e}")
            predictions['parsing_error'] = str(e)

        return predictions
    
    def _parse_recommendations_section(self, section: str, predictions: Dict):
        """Parse the recommendations section for individual stocks"""
        lines = section.split('\n')
        current_symbol = None
        current_recommendation = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line contains a stock symbol
            symbol = self._extract_symbol(line)
            if symbol:
                # Save previous recommendation if exists
                if current_symbol and current_recommendation:
                    predictions['individual_recommendations'][current_symbol] = current_recommendation
                
                # Start new recommendation
                current_symbol = symbol
                current_recommendation = {
                    'recommendation': None,
                    'confidence': 5,
                    'reasoning': line
                }
                
                # Try to extract recommendation from the same line
                rec = self._extract_recommendation(line)
                if rec:
                    current_recommendation['recommendation'] = rec
                    current_recommendation['confidence'] = self._extract_confidence(line)
            
            elif current_symbol:
                # Continue building recommendation for current symbol
                if not current_recommendation.get('recommendation'):
                    rec = self._extract_recommendation(line)
                    if rec:
                        current_recommendation['recommendation'] = rec
                        current_recommendation['confidence'] = self._extract_confidence(line)
                
                # Add to reasoning
                current_recommendation['reasoning'] += ' ' + line
        
        # Save last recommendation
        if current_symbol and current_recommendation:
            predictions['individual_recommendations'][current_symbol] = current_recommendation
    
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
        """Generate fallback predictions when GPT fails"""
        predictions = super()._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data)
        predictions['provider'] = 'gpt_fallback'
        return predictions
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
        self.model_name = kwargs.get('model_name', 'gemini-2.0-flash')
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
                           financial_data: Optional[Dict] = None,
                           available_cash: float = 0.0) -> Dict:
        """Generate predictions using Gemini"""
        try:
            if not self.client:
                self.logger.error("Gemini client not initialized")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            # Build the analysis prompt
            prompt = self._build_analysis_prompt(rag_context, portfolio_data, market_data, sentiment_data, financial_data, available_cash)

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
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            data = response.json()

            if 'candidates' not in data or not data['candidates']:
                self.logger.error("Gemini returned no candidates")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            # Extract the generated text
            candidate = data['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content']:
                self.logger.error(f"Gemini returned malformed response. Response structure: {json.dumps(data, indent=2)}")
                return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

            analysis_text = candidate['content']['parts'][0]['text']

            # Parse Gemini's response
            predictions = self._parse_predictions(analysis_text, available_cash)
            predictions['provider'] = 'gemini'
            predictions['model'] = self.model_name

            self.logger.info("✅ Generated predictions successfully using Gemini API")
            return predictions

        except Exception as e:
            self.logger.error(f"❌ Error generating predictions with Gemini: {e}")
            return self._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)

    def _parse_predictions(self, analysis_text: str, available_cash: float = 0.0) -> Dict:
        """Parse Gemini's structured response"""
        import re
        
        predictions = {
            'individual_recommendations': {},
            'new_stock_recommendations': {},
            'portfolio_analysis': '',
            'action_items': [],
            'market_insights': '',
            'timestamp': datetime.now().isoformat(),
            'raw_analysis': analysis_text,
            'available_cash': available_cash
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

            # Parse NEW STOCK PURCHASE RECOMMENDATIONS section
            new_stock_patterns = [
                r'NEW STOCK PURCHASE RECOMMENDATIONS?:?\s*(.*?)(?=\d+\.\s+(INDIVIDUAL|PORTFOLIO)|INDIVIDUAL STOCK|$)',
                r'1\.\s+NEW STOCK PURCHASE RECOMMENDATIONS?:?\s*(.*?)(?=\d+\.\s+(INDIVIDUAL|PORTFOLIO)|INDIVIDUAL STOCK|$)',
                r'NEW STOCK.{0,20}RECOMMENDATIONS?:?\s*(.*?)(?=\d+\.\s+(INDIVIDUAL|PORTFOLIO)|INDIVIDUAL STOCK|$)'
            ]
            
            for pattern in new_stock_patterns:
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                if match:
                    new_stock_section = match.group(1).strip()
                    self._parse_new_stock_recommendations(new_stock_section, predictions)
                    break

            self.logger.info(f"Successfully parsed {len(predictions['new_stock_recommendations'])} new stock recommendations")

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

    def _parse_new_stock_recommendations(self, section_text: str, predictions: Dict):
        """Parse the new stock purchase recommendations section"""
        lines = section_text.split('\n')
        current_stock = {}
        
        # First try to parse table format
        table_parsed = self._parse_table_format(section_text, predictions)
        if table_parsed:
            self.logger.info(f"Parsed {len(predictions['new_stock_recommendations'])} new stock recommendations from table format")
            return
        
        # Fallback to original bullet-point parsing
        for line in lines:
            line = line.strip()
            if not line or line.startswith('Available Cash:'):
                continue
            
            # Look for stock symbol patterns
            symbol_match = re.search(r'([A-Z0-9]+\.NS|[A-Z0-9]+\.BSE)', line.upper())
            if symbol_match:
                # Save previous stock if complete
                if current_stock and 'symbol' in current_stock:
                    predictions['new_stock_recommendations'][current_stock['symbol']] = current_stock
                
                # Start new stock
                current_stock = {'symbol': symbol_match.group(1)}
                
                # Extract recommendation amount from same line
                amount_match = re.search(r'₹([\d,]+)', line)
                if amount_match:
                    current_stock['recommended_amount'] = amount_match.group(1).replace(',', '')
                
                # Extract current price
                price_match = re.search(r'Current.*?₹([\d,.]+)', line, re.IGNORECASE)
                if price_match:
                    current_stock['current_price'] = price_match.group(1).replace(',', '')
                
                # Extract target price
                target_match = re.search(r'Target.*?₹([\d,.]+)', line, re.IGNORECASE)
                if target_match:
                    current_stock['target_price'] = target_match.group(1).replace(',', '')
                    
            elif current_stock:
                # Continue parsing details for current stock
                if 'recommended amount' in line.lower() and 'recommended_amount' not in current_stock:
                    amount_match = re.search(r'₹([\d,]+)', line)
                    if amount_match:
                        current_stock['recommended_amount'] = amount_match.group(1).replace(',', '')
                
                elif 'current price' in line.lower() and 'current_price' not in current_stock:
                    price_match = re.search(r'₹([\d,.]+)', line)
                    if price_match:
                        current_stock['current_price'] = price_match.group(1).replace(',', '')
                
                elif 'target price' in line.lower() and 'target_price' not in current_stock:
                    price_match = re.search(r'₹([\d,.]+)', line)
                    if price_match:
                        current_stock['target_price'] = price_match.group(1).replace(',', '')
                
                elif 'sector' in line.lower() and 'sector' not in current_stock:
                    current_stock['sector'] = line.split(':', 1)[1].strip() if ':' in line else line
                
                elif 'investment thesis' in line.lower() or 'why' in line.lower():
                    current_stock['investment_thesis'] = line.split(':', 1)[1].strip() if ':' in line else line
                
                elif 'risk level' in line.lower():
                    risk_match = re.search(r'(LOW|MEDIUM|HIGH)', line.upper())
                    if risk_match:
                        current_stock['risk_level'] = risk_match.group(1)
                
                elif 'confidence' in line.lower():
                    conf_match = re.search(r'(\d+)', line)
                    if conf_match:
                        current_stock['confidence'] = int(conf_match.group(1))
        
        # Save last stock
        if current_stock and 'symbol' in current_stock:
            predictions['new_stock_recommendations'][current_stock['symbol']] = current_stock
        
        self.logger.info(f"Parsed {len(predictions['new_stock_recommendations'])} new stock recommendations from bullet format")

    def _parse_table_format(self, section_text: str, predictions: Dict) -> bool:
        """Parse table format for new stock recommendations"""
        lines = section_text.split('\n')
        
        # Find table rows (lines with multiple | separators)
        table_rows = []
        for line in lines:
            if line.count('|') >= 6:  # Table should have at least 7 columns (6 separators)
                table_rows.append(line.strip())
        
        if not table_rows:
            return False
        
        parsed_count = 0
        for row in table_rows:
            # Skip header rows and separator rows
            if '---' in row or 'Stock Symbol' in row or 'Recommended Amount' in row:
                continue
            
            # Split by | and clean up
            columns = [col.strip() for col in row.split('|')]
            if len(columns) < 8:  # Need at least 8 columns (including empty first/last)
                continue
            
            # Extract data from columns
            # Expected format: | Stock Name (SYMBOL.NS) | Amount | Current Price | Target Price | Sector | Thesis | Risk | Confidence |
            try:
                stock_name_col = columns[1] if len(columns) > 1 else ""
                amount_col = columns[2] if len(columns) > 2 else ""
                current_price_col = columns[3] if len(columns) > 3 else ""
                target_price_col = columns[4] if len(columns) > 4 else ""
                sector_col = columns[5] if len(columns) > 5 else ""
                thesis_col = columns[6] if len(columns) > 6 else ""
                risk_col = columns[7] if len(columns) > 7 else ""
                confidence_col = columns[8] if len(columns) > 8 else ""
                
                # Extract symbol from stock name column
                symbol_match = re.search(r'\b([A-Z0-9]+\.NS)\b', stock_name_col.upper())
                if not symbol_match:
                    continue
                
                symbol = symbol_match.group(1)
                
                # Extract numeric values
                recommended_amount = re.sub(r'[^0-9,]', '', amount_col).replace(',', '')
                current_price = re.sub(r'[^0-9,.]', '', current_price_col).replace(',', '')
                target_price = re.sub(r'[^0-9,.]', '', target_price_col).replace(',', '')
                
                # Extract confidence number
                confidence_match = re.search(r'(\d+)', confidence_col)
                confidence = int(confidence_match.group(1)) if confidence_match else 5
                
                # Clean up text fields
                sector = sector_col.strip()
                investment_thesis = thesis_col.strip()
                risk_level = risk_col.strip().upper()
                
                # Validate that we have the essential fields
                if not (recommended_amount and current_price and symbol):
                    continue
                
                # Create stock recommendation
                stock_rec = {
                    'symbol': symbol,
                    'recommended_amount': recommended_amount,
                    'current_price': current_price,
                    'target_price': target_price,
                    'sector': sector,
                    'investment_thesis': investment_thesis,
                    'risk_level': risk_level,
                    'confidence': confidence
                }
                
                predictions['new_stock_recommendations'][symbol] = stock_rec
                parsed_count += 1
                
                self.logger.info(f"Table-parsed {symbol}: ₹{recommended_amount} investment (confidence: {confidence})")
                
            except Exception as e:
                self.logger.warning(f"Error parsing table row: {row[:100]}... Error: {e}")
                continue
        
        return parsed_count > 0

    def _generate_fallback_predictions(self, portfolio_data: Dict, market_data: Dict,
                                     sentiment_data: Dict, financial_data: Optional[Dict] = None,
                                     available_cash: float = 0.0) -> Dict:
        """Generate fallback predictions when Gemini fails"""
        predictions = super()._generate_fallback_predictions(portfolio_data, market_data, sentiment_data, financial_data, available_cash)
        predictions['provider'] = 'gemini_fallback'
        return predictions
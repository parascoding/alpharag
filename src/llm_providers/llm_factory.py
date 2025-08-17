#!/usr/bin/env python3
"""
LLM Factory with Fallback Chain
Manages LLM providers with automatic fallback capability
"""

from typing import Dict, List, Optional, Any, Type
import logging
from datetime import datetime

from .base_llm_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .gpt_provider import GPTProvider
from .claude_provider import ClaudeProvider

logger = logging.getLogger(__name__)

class LLMFactory:
    """
    Factory class for creating and managing LLM providers with fallback chain
    """
    
    # Registry of available providers
    PROVIDER_REGISTRY = {
        'gemini': GeminiProvider,
        'gpt': GPTProvider,
        'claude': ClaudeProvider
    }
    
    def __init__(self, primary_provider: str, fallback_providers: List[str], **api_keys):
        """
        Initialize LLM factory with fallback chain
        
        Args:
            primary_provider: Primary LLM provider to use
            fallback_providers: List of fallback providers in order
            **api_keys: API keys for different providers
        """
        self.primary_provider_name = primary_provider
        self.fallback_provider_names = fallback_providers
        self.api_keys = api_keys
        
        # Initialize providers
        self.providers = {}
        self.provider_chain = []
        
        # Create complete provider chain
        all_providers = [primary_provider] + fallback_providers
        
        for provider_name in all_providers:
            if provider_name in self.PROVIDER_REGISTRY:
                api_key = self._get_api_key_for_provider(provider_name)
                if api_key:
                    try:
                        provider = self._create_provider(provider_name, api_key)
                        if provider:
                            self.providers[provider_name] = provider
                            self.provider_chain.append(provider_name)
                            logger.info(f"✅ {provider_name.upper()} provider initialized")
                        else:
                            logger.warning(f"⚠️ Failed to create {provider_name} provider")
                    except Exception as e:
                        logger.error(f"❌ Error initializing {provider_name}: {e}")
                else:
                    logger.warning(f"⚠️ No API key provided for {provider_name}")
            else:
                logger.error(f"❌ Unknown provider: {provider_name}")
        
        if not self.providers:
            logger.error("❌ No LLM providers could be initialized!")
        else:
            logger.info(f"🚀 LLM Factory initialized with chain: {' → '.join(self.provider_chain)}")
    
    def _get_api_key_for_provider(self, provider_name: str) -> Optional[str]:
        """Get API key for a specific provider"""
        key_mappings = {
            'gemini': ['GEMINI_API_KEY', 'GOOGLE_API_KEY'],
            'gpt': ['OPENAI_API_KEY', 'GPT_API_KEY'],
            'claude': ['ANTHROPIC_API_KEY', 'CLAUDE_API_KEY']
        }
        
        if provider_name in key_mappings:
            for key_name in key_mappings[provider_name]:
                if key_name in self.api_keys and self.api_keys[key_name]:
                    return self.api_keys[key_name]
        
        return None
    
    def _create_provider(self, provider_name: str, api_key: str) -> Optional[BaseLLMProvider]:
        """Create a provider instance"""
        try:
            provider_class = self.PROVIDER_REGISTRY[provider_name]
            
            # Provider-specific configurations
            provider_kwargs = {
                'api_key': api_key,
                'max_tokens': 4000,
                'temperature': 0.7
            }
            
            # Add specific configurations for each provider
            if provider_name == 'gemini':
                provider_kwargs.update({
                    'model_name': 'gemini-2.5-flash',
                    'safety_settings': {
                        'HARASSMENT': 'BLOCK_NONE',
                        'HATE_SPEECH': 'BLOCK_NONE',
                        'SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                        'DANGEROUS_CONTENT': 'BLOCK_NONE'
                    }
                })
            elif provider_name == 'gpt':
                provider_kwargs.update({
                    'model_name': 'gpt-4o-mini',
                    'organization': self.api_keys.get('OPENAI_ORG_ID')
                })
            elif provider_name == 'claude':
                provider_kwargs.update({
                    'model_name': 'claude-3-sonnet-20240229'
                })
            
            return provider_class(**provider_kwargs)
            
        except Exception as e:
            logger.error(f"Error creating {provider_name} provider: {e}")
            return None
    
    def generate_predictions(self, rag_context: str, portfolio_data: Dict,
                           market_data: Dict, sentiment_data: Dict,
                           financial_data: Optional[Dict] = None) -> Dict:
        """
        Generate predictions using the fallback chain
        """
        if not self.providers:
            logger.error("❌ No LLM providers available - using rule-based fallback")
            return self._generate_emergency_fallback(portfolio_data, market_data, sentiment_data, financial_data)
        
        # Try each provider in the chain
        for provider_name in self.provider_chain:
            try:
                provider = self.providers[provider_name]
                
                # Check if provider is available
                if not provider.is_available():
                    logger.warning(f"⚠️ {provider_name.upper()} provider not available, trying next...")
                    continue
                
                logger.info(f"🤖 Attempting to generate predictions with {provider_name.upper()}...")
                
                # Generate predictions
                predictions = provider.generate_predictions(
                    rag_context, portfolio_data, market_data, sentiment_data, financial_data
                )
                
                # Check if we got valid predictions (not fallback)
                if predictions and not predictions.get('fallback_mode', False):
                    logger.info(f"✅ Successfully generated predictions using {provider_name.upper()}")
                    predictions['provider_used'] = provider_name
                    predictions['fallback_chain'] = self.provider_chain
                    return predictions
                else:
                    logger.warning(f"⚠️ {provider_name.upper()} returned fallback predictions, trying next...")
                    
            except Exception as e:
                logger.error(f"❌ Error with {provider_name}: {e}, trying next...")
                continue
        
        # If all providers failed, use emergency fallback
        logger.error("❌ All LLM providers failed - using emergency rule-based fallback")
        return self._generate_emergency_fallback(portfolio_data, market_data, sentiment_data, financial_data)
    
    def _generate_emergency_fallback(self, portfolio_data: Dict, market_data: Dict,
                                   sentiment_data: Dict, financial_data: Optional[Dict] = None) -> Dict:
        """Emergency fallback when all LLM providers fail"""
        logger.error("🚨 EMERGENCY FALLBACK - All LLM providers failed")
        
        predictions = {
            'individual_recommendations': {},
            'portfolio_analysis': 'Emergency analysis: All AI providers unavailable. Using rule-based recommendations.',
            'action_items': [
                'Check API connectivity and quotas',
                'Verify API keys are valid',
                'Monitor market manually until AI services restore',
                'Consider manual portfolio review'
            ],
            'market_insights': 'Manual market analysis required - All AI services unavailable',
            'timestamp': datetime.now().isoformat(),
            'emergency_fallback': True,
            'provider_used': 'emergency_rules',
            'fallback_chain': self.provider_chain
        }

        # Enhanced rule-based recommendations
        for holding in portfolio_data['holdings']:
            symbol = holding['symbol']
            pnl_percent = holding['pnl_percent']
            sentiment_score = sentiment_data['individual_sentiment'].get(symbol, {}).get('sentiment_score', 0)

            # Get financial health score if available
            financial_score = 5
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
                    reasoning = f'Emergency rule: Strong financials + oversold + neutral sentiment{financial_reasoning}'
                elif financial_score <= 4 and pnl_percent > 15:
                    recommendation = 'SELL'
                    confidence = 7
                    reasoning = f'Emergency rule: Weak financials + overvalued{financial_reasoning}'
                elif pnl_percent > 10 and sentiment_score < -0.2:
                    recommendation = 'SELL'
                    confidence = 6
                    reasoning = f'Emergency rule: High gains + negative sentiment{financial_reasoning}'
                elif pnl_percent < -5 and sentiment_score > 0.2 and financial_score >= 6:
                    recommendation = 'BUY'
                    confidence = 6
                    reasoning = f'Emergency rule: Oversold + positive sentiment + good financials{financial_reasoning}'
                else:
                    recommendation = 'HOLD'
                    confidence = 5
                    reasoning = f'Emergency rule: Neutral conditions{financial_reasoning}'
            else:
                # Basic rules without financials
                if pnl_percent > 15:
                    recommendation = 'SELL'
                    confidence = 6
                elif pnl_percent < -10:
                    recommendation = 'BUY'
                    confidence = 6
                else:
                    recommendation = 'HOLD'
                    confidence = 5
                reasoning = f'Emergency rule: P&L {pnl_percent:.2f}%, Sentiment {sentiment_score:.3f}'

            predictions['individual_recommendations'][symbol] = {
                'recommendation': recommendation,
                'confidence': confidence,
                'reasoning': reasoning
            }

        return predictions
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            'primary_provider': self.primary_provider_name,
            'fallback_providers': self.fallback_provider_names,
            'provider_chain': self.provider_chain,
            'provider_details': {},
            'healthy_providers': 0,
            'total_providers': len(self.providers)
        }
        
        for name, provider in self.providers.items():
            try:
                health = provider.health_check()
                status['provider_details'][name] = health
                if health['healthy']:
                    status['healthy_providers'] += 1
            except Exception as e:
                status['provider_details'][name] = {
                    'provider': name,
                    'healthy': False,
                    'error': str(e)
                }
        
        return status
    
    def get_available_providers(self) -> List[str]:
        """Get list of currently available providers"""
        available = []
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    available.append(name)
            except:
                continue
        return available
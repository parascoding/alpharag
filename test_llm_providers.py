#!/usr/bin/env python3
"""
Test script for LLM providers with fallback chain
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Settings
from src.llm_providers.llm_factory import LLMFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_llm_providers():
    """Test LLM providers and fallback chain"""
    
    try:
        # Load settings
        settings = Settings()
        logger.info("🔧 Settings loaded")
        
        # Get available API keys
        api_keys = settings.get_available_llm_api_keys()
        available_keys = [k for k, v in api_keys.items() if v]
        
        if not available_keys:
            logger.error("❌ No LLM API keys configured")
            logger.info("💡 Please set at least one of: GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY")
            return False
            
        logger.info(f"🔑 Available API keys: {available_keys}")
        
        # Initialize LLM Factory
        logger.info("🚀 Initializing LLM Factory...")
        llm_factory = LLMFactory(
            primary_provider=settings.PRIMARY_LLM_PROVIDER,
            fallback_providers=settings.FALLBACK_LLM_PROVIDERS,
            **api_keys
        )
        
        # Check provider status
        status = llm_factory.get_provider_status()
        logger.info(f"📊 Provider Status: {status['healthy_providers']}/{status['total_providers']} healthy")
        
        for provider, details in status['provider_details'].items():
            health_status = "✅ Healthy" if details['healthy'] else "❌ Unhealthy"
            logger.info(f"   {provider.upper()}: {health_status}")
            
        # Test availability
        available_providers = llm_factory.get_available_providers()
        if not available_providers:
            logger.error("❌ No LLM providers available")
            return False
            
        logger.info(f"🤖 Available providers: {available_providers}")
        
        # Test prediction generation with mock data
        logger.info("\n" + "="*60)
        logger.info("🧪 TESTING PREDICTION GENERATION")
        logger.info("="*60)
        
        # Mock portfolio data
        mock_portfolio_data = {
            'summary': {
                'total_investment': 55000.0,
                'total_current_value': 48500.0,
                'total_pnl': -6500.0,
                'total_pnl_percent': -11.82
            },
            'holdings': [
                {
                    'symbol': 'RELIANCE.NS',
                    'quantity': 10,
                    'buy_price': 2500.0,
                    'current_price': 2350.0,
                    'pnl_percent': -6.0
                },
                {
                    'symbol': 'TCS.NS',
                    'quantity': 5,
                    'buy_price': 3600.0,
                    'current_price': 3800.0,
                    'pnl_percent': 5.56
                }
            ]
        }
        
        # Mock market data
        mock_market_data = {
            'market_status': 'CLOSED',
            'timestamp': datetime.now().isoformat(),
            'prices': {
                'RELIANCE.NS': 2350.0,
                'TCS.NS': 3800.0
            }
        }
        
        # Mock sentiment data
        mock_sentiment_data = {
            'overall_sentiment': {
                'label': 'NEUTRAL',
                'score': 0.1
            },
            'total_articles': 15,
            'individual_sentiment': {
                'RELIANCE.NS': {
                    'sentiment_label': 'POSITIVE',
                    'sentiment_score': 0.3,
                    'article_count': 8
                },
                'TCS.NS': {
                    'sentiment_label': 'NEUTRAL',
                    'sentiment_score': 0.05,
                    'article_count': 7
                }
            }
        }
        
        # Mock financial data
        mock_financial_data = {
            'RELIANCE.NS': {
                'sector': 'Oil & Gas',
                'pe_ratio': 22.4,
                'pb_ratio': 1.8,
                'roe': 12.8,
                'debt_to_equity': 0.65,
                'net_profit_margin': 8.5,
                'health_score': {
                    'overall_score': 6.8,
                    'rating': 'FAIR'
                }
            },
            'TCS.NS': {
                'sector': 'IT Services',
                'pe_ratio': 28.5,
                'pb_ratio': 12.4,
                'roe': 42.8,
                'debt_to_equity': 0.01,
                'net_profit_margin': 25.8,
                'health_score': {
                    'overall_score': 8.5,
                    'rating': 'EXCELLENT'
                }
            }
        }
        
        # Mock RAG context
        mock_rag_context = """
        Portfolio Analysis Context:
        - Current portfolio shows mixed performance with oil & gas underperforming
        - IT sector showing resilience with positive sentiment
        - Market volatility observed in recent weeks
        """
        
        # Generate predictions
        logger.info("🔮 Generating test predictions...")
        predictions = llm_factory.generate_predictions(
            mock_rag_context,
            mock_portfolio_data,
            mock_market_data,
            mock_sentiment_data,
            mock_financial_data
        )
        
        # Display results
        if predictions:
            provider_used = predictions.get('provider_used', 'unknown')
            model_used = predictions.get('model', 'unknown')
            
            print(f"\n✅ PREDICTION RESULTS:")
            print(f"   Provider: {provider_used.upper()}")
            print(f"   Model: {model_used}")
            
            if predictions.get('emergency_fallback', False):
                print("   Mode: 🚨 Emergency Fallback")
            elif predictions.get('fallback_mode', False):
                print("   Mode: ⚠️ Provider Fallback")
            else:
                print("   Mode: ✅ Normal Operation")
                
            print(f"   Timestamp: {predictions.get('timestamp', 'N/A')}")
            
            # Show individual recommendations
            recommendations = predictions.get('individual_recommendations', {})
            if recommendations:
                print(f"\n📈 INDIVIDUAL RECOMMENDATIONS:")
                for symbol, rec in recommendations.items():
                    print(f"   {symbol}: {rec.get('recommendation', 'N/A')} "
                          f"(Confidence: {rec.get('confidence', 'N/A')}/10)")
                    print(f"      Reason: {rec.get('reasoning', 'N/A')[:100]}...")
            
            # Show action items
            action_items = predictions.get('action_items', [])
            if action_items:
                print(f"\n🎯 ACTION ITEMS:")
                for i, item in enumerate(action_items[:3], 1):
                    print(f"   {i}. {item}")
                    
            # Show usage info if available
            if 'usage' in predictions:
                usage = predictions['usage']
                print(f"\n📊 API USAGE:")
                for key, value in usage.items():
                    print(f"   {key}: {value}")
                    
        else:
            logger.error("❌ Failed to generate predictions")
            return False
            
        logger.info("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Testing LLM Providers with Fallback Chain")
    print("="*60)
    
    success = test_llm_providers()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n💡 To use in production:")
        print("   1. Set your preferred LLM API keys in .env")
        print("   2. Configure PRIMARY_LLM_PROVIDER and FALLBACK_LLM_PROVIDERS")
        print("   3. Run: python main.py --mode analyze")
    else:
        print("\n❌ Tests failed!")
        print("\n🔧 Check your configuration:")
        print("   1. Ensure at least one LLM API key is set in .env")
        print("   2. Verify API keys are valid and have quota")
        print("   3. Check network connectivity")

if __name__ == "__main__":
    main()
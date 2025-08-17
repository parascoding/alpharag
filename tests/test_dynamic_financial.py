#!/usr/bin/env python3
"""
Test script for the dynamic financial data provider
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from src.dynamic_financial_data_provider import DynamicFinancialDataProvider
from src.financial_indicators import FinancialIndicatorsFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dynamic_financial_provider():
    """Test the dynamic financial data provider with real portfolio symbols"""
    logger.info("=== Testing Dynamic Financial Data Provider ===")

    try:
        # Test symbols from real portfolio
        test_symbols = ['ACUTAAS.NS', 'CSBBANK.NS', 'ECLERX.NS', 'GOLDBEES.NS']

        # Test 1: Basic Dynamic Provider
        logger.info("\n=== Step 1: Testing Basic Dynamic Provider ===")
        provider = DynamicFinancialDataProvider()

        for symbol in test_symbols:
            logger.info(f"\nTesting {symbol}:")
            try:
                financial_data = provider.get_financial_indicators(symbol)

                print(f"✅ {symbol} Financial Analysis:")
                print(f"   📊 Sector: {financial_data.get('sector', 'Unknown')}")
                print(f"   💰 Current Price: ₹{financial_data.get('current_price', 0):.2f}")
                print(f"   📈 P/E Ratio: {financial_data.get('pe_ratio', 0):.2f}")
                print(f"   📘 P/B Ratio: {financial_data.get('pb_ratio', 0):.2f}")
                print(f"   🔄 ROE: {financial_data.get('roe', 0):.2f}%")
                print(f"   💎 Overall Score: {financial_data.get('overall_score', 0):.1f}/10")
                print(f"   🏆 Rating: {financial_data.get('rating_emoji', '❓')} {financial_data.get('rating', 'Unknown')}")
                print(f"   📊 Data Source: {financial_data.get('data_source', 'Unknown')}")

            except Exception as e:
                print(f"❌ Error for {symbol}: {e}")

        # Test 2: Batch Processing
        logger.info("\n=== Step 2: Testing Batch Processing ===")
        batch_results = provider.get_financial_indicators_batch(test_symbols)

        print(f"\n📊 Batch Results Summary:")
        print(f"   🎯 Symbols Processed: {len(batch_results)}/{len(test_symbols)}")

        # Create a summary table
        print(f"\n{'Symbol':<12} {'Sector':<15} {'P/E':<8} {'P/B':<8} {'ROE':<8} {'Score':<8} {'Rating':<12}")
        print(f"{'-'*12} {'-'*15} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*12}")

        for symbol, data in batch_results.items():
            sector = data.get('sector', 'Unknown')[:14]
            pe = data.get('pe_ratio', 0)
            pb = data.get('pb_ratio', 0)
            roe = data.get('roe', 0)
            score = data.get('overall_score', 0)
            rating = data.get('rating', 'Unknown')[:11]

            print(f"{symbol:<12} {sector:<15} {pe:<8.2f} {pb:<8.2f} {roe:<8.2f} {score:<8.1f} {rating:<12}")

        # Test 3: Integration with Financial Indicators Module
        logger.info("\n=== Step 3: Testing Integration with Financial Indicators Module ===")

        # Test with enhanced financial indicators
        indicators_fetcher = FinancialIndicatorsFetcher(use_real_apis=True)
        enhanced_results = indicators_fetcher.get_financial_indicators(test_symbols)

        print(f"\n🔧 Enhanced Financial Indicators:")
        print(f"   📈 Symbols Processed: {len(enhanced_results)}/{len(test_symbols)}")

        for symbol, data in enhanced_results.items():
            print(f"\n📋 {symbol}:")
            print(f"   🎯 Mode: {data.get('data_source', 'Unknown')}")
            print(f"   🏢 Sector: {data.get('sector', 'Unknown')}")
            print(f"   📊 Valuation Score: {data.get('valuation_score', 0):.1f}/10")
            print(f"   💰 Profitability Score: {data.get('profitability_score', 0):.1f}/10")
            print(f"   🏥 Financial Health: {data.get('financial_health_score', 0):.1f}/10")
            print(f"   📈 Growth Score: {data.get('growth_score', 0):.1f}/10")
            print(f"   🏆 Overall: {data.get('overall_score', 0):.1f}/10 ({data.get('rating', 'Unknown')})")

        # Test 4: Compare with Static vs Dynamic
        logger.info("\n=== Step 4: Comparing Static vs Dynamic Approaches ===")

        static_fetcher = FinancialIndicatorsFetcher(use_real_apis=False)  # Mock data only
        static_results = static_fetcher.get_financial_indicators(['RELIANCE.NS', 'TCS.NS'])  # Known static symbols

        dynamic_results = provider.get_financial_indicators_batch(['RELIANCE.NS', 'TCS.NS'])

        print(f"\n📊 Static vs Dynamic Comparison:")
        print(f"{'Source':<12} {'Symbol':<12} {'P/E':<8} {'P/B':<8} {'Score':<8} {'Rating':<12}")
        print(f"{'-'*12} {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*12}")

        for symbol in ['RELIANCE.NS', 'TCS.NS']:
            # Static data
            if symbol in static_results:
                static_data = static_results[symbol]
                pe = static_data.get('pe_ratio', 0)
                pb = static_data.get('pb_ratio', 0)
                score = static_data.get('overall_score', 0)
                rating = static_data.get('rating', 'Unknown')[:11]
                print(f"{'Static':<12} {symbol:<12} {pe:<8.2f} {pb:<8.2f} {score:<8.1f} {rating:<12}")

            # Dynamic data
            if symbol in dynamic_results:
                dynamic_data = dynamic_results[symbol]
                pe = dynamic_data.get('pe_ratio', 0)
                pb = dynamic_data.get('pb_ratio', 0)
                score = dynamic_data.get('overall_score', 0)
                rating = dynamic_data.get('rating', 'Unknown')[:11]
                print(f"{'Dynamic':<12} {symbol:<12} {pe:<8.2f} {pb:<8.2f} {score:<8.1f} {rating:<12}")

        logger.info("✅ Dynamic financial data provider test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error in dynamic financial test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Dynamic Financial Data Provider")

    success = test_dynamic_financial_provider()

    if success:
        print("\n🎉 Dynamic financial data provider test completed!")
    else:
        print("\n❌ Dynamic financial data provider test failed!")
        sys.exit(1)
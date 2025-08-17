#!/usr/bin/env python3
"""
Test script for Upstox-based financial ratio calculations
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import Settings
from src.data_providers.provider_factory import DataProviderFactory
from src.upstox_financial_calculator import UpstoxFinancialCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_upstox_financial_ratios():
    """Test Upstox-based financial ratio calculations"""

    try:
        # Load settings
        settings = Settings()
        logger.info("🔧 Settings loaded")

        # Check if Upstox is configured
        if not settings.UPSTOX_ACCESS_TOKEN:
            logger.error("❌ UPSTOX_ACCESS_TOKEN not configured")
            logger.info("💡 To test, set UPSTOX_ACCESS_TOKEN in .env file")
            return False

        # Initialize Upstox provider
        logger.info("🚀 Initializing Upstox provider...")
        provider_factory = DataProviderFactory()
        upstox_provider = provider_factory.create_provider(
            'upstox',
            access_token=settings.UPSTOX_ACCESS_TOKEN
        )

        # Test provider availability
        if not upstox_provider.is_available():
            logger.error("❌ Upstox provider not available")
            return False

        logger.info("✅ Upstox provider initialized and available")

        # Initialize financial calculator
        calculator = UpstoxFinancialCalculator(upstox_provider)
        logger.info("✅ Financial calculator initialized")

        # Test symbols
        test_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']

        # Test supported symbols
        supported_symbols = calculator.get_supported_symbols()
        logger.info(f"📊 Supported symbols: {supported_symbols}")

        # Test individual ratio calculation
        logger.info("\n" + "="*60)
        logger.info("🧮 TESTING INDIVIDUAL RATIO CALCULATIONS")
        logger.info("="*60)

        for symbol in test_symbols:
            if symbol in supported_symbols:
                logger.info(f"\n📈 Calculating ratios for {symbol}...")
                ratios = calculator.calculate_basic_ratios(symbol)

                if ratios:
                    print(f"\n✅ {symbol} Financial Ratios:")
                    print(f"   Current Price: ₹{ratios.get('current_price', 0):,.2f}")
                    print(f"   PE Ratio: {ratios.get('pe_ratio', 0)}")
                    print(f"   PB Ratio: {ratios.get('pb_ratio', 0)}")
                    print(f"   ROE: {ratios.get('roe', 0):.2f}%")
                    print(f"   Debt/Equity: {ratios.get('debt_to_equity', 0)}")
                    print(f"   Net Margin: {ratios.get('net_profit_margin', 0):.2f}%")
                    print(f"   Market Cap: ₹{ratios.get('market_cap_cr', 0):,.0f} Cr")
                    print(f"   Overall Score: {ratios.get('overall_score', 0)}/10 ({ratios.get('rating', 'N/A')})")
                    print(f"   Data Source: {ratios.get('data_source', 'unknown')}")
                else:
                    logger.warning(f"⚠️ No ratios calculated for {symbol}")
            else:
                logger.warning(f"⚠️ {symbol} not supported by calculator")

        # Test batch calculation
        logger.info("\n" + "="*60)
        logger.info("📊 TESTING BATCH RATIO CALCULATIONS")
        logger.info("="*60)

        batch_results = calculator.get_financial_indicators_batch(test_symbols)

        if batch_results:
            print(f"\n✅ Batch calculation successful for {len(batch_results)} symbols:")
            for symbol, data in batch_results.items():
                print(f"\n📈 {symbol}:")
                print(f"   PE: {data.get('pe_ratio', 0)} | PB: {data.get('pb_ratio', 0)} | ROE: {data.get('roe', 0):.1f}%")
                print(f"   Score: {data.get('overall_score', 0)}/10 ({data.get('rating_emoji', '')} {data.get('rating', 'N/A')})")
        else:
            logger.error("❌ Batch calculation failed")

        # Test data freshness
        logger.info("\n" + "="*60)
        logger.info("📅 DATA FRESHNESS CHECK")
        logger.info("="*60)

        for symbol in supported_symbols:
            freshness = calculator.get_data_freshness(symbol)
            print(f"   {symbol}: {freshness}")

        logger.info("\n🎉 Test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Testing Upstox Financial Ratio Calculations")
    print("="*60)

    success = test_upstox_financial_ratios()

    if success:
        print("\n✅ All tests passed!")
        print("\n💡 To use in production:")
        print("   1. Set USE_REAL_FINANCIAL_APIS=true in .env")
        print("   2. Set PRIMARY_DATA_PROVIDER=upstox in .env")
        print("   3. Run: python main.py --mode analyze")
    else:
        print("\n❌ Tests failed!")
        print("\n🔧 Check your configuration:")
        print("   1. Ensure UPSTOX_ACCESS_TOKEN is set in .env")
        print("   2. Verify Upstox API access is working")
        print("   3. Check network connectivity")

if __name__ == "__main__":
    main()
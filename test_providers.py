#!/usr/bin/env python3
"""
Test script for data providers - incremental testing
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_base_provider_interface():
    """Test that the base provider interface is working"""
    print("🧪 Testing Base Data Provider Interface...")

    try:
        from src.data_providers.base_provider import BaseDataProvider
        print("✅ Successfully imported BaseDataProvider")

        # Test that it's abstract (can't be instantiated)
        try:
            provider = BaseDataProvider("test")
            print("❌ ERROR: BaseDataProvider should not be instantiable")
            return False
        except TypeError as e:
            print(f"✅ BaseDataProvider is properly abstract: {e}")

        print("✅ Base provider interface test passed!")
        return True

    except Exception as e:
        print(f"❌ Base provider test failed: {e}")
        return False

def test_yfinance_provider():
    """Test yfinance provider implementation"""
    print("\n🧪 Testing YFinance Provider...")

    try:
        from src.data_providers.yfinance_provider import YFinanceProvider
        print("✅ Successfully imported YFinanceProvider")

        # Create provider instance
        provider = YFinanceProvider()
        print(f"✅ Created provider: {provider.name}")

        # Test availability
        print("🔍 Testing provider availability...")
        available = provider.is_available()
        print(f"{'✅' if available else '⚠️ '} Provider available: {available}")

        if available:
            # Test with a reliable Indian stock
            test_symbol = "RELIANCE.NS"
            print(f"\n📊 Testing current price for {test_symbol}...")

            price = provider.get_current_price(test_symbol)
            if price and price > 0:
                print(f"✅ Current price: ₹{price:.2f}")
            else:
                print("⚠️  Could not fetch current price (might be market closed)")

            # Test company info
            print(f"\n🏢 Testing company info for {test_symbol}...")
            info = provider.get_company_info(test_symbol)
            if info:
                print(f"✅ Company: {info.get('name', 'N/A')}")
                print(f"   Sector: {info.get('sector', 'N/A')}")
                print(f"   Market Cap: {info.get('market_cap', 0):,}")
            else:
                print("⚠️  Could not fetch company info")

        print("✅ YFinance provider test completed!")
        return True

    except Exception as e:
        print(f"❌ YFinance provider test failed: {e}")
        return False

def test_multiple_symbols():
    """Test fetching multiple symbols"""
    print("\n🧪 Testing Multiple Symbols...")

    try:
        from src.data_providers.yfinance_provider import YFinanceProvider

        provider = YFinanceProvider()
        test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

        print(f"📊 Testing prices for: {', '.join(test_symbols)}")
        prices = provider.get_current_prices(test_symbols)

        success_count = 0
        for symbol, price in prices.items():
            if price > 0:
                print(f"✅ {symbol}: ₹{price:.2f}")
                success_count += 1
            else:
                print(f"⚠️  {symbol}: No price data")

        print(f"✅ Successfully fetched {success_count}/{len(test_symbols)} prices")
        return True

    except Exception as e:
        print(f"❌ Multiple symbols test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting incremental data provider tests...")

    tests = [
        test_base_provider_interface,
        test_yfinance_provider,
        test_multiple_symbols
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    if all(results):
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {sum(results)}/{len(results)} tests passed")
        sys.exit(1)
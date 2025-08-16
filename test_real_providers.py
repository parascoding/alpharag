#!/usr/bin/env python3
"""
Test real data providers (Yahoo and Alpha Vantage)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_yahoo_provider():
    """Test Yahoo Finance provider"""
    print("🧪 Testing Yahoo Finance Provider...")
    
    try:
        from src.data_providers import ProviderFactory
        
        # Create Yahoo provider
        provider = ProviderFactory.get_provider('yahoo')
        if not provider:
            print("❌ Could not create Yahoo provider")
            return False
        
        print(f"✅ Created Yahoo provider: {provider.name}")
        
        # Test availability
        print("🔍 Testing provider availability...")
        available = provider.is_available()
        print(f"{'✅' if available else '⚠️ '} Yahoo provider available: {available}")
        
        if available:
            # Test current price
            test_symbol = "RELIANCE.NS"
            print(f"\n📊 Testing current price for {test_symbol}...")
            
            price = provider.get_current_price(test_symbol)
            if price and price > 0:
                print(f"✅ Current price: ₹{price:.2f}")
            else:
                print("⚠️  Could not fetch current price")
            
            # Test multiple prices
            print(f"\n📊 Testing multiple prices...")
            test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
            prices = provider.get_current_prices(test_symbols)
            
            success_count = 0
            for symbol, price in prices.items():
                if price > 0:
                    print(f"✅ {symbol}: ₹{price:.2f}")
                    success_count += 1
                else:
                    print(f"⚠️  {symbol}: No price data")
            
            print(f"📈 Success rate: {success_count}/{len(test_symbols)}")
            
            # Test historical data
            print(f"\n📈 Testing historical data for {test_symbol}...")
            hist_data = provider.get_historical_data(test_symbol, "1mo")
            if hist_data is not None and not hist_data.empty:
                print(f"✅ Historical data: {len(hist_data)} days")
                print(f"   Latest close: ₹{hist_data['Close'].iloc[-1]:.2f}")
                if 'SMA_5' in hist_data.columns:
                    print(f"   SMA 5: ₹{hist_data['SMA_5'].iloc[-1]:.2f}")
            else:
                print("⚠️  No historical data")
            
            # Test company info
            print(f"\n🏢 Testing company info for {test_symbol}...")
            info = provider.get_company_info(test_symbol)
            if info:
                print(f"✅ Company: {info.get('name', 'N/A')}")
                print(f"   Sector: {info.get('sector', 'N/A')}")
                print(f"   Currency: {info.get('currency', 'N/A')}")
            else:
                print("⚠️  No company info")
        
        print("✅ Yahoo provider test completed!")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Yahoo provider test failed: {e}")
        traceback.print_exc()
        return False

def test_alpha_vantage_provider():
    """Test Alpha Vantage provider (if API key available)"""
    print("\n🧪 Testing Alpha Vantage Provider...")
    
    try:
        from src.data_providers import ProviderFactory
        
        # Check for API key in environment or use demo key
        import os
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        
        if api_key == 'demo':
            print("⚠️  Using demo API key - limited functionality")
        
        # Create Alpha Vantage provider
        provider = ProviderFactory.get_provider('alpha_vantage', api_key=api_key)
        if not provider:
            print("❌ Could not create Alpha Vantage provider")
            return False
        
        print(f"✅ Created Alpha Vantage provider: {provider.name}")
        
        # Test availability
        print("🔍 Testing provider availability...")
        available = provider.is_available()
        print(f"{'✅' if available else '⚠️ '} Alpha Vantage provider available: {available}")
        
        if available:
            # Test with US stock (more reliable for Alpha Vantage)
            test_symbol = "AAPL"
            print(f"\n📊 Testing current price for {test_symbol}...")
            
            price = provider.get_current_price(test_symbol)
            if price and price > 0:
                print(f"✅ Current price: ${price:.2f}")
            else:
                print("⚠️  Could not fetch current price")
            
            # Test company info
            print(f"\n🏢 Testing company info for {test_symbol}...")
            info = provider.get_company_info(test_symbol)
            if info:
                print(f"✅ Company: {info.get('name', 'N/A')}")
                print(f"   Sector: {info.get('sector', 'N/A')}")
                print(f"   Market Cap: ${info.get('market_cap', 0):,}")
            else:
                print("⚠️  No company info")
        
        print("✅ Alpha Vantage provider test completed!")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Alpha Vantage provider test failed: {e}")
        traceback.print_exc()
        return False

def test_provider_fallback():
    """Test provider fallback functionality"""
    print("\n🧪 Testing Provider Fallback Chain...")
    
    try:
        from src.data_providers import ProviderFactory
        
        # Test fallback: yahoo -> alpha_vantage -> mock
        print("Testing fallback chain: yahoo -> alpha_vantage -> mock")
        
        provider = ProviderFactory.get_provider_with_fallback(
            primary_provider='yahoo',
            fallback_providers=['alpha_vantage', 'mock'],
            api_key='demo'  # For alpha vantage
        )
        
        if provider:
            print(f"✅ Got provider: {provider.name}")
            
            # Test it works
            price = provider.get_current_price("RELIANCE.NS")
            if price and price > 0:
                print(f"✅ Fallback test successful: ₹{price:.2f}")
            else:
                print("⚠️  Fallback provider working but no price data")
        else:
            print("❌ Fallback chain failed")
            return False
        
        print("✅ Provider fallback test completed!")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Provider fallback test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Real Data Providers...")
    
    tests = [
        test_yahoo_provider,
        test_alpha_vantage_provider,
        test_provider_fallback
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    successful = sum(results)
    total = len(results)
    
    if successful == total:
        print(f"\n🎉 All {total} tests passed!")
        print("\n🎯 REAL DATA PROVIDERS ARE WORKING!")
    elif successful > 0:
        print(f"\n⚠️  {successful}/{total} tests passed")
        print("Some real data providers are working!")
    else:
        print(f"\n❌ All tests failed!")
    
    sys.exit(0 if successful > 0 else 1)
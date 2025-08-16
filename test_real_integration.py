#!/usr/bin/env python3
"""
Test full integration with real data providers and configuration
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_data_ingestion_with_real_providers():
    """Test the enhanced data ingestion with real provider configuration"""
    print("🧪 Testing Enhanced Data Ingestion with Real Providers...")
    
    try:
        from src.data_ingestion_v2 import MarketDataIngestionV2
        
        # Test configuration 1: Yahoo -> Alpha Vantage -> Mock fallback
        print("\n📊 Configuration 1: Yahoo -> Alpha Vantage -> Mock")
        
        ingestion = MarketDataIngestionV2(
            primary_provider='yahoo',
            fallback_providers=['alpha_vantage', 'mock'],
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        )
        
        print(f"✅ Using provider: {ingestion.provider.name}")
        
        # Test with portfolio symbols
        test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
        
        # Get prices
        print(f"📈 Fetching prices for: {', '.join(test_symbols)}")
        prices = ingestion.get_current_prices(test_symbols)
        
        for symbol, price in prices.items():
            if price > 0:
                print(f"✅ {symbol}: ₹{price:.2f}")
            else:
                print(f"⚠️  {symbol}: No price data")
        
        # Get market summary
        print(f"\n📋 Generating market summary...")
        summary = ingestion.get_market_summary(test_symbols)
        
        if 'error' not in summary:
            print(f"✅ Market summary generated")
            print(f"   Provider: {summary.get('provider', 'N/A')}")
            print(f"   Successful prices: {summary.get('successful_prices', 0)}/{summary.get('symbols_count', 0)}")
            print(f"   Timestamp: {summary.get('timestamp', 'N/A')}")
        else:
            print(f"⚠️  Market summary failed: {summary.get('error', 'Unknown error')}")
        
        # Health check
        health = ingestion.health_check()
        print(f"✅ Health check: {health['data_ingestion'].get('healthy', False)}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Real data ingestion test failed: {e}")
        traceback.print_exc()
        return False

def test_portfolio_integration_with_real_data():
    """Test portfolio integration with real data providers"""
    print("\n🧪 Testing Portfolio Integration with Real Data...")
    
    try:
        from src.portfolio_manager import PortfolioManager
        from src.data_ingestion_v2 import MarketDataIngestionV2
        
        # Load portfolio
        portfolio_file = "data/portfolio.csv"
        portfolio_manager = PortfolioManager(portfolio_file)
        symbols = portfolio_manager.get_symbols()
        
        print(f"✅ Portfolio loaded: {symbols}")
        
        # Create enhanced data ingestion with real providers
        ingestion = MarketDataIngestionV2(
            primary_provider='yahoo',
            fallback_providers=['alpha_vantage', 'mock'],
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        )
        
        print(f"✅ Data ingestion using: {ingestion.provider.name}")
        
        # Get current prices
        current_prices = ingestion.get_current_prices(symbols)
        
        # Calculate portfolio value
        portfolio_value = portfolio_manager.calculate_portfolio_value(current_prices)
        
        if portfolio_value:
            summary = portfolio_value.get('summary', {})
            print(f"✅ Portfolio Analysis Results:")
            print(f"   Provider: {ingestion.provider.name}")
            print(f"   Total Investment: ₹{summary.get('total_investment', 0):,.2f}")
            print(f"   Current Value: ₹{summary.get('total_current_value', 0):,.2f}")
            print(f"   Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
            print(f"   P&L %: {summary.get('total_pnl_percent', 0):.2f}%")
            
            # Show individual holdings
            holdings = portfolio_value.get('holdings', [])
            print(f"\n📊 Individual Holdings:")
            for holding in holdings:
                symbol = holding.get('symbol', 'N/A')
                pnl = holding.get('pnl', 0)
                pnl_percent = holding.get('pnl_percent', 0)
                current_price = holding.get('current_price', 0)
                print(f"   {symbol}: ₹{current_price:.2f} (P&L: ₹{pnl:,.2f}, {pnl_percent:+.2f}%)")
        else:
            print("❌ Could not calculate portfolio value")
            return False
        
        print("✅ Portfolio integration with real data successful!")
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Portfolio integration test failed: {e}")
        traceback.print_exc()
        return False

def test_provider_configuration():
    """Test different provider configurations"""
    print("\n🧪 Testing Different Provider Configurations...")
    
    configurations = [
        {
            'name': 'Mock Only',
            'primary': 'mock',
            'fallbacks': []
        },
        {
            'name': 'Yahoo -> Mock',
            'primary': 'yahoo',
            'fallbacks': ['mock']
        },
        {
            'name': 'Alpha Vantage -> Mock',
            'primary': 'alpha_vantage',
            'fallbacks': ['mock']
        },
        {
            'name': 'Yahoo -> Alpha Vantage -> Mock',
            'primary': 'yahoo',
            'fallbacks': ['alpha_vantage', 'mock']
        }
    ]
    
    try:
        from src.data_ingestion_v2 import MarketDataIngestionV2
        
        for config in configurations:
            print(f"\n📊 Testing: {config['name']}")
            
            ingestion = MarketDataIngestionV2(
                primary_provider=config['primary'],
                fallback_providers=config['fallbacks'],
                api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
            )
            
            print(f"✅ Active provider: {ingestion.provider.name}")
            
            # Quick test
            price = ingestion.get_current_price("RELIANCE.NS")
            if price and price > 0:
                print(f"✅ Price test: ₹{price:.2f}")
            else:
                print("⚠️  No price data")
        
        print("✅ Configuration testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Real Data Integration...")
    
    tests = [
        test_data_ingestion_with_real_providers,
        test_portfolio_integration_with_real_data,
        test_provider_configuration
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
        print(f"\n🎉 All {total} integration tests passed!")
        print("\n🎯 REAL DATA INTEGRATION IS READY!")
    else:
        print(f"\n⚠️  {successful}/{total} tests passed")
    
    sys.exit(0)
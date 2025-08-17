#!/usr/bin/env python3
"""
Test integration with existing portfolio workflow
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_new_data_ingestion():
    """Test the new data ingestion system"""
    print("🧪 Testing New Data Ingestion System...")

    try:
        from src.data_ingestion_v2 import MarketDataIngestionV2
        print("✅ Successfully imported MarketDataIngestionV2")

        # Create ingestion instance
        ingestion = MarketDataIngestionV2(primary_provider='mock')
        print(f"✅ Created ingestion with provider: {ingestion.provider.name}")

        # Test with portfolio symbols
        test_symbols = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]

        # Test current prices
        print(f"\n📊 Testing current prices for: {', '.join(test_symbols)}")
        prices = ingestion.get_current_prices(test_symbols)

        for symbol, price in prices.items():
            if price > 0:
                print(f"✅ {symbol}: ₹{price:.2f}")
            else:
                print(f"⚠️  {symbol}: No price data")

        # Test individual price
        print(f"\n💰 Testing individual price fetch...")
        single_price = ingestion.get_current_price("RELIANCE.NS")
        if single_price:
            print(f"✅ RELIANCE.NS individual fetch: ₹{single_price:.2f}")

        # Test historical data
        print(f"\n📈 Testing historical data...")
        hist_data = ingestion.get_historical_data("RELIANCE.NS", "1mo")
        if hist_data is not None and not hist_data.empty:
            print(f"✅ Historical data: {len(hist_data)} days")
            print(f"   Latest close: ₹{hist_data['Close'].iloc[-1]:.2f}")
            if 'SMA_5' in hist_data.columns:
                print(f"   SMA 5: ₹{hist_data['SMA_5'].iloc[-1]:.2f}")
        else:
            print("⚠️  No historical data available")

        # Test company info
        print(f"\n🏢 Testing company info...")
        company_info = ingestion.get_company_info("RELIANCE.NS")
        if company_info:
            print(f"✅ Company: {company_info.get('name', 'N/A')}")
            print(f"   Sector: {company_info.get('sector', 'N/A')}")
            print(f"   Market Cap: ₹{company_info.get('market_cap', 0):,}")
        else:
            print("⚠️  No company info available")

        # Test market summary
        print(f"\n📋 Testing market summary...")
        summary = ingestion.get_market_summary(test_symbols)
        if 'error' not in summary:
            print(f"✅ Market summary generated")
            print(f"   Provider: {summary.get('provider', 'N/A')}")
            print(f"   Successful prices: {summary.get('successful_prices', 0)}/{summary.get('symbols_count', 0)}")
            print(f"   Timestamp: {summary.get('timestamp', 'N/A')}")
        else:
            print(f"⚠️  Market summary failed: {summary.get('error', 'Unknown error')}")

        # Test health check
        print(f"\n🏥 Testing health check...")
        health = ingestion.health_check()
        ingestion_health = health.get('data_ingestion', {})
        provider_health = health.get('provider_health', {})

        print(f"✅ Health check completed")
        print(f"   Ingestion healthy: {ingestion_health.get('healthy', False)}")
        print(f"   Provider healthy: {provider_health.get('healthy', False)}")
        print(f"   Cache size: {ingestion_health.get('cache_size', 0)}")

        print("✅ New data ingestion system tests passed!")
        return True

    except Exception as e:
        import traceback
        print(f"❌ New data ingestion test failed: {e}")
        traceback.print_exc()
        return False

def test_compatibility_with_portfolio():
    """Test compatibility with existing portfolio manager"""
    print("\n🧪 Testing Compatibility with Portfolio Manager...")

    try:
        from src.portfolio_manager import PortfolioManager
        from src.data_ingestion_v2 import MarketDataIngestionV2

        # Create portfolio manager
        portfolio_file = "data/portfolio.csv"
        portfolio_manager = PortfolioManager(portfolio_file)
        print("✅ Portfolio manager loaded")

        # Get portfolio symbols
        symbols = portfolio_manager.get_symbols()
        print(f"✅ Portfolio symbols: {symbols}")

        # Create new data ingestion
        ingestion = MarketDataIngestionV2(primary_provider='mock')

        # Get current prices using new system
        current_prices = ingestion.get_current_prices(symbols)
        print(f"✅ Fetched prices using new system: {len(current_prices)} symbols")

        # Calculate portfolio value using new prices
        portfolio_value = portfolio_manager.calculate_portfolio_value(current_prices)

        if portfolio_value:
            summary = portfolio_value.get('summary', {})
            print(f"✅ Portfolio value calculated:")
            print(f"   Total Investment: ₹{summary.get('total_investment', 0):,.2f}")
            print(f"   Current Value: ₹{summary.get('total_current_value', 0):,.2f}")
            print(f"   Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
            print(f"   P&L %: {summary.get('total_pnl_percent', 0):.2f}%")
        else:
            print("⚠️  Could not calculate portfolio value")
            return False

        print("✅ Portfolio compatibility test passed!")
        return True

    except Exception as e:
        import traceback
        print(f"❌ Portfolio compatibility test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Integration with Existing System...")

    tests = [
        test_new_data_ingestion,
        test_compatibility_with_portfolio
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
        print("\n🎉 All integration tests passed!")
        print("\n🎯 READY TO REPLACE EXISTING DATA INGESTION!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {sum(results)}/{len(results)} tests passed")
        sys.exit(1)
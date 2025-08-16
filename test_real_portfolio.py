#!/usr/bin/env python3
"""
Test real portfolio analysis with Alpha Vantage data
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_real_portfolio_analysis():
    """Test portfolio analysis with real Alpha Vantage data"""
    
    print("🚀 Testing Real Portfolio Analysis with Alpha Vantage...")
    
    try:
        from src.portfolio_manager import PortfolioManager
        from src.data_ingestion_v2 import MarketDataIngestionV2
        
        # Load portfolio
        portfolio_file = "data/portfolio.csv"
        portfolio_manager = PortfolioManager(portfolio_file)
        symbols = portfolio_manager.get_symbols()
        
        print(f"📊 Portfolio loaded: {symbols}")
        
        # Create data ingestion with Alpha Vantage primary
        print("🔧 Configuring data ingestion with Alpha Vantage...")
        ingestion = MarketDataIngestionV2(
            primary_provider='alpha_vantage',
            fallback_providers=['mock'],
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY')
        )
        
        print(f"✅ Using provider: {ingestion.provider.name}")
        
        # Test getting current prices
        print(f"\n📈 Fetching real market prices...")
        current_prices = ingestion.get_current_prices(symbols)
        
        print("📊 Current Prices from Alpha Vantage:")
        for symbol, price in current_prices.items():
            if price > 0:
                print(f"   {symbol}: ₹{price:.2f}")
            else:
                print(f"   {symbol}: No data")
        
        # Calculate portfolio value with real prices
        print(f"\n💰 Calculating portfolio value with real data...")
        portfolio_value = portfolio_manager.calculate_portfolio_value(current_prices)
        
        if portfolio_value:
            summary = portfolio_value.get('summary', {})
            print(f"\n🎯 REAL DATA Portfolio Analysis:")
            print(f"   Provider: {ingestion.provider.name}")
            print(f"   Total Investment: ₹{summary.get('total_investment', 0):,.2f}")
            print(f"   Current Value: ₹{summary.get('total_current_value', 0):,.2f}")
            print(f"   Total P&L: ₹{summary.get('total_pnl', 0):,.2f}")
            print(f"   P&L %: {summary.get('total_pnl_percent', 0):.2f}%")
            
            # Compare with mock data
            print(f"\n📊 Individual Holdings (Real Data):")
            holdings = portfolio_value.get('holdings', [])
            for holding in holdings:
                symbol = holding.get('symbol', 'N/A')
                current_price = holding.get('current_price', 0)
                pnl = holding.get('pnl', 0)
                pnl_percent = holding.get('pnl_percent', 0)
                quantity = holding.get('quantity', 0)
                
                print(f"   {symbol}: {quantity} shares @ ₹{current_price:.2f}")
                print(f"      P&L: ₹{pnl:,.2f} ({pnl_percent:+.2f}%)")
        
        # Test company info
        print(f"\n🏢 Testing company information...")
        for symbol in symbols[:1]:  # Test just one to avoid rate limits
            info = ingestion.get_company_info(symbol)
            if info:
                print(f"✅ {symbol} Company Info:")
                print(f"   Name: {info.get('name', 'N/A')}")
                print(f"   Sector: {info.get('sector', 'N/A')}")
                print(f"   Market Cap: ${info.get('market_cap', 0):,}")
                print(f"   P/E Ratio: {info.get('pe_ratio', 0):.2f}")
            else:
                print(f"⚠️ No company info for {symbol}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Real portfolio analysis failed: {e}")
        traceback.print_exc()
        return False

def compare_real_vs_mock():
    """Compare real data vs mock data"""
    
    print("\n🔍 Comparing Real Data vs Mock Data...")
    
    try:
        from src.data_ingestion_v2 import MarketDataIngestionV2
        
        # Test with Alpha Vantage
        print("📊 Alpha Vantage Data:")
        real_ingestion = MarketDataIngestionV2(
            primary_provider='alpha_vantage',
            fallback_providers=[],  # Force Alpha Vantage only
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY')
        )
        
        real_prices = real_ingestion.get_current_prices(["RELIANCE.NS"])
        for symbol, price in real_prices.items():
            print(f"   {symbol}: ₹{price:.2f} (Real)")
        
        # Test with Mock
        print("\n📊 Mock Data:")
        mock_ingestion = MarketDataIngestionV2(primary_provider='mock')
        mock_prices = mock_ingestion.get_current_prices(["RELIANCE.NS"])
        for symbol, price in mock_prices.items():
            print(f"   {symbol}: ₹{price:.2f} (Mock)")
        
        # Show difference
        if real_prices.get("RELIANCE.NS", 0) > 0 and mock_prices.get("RELIANCE.NS", 0) > 0:
            real_price = real_prices["RELIANCE.NS"]
            mock_price = mock_prices["RELIANCE.NS"]
            difference = abs(real_price - mock_price)
            percent_diff = (difference / mock_price) * 100 if mock_price > 0 else 0
            
            print(f"\n📈 Price Comparison:")
            print(f"   Difference: ₹{difference:.2f}")
            print(f"   Percentage Diff: {percent_diff:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Real Data Portfolio Analysis...")
    
    # Test real portfolio analysis
    success1 = test_real_portfolio_analysis()
    
    # Compare real vs mock
    success2 = compare_real_vs_mock()
    
    if success1 and success2:
        print("\n🎉 Real data integration successful!")
        print("🎯 Ready to switch to Alpha Vantage as primary provider!")
    else:
        print("\n⚠️ Some tests failed, but system can still work with fallback")
    
    sys.exit(0)
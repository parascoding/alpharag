#!/usr/bin/env python3
"""
Direct test of Alpha Vantage API with the configured key
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_alpha_vantage_direct():
    """Test Alpha Vantage API directly"""
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    print(f"🔑 API Key: {api_key[:8]}***" if api_key else "❌ No API key found")
    
    if not api_key:
        print("Please set ALPHA_VANTAGE_API_KEY in .env file")
        return False
    
    try:
        from src.data_providers.alpha_vantage_provider import AlphaVantageProvider
        
        # Create provider with real API key
        provider = AlphaVantageProvider(api_key=api_key)
        print(f"✅ Created Alpha Vantage provider")
        
        # Test availability
        print("🔍 Testing provider availability...")
        available = provider.is_available()
        print(f"{'✅' if available else '❌'} Alpha Vantage available: {available}")
        
        if available:
            # Test with a US stock first (more reliable)
            print("\n📊 Testing US stock (AAPL)...")
            us_price = provider.get_current_price("AAPL")
            if us_price:
                print(f"✅ AAPL price: ${us_price:.2f}")
            else:
                print("⚠️ Could not fetch AAPL price")
            
            # Test with Indian stock
            print("\n📊 Testing Indian stock (RELIANCE.NS)...")
            indian_price = provider.get_current_price("RELIANCE.NS")
            if indian_price:
                print(f"✅ RELIANCE.NS price: ₹{indian_price:.2f}")
            else:
                print("⚠️ Could not fetch RELIANCE.NS price")
            
            # Test company info
            print("\n🏢 Testing company info (AAPL)...")
            info = provider.get_company_info("AAPL")
            if info:
                print(f"✅ Company: {info.get('name', 'N/A')}")
                print(f"   Sector: {info.get('sector', 'N/A')}")
                print(f"   Market Cap: ${info.get('market_cap', 0):,}")
            else:
                print("⚠️ Could not fetch company info")
        
        return available
        
    except Exception as e:
        import traceback
        print(f"❌ Alpha Vantage test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Alpha Vantage API with Real Key...")
    success = test_alpha_vantage_direct()
    
    if success:
        print("\n🎉 Alpha Vantage is working with real data!")
    else:
        print("\n❌ Alpha Vantage test failed!")
    
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Debug test for providers
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

try:
    print("Testing mock provider...")
    from src.data_providers.mock_provider import MockProvider
    print("✅ Mock provider imported successfully")

    provider = MockProvider()
    print(f"✅ Provider created: {provider.name}")

    print("Testing availability...")
    available = provider.is_available()
    print(f"✅ Available: {available}")

    print("Testing current price...")
    price = provider.get_current_price("RELIANCE.NS")
    print(f"✅ RELIANCE.NS price: ₹{price:.2f}")

    print("Testing multiple prices...")
    prices = provider.get_current_prices(["RELIANCE.NS", "TCS.NS", "INFY.NS"])
    for symbol, price in prices.items():
        print(f"   {symbol}: ₹{price:.2f}")

    print("Testing company info...")
    info = provider.get_company_info("RELIANCE.NS")
    if info:
        print(f"   Company: {info['name']}")
        print(f"   Sector: {info['sector']}")

    print("✅ All mock provider tests passed!")

except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    print("Full traceback:")
    traceback.print_exc()
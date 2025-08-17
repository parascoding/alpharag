#!/usr/bin/env python3
"""
Simple test for yfinance compatibility
"""

try:
    print("Testing yfinance import...")
    import yfinance as yf
    print("✅ yfinance imported successfully!")

    print("Testing basic functionality...")
    # Test with a simple ticker
    ticker = yf.Ticker("RELIANCE.NS")
    print("✅ Ticker created")

    # Try to get basic info
    print("Fetching basic info...")
    info = ticker.info
    if info:
        print(f"✅ Info fetched - Company: {info.get('longName', 'N/A')}")

    # Try to get current data
    print("Fetching current price...")
    hist = ticker.history(period="1d")
    if not hist.empty:
        current_price = hist['Close'].iloc[-1]
        print(f"✅ Current price: ₹{current_price:.2f}")
    else:
        print("⚠️ No price data (might be market closed)")

    print("🎉 yfinance is working!")

except Exception as e:
    import traceback
    print(f"❌ yfinance test failed: {e}")
    traceback.print_exc()
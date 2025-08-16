#!/usr/bin/env python3
"""
Configuration script for data providers
Easy way to test and configure different data sources
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def show_provider_configurations():
    """Display available provider configurations"""

    print("🔧 AlphaRAG Data Provider Configurations")
    print("=" * 50)

    configs = {
        'development': {
            'description': 'Mock data for development/testing',
            'primary_provider': 'mock',
            'fallback_providers': [],
            'requirements': 'None - always works'
        },
        'basic_real': {
            'description': 'Alpha Vantage with mock fallback',
            'primary_provider': 'alpha_vantage',
            'fallback_providers': ['mock'],
            'requirements': 'ALPHA_VANTAGE_API_KEY environment variable'
        },
        'production': {
            'description': 'Yahoo -> Alpha Vantage -> Mock fallback chain',
            'primary_provider': 'yahoo',
            'fallback_providers': ['alpha_vantage', 'mock'],
            'requirements': 'ALPHA_VANTAGE_API_KEY (optional but recommended)'
        },
        'alpha_only': {
            'description': 'Alpha Vantage only (no fallback)',
            'primary_provider': 'alpha_vantage',
            'fallback_providers': [],
            'requirements': 'Valid ALPHA_VANTAGE_API_KEY required'
        }
    }

    for name, config in configs.items():
        print(f"\n📊 {name.upper()}")
        print(f"   Description: {config['description']}")
        print(f"   Primary: {config['primary_provider']}")
        print(f"   Fallbacks: {config['fallback_providers']}")
        print(f"   Requirements: {config['requirements']}")

    print("\n" + "=" * 50)

def test_configuration(config_name: str):
    """Test a specific configuration"""

    configs = {
        'development': {
            'primary_provider': 'mock',
            'fallback_providers': []
        },
        'basic_real': {
            'primary_provider': 'alpha_vantage',
            'fallback_providers': ['mock']
        },
        'production': {
            'primary_provider': 'yahoo',
            'fallback_providers': ['alpha_vantage', 'mock']
        },
        'alpha_only': {
            'primary_provider': 'alpha_vantage',
            'fallback_providers': []
        }
    }

    if config_name not in configs:
        print(f"❌ Unknown configuration: {config_name}")
        print(f"Available: {list(configs.keys())}")
        return False

    try:
        from src.data_ingestion_v2 import MarketDataIngestionV2

        config = configs[config_name]
        print(f"\n🧪 Testing configuration: {config_name}")
        print(f"Primary: {config['primary_provider']}")
        print(f"Fallbacks: {config['fallback_providers']}")

        # Create ingestion instance
        ingestion = MarketDataIngestionV2(
            primary_provider=config['primary_provider'],
            fallback_providers=config['fallback_providers'],
            api_key=os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        )

        print(f"✅ Active provider: {ingestion.provider.name}")

        # Test basic functionality
        test_symbol = "RELIANCE.NS"
        price = ingestion.get_current_price(test_symbol)

        if price and price > 0:
            print(f"✅ Price test successful: {test_symbol} = ₹{price:.2f}")
        else:
            print("⚠️  Price test failed - no data returned")

        # Health check
        health = ingestion.health_check()
        healthy = health['data_ingestion'].get('healthy', False)
        print(f"✅ Health check: {'Healthy' if healthy else 'Unhealthy'}")

        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def setup_environment():
    """Help user set up environment variables"""

    print("\n🔧 Environment Setup")
    print("=" * 30)

    # Check current environment
    alpha_key = os.getenv('ALPHA_VANTAGE_API_KEY')

    if alpha_key and alpha_key != 'demo':
        print(f"✅ ALPHA_VANTAGE_API_KEY: Found (***{alpha_key[-4:]})")
    else:
        print("⚠️  ALPHA_VANTAGE_API_KEY: Not found or using demo key")
        print("\nTo get real market data:")
        print("1. Visit: https://www.alphavantage.co/support/#api-key")
        print("2. Sign up for free API key (500 calls/day)")
        print("3. Add to your .env file:")
        print("   ALPHA_VANTAGE_API_KEY=your_key_here")

    print("\n📝 Current .env template:")
    env_template = """
# Alpha Vantage API (for real market data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# Data Provider Configuration
PRIMARY_DATA_PROVIDER=alpha_vantage
FALLBACK_DATA_PROVIDERS=mock

# Alternative configurations:
# PRIMARY_DATA_PROVIDER=mock  # For development
# PRIMARY_DATA_PROVIDER=yahoo # For Yahoo Finance (when working)
"""
    print(env_template)

def main():
    """Main configuration tool"""

    if len(sys.argv) < 2:
        print("Usage: python3 data_providers_config.py <command>")
        print("\nCommands:")
        print("  show     - Show available configurations")
        print("  test <config> - Test a configuration")
        print("  setup    - Help with environment setup")
        print("\nExample:")
        print("  python3 data_providers_config.py show")
        print("  python3 data_providers_config.py test production")
        return

    command = sys.argv[1]

    if command == 'show':
        show_provider_configurations()

    elif command == 'test':
        if len(sys.argv) < 3:
            print("Usage: python3 data_providers_config.py test <config_name>")
            print("Available configs: development, basic_real, production, alpha_only")
            return

        config_name = sys.argv[2]
        test_configuration(config_name)

    elif command == 'setup':
        setup_environment()

    else:
        print(f"Unknown command: {command}")
        print("Available: show, test, setup")

if __name__ == "__main__":
    main()
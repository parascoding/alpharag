#!/usr/bin/env python3
"""
Test provider factory
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def test_provider_factory():
    """Test the provider factory functionality"""
    print("🧪 Testing Provider Factory...")

    try:
        from src.data_providers import ProviderFactory
        print("✅ Successfully imported ProviderFactory")

        # Test available providers
        providers = ProviderFactory.get_available_providers()
        print(f"✅ Available providers: {providers}")

        # Test creating mock provider
        mock_provider = ProviderFactory.get_provider('mock')
        if mock_provider:
            print(f"✅ Created mock provider: {mock_provider.name}")

            # Test with provider
            price = mock_provider.get_current_price("RELIANCE.NS")
            print(f"✅ Test price from factory provider: ₹{price:.2f}")
        else:
            print("❌ Failed to create mock provider")
            return False

        # Test fallback functionality
        print("\n🔄 Testing fallback functionality...")
        provider = ProviderFactory.get_provider_with_fallback(
            primary_provider='non_existent',
            fallback_providers=['mock']
        )

        if provider:
            print(f"✅ Fallback worked, got provider: {provider.name}")
        else:
            print("❌ Fallback failed")
            return False

        # Test health check
        print("\n🏥 Testing health check...")
        health = ProviderFactory.health_check_all()
        print(f"✅ Health check completed for {len(health['providers'])} providers")

        for provider_name, status in health['providers'].items():
            healthy = status.get('healthy', False)
            print(f"   {'✅' if healthy else '❌'} {provider_name}: {'Healthy' if healthy else 'Unhealthy'}")

        print("✅ Provider factory tests passed!")
        return True

    except Exception as e:
        import traceback
        print(f"❌ Provider factory test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Provider Factory...")

    success = test_provider_factory()

    if success:
        print("\n🎉 Factory tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Factory tests failed!")
        sys.exit(1)
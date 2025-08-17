#!/usr/bin/env python3
"""
AlphaRAG - AI-Powered Portfolio Analysis System
Main entry point for the application
"""

import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.orchestrator import AlphaRAGOrchestrator
from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AlphaRAG - AI-Powered Portfolio Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--mode',
        choices=['analyze', 'test-email', 'validate'],
        default='analyze',
        help='Operation mode (default: analyze)'
    )

    args = parser.parse_args()

    print("🚀 AlphaRAG - AI-Powered Portfolio Analysis System")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    try:
        # Initialize orchestrator
        orchestrator = AlphaRAGOrchestrator()

        if args.mode == 'validate':
            success = orchestrator.validate_setup()
        elif args.mode == 'test-email':
            success = orchestrator.test_email()
        else:  # analyze mode
            success = orchestrator.run_full_analysis()

        if success:
            print("\n✅ Operation completed successfully!")
            return 0
        else:
            print("\n❌ Operation failed!")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
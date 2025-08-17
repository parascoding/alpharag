#!/usr/bin/env python3
"""
Test script to examine the NSE CSV structure and test with known symbols
"""

import sys
import csv
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent))

from src.data_providers.upstox_instrument_mapper import upstox_mapper

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def examine_csv_structure():
    """Examine the downloaded CSV file structure"""
    logger.info("=== Examining NSE CSV Structure ===")

    try:
        # Ensure we have fresh data
        cache_info = upstox_mapper.get_cache_info()
        logger.info(f"Cache info: {cache_info}")

        if not cache_info['instrument_file_exists']:
            logger.info("Downloading fresh instrument file...")
            upstox_mapper._download_instrument_file()

        # Read first few rows to understand structure
        csv_file = upstox_mapper.instrument_file
        logger.info(f"Reading CSV file: {csv_file}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)

            # Get column headers
            headers = csv_reader.fieldnames
            logger.info(f"CSV Headers: {headers}")

            # Read first 10 rows
            logger.info("First 10 rows:")
            count = 0
            equity_count = 0
            for row in csv_reader:
                count += 1
                if row.get('instrument_type', '').upper() == 'EQ':
                    equity_count += 1
                    if equity_count <= 5:  # Show first 5 equity instruments
                        logger.info(f"  Equity {equity_count}: {dict(row)}")

                if count >= 100:  # Check first 100 rows
                    break

            logger.info(f"Found {equity_count} equity instruments in first {count} rows")

        return True

    except Exception as e:
        logger.error(f"Error examining CSV structure: {e}")
        return False

def test_known_symbols():
    """Test with known NSE symbols"""
    logger.info("\n=== Testing Known NSE Symbols ===")

    # Test with well-known NSE symbols
    known_symbols = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'SBIN.NS',
        'HDFCBANK.NS',
        'ITC.NS'
    ]

    for symbol in known_symbols:
        try:
            logger.info(f"\nTesting {symbol}:")
            instrument_key = upstox_mapper.get_instrument_key(symbol)
            logger.info(f"  Instrument Key: {instrument_key}")

            if instrument_key:
                company_info = upstox_mapper.get_company_info(symbol)
                if company_info:
                    logger.info(f"  Company: {company_info['company_name']}")
                    logger.info(f"  Trading Symbol: {company_info['trading_symbol']}")
                    logger.info(f"  Exchange: {company_info['exchange']}")
                else:
                    logger.info("  No company info found")
            else:
                logger.info("  No instrument key found")

        except Exception as e:
            logger.error(f"  Error testing {symbol}: {e}")

def search_for_test_symbols():
    """Search for our test symbols in the CSV"""
    logger.info("\n=== Searching for Test Symbols ===")

    test_symbols = ['ACUTAAS', 'CSBBANK', 'ECLERX', 'GOLDBEES']

    try:
        csv_file = upstox_mapper.instrument_file

        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)

            found_symbols = {}

            for row in csv_reader:
                trading_symbol = row.get('trading_symbol', '').upper()
                name = row.get('name', '')

                for test_symbol in test_symbols:
                    if (test_symbol.upper() in trading_symbol or
                        trading_symbol in test_symbol.upper() or
                        test_symbol.upper() in name.upper()):

                        if test_symbol not in found_symbols:
                            found_symbols[test_symbol] = []

                        found_symbols[test_symbol].append({
                            'trading_symbol': trading_symbol,
                            'name': name,
                            'instrument_key': row.get('instrument_key', ''),
                            'instrument_type': row.get('instrument_type', ''),
                            'exchange': row.get('exchange', '')
                        })

            logger.info("Search results:")
            for test_symbol, matches in found_symbols.items():
                logger.info(f"\n{test_symbol}:")
                for match in matches[:3]:  # Show top 3 matches
                    logger.info(f"  - {match['trading_symbol']} | {match['name']} | {match['instrument_key']}")

            if not found_symbols:
                logger.info("No matches found for test symbols")

                # Show some random equity symbols for reference
                logger.info("\nSome random equity symbols from NSE:")
                with open(csv_file, 'r', encoding='utf-8') as f2:
                    csv_reader2 = csv.DictReader(f2)
                    count = 0
                    for row in csv_reader2:
                        if (row.get('instrument_type', '').upper() == 'EQ' and
                            row.get('exchange', '').upper() == 'NSE'):
                            count += 1
                            if count <= 10:
                                logger.info(f"  {row.get('trading_symbol', '')} - {row.get('name', '')}")
                            if count >= 10:
                                break

    except Exception as e:
        logger.error(f"Error searching for test symbols: {e}")

if __name__ == "__main__":
    print("🔍 Examining NSE CSV Structure and Testing Symbols")

    # Examine CSV structure
    examine_csv_structure()

    # Test known symbols
    test_known_symbols()

    # Search for test symbols
    search_for_test_symbols()

    print("\n✅ Analysis complete!")
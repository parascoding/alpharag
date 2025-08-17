#!/usr/bin/env python3
"""
Debug script to examine specific entries in the CSV
"""

import csv
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def examine_specific_entries():
    """Look for specific instrument keys in the CSV"""

    csv_file = Path(__file__).parent / 'cache' / 'upstox_instruments.csv'

    if not csv_file.exists():
        print("❌ CSV file not found")
        return

    print("🔍 Looking for specific instrument keys...")

    # Known instrument keys from manual mappings
    target_keys = [
        'NSE_EQ|INE002A01018',  # RELIANCE
        'NSE_EQ|INE467B01029',  # TCS
        'NSE_EQ|INE009A01021',  # INFY
    ]

    found_entries = {}

    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)

        print(f"📋 CSV Headers: {list(csv_reader.fieldnames)}")
        print()

        for row in csv_reader:
            instrument_key = row.get('instrument_key', '')

            if instrument_key in target_keys:
                found_entries[instrument_key] = dict(row)
                print(f"✅ Found {instrument_key}:")
                for key, value in row.items():
                    if value:  # Only show non-empty values
                        print(f"   {key}: {value}")
                print()

    if not found_entries:
        print("❌ No target instrument keys found")

        # Show first few equity entries
        print("📊 First few equity entries from NSE:")
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            count = 0
            for row in csv_reader:
                if (row.get('instrument_type', '').upper() == 'EQ' and
                    row.get('exchange', '').upper() == 'NSE'):
                    count += 1
                    print(f"\nEntry {count}:")
                    for key, value in row.items():
                        if value:  # Only show non-empty values
                            print(f"   {key}: {value}")

                    if count >= 3:
                        break

    # Also look for patterns that might match our test symbols
    print("\n🔍 Looking for test symbol patterns...")
    test_patterns = ['ACUTAAS', 'CSBBANK', 'ECLERX', 'GOLDBEES']

    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)

        for row in csv_reader:
            name = row.get('name', '').upper()
            tradingsymbol = row.get('tradingsymbol', '').upper()

            for pattern in test_patterns:
                if (pattern in name or pattern in tradingsymbol or
                    name.replace(' ', '').startswith(pattern[:4])):
                    print(f"\n🎯 Potential match for {pattern}:")
                    for key, value in row.items():
                        if value:
                            print(f"   {key}: {value}")
                    break

if __name__ == "__main__":
    examine_specific_entries()
"""
Upstox Instrument Mapper for converting symbols to instrument keys
"""

import requests
import json
import gzip
import csv
from typing import Dict, Optional, List
import logging
from datetime import datetime, timedelta
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class UpstoxInstrumentMapper:
    """
    Maps stock symbols (like RELIANCE.NS) to Upstox instrument keys (like NSE_EQ|INE002A01018)
    Downloads and caches the daily instrument file from Upstox
    """

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.instrument_file = self.cache_dir / "upstox_instruments.csv"
        self.symbol_map_cache = {}
        self.cache_date = None

        # Common symbol mappings for quick lookup
        self.manual_mappings = {
            'RELIANCE.NS': 'NSE_EQ|INE002A01018',
            'TCS.NS': 'NSE_EQ|INE467B01029',
            'INFY.NS': 'NSE_EQ|INE009A01021',
            'WIPRO.NS': 'NSE_EQ|INE075A01022',
            'HDFCBANK.NS': 'NSE_EQ|INE040A01034',
            'ICICIBANK.NS': 'NSE_EQ|INE090A01021',
            'SBIN.NS': 'NSE_EQ|INE062A01020',
            'LT.NS': 'NSE_EQ|INE018A01030',
            'HCLTECH.NS': 'NSE_EQ|INE860A01027',
            'TECHM.NS': 'NSE_EQ|INE669C01036',
            'ADANIPORTS.NS': 'NSE_EQ|INE742F01042',
            'HINDUNILVR.NS': 'NSE_EQ|INE030A01027',
            'ITC.NS': 'NSE_EQ|INE154A01025',
            'BHARTIARTL.NS': 'NSE_EQ|INE397D01024',
            'MARUTI.NS': 'NSE_EQ|INE585B01010'
        }

    def get_instrument_key(self, symbol: str) -> Optional[str]:
        """
        Get Upstox instrument key for a given symbol

        Args:
            symbol: Stock symbol like 'RELIANCE.NS' or 'RELIANCE'

        Returns:
            Instrument key like 'NSE_EQ|INE002A01018' or None if not found
        """
        try:
            # Normalize symbol
            normalized_symbol = self._normalize_symbol(symbol)

            # Check manual mappings first (for common stocks)
            if normalized_symbol in self.manual_mappings:
                instrument_key = self.manual_mappings[normalized_symbol]
                logger.debug(f"Found {symbol} -> {instrument_key} in manual mappings")
                return instrument_key

            # Load and search instrument file
            if self._ensure_instrument_file():
                return self._search_instrument_file(symbol, normalized_symbol)

            # Fallback: generate instrument key based on pattern
            logger.warning(f"Could not find instrument key for {symbol}, using fallback")
            return self._generate_fallback_key(symbol)

        except Exception as e:
            logger.error(f"Error getting instrument key for {symbol}: {e}")
            return self._generate_fallback_key(symbol)

    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol to standard format"""
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            symbol = f"{symbol}.NS"  # Default to NSE
        return symbol.upper()

    def _ensure_instrument_file(self) -> bool:
        """Ensure we have a fresh instrument file"""
        try:
            # Check if we need to download/refresh the file
            today = datetime.now().date()

            if (not self.instrument_file.exists() or
                self.cache_date != today or
                self._is_file_stale()):

                logger.info("Downloading fresh Upstox instrument file...")
                return self._download_instrument_file()

            return True

        except Exception as e:
            logger.error(f"Error ensuring instrument file: {e}")
            return False

    def _is_file_stale(self) -> bool:
        """Check if the instrument file is stale (older than 1 day)"""
        try:
            if not self.instrument_file.exists():
                return True

            file_time = datetime.fromtimestamp(self.instrument_file.stat().st_mtime)
            return datetime.now() - file_time > timedelta(days=1)

        except Exception:
            return True

    def _download_instrument_file(self) -> bool:
        """Download the latest NSE instrument file from Upstox"""
        try:
            # Use NSE.csv.gz endpoint which is more reliable
            url = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.csv.gz"

            logger.info(f"Downloading NSE instrument file from: {url}")
            response = requests.get(url, timeout=30, stream=True)

            if response.status_code == 200:
                # Download and decompress the gzipped CSV file
                with gzip.open(response.raw, 'rt', encoding='utf-8') as gz_file:
                    csv_content = gz_file.read()

                # Save the decompressed CSV content
                with open(self.instrument_file, 'w', encoding='utf-8') as f:
                    f.write(csv_content)

                self.cache_date = datetime.now().date()
                logger.info(f"Successfully downloaded and extracted NSE instrument file: {len(csv_content)} bytes")
                return True
            else:
                logger.error(f"Failed to download NSE instrument file: HTTP {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error downloading NSE instrument file: {e}")
            return False

    def _search_instrument_file(self, original_symbol: str, normalized_symbol: str) -> Optional[str]:
        """Search for symbol in the CSV instrument file with enhanced fuzzy matching"""
        try:
            # Extract base symbol and exchange
            if normalized_symbol.endswith('.NS'):
                base_symbol = normalized_symbol.replace('.NS', '')
                target_exchange = 'NSE'
            elif normalized_symbol.endswith('.BO'):
                base_symbol = normalized_symbol.replace('.BO', '')
                target_exchange = 'BSE'
            else:
                base_symbol = normalized_symbol
                target_exchange = 'NSE'  # Default to NSE

            # Load and parse the CSV file
            instruments = []
            with open(self.instrument_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)

                # Convert CSV rows to list of dictionaries, normalizing column names
                for row in csv_reader:
                    # Normalize column names (handle both tradingsymbol and trading_symbol)
                    normalized_row = {}
                    for key, value in row.items():
                        if key == 'tradingsymbol':
                            normalized_row['trading_symbol'] = value
                        else:
                            normalized_row[key] = value

                    # Skip non-equity instruments or wrong exchange
                    instrument_type = normalized_row.get('instrument_type', '').upper()
                    exchange = normalized_row.get('exchange', '').upper()

                    # Handle both EQ/EQUITY and NSE/NSE_EQ formats
                    is_equity = instrument_type in ['EQ', 'EQUITY']
                    is_target_exchange = (exchange == target_exchange.upper() or
                                        exchange == f"{target_exchange.upper()}_EQ")

                    if is_equity and is_target_exchange:
                        instruments.append(normalized_row)

            # 1. Try exact match first
            for instrument in instruments:
                trading_symbol = instrument.get('trading_symbol', '').upper()
                if trading_symbol == base_symbol.upper():
                    instrument_key = instrument.get('instrument_key')
                    if instrument_key:
                        logger.info(f"Found exact match {original_symbol} -> {instrument_key}")
                        self.manual_mappings[normalized_symbol] = instrument_key
                        return instrument_key

            # 2. Try fuzzy matching on trading symbol
            matches = []
            for instrument in instruments:
                trading_symbol = instrument.get('trading_symbol', '')
                company_name = instrument.get('name', '')

                # Fuzzy matching strategies
                if self._is_symbol_match(base_symbol, trading_symbol, company_name):
                    matches.append({
                        'instrument': instrument,
                        'similarity': self._calculate_similarity(base_symbol, trading_symbol)
                    })

            # Sort by similarity and return best match
            if matches:
                best_match = max(matches, key=lambda x: x['similarity'])
                if best_match['similarity'] > 0.7:  # 70% similarity threshold
                    instrument_key = best_match['instrument'].get('instrument_key')
                    trading_symbol = best_match['instrument'].get('trading_symbol')
                    logger.info(f"Found fuzzy match {original_symbol} -> {trading_symbol} -> {instrument_key} (similarity: {best_match['similarity']:.2f})")
                    self.manual_mappings[normalized_symbol] = instrument_key
                    return instrument_key

            logger.warning(f"Symbol {original_symbol} not found in NSE instrument file")
            return None

        except Exception as e:
            logger.error(f"Error searching NSE instrument file for {original_symbol}: {e}")
            return None

    def _is_symbol_match(self, query_symbol: str, trading_symbol: str, company_name: str) -> bool:
        """
        Check if symbols might be a match using various strategies
        """
        query_symbol = query_symbol.upper()
        trading_symbol = trading_symbol.upper()
        company_name = company_name.upper()

        # Strategy 1: Substring matching
        if query_symbol in trading_symbol or trading_symbol in query_symbol:
            return True

        # Strategy 2: Check for common abbreviations/variations
        # E.g., CSBBANK could match CSBK or CSB
        if len(query_symbol) >= 3 and len(trading_symbol) >= 3:
            if query_symbol[:3] == trading_symbol[:3] or query_symbol[:4] == trading_symbol[:4]:
                return True

        # Strategy 3: Check company name for symbol matches
        if query_symbol in company_name or any(word in company_name for word in query_symbol.split()):
            return True

        # Strategy 4: Common banking/financial abbreviations
        bank_variations = {
            'BANK': ['BNK', 'BK'],
            'FINANCE': ['FIN', 'FINC'],
            'SERVICES': ['SERV', 'SVC'],
            'LIMITED': ['LTD', 'LIM'],
            'INDUSTRIES': ['IND', 'INDS']
        }

        for full_word, abbreviations in bank_variations.items():
            if full_word in query_symbol:
                for abbr in abbreviations:
                    if abbr in trading_symbol:
                        return True

        return False

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate string similarity using simple character-based matching
        """
        if not str1 or not str2:
            return 0.0

        str1, str2 = str1.upper(), str2.upper()

        # Length similarity
        len_sim = min(len(str1), len(str2)) / max(len(str1), len(str2))

        # Character overlap
        set1, set2 = set(str1), set(str2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        char_sim = intersection / union if union > 0 else 0

        # Weighted combination
        return 0.6 * char_sim + 0.4 * len_sim

    def _generate_fallback_key(self, symbol: str) -> str:
        """Generate a fallback instrument key based on symbol pattern"""
        try:
            if symbol.endswith('.NS'):
                base_symbol = symbol.replace('.NS', '')
                return f"NSE_EQ|{base_symbol}"
            elif symbol.endswith('.BO'):
                base_symbol = symbol.replace('.BO', '')
                return f"BSE_EQ|{base_symbol}"
            else:
                return f"NSE_EQ|{symbol}"

        except Exception:
            return f"NSE_EQ|{symbol}"

    def bulk_map_symbols(self, symbols: list) -> Dict[str, str]:
        """Map multiple symbols to instrument keys"""
        mapping = {}

        for symbol in symbols:
            instrument_key = self.get_instrument_key(symbol)
            if instrument_key:
                mapping[symbol] = instrument_key

        return mapping

    def get_company_info(self, symbol: str) -> Optional[Dict]:
        """
        Get company information for a given symbol from CSV instrument file
        """
        try:
            instrument_key = self.get_instrument_key(symbol)
            if not instrument_key:
                return None

            # Load instrument file and find matching company
            if not self._ensure_instrument_file():
                return None

            # Read CSV file and search for the instrument
            with open(self.instrument_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)

                for row in csv_reader:
                    if row.get('instrument_key') == instrument_key:
                        # Handle column name variations
                        trading_symbol = row.get('trading_symbol') or row.get('tradingsymbol', '')

                        return {
                            'symbol': symbol,
                            'trading_symbol': trading_symbol,
                            'company_name': row.get('name', ''),
                            'exchange': row.get('exchange', ''),
                            'segment': row.get('segment', ''),
                            'instrument_key': instrument_key,
                            'isin': row.get('isin', ''),
                            'instrument_type': row.get('instrument_type', '')
                        }

            return None

        except Exception as e:
            logger.error(f"Error getting company info for {symbol}: {e}")
            return None

    def bulk_get_company_info(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Get company information for multiple symbols
        """
        company_info = {}

        for symbol in symbols:
            info = self.get_company_info(symbol)
            if info:
                company_info[symbol] = info

        return company_info

    def get_cache_info(self) -> Dict:
        """Get information about the cache status"""
        return {
            'cache_dir': str(self.cache_dir),
            'instrument_file_exists': self.instrument_file.exists(),
            'file_size': self.instrument_file.stat().st_size if self.instrument_file.exists() else 0,
            'cache_date': self.cache_date,
            'manual_mappings_count': len(self.manual_mappings),
            'is_file_stale': self._is_file_stale()
        }

# Global instance for easy access
upstox_mapper = UpstoxInstrumentMapper()
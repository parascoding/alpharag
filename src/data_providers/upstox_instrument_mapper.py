"""
Upstox Instrument Mapper for converting symbols to instrument keys
"""

import requests
import json
from typing import Dict, Optional
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
        self.instrument_file = self.cache_dir / "upstox_instruments.json"
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
        """Download the latest instrument file from Upstox"""
        try:
            # Upstox provides instrument files without authentication
            url = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json"
            
            logger.info(f"Downloading instrument file from: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Save the file
                with open(self.instrument_file, 'w') as f:
                    f.write(response.text)
                
                self.cache_date = datetime.now().date()
                logger.info(f"Successfully downloaded instrument file: {len(response.text)} bytes")
                return True
            else:
                logger.error(f"Failed to download instrument file: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading instrument file: {e}")
            return False
    
    def _search_instrument_file(self, original_symbol: str, normalized_symbol: str) -> Optional[str]:
        """Search for symbol in the instrument file"""
        try:
            # Extract base symbol and exchange
            if normalized_symbol.endswith('.NS'):
                base_symbol = normalized_symbol.replace('.NS', '')
                target_segment = 'NSE_EQ'
            elif normalized_symbol.endswith('.BO'):
                base_symbol = normalized_symbol.replace('.BO', '')
                target_segment = 'BSE_EQ'
            else:
                base_symbol = normalized_symbol
                target_segment = 'NSE_EQ'  # Default to NSE
            
            # Load and parse the JSON file
            with open(self.instrument_file, 'r') as f:
                instruments = json.load(f)
            
            # Search for matching instrument
            for instrument in instruments:
                if (instrument.get('segment') == target_segment and 
                    instrument.get('instrument_type') == 'EQ' and
                    instrument.get('trading_symbol') == base_symbol):
                    
                    instrument_key = instrument.get('instrument_key')
                    if instrument_key:
                        logger.info(f"Found {original_symbol} -> {instrument_key} in instrument file")
                        # Cache the mapping for future use
                        self.manual_mappings[normalized_symbol] = instrument_key
                        return instrument_key
            
            logger.warning(f"Symbol {original_symbol} not found in instrument file")
            return None
            
        except Exception as e:
            logger.error(f"Error searching instrument file for {original_symbol}: {e}")
            return None
    
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
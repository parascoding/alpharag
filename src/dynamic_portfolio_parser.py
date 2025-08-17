"""
Dynamic Portfolio Parser for handling various CSV formats (Upstox, manual, etc.)
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class DynamicPortfolioParser:
    """
    Intelligent portfolio parser that can handle multiple CSV formats:
    1. Upstox format: "Instrument","Qty.","Avg. cost","LTP","Invested","Cur. val","P&L","Net chg.","Day chg.",""
    2. Manual format: symbol,quantity,buy_price,purchase_date
    """

    def __init__(self, portfolio_file: str):
        self.portfolio_file = portfolio_file
        self.portfolio_df = None
        self.detected_format = None
        self.raw_df = None

    def load_and_parse_portfolio(self) -> pd.DataFrame:
        """
        Load portfolio and automatically detect format
        """
        try:
            # Load raw CSV data
            self.raw_df = pd.read_csv(self.portfolio_file)
            logger.info(f"Loaded raw portfolio with {len(self.raw_df)} rows and columns: {list(self.raw_df.columns)}")

            # Detect format and parse accordingly
            self.detected_format = self._detect_format()
            logger.info(f"Detected portfolio format: {self.detected_format}")

            if self.detected_format == "upstox":
                self.portfolio_df = self._parse_upstox_format()
            elif self.detected_format == "manual":
                self.portfolio_df = self._parse_manual_format()
            else:
                raise ValueError(f"Unsupported portfolio format: {self.detected_format}")

            # Normalize symbols and validate
            self._normalize_symbols()
            self._validate_portfolio()

            logger.info(f"Successfully parsed {self.detected_format} portfolio with {len(self.portfolio_df)} holdings")
            return self.portfolio_df

        except Exception as e:
            logger.error(f"Error loading and parsing portfolio: {e}")
            raise

    def _detect_format(self) -> str:
        """
        Detect portfolio format based on column names
        """
        columns = [col.strip().lower() for col in self.raw_df.columns]

        # Upstox format indicators
        upstox_indicators = ['instrument', 'qty.', 'avg. cost', 'ltp', 'invested', 'cur. val', 'p&l']

        # Manual format indicators
        manual_indicators = ['symbol', 'quantity', 'buy_price']

        # Count matches
        upstox_matches = sum(1 for indicator in upstox_indicators if any(indicator in col for col in columns))
        manual_matches = sum(1 for indicator in manual_indicators if any(indicator in col for col in columns))

        logger.debug(f"Format detection - Upstox matches: {upstox_matches}, Manual matches: {manual_matches}")

        if upstox_matches >= 4:  # At least 4 key Upstox columns
            return "upstox"
        elif manual_matches >= 2:  # At least 2 key manual columns
            return "manual"
        else:
            # Try to infer from column patterns
            if len(columns) >= 8 and any('instrument' in col for col in columns):
                return "upstox"
            else:
                return "manual"

    def _parse_upstox_format(self) -> pd.DataFrame:
        """
        Parse Upstox CSV format:
        "Instrument","Qty.","Avg. cost","LTP","Invested","Cur. val","P&L","Net chg.","Day chg.",""
        """
        df = self.raw_df.copy()

        # Clean column names (remove quotes, spaces, etc.)
        df.columns = [col.strip().strip('"') for col in df.columns]

        # Create standardized portfolio DataFrame
        parsed_data = []

        for idx, row in df.iterrows():
            try:
                # Extract key fields with flexible column matching
                instrument = self._get_column_value(row, ['Instrument', 'instrument'])
                quantity = self._get_column_value(row, ['Qty.', 'Qty', 'quantity'])
                avg_cost = self._get_column_value(row, ['Avg. cost', 'Avg cost', 'avg_cost', 'buy_price'])
                ltp = self._get_column_value(row, ['LTP', 'ltp', 'current_price'])

                # Skip empty rows or invalid data
                if pd.isna(instrument) or instrument == '' or pd.isna(quantity) or quantity == 0:
                    continue

                # Clean and validate data
                instrument = str(instrument).strip()
                quantity = float(quantity) if pd.notna(quantity) else 0
                avg_cost = float(avg_cost) if pd.notna(avg_cost) else 0
                ltp = float(ltp) if pd.notna(ltp) else 0

                if quantity <= 0 or avg_cost <= 0:
                    logger.warning(f"Skipping invalid holding: {instrument} (qty: {quantity}, cost: {avg_cost})")
                    continue

                parsed_data.append({
                    'symbol': instrument,
                    'quantity': quantity,
                    'buy_price': avg_cost,
                    'current_price': ltp,
                    'purchase_date': None  # Not available in Upstox format
                })

            except Exception as e:
                logger.error(f"Error parsing row {idx}: {e}")
                continue

        if not parsed_data:
            raise ValueError("No valid holdings found in Upstox portfolio")

        return pd.DataFrame(parsed_data)

    def _parse_manual_format(self) -> pd.DataFrame:
        """
        Parse manual CSV format: symbol,quantity,buy_price,purchase_date
        """
        df = self.raw_df.copy()

        # Clean column names
        df.columns = [col.strip().lower() for col in df.columns]

        # Ensure we have required columns
        required_mappings = {
            'symbol': ['symbol', 'instrument', 'stock'],
            'quantity': ['quantity', 'qty', 'shares'],
            'buy_price': ['buy_price', 'avg_cost', 'cost', 'price']
        }

        standardized_data = []

        for idx, row in df.iterrows():
            try:
                symbol = self._get_column_value(row, required_mappings['symbol'])
                quantity = self._get_column_value(row, required_mappings['quantity'])
                buy_price = self._get_column_value(row, required_mappings['buy_price'])
                purchase_date = self._get_column_value(row, ['purchase_date', 'date', 'buy_date'])

                # Skip invalid rows
                if pd.isna(symbol) or pd.isna(quantity) or pd.isna(buy_price):
                    continue

                standardized_data.append({
                    'symbol': str(symbol).strip(),
                    'quantity': float(quantity),
                    'buy_price': float(buy_price),
                    'current_price': 0,  # Will be fetched later
                    'purchase_date': purchase_date
                })

            except Exception as e:
                logger.error(f"Error parsing manual row {idx}: {e}")
                continue

        return pd.DataFrame(standardized_data)

    def _get_column_value(self, row: pd.Series, possible_columns: List[str]):
        """
        Get value from row using flexible column name matching
        """
        for col_name in possible_columns:
            # Try exact match first
            if col_name in row.index:
                return row[col_name]

            # Try case-insensitive partial match
            for actual_col in row.index:
                if col_name.lower() in actual_col.lower():
                    return row[actual_col]

        return None

    def _normalize_symbols(self):
        """
        Normalize symbol formats for consistent processing
        """
        if self.portfolio_df is None:
            return

        normalized_symbols = []

        for symbol in self.portfolio_df['symbol']:
            # Clean the symbol
            clean_symbol = str(symbol).strip().upper()

            # Remove any quotes or special characters
            clean_symbol = re.sub(r'["\'\s]', '', clean_symbol)

            # Add .NS suffix if not present (for NSE stocks)
            if not clean_symbol.endswith(('.NS', '.BO')):
                # Default to NSE unless it's clearly a BSE stock
                clean_symbol = f"{clean_symbol}.NS"

            normalized_symbols.append(clean_symbol)

        self.portfolio_df['symbol'] = normalized_symbols
        self.portfolio_df['original_symbol'] = self.portfolio_df['symbol'].apply(lambda x: x.replace('.NS', '').replace('.BO', ''))

        logger.info(f"Normalized symbols: {list(self.portfolio_df['symbol'])}")

    def _validate_portfolio(self):
        """
        Validate the parsed portfolio data
        """
        if self.portfolio_df is None or self.portfolio_df.empty:
            raise ValueError("No valid portfolio data found")

        required_columns = ['symbol', 'quantity', 'buy_price']
        missing_columns = [col for col in required_columns if col not in self.portfolio_df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns after parsing: {missing_columns}")

        # Check for valid data
        invalid_rows = []
        for idx, row in self.portfolio_df.iterrows():
            if (pd.isna(row['symbol']) or
                pd.isna(row['quantity']) or
                pd.isna(row['buy_price']) or
                row['quantity'] <= 0 or
                row['buy_price'] <= 0):
                invalid_rows.append(idx)

        if invalid_rows:
            logger.warning(f"Removing {len(invalid_rows)} invalid rows")
            self.portfolio_df = self.portfolio_df.drop(invalid_rows).reset_index(drop=True)

        if self.portfolio_df.empty:
            raise ValueError("No valid holdings remain after validation")

    def get_symbols(self) -> List[str]:
        """Get list of portfolio symbols"""
        return self.portfolio_df['symbol'].tolist() if self.portfolio_df is not None else []

    def get_original_symbols(self) -> List[str]:
        """Get list of original symbols (without .NS/.BO suffix)"""
        return self.portfolio_df['original_symbol'].tolist() if self.portfolio_df is not None else []

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        if self.portfolio_df is None:
            return {}

        total_holdings = len(self.portfolio_df)
        total_quantity = self.portfolio_df['quantity'].sum()
        total_investment = (self.portfolio_df['quantity'] * self.portfolio_df['buy_price']).sum()

        return {
            'total_holdings': total_holdings,
            'total_quantity': int(total_quantity),
            'total_investment': round(total_investment, 2),
            'symbols': self.get_symbols(),
            'original_symbols': self.get_original_symbols(),
            'detected_format': self.detected_format
        }

    def get_portfolio_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the parsed portfolio DataFrame"""
        return self.portfolio_df
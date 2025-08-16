import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self, portfolio_file: str):
        self.portfolio_file = portfolio_file
        self.portfolio_df = None
        self.load_portfolio()

    def load_portfolio(self) -> pd.DataFrame:
        try:
            self.portfolio_df = pd.read_csv(self.portfolio_file)
            self._validate_portfolio()
            logger.info(f"Loaded portfolio with {len(self.portfolio_df)} holdings")
            return self.portfolio_df
        except Exception as e:
            logger.error(f"Error loading portfolio: {e}")
            raise

    def _validate_portfolio(self):
        required_columns = ['symbol', 'quantity', 'buy_price', 'purchase_date']
        missing_columns = [col for col in required_columns if col not in self.portfolio_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if self.portfolio_df.empty:
            raise ValueError("Portfolio file is empty")

        for idx, row in self.portfolio_df.iterrows():
            if pd.isna(row['symbol']) or pd.isna(row['quantity']) or pd.isna(row['buy_price']):
                raise ValueError(f"Missing data in row {idx + 1}")

    def get_symbols(self) -> List[str]:
        return self.portfolio_df['symbol'].tolist()

    def get_portfolio_summary(self) -> Dict:
        total_holdings = len(self.portfolio_df)
        total_quantity = self.portfolio_df['quantity'].sum()
        total_investment = (self.portfolio_df['quantity'] * self.portfolio_df['buy_price']).sum()

        return {
            'total_holdings': total_holdings,
            'total_quantity': int(total_quantity),
            'total_investment': round(total_investment, 2),
            'symbols': self.get_symbols()
        }

    def get_holding_by_symbol(self, symbol: str) -> Optional[Dict]:
        holding = self.portfolio_df[self.portfolio_df['symbol'] == symbol]
        if holding.empty:
            return None

        row = holding.iloc[0]
        return {
            'symbol': row['symbol'],
            'quantity': int(row['quantity']),
            'buy_price': float(row['buy_price']),
            'purchase_date': row['purchase_date'],
            'investment_value': float(row['quantity'] * row['buy_price'])
        }

    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> Dict:
        if self.portfolio_df is None:
            raise ValueError("Portfolio not loaded")

        results = []
        total_current_value = 0
        total_investment = 0

        for _, row in self.portfolio_df.iterrows():
            symbol = row['symbol']
            quantity = row['quantity']
            buy_price = row['buy_price']
            investment_value = quantity * buy_price

            current_price = current_prices.get(symbol, 0)
            current_value = quantity * current_price if current_price else 0
            pnl = current_value - investment_value
            pnl_percent = (pnl / investment_value * 100) if investment_value else 0

            results.append({
                'symbol': symbol,
                'quantity': int(quantity),
                'buy_price': float(buy_price),
                'current_price': float(current_price),
                'investment_value': float(investment_value),
                'current_value': float(current_value),
                'pnl': float(pnl),
                'pnl_percent': float(pnl_percent)
            })

            total_current_value += current_value
            total_investment += investment_value

        total_pnl = total_current_value - total_investment
        total_pnl_percent = (total_pnl / total_investment * 100) if total_investment else 0

        return {
            'holdings': results,
            'summary': {
                'total_investment': float(total_investment),
                'total_current_value': float(total_current_value),
                'total_pnl': float(total_pnl),
                'total_pnl_percent': float(total_pnl_percent)
            }
        }
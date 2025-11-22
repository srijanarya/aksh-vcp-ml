"""
Angel One Historical Data Fetcher for ML Training

This module integrates Angel One API to fetch historical OHLCV data
for ML training, addressing "insufficient data" warnings.
"""

import logging
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
import sqlite3

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

logger = logging.getLogger(__name__)

class AngelOneDataIntegration:
    """Fetch historical data from Angel One for ML training"""
    
    def __init__(self, credentials_path: str = "/Users/srijan/vcp_clean_test/vcp/.env.angel"):
        """Initialize with Angel One credentials"""
        self.credentials_path = credentials_path
        self.client = None
        self.fetcher = None
        
    def authenticate(self) -> bool:
        """Authenticate with Angel One"""
        try:
            self.client = AngelOneClient.from_env_file(self.credentials_path)
            success = self.client.authenticate()
            
            if success:
                self.fetcher = AngelOneOHLCVFetcher(self.client)
                logger.info("✅ Angel One authentication successful")
                return True
            else:
                logger.error("❌ Angel One authentication failed")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def fetch_historical_prices(
        self,
        symbol: str,
        exchange: str = "NSE",
        days_back: int = 365
    ) -> pd.DataFrame:
        """
        Fetch historical daily prices for a symbol
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            exchange: "NSE" or "BSE"
            days_back: Number of days to fetch
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not self.fetcher:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        logger.info(f"Fetching {symbol} data from {from_date.date()} to {to_date.date()}")
        
        df = self.fetcher.fetch_ohlcv(
            symbol=symbol,
            exchange=exchange,
            interval="ONE_DAY",
            from_date=from_date,
            to_date=to_date
        )
        
        # Validate data
        is_valid, errors = self.fetcher.validate_ohlc(df)
        if not is_valid:
            logger.warning(f"Data validation issues for {symbol}: {errors}")
        
        return df
    
    def store_to_db(self, df: pd.DataFrame, symbol: str, db_path: str = "data/historical_prices.db"):
        """Store fetched data to SQLite database"""
        conn = sqlite3.connect(db_path)
        
        # Ensure table exists
        conn.execute("""
            CREATE TABLE IF NOT EXISTS historical_prices (
                symbol TEXT,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                PRIMARY KEY (symbol, date)
            )
        """)
        
        # Prepare data
        df_store = df.copy()
        df_store['symbol'] = symbol
        df_store['date'] = df_store['timestamp'].dt.date
        
        # Store
        df_store[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']].to_sql(
            'historical_prices',
            conn,
            if_exists='append',
            index=False
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Stored {len(df)} records for {symbol} to {db_path}")
    
    def backfill_for_bse_codes(self, bse_codes: List[str], symbol_map: Dict[str, str] = None):
        """
        Backfill historical data for multiple BSE codes
        
        Args:
            bse_codes: List of BSE codes
            symbol_map: Optional mapping of BSE code to NSE symbol
        """
        if not self.fetcher:
            if not self.authenticate():
                logger.error("Cannot backfill without authentication")
                return
        
        # Default mapping (you'll need to expand this)
        if symbol_map is None:
            symbol_map = {
                '500325': 'RELIANCE',
                '500112': 'SBIN',
                '532540': 'TCS',
                # Add more mappings as needed
            }
        
        for bse_code in bse_codes:
            nse_symbol = symbol_map.get(bse_code)
            if not nse_symbol:
                logger.warning(f"No NSE mapping for BSE code {bse_code}, skipping")
                continue
            
            try:
                df = self.fetch_historical_prices(nse_symbol)
                self.store_to_db(df, nse_symbol)
                logger.info(f"✅ Backfilled {nse_symbol} ({bse_code})")
            except Exception as e:
                logger.error(f"Failed to backfill {nse_symbol}: {e}")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize
    fetcher = AngelOneDataIntegration()
    
    # Test connection
    if fetcher.authenticate():
        # Fetch sample data (Angel One uses -EQ suffix for equity)
        df = fetcher.fetch_historical_prices("RELIANCE-EQ", days_back=90)
        print(f"Fetched {len(df)} records for RELIANCE")
        print(df.head())
        
        # Store to DB
        fetcher.store_to_db(df, "RELIANCE")
        print("✅ Data stored successfully")
    else:
        print("❌ Authentication failed - check credentials")

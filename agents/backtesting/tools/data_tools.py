#!/usr/bin/env python3
"""
Data Fetcher Tool - Story 1.1

Fetches multi-timeframe OHLCV data with intelligent caching and fallback.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import time

# Try to import nsepython for NSE fallback
try:
    from nsepython import equity_history
    NSE_AVAILABLE = True
except ImportError:
    NSE_AVAILABLE = False

logger = logging.getLogger(__name__)


class DataFetcherTool:
    """
    Robust data fetching with multiple sources and caching
    
    Features:
    - Multi-timeframe support (daily, weekly, 4h, 1h)
    - Yahoo Finance primary source
    - Data validation and gap filling
    - Caching to avoid redundant API calls
    """
    
    def __init__(self, cache_dir: Optional[str] = None, request_delay: float = 2.0):
        """
        Initialize Data Fetcher

        Args:
            cache_dir: Directory for caching data
            request_delay: Delay in seconds between API requests (default: 2.0s to avoid rate limits)
        """
        self.cache_dir = cache_dir or "/tmp/backtest_cache"
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self.request_delay = request_delay
        self.last_request_time = 0
    
    def fetch_multi_timeframe_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframes: List[str] = ['daily', 'weekly']
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple timeframes
        
        Args:
            symbol: Stock symbol (e.g., "TATAMOTORS.NS")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframes: List of timeframes to fetch
        
        Returns:
            Dict with timeframe as key, DataFrame as value
        """
        logger.info(f"Fetching {symbol} data from {start_date} to {end_date}")
        
        result = {}
        
        # Fetch daily data first (base timeframe)
        daily_data = self.fetch_daily_data(symbol, start_date, end_date)
        
        if daily_data.empty:
            logger.error(f"Failed to fetch daily data for {symbol}")
            return result
        
        result['daily'] = daily_data
        
        # Generate other timeframes from daily
        for tf in timeframes:
            if tf == 'daily':
                continue  # Already have it
            elif tf == 'weekly':
                result['weekly'] = self._resample_to_weekly(daily_data)
            elif tf == '4h':
                # For 4H, we'd need intraday data (not available from Yahoo free tier)
                # Skip for now or use daily as proxy
                logger.warning("4H data not available, skipping")
            elif tf == '1h':
                logger.warning("1H data not available, skipping")
        
        return result
    
    def fetch_daily_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Fetch daily OHLCV data
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_daily"
        
        # Check cache
        if cache_key in self.cache:
            logger.info(f"Cache hit for {cache_key}")
            return self.cache[cache_key].copy()

        # Rate limiting: ensure minimum delay between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        try:
            # Try Yahoo Finance first
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)

            # Update last request time after successful request
            self.last_request_time = time.time()

            if data.empty:
                logger.warning(f"No data from Yahoo Finance for {symbol}, trying NSE fallback...")
                data = self._fetch_from_nse(symbol, start_date, end_date)

            if data.empty:
                logger.error(f"Failed to fetch daily data for {symbol}")
                return pd.DataFrame()

            # Standardize column names
            data.columns = [col.lower() for col in data.columns]

            # Validate data
            data = self._validate_and_clean(data)

            # Cache it
            self.cache[cache_key] = data.copy()

            logger.info(f"Fetched {len(data)} bars for {symbol}")
            return data

        except Exception as e:
            # If Yahoo Finance fails (rate limit, network error, etc.), try NSE
            if "Rate limited" in str(e) or "Too Many Requests" in str(e):
                logger.warning(f"Yahoo Finance rate limited for {symbol}, trying NSE fallback...")
                try:
                    data = self._fetch_from_nse(symbol, start_date, end_date)
                    if not data.empty:
                        # Standardize and cache
                        data.columns = [col.lower() for col in data.columns]
                        data = self._validate_and_clean(data)
                        self.cache[cache_key] = data.copy()
                        logger.info(f"Fetched {len(data)} bars for {symbol} from NSE")
                        return data
                except Exception as nse_error:
                    logger.error(f"NSE fallback also failed for {symbol}: {nse_error}")

            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _resample_to_weekly(self, daily_data: pd.DataFrame) -> pd.DataFrame:
        """Resample daily data to weekly"""
        if daily_data.empty:
            return pd.DataFrame()
        
        weekly = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Drop any rows with NaN (incomplete weeks)
        weekly = weekly.dropna()
        
        return weekly
    
    def _validate_and_clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean OHLCV data
        
        Checks:
        - Remove rows with NaN
        - Ensure OHLCV consistency (high >= low, etc.)
        - Remove zero-volume bars
        """
        if data.empty:
            return data
        
        # Remove NaN
        data = data.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        
        # Ensure OHLCV consistency
        invalid = (
            (data['high'] < data['low']) |
            (data['high'] < data['close']) |
            (data['high'] < data['open']) |
            (data['low'] > data['close']) |
            (data['low'] > data['open'])
        )
        
        if invalid.any():
            logger.warning(f"Found {invalid.sum()} invalid OHLCV bars, removing")
            data = data[~invalid]
        
        # Remove zero volume bars
        data = data[data['volume'] > 0]

        return data

    def _fetch_from_nse(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch data from NSE using nsepython library

        Args:
            symbol: NSE symbol (e.g., "TATAMOTORS.NS" or "TATAMOTORS")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
        """
        # Check if NSE library is available
        if not NSE_AVAILABLE:
            logger.warning("nsepython library not available, skipping NSE fallback")
            return pd.DataFrame()

        try:
            # Remove .NS suffix if present
            nse_symbol = symbol.replace('.NS', '')

            # Convert dates to datetime objects
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            # NSE Python uses different date format
            logger.info(f"Fetching {nse_symbol} from NSE...")

            # Fetch historical data using nsepython
            # nsepython.equity_history provides historical data
            try:
                data = equity_history(
                    nse_symbol,
                    "EQ",  # Series
                    start_dt,
                    end_dt
                )
            except Exception as e:
                # Fallback: Return empty DataFrame if NSE method not available
                logger.warning(f"NSE data fetch not available for {nse_symbol}: {e}")
                return pd.DataFrame()

            if data is None or (isinstance(data, pd.DataFrame) and data.empty):
                return pd.DataFrame()

            # Convert to DataFrame if needed
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            # Standardize column names to match Yahoo Finance format
            # NSE typically has: Date, Open, High, Low, Close, Volume
            column_mapping = {
                'Date': 'date',
                'CH_TIMESTAMP': 'date',
                'CH_OPENING_PRICE': 'open',
                'CH_TRADE_HIGH_PRICE': 'high',
                'CH_TRADE_LOW_PRICE': 'low',
                'CH_CLOSING_PRICE': 'close',
                'CH_TOT_TRADED_QTY': 'volume',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }

            data = data.rename(columns=column_mapping)

            # Set date as index
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data = data.set_index('date')

            # Keep only OHLCV columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            data = data[[col for col in required_cols if col in data.columns]]

            if len(data.columns) < 5:
                logger.warning(f"Incomplete data from NSE for {nse_symbol}")
                return pd.DataFrame()

            logger.info(f"Successfully fetched {len(data)} bars from NSE for {nse_symbol}")
            return data

        except ImportError:
            logger.error("nsepython library not available")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"NSE fetch error for {symbol}: {e}")
            return pd.DataFrame()


# Test function
if __name__ == '__main__':
    fetcher = DataFetcherTool()
    
    # Test fetch
    data = fetcher.fetch_multi_timeframe_data(
        symbol="TATAMOTORS.NS",
        start_date="2023-01-01",
        end_date="2024-11-01",
        timeframes=['daily', 'weekly']
    )
    
    print(f"\nFetched data:")
    for tf, df in data.items():
        print(f"{tf}: {len(df)} bars")
        if not df.empty:
            print(df.tail(3))

# FX-001: Data Ingestion System

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-1 (Data Ingestion & Validation)
**Priority**: CRITICAL
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Functional Design](#functional-design)
5. [Technical Specification](#technical-specification)
6. [API Contracts](#api-contracts)
7. [Data Models](#data-models)
8. [Business Rules](#business-rules)
9. [Test Cases](#test-cases)
10. [Edge Cases](#edge-cases)
11. [Performance Requirements](#performance-requirements)
12. [Dependencies](#dependencies)

---

## Overview

### Purpose

The Data Ingestion System fetches, validates, and caches market data from multiple sources (Angel One, Yahoo Finance) to ensure high-quality inputs for trading signals and backtesting.

### Background

**Data Quality = Signal Quality**

Poor data leads to:
- False signals (garbage in, garbage out)
- Missed opportunities (incomplete data)
- System crashes (malformed data)
- Compliance issues (audit trail gaps)

**Why Multiple Sources?**
- **Angel One**: Real-time Indian market data, live order book
- **Yahoo Finance**: Historical data, corporate actions, fallback source
- **Redundancy**: If one source fails, use backup

### Scope

**In Scope**:
- Fetch OHLCV data from Angel One API
- Fetch historical data from Yahoo Finance
- Validate data quality (no gaps, no outliers)
- Handle corporate actions (splits, bonuses)
- Cache data locally (SQLite)
- Real-time data for paper/live trading
- Historical data for backtesting

**Out of Scope**:
- Fundamental data (earnings, ratios) - handled separately
- News/sentiment data - handled by FX-008
- Options chain data (future version)
- Level 2 order book data (future version)

---

## User Story

**As** the Trading System
**I want** reliable market data from Angel One and Yahoo Finance
**So that** I can generate accurate trading signals and backtest strategies

### Scenarios

#### Scenario 1: Fetch Live OHLCV Data

**Given**:
- Market is open (9:15 AM - 3:30 PM IST)
- Symbol: "RELIANCE-EQ"

**When**: Fetch current 5-minute candle

**Then**:
1. API request to Angel One
2. Receive candle: {open: 2500, high: 2505, low: 2498, close: 2502, volume: 150000}
3. Validate: No nulls, high >= low, volume > 0
4. Store in cache
5. Return candle to caller

#### Scenario 2: Fetch Historical Data for Backtest

**Given**:
- Symbol: "TCS.NS"
- Date range: 2024-01-01 to 2024-12-31

**When**: Fetch 1-year daily data

**Then**:
1. Check cache first (avoid redundant API calls)
2. If missing, fetch from Yahoo Finance
3. Validate 250+ trading days (expected for 1 year)
4. Check for gaps (holidays, suspensions)
5. Store in cache
6. Return DataFrame with 252 rows

#### Scenario 3: Handle Corporate Action (Stock Split)

**Given**:
- Symbol: "INFY"
- Split: 1:1 on 2024-06-15
- Historical data: Pre-split prices not adjusted

**When**: Fetch data spanning split date

**Then**:
1. Detect split in Yahoo Finance metadata
2. Adjust all pre-split prices (divide by 2)
3. Adjust all pre-split volumes (multiply by 2)
4. Flag data as "SPLIT_ADJUSTED"
5. Store adjusted data

#### Scenario 4: Data Validation Failure

**Given**:
- API returns: {open: 2500, high: 2400, low: 2600, close: 2550}
- Invalid: high < low

**When**: Validate data

**Then**:
1. Detect anomaly: high (2400) < low (2600)
2. Log error: "Invalid OHLC: high < low"
3. Reject data
4. Attempt fallback source (Yahoo Finance)
5. If fallback fails, return error to caller

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Fetch live OHLCV data from Angel One API with <500ms latency
✅ **AC-2**: Fetch historical daily data from Yahoo Finance for any symbol
✅ **AC-3**: Validate all data: no nulls, high >= low >= close >= open, volume >= 0
✅ **AC-4**: Detect and handle corporate actions (splits, bonuses, dividends)
✅ **AC-5**: Cache data locally to reduce API calls (SQLite)
✅ **AC-6**: Handle API failures gracefully (retry with exponential backoff)
✅ **AC-7**: Support multiple timeframes: 1min, 5min, 15min, 1day
✅ **AC-8**: Provide fallback to Yahoo Finance if Angel One fails
✅ **AC-9**: Log all API calls and errors for debugging

### Should Have

⭕ **AC-10**: Fetch intraday data (1min, 5min) from Angel One
⭕ **AC-11**: Auto-refresh cache daily (scheduled task)
⭕ **AC-12**: Track API usage to avoid rate limits
⭕ **AC-13**: Support batch fetching (multiple symbols in one call)

### Nice to Have

🔵 **AC-14**: WebSocket streaming for real-time data
🔵 **AC-15**: Pre-fetch data for watchlist symbols
🔵 **AC-16**: Data quality metrics dashboard

---

## Functional Design

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DataIngestionManager                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  AngelOneClient                                       │ │
│  │  - Authenticate (JWT token)                           │ │
│  │  - Fetch live OHLCV                                   │ │
│  │  - Fetch historical intraday                          │ │
│  │  - Handle rate limits                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  YahooFinanceClient                                   │ │
│  │  - Fetch historical daily data                        │ │
│  │  - Fetch corporate actions                            │ │
│  │  - Fallback for missing data                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  DataValidator                                        │ │
│  │  - Validate OHLCV integrity                           │ │
│  │  - Detect outliers                                    │ │
│  │  - Check for gaps                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  CorporateActionHandler                               │ │
│  │  - Detect splits/bonuses                              │ │
│  │  - Adjust historical prices                           │ │
│  │  - Flag adjusted data                                 │ │
│  └───────────────────────────────────────────────────────┘ │
│                          ↓                                  │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  DataCache (SQLite)                                   │ │
│  │  - Store OHLCV data                                   │ │
│  │  - Query cached data                                  │ │
│  │  - Manage TTL (time to live)                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Request: Fetch OHLCV for "RELIANCE-EQ", timeframe=5min, from Angel One

Step 1: Check Cache
  ├─ Query: SELECT * FROM ohlcv WHERE symbol='RELIANCE-EQ'
  │         AND timeframe='5min' AND timestamp > NOW() - 5min
  ├─ Cache hit? Return cached data
  └─ Cache miss? Proceed to API

Step 2: Fetch from Angel One
  ├─ Authenticate (JWT token from stored credentials)
  ├─ API call: GET /api/v1/quote?symbol=RELIANCE-EQ&exchange=NSE
  ├─ Response: {open: 2500, high: 2505, low: 2498, close: 2502, volume: 150000}
  └─ Status: 200 OK

Step 3: Validate Data
  ├─ Check nulls: All fields present ✅
  ├─ Check OHLC integrity: high (2505) >= low (2498) ✅
  ├─ Check volume: 150000 > 0 ✅
  ├─ Check outliers: Price within 5% of yesterday close ✅
  └─ Validation: PASS

Step 4: Store in Cache
  ├─ INSERT INTO ohlcv (symbol, timeframe, timestamp, open, high, low, close, volume)
  │  VALUES ('RELIANCE-EQ', '5min', '2025-11-19 09:35:00', 2500, 2505, 2498, 2502, 150000)
  └─ TTL: 5 minutes (for intraday data)

Step 5: Return Data
  └─ Output: {
      symbol: "RELIANCE-EQ",
      timeframe: "5min",
      timestamp: "2025-11-19 09:35:00",
      open: 2500,
      high: 2505,
      low: 2498,
      close: 2502,
      volume: 150000,
      source: "ANGEL_ONE",
      cached: false
    }
```

---

## Technical Specification

### Class: `DataIngestionManager`

```python
# data/ingestion_manager.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import pandas as pd

@dataclass
class OHLCVCandle:
    """Single OHLCV candle"""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
    adjusted: bool = False

@dataclass
class DataFetchResult:
    """Result of data fetch operation"""
    success: bool
    data: Optional[pd.DataFrame]
    source: str
    error: Optional[str] = None
    cached: bool = False

class DataIngestionManager:
    """
    Centralized data ingestion from multiple sources

    Responsibilities:
    - Fetch data from Angel One and Yahoo Finance
    - Validate data quality
    - Handle corporate actions
    - Cache data locally
    - Provide fallback mechanisms
    """

    def __init__(
        self,
        angel_one_api_key: str,
        angel_one_client_id: str,
        angel_one_password: str,
        angel_one_totp_secret: str,
        cache_db_path: str = "data_cache.db",
    ):
        """
        Initialize Data Ingestion Manager

        Args:
            angel_one_api_key: Angel One API key
            angel_one_client_id: Angel One client ID
            angel_one_password: Angel One password
            angel_one_totp_secret: TOTP secret for 2FA
            cache_db_path: Path to SQLite cache database
        """
        self.logger = logging.getLogger(__name__)

        # Data sources
        self.angel_client = AngelOneClient(
            api_key=angel_one_api_key,
            client_id=angel_one_client_id,
            password=angel_one_password,
            totp_secret=angel_one_totp_secret,
        )

        self.yahoo_client = YahooFinanceClient()

        # Validation and processing
        self.validator = DataValidator()
        self.corporate_action_handler = CorporateActionHandler()

        # Cache
        self.cache = DataCache(cache_db_path)

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: str = "auto",
        use_cache: bool = True,
    ) -> DataFetchResult:
        """
        Fetch OHLCV data with validation and caching

        Args:
            symbol: Stock symbol (e.g., "RELIANCE-EQ" for Angel One, "RELIANCE.NS" for Yahoo)
            timeframe: Timeframe (1min, 5min, 15min, 1day)
            start_date: Start date (for historical data)
            end_date: End date (for historical data)
            source: Data source ("angel_one", "yahoo", "auto")
            use_cache: Whether to use cached data

        Returns:
            DataFetchResult with OHLCV DataFrame
        """
        # Step 1: Try cache first
        if use_cache:
            cached_data = self.cache.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
            )

            if cached_data is not None and not cached_data.empty:
                self.logger.info(f"Cache HIT: {symbol} {timeframe}")
                return DataFetchResult(
                    success=True,
                    data=cached_data,
                    source="CACHE",
                    cached=True,
                )

        # Step 2: Determine source
        if source == "auto":
            # Use Angel One for intraday, Yahoo for daily
            if timeframe in ["1min", "5min", "15min"]:
                source = "angel_one"
            else:
                source = "yahoo"

        # Step 3: Fetch from source
        try:
            if source == "angel_one":
                df = self._fetch_from_angel_one(
                    symbol, timeframe, start_date, end_date
                )
            elif source == "yahoo":
                df = self._fetch_from_yahoo(
                    symbol, timeframe, start_date, end_date
                )
            else:
                return DataFetchResult(
                    success=False,
                    data=None,
                    source=source,
                    error=f"Unknown source: {source}",
                )

        except Exception as e:
            self.logger.error(f"Failed to fetch from {source}: {e}")

            # Fallback
            if source == "angel_one":
                self.logger.info("Trying Yahoo Finance fallback...")
                try:
                    df = self._fetch_from_yahoo(
                        symbol, timeframe, start_date, end_date
                    )
                    source = "yahoo_fallback"
                except Exception as fallback_error:
                    return DataFetchResult(
                        success=False,
                        data=None,
                        source=source,
                        error=f"All sources failed: {e}, {fallback_error}",
                    )
            else:
                return DataFetchResult(
                    success=False,
                    data=None,
                    source=source,
                    error=str(e),
                )

        # Step 4: Validate data
        validation_result = self.validator.validate_ohlcv(df)

        if not validation_result.is_valid:
            return DataFetchResult(
                success=False,
                data=None,
                source=source,
                error=f"Validation failed: {validation_result.errors}",
            )

        # Step 5: Handle corporate actions
        df = self.corporate_action_handler.adjust_for_corporate_actions(
            df, symbol
        )

        # Step 6: Store in cache
        self.cache.store_ohlcv(df, symbol, timeframe)

        # Step 7: Return result
        return DataFetchResult(
            success=True,
            data=df,
            source=source,
            cached=False,
        )

    def _fetch_from_angel_one(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> pd.DataFrame:
        """Fetch data from Angel One API"""

        # Authenticate if needed
        if not self.angel_client.is_authenticated():
            self.angel_client.login()

        # Convert timeframe to Angel One format
        interval = self._convert_timeframe_to_angel_one_interval(timeframe)

        # Fetch data
        data = self.angel_client.get_historical_data(
            exchange="NSE",
            symbol_token=self._get_symbol_token(symbol),
            interval=interval,
            from_date=start_date,
            to_date=end_date,
        )

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Rename columns to standard format
        df = df.rename(columns={
            "timestamp": "datetime",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
        })

        df["symbol"] = symbol
        df["source"] = "ANGEL_ONE"

        return df

    def _fetch_from_yahoo(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""

        import yfinance as yf

        # Convert symbol to Yahoo format (e.g., RELIANCE.NS)
        yahoo_symbol = self._convert_to_yahoo_symbol(symbol)

        # Convert timeframe to Yahoo interval
        interval = self._convert_timeframe_to_yahoo_interval(timeframe)

        # Fetch data
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(
            start=start_date,
            end=end_date,
            interval=interval,
        )

        # Standardize column names
        df = df.rename(columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })

        df["symbol"] = symbol
        df["source"] = "YAHOO_FINANCE"
        df.reset_index(inplace=True)
        df = df.rename(columns={"Date": "datetime"})

        return df

    def _convert_timeframe_to_angel_one_interval(self, timeframe: str) -> str:
        """Convert standard timeframe to Angel One interval"""
        mapping = {
            "1min": "ONE_MINUTE",
            "5min": "FIVE_MINUTE",
            "15min": "FIFTEEN_MINUTE",
            "1day": "ONE_DAY",
        }
        return mapping.get(timeframe, "ONE_DAY")

    def _convert_timeframe_to_yahoo_interval(self, timeframe: str) -> str:
        """Convert standard timeframe to Yahoo Finance interval"""
        mapping = {
            "1min": "1m",
            "5min": "5m",
            "15min": "15m",
            "1day": "1d",
        }
        return mapping.get(timeframe, "1d")

    def _convert_to_yahoo_symbol(self, symbol: str) -> str:
        """Convert Angel One symbol to Yahoo Finance format"""
        # Remove -EQ suffix for NSE
        symbol = symbol.replace("-EQ", "")

        # Add .NS for NSE symbols
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            symbol = symbol + ".NS"

        return symbol

    def _get_symbol_token(self, symbol: str) -> str:
        """Get Angel One symbol token for a given symbol"""
        # This would query Angel One's master symbol list
        # For now, return placeholder
        # TODO: Implement symbol token lookup
        return symbol
```

### Class: `DataValidator`

```python
# data/validator.py
from dataclasses import dataclass
from typing import List
import pandas as pd
import numpy as np

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class DataValidator:
    """Validate OHLCV data quality"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_ohlcv(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate OHLCV DataFrame

        Checks:
        - No null values
        - High >= Low
        - Close within [Low, High]
        - Open within [Low, High]
        - Volume >= 0
        - No extreme outliers (>10% price jump)
        - No duplicate timestamps

        Args:
            df: DataFrame with OHLCV data

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Check 1: No nulls
        if df.isnull().any().any():
            null_cols = df.columns[df.isnull().any()].tolist()
            errors.append(f"Null values found in columns: {null_cols}")

        # Check 2: OHLC integrity
        invalid_ohlc = df[
            (df["high"] < df["low"]) |
            (df["close"] > df["high"]) |
            (df["close"] < df["low"]) |
            (df["open"] > df["high"]) |
            (df["open"] < df["low"])
        ]

        if not invalid_ohlc.empty:
            errors.append(
                f"Invalid OHLC relationships in {len(invalid_ohlc)} rows"
            )

        # Check 3: Volume >= 0
        invalid_volume = df[df["volume"] < 0]
        if not invalid_volume.empty:
            errors.append(
                f"Negative volume in {len(invalid_volume)} rows"
            )

        # Check 4: Outliers (>10% jump from previous close)
        df["prev_close"] = df["close"].shift(1)
        df["price_change_pct"] = (
            (df["close"] - df["prev_close"]) / df["prev_close"]
        ).abs()

        outliers = df[df["price_change_pct"] > 0.10]
        if not outliers.empty:
            warnings.append(
                f"{len(outliers)} candles with >10% price jump. "
                f"Check for corporate actions or data errors."
            )

        # Check 5: Duplicate timestamps
        duplicates = df[df.duplicated(subset=["datetime"], keep=False)]
        if not duplicates.empty:
            errors.append(
                f"Duplicate timestamps found: {len(duplicates)} rows"
            )

        # Check 6: Chronological order
        if not df["datetime"].is_monotonic_increasing:
            errors.append("Data is not in chronological order")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )
```

### Class: `CorporateActionHandler`

```python
# data/corporate_actions.py
from datetime import datetime
import pandas as pd
import yfinance as yf

class CorporateActionHandler:
    """Handle corporate actions (splits, bonuses, dividends)"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def adjust_for_corporate_actions(
        self, df: pd.DataFrame, symbol: str
    ) -> pd.DataFrame:
        """
        Adjust OHLCV data for corporate actions

        Args:
            df: OHLCV DataFrame
            symbol: Stock symbol

        Returns:
            Adjusted DataFrame
        """
        # Get corporate actions from Yahoo Finance
        yahoo_symbol = self._convert_to_yahoo_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)

        try:
            # Get splits
            splits = ticker.splits

            if not splits.empty:
                self.logger.info(
                    f"Found {len(splits)} splits for {symbol}"
                )

                # Adjust prices and volumes
                for split_date, split_ratio in splits.items():
                    df = self._adjust_for_split(
                        df, split_date, split_ratio
                    )

                df["adjusted"] = True

        except Exception as e:
            self.logger.warning(
                f"Could not fetch corporate actions for {symbol}: {e}"
            )

        return df

    def _adjust_for_split(
        self, df: pd.DataFrame, split_date: datetime, split_ratio: float
    ) -> pd.DataFrame:
        """
        Adjust data for stock split

        Args:
            df: OHLCV DataFrame
            split_date: Date of split
            split_ratio: Split ratio (e.g., 2.0 for 1:2 split)

        Returns:
            Adjusted DataFrame
        """
        # Adjust all prices before split date
        mask = df["datetime"] < split_date

        df.loc[mask, "open"] = df.loc[mask, "open"] / split_ratio
        df.loc[mask, "high"] = df.loc[mask, "high"] / split_ratio
        df.loc[mask, "low"] = df.loc[mask, "low"] / split_ratio
        df.loc[mask, "close"] = df.loc[mask, "close"] / split_ratio

        # Adjust volume (multiply)
        df.loc[mask, "volume"] = df.loc[mask, "volume"] * split_ratio

        self.logger.info(
            f"Adjusted {mask.sum()} rows for split ratio {split_ratio}"
        )

        return df

    def _convert_to_yahoo_symbol(self, symbol: str) -> str:
        """Convert to Yahoo Finance symbol format"""
        symbol = symbol.replace("-EQ", "")
        if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
            symbol = symbol + ".NS"
        return symbol
```

### Class: `DataCache`

```python
# data/cache.py
import sqlite3
from datetime import datetime
import pandas as pd
from typing import Optional

class DataCache:
    """SQLite cache for OHLCV data"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create cache tables if not exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ohlcv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            datetime TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            source TEXT NOT NULL,
            adjusted BOOLEAN DEFAULT 0,
            cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timeframe, datetime)
        )
        """)

        # Index for fast queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_symbol_timeframe_datetime
        ON ohlcv(symbol, timeframe, datetime)
        """)

        conn.commit()
        conn.close()

    def store_ohlcv(
        self, df: pd.DataFrame, symbol: str, timeframe: str
    ) -> None:
        """Store OHLCV data in cache"""
        conn = sqlite3.connect(self.db_path)

        # Prepare data
        df_to_store = df.copy()
        df_to_store["symbol"] = symbol
        df_to_store["timeframe"] = timeframe
        df_to_store["cached_at"] = datetime.now().isoformat()

        # Insert or replace
        df_to_store.to_sql(
            "ohlcv",
            conn,
            if_exists="append",
            index=False,
        )

        conn.close()

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[pd.DataFrame]:
        """Retrieve OHLCV data from cache"""
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT datetime, open, high, low, close, volume, source, adjusted
        FROM ohlcv
        WHERE symbol = ? AND timeframe = ?
        """

        params = [symbol, timeframe]

        if start_date:
            query += " AND datetime >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND datetime <= ?"
            params.append(end_date.isoformat())

        query += " ORDER BY datetime ASC"

        df = pd.read_sql_query(query, conn, params=params)

        conn.close()

        if df.empty:
            return None

        # Convert datetime column
        df["datetime"] = pd.to_datetime(df["datetime"])

        return df
```

---

## API Contracts

### Input: Fetch OHLCV Request

```python
request = {
    "symbol": "RELIANCE-EQ",
    "timeframe": "5min",
    "start_date": datetime(2025, 11, 1),
    "end_date": datetime(2025, 11, 19),
    "source": "auto",  # or "angel_one", "yahoo"
    "use_cache": True,
}
```

### Output: DataFetchResult

```python
result = DataFetchResult(
    success=True,
    data=pd.DataFrame({
        "datetime": [...],
        "open": [...],
        "high": [...],
        "low": [...],
        "close": [...],
        "volume": [...],
    }),
    source="ANGEL_ONE",
    cached=False,
    error=None,
)
```

### Integration with Signal Generator

```python
# signals/adx_dma_scanner.py
from data.ingestion_manager import DataIngestionManager

def generate_signals():
    """Generate ADX+DMA signals"""

    # Fetch data
    ingestion_mgr = DataIngestionManager(...)

    result = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="1day",
        start_date=datetime.now() - timedelta(days=100),
        end_date=datetime.now(),
    )

    if not result.success:
        logger.error(f"Data fetch failed: {result.error}")
        return []

    df = result.data

    # Calculate ADX and DMA
    # ... signal generation logic ...

    return signals
```

---

## Data Models

### Database: `data_cache.db`

#### Table: `ohlcv`

```sql
CREATE TABLE ohlcv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,  -- '1min', '5min', '15min', '1day'
    datetime TEXT NOT NULL,   -- ISO format: '2025-11-19T09:35:00'
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume INTEGER NOT NULL,
    source TEXT NOT NULL,     -- 'ANGEL_ONE', 'YAHOO_FINANCE', 'CACHE'
    adjusted BOOLEAN DEFAULT 0,  -- 1 if adjusted for corporate actions
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, timeframe, datetime)
);

CREATE INDEX idx_symbol_timeframe_datetime
ON ohlcv(symbol, timeframe, datetime);
```

---

## Business Rules

### BR-1: Data Freshness

**Rule**: Cached intraday data expires after 5 minutes

**Implementation**:
```python
if timeframe in ["1min", "5min", "15min"]:
    cache_ttl = timedelta(minutes=5)
else:
    cache_ttl = timedelta(hours=24)

cached_at = row["cached_at"]
if datetime.now() - cached_at > cache_ttl:
    # Cache expired, fetch fresh data
    return None
```

### BR-2: OHLC Integrity

**Rule**: high >= low and close, open within [low, high]

**Implementation**:
```python
def validate_ohlc_integrity(row):
    if row["high"] < row["low"]:
        raise ValueError("high must be >= low")

    if row["close"] > row["high"] or row["close"] < row["low"]:
        raise ValueError("close must be within [low, high]")

    if row["open"] > row["high"] or row["open"] < row["low"]:
        raise ValueError("open must be within [low, high]")
```

### BR-3: Corporate Action Adjustment

**Rule**: All historical prices must be split-adjusted

**Implementation**:
```python
# If split detected (e.g., 1:2 on 2024-06-15)
for row in df.iterrows():
    if row["datetime"] < split_date:
        row["open"] /= split_ratio
        row["high"] /= split_ratio
        row["low"] /= split_ratio
        row["close"] /= split_ratio
        row["volume"] *= split_ratio
```

### BR-4: Rate Limiting

**Rule**: Max 10 Angel One API calls per second

**Implementation**:
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls_per_second):
        self.max_calls = max_calls_per_second
        self.calls = deque()

    def wait_if_needed(self):
        now = time.time()

        # Remove calls older than 1 second
        while self.calls and self.calls[0] < now - 1:
            self.calls.popleft()

        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = 1 - (now - self.calls[0])
            time.sleep(sleep_time)

        self.calls.append(time.time())
```

### BR-5: Fallback Mechanism

**Rule**: If Angel One fails, use Yahoo Finance

**Implementation**:
```python
try:
    df = angel_client.fetch_data(symbol)
except Exception as e:
    logger.warning(f"Angel One failed: {e}")
    logger.info("Trying Yahoo Finance fallback...")
    df = yahoo_client.fetch_data(symbol)
```

---

## Test Cases

### TC-001: Fetch Live OHLCV from Angel One

**Test Code**:
```python
def test_fetch_live_ohlcv_angel_one():
    ingestion_mgr = DataIngestionManager(...)

    result = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="5min",
        source="angel_one",
        use_cache=False,
    )

    assert result.success is True
    assert result.source == "angel_one"
    assert result.data is not None
    assert len(result.data) > 0

    # Check columns
    assert "open" in result.data.columns
    assert "high" in result.data.columns
    assert "low" in result.data.columns
    assert "close" in result.data.columns
    assert "volume" in result.data.columns
```

### TC-002: Fetch Historical Data from Yahoo Finance

**Test Code**:
```python
def test_fetch_historical_yahoo():
    ingestion_mgr = DataIngestionManager(...)

    result = ingestion_mgr.fetch_ohlcv(
        symbol="TCS.NS",
        timeframe="1day",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        source="yahoo",
        use_cache=False,
    )

    assert result.success is True
    assert result.source == "yahoo"

    # Should have ~250 trading days
    assert len(result.data) >= 240
    assert len(result.data) <= 260
```

### TC-003: Data Validation - Invalid OHLC

**Test Code**:
```python
def test_validation_invalid_ohlc():
    validator = DataValidator()

    # Create invalid data (high < low)
    df = pd.DataFrame({
        "datetime": [datetime.now()],
        "open": [2500],
        "high": [2400],  # Invalid: high < low
        "low": [2600],   # Invalid: high < low
        "close": [2550],
        "volume": [100000],
    })

    result = validator.validate_ohlcv(df)

    assert result.is_valid is False
    assert "Invalid OHLC" in result.errors[0]
```

### TC-004: Corporate Action Adjustment

**Test Code**:
```python
def test_corporate_action_split_adjustment():
    handler = CorporateActionHandler()

    # Create data spanning split date
    df = pd.DataFrame({
        "datetime": [
            datetime(2024, 6, 14),  # Before split
            datetime(2024, 6, 16),  # After split
        ],
        "open": [1000, 500],
        "high": [1010, 510],
        "low": [990, 490],
        "close": [1005, 505],
        "volume": [100000, 200000],
    })

    # Assume 1:2 split on 2024-06-15
    adjusted_df = handler._adjust_for_split(
        df,
        split_date=datetime(2024, 6, 15),
        split_ratio=2.0,
    )

    # Pre-split prices should be halved
    assert adjusted_df.iloc[0]["close"] == 502.5  # 1005 / 2

    # Pre-split volume should be doubled
    assert adjusted_df.iloc[0]["volume"] == 200000  # 100000 * 2

    # Post-split data unchanged
    assert adjusted_df.iloc[1]["close"] == 505
```

### TC-005: Cache Hit

**Test Code**:
```python
def test_cache_hit():
    ingestion_mgr = DataIngestionManager(...)

    # First fetch (cache miss)
    result1 = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="1day",
        start_date=datetime(2024, 11, 1),
        end_date=datetime(2024, 11, 19),
        use_cache=True,
    )

    assert result1.cached is False

    # Second fetch (cache hit)
    result2 = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="1day",
        start_date=datetime(2024, 11, 1),
        end_date=datetime(2024, 11, 19),
        use_cache=True,
    )

    assert result2.cached is True
    assert result2.source == "CACHE"

    # Data should match
    pd.testing.assert_frame_equal(result1.data, result2.data)
```

### TC-006: Angel One Fallback to Yahoo

**Test Code**:
```python
def test_angel_one_fallback_to_yahoo(mocker):
    ingestion_mgr = DataIngestionManager(...)

    # Mock Angel One to fail
    mocker.patch.object(
        ingestion_mgr.angel_client,
        "get_historical_data",
        side_effect=Exception("API timeout"),
    )

    # Fetch should fallback to Yahoo
    result = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="1day",
        source="angel_one",  # Requested Angel One
        use_cache=False,
    )

    assert result.success is True
    assert result.source == "yahoo_fallback"
```

### TC-007: Rate Limiting

**Test Code**:
```python
def test_rate_limiting():
    limiter = RateLimiter(max_calls_per_second=10)

    start = time.time()

    # Make 15 calls
    for i in range(15):
        limiter.wait_if_needed()

    end = time.time()
    elapsed = end - start

    # Should take at least 1 second (15 calls > 10/sec limit)
    assert elapsed >= 1.0
```

---

## Edge Cases

### Edge Case 1: Missing Data (Market Holiday)

**Scenario**: Fetch data for a market holiday

**Expected**:
- Return empty DataFrame (no error)
- Log warning: "No data for 2025-01-26 (Holiday)"

**Implementation**:
```python
if df.empty:
    logger.warning(f"No data for {symbol} on {date}. Possible holiday.")
    return DataFetchResult(success=True, data=pd.DataFrame(), source=source)
```

### Edge Case 2: Stock Suspended

**Scenario**: Fetch data for suspended stock

**Expected**:
- Return last known data
- Flag: "SUSPENDED"
- Do not generate signals

**Implementation**:
```python
if is_suspended(symbol):
    logger.warning(f"{symbol} is suspended")
    df["suspended"] = True
    return df
```

### Edge Case 3: Extreme Volatility (Circuit Breaker)

**Scenario**: Stock hits upper/lower circuit (20% limit)

**Expected**:
- Data is valid (not an error)
- Volume may be 0 (no trades)
- Flag: "CIRCUIT_BREAKER"

**Implementation**:
```python
price_change_pct = (close - prev_close) / prev_close

if abs(price_change_pct) >= 0.20:
    logger.info(f"{symbol} hit circuit breaker: {price_change_pct:.2%}")
    df["circuit_breaker"] = True
```

### Edge Case 4: Token Expiry (Angel One)

**Scenario**: JWT token expires mid-session

**Expected**:
- Detect 401 error
- Re-authenticate automatically
- Retry request

**Implementation**:
```python
try:
    data = angel_client.fetch_data(symbol)
except UnauthorizedError:
    logger.warning("Token expired. Re-authenticating...")
    angel_client.login()
    data = angel_client.fetch_data(symbol)  # Retry
```

### Edge Case 5: IPO Listing (No Historical Data)

**Scenario**: Fetch data for newly listed stock

**Expected**:
- Return limited data (only since listing)
- Log: "Limited history: Stock listed on 2025-11-15"
- Do not generate signals (insufficient data)

**Implementation**:
```python
if len(df) < 100:  # Insufficient for ADX calculation
    logger.warning(
        f"{symbol} has only {len(df)} candles. "
        f"Need 100+ for ADX. Skipping."
    )
    return []  # No signals
```

---

## Performance Requirements

### PR-1: API Latency

**Requirement**: Live data fetch < 500ms

**Test**:
```python
def test_api_latency():
    ingestion_mgr = DataIngestionManager(...)

    start = time.time()
    result = ingestion_mgr.fetch_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="5min",
        use_cache=False,
    )
    end = time.time()

    latency = (end - start) * 1000  # ms
    assert latency < 500
```

### PR-2: Cache Query Speed

**Requirement**: Cache query < 10ms

**Test**:
```python
def test_cache_query_speed():
    cache = DataCache("data_cache.db")

    start = time.time()
    df = cache.get_ohlcv(
        symbol="RELIANCE-EQ",
        timeframe="1day",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
    )
    end = time.time()

    latency = (end - start) * 1000
    assert latency < 10
```

### PR-3: Batch Fetch

**Requirement**: Fetch 50 symbols in < 30 seconds

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor

def batch_fetch(symbols):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(ingestion_mgr.fetch_ohlcv, symbol)
            for symbol in symbols
        ]
        results = [f.result() for f in futures]
    return results
```

---

## Dependencies

### Internal Dependencies

- **Angel One API**: Real-time and historical data
- **Yahoo Finance API**: Historical data and corporate actions
- **SQLite**: Data caching

### External Dependencies

- **SmartAPI Python SDK**: Angel One client
- **yfinance**: Yahoo Finance client
- **pandas**: Data manipulation
- **pyotp**: TOTP for Angel One 2FA

### Environment Variables

```bash
ANGEL_ONE_API_KEY=your_api_key
ANGEL_ONE_CLIENT_ID=your_client_id
ANGEL_ONE_PASSWORD=your_password
ANGEL_ONE_TOTP_SECRET=your_totp_secret
```

---

## Implementation Checklist

- [ ] Create `data/ingestion_manager.py`
- [ ] Create `data/angel_one_client.py`
- [ ] Create `data/yahoo_finance_client.py`
- [ ] Create `data/validator.py`
- [ ] Create `data/corporate_actions.py`
- [ ] Create `data/cache.py`
- [ ] Create SQLite schema for data_cache.db
- [ ] Write 15 unit tests
- [ ] Write 3 integration tests
- [ ] Implement rate limiting
- [ ] Implement fallback mechanism
- [ ] Add logging for all API calls
- [ ] Performance testing (<500ms latency)
- [ ] Documentation

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-003 (Signal Generation ADX+DMA)

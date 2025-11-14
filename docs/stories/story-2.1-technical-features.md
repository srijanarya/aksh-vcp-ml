# Story 2.1: Technical Features Extraction

**Story ID**: EPIC2-S1
**Priority**: P0
**Estimated Effort**: 3 days
**Dependencies**: EPIC1 (price_movements.db available)

---

## User Story

**As a** ML Feature Engineer,
**I want** to extract technical indicators (RSI, MACD, Bollinger Bands) from price/volume data,
**so that** the model can capture momentum and volatility patterns before upper circuits.

---

## Acceptance Criteria

### AC2.1.1: TechnicalFeatureExtractor class initialization
- Class: `TechnicalFeatureExtractor(price_db_path: str)`
- Connects to `price_movements.db`
- Validates required columns exist (date, open, high, low, close, volume)

### AC2.1.2: RSI (Relative Strength Index) calculation
- Calculate 14-day RSI for each sample
- Formula: RSI = 100 - (100 / (1 + RS)), where RS = avg_gain / avg_loss
- Handle edge case: RSI = 50 if no price changes
- Output: `rsi_14` (0-100 scale)

### AC2.1.3: MACD (Moving Average Convergence Divergence)
- Calculate MACD with periods (12, 26, 9)
- MACD Line = EMA(12) - EMA(26)
- Signal Line = EMA(9) of MACD Line
- MACD Histogram = MACD Line - Signal Line
- Output: `macd_line`, `macd_signal`, `macd_histogram`

### AC2.1.4: Bollinger Bands
- Calculate 20-day Bollinger Bands (2 std dev)
- Middle Band = 20-day SMA
- Upper Band = Middle + (2 × std dev)
- Lower Band = Middle - (2 × std dev)
- BB %B = (Close - Lower) / (Upper - Lower)  # Position within bands
- Output: `bb_upper`, `bb_middle`, `bb_lower`, `bb_percent_b`

### AC2.1.5: Volume indicators
- Volume ratio = current_volume / 30-day avg volume
- Volume spike = 1 if volume_ratio > 2.0, else 0
- Output: `volume_ratio`, `volume_spike`

### AC2.1.6: Price momentum
- 5-day momentum = (close_today - close_5_days_ago) / close_5_days_ago × 100
- 10-day momentum = similar for 10 days
- 30-day momentum = similar for 30 days
- Output: `momentum_5d`, `momentum_10d`, `momentum_30d`

### AC2.1.7: Batch processing for all samples
- Method: `extract_features_for_sample(bse_code: str, date: str) -> Dict[str, float]`
- Method: `extract_features_batch(sample_ids: List[int]) -> pd.DataFrame`
- Process 200K+ samples in <5 minutes
- Use vectorized operations (pandas/numpy)

### AC2.1.8: Handle missing data gracefully
- If insufficient historical data (<30 days), return NaN for that feature
- Log warning for samples with missing features
- Target: ≤5% missing values across all technical features

---

## Technical Specifications

### Input
- Database: `price_movements.db`
- Required columns: `bse_code`, `date`, `open`, `high`, `low`, `close`, `volume`
- Date range: 2022-01-01 to 2025-11-13

### Output
Database: `feature_candidates.db`

Table: `technical_features`
```sql
CREATE TABLE technical_features (
    feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL,  -- References historical_upper_circuits.label_id
    bse_code TEXT NOT NULL,
    date DATE NOT NULL,

    -- RSI
    rsi_14 REAL,

    -- MACD
    macd_line REAL,
    macd_signal REAL,
    macd_histogram REAL,

    -- Bollinger Bands
    bb_upper REAL,
    bb_middle REAL,
    bb_lower REAL,
    bb_percent_b REAL,  -- Position within bands

    -- Volume
    volume_ratio REAL,
    volume_spike INTEGER,

    -- Momentum
    momentum_5d REAL,
    momentum_10d REAL,
    momentum_30d REAL,

    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sample_id)
);

CREATE INDEX idx_sample_id ON technical_features(sample_id);
CREATE INDEX idx_bse_date ON technical_features(bse_code, date);
```

### Feature Dictionary

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `rsi_14` | float | 0-100 | 14-day RSI (oversold <30, overbought >70) |
| `macd_line` | float | unbounded | MACD line (EMA12 - EMA26) |
| `macd_signal` | float | unbounded | Signal line (EMA9 of MACD) |
| `macd_histogram` | float | unbounded | MACD - Signal (momentum strength) |
| `bb_upper` | float | > close | Upper Bollinger Band (resistance) |
| `bb_middle` | float | ≈ close | Middle BB (20-day SMA) |
| `bb_lower` | float | < close | Lower BB (support) |
| `bb_percent_b` | float | 0-1 | Position within bands (>1 above upper, <0 below lower) |
| `volume_ratio` | float | >0 | Current volume / 30-day avg (spike if >2.0) |
| `volume_spike` | int | 0/1 | 1 if volume >2x average |
| `momentum_5d` | float | % | 5-day price momentum |
| `momentum_10d` | float | % | 10-day price momentum |
| `momentum_30d` | float | % | 30-day price momentum |

---

## Implementation Details

### File: `agents/ml/technical_feature_extractor.py`

```python
import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class TechnicalFeatures:
    """Technical features for a single sample"""
    rsi_14: Optional[float]
    macd_line: Optional[float]
    macd_signal: Optional[float]
    macd_histogram: Optional[float]
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]
    bb_percent_b: Optional[float]
    volume_ratio: Optional[float]
    volume_spike: Optional[int]
    momentum_5d: Optional[float]
    momentum_10d: Optional[float]
    momentum_30d: Optional[float]

class TechnicalFeatureExtractor:
    def __init__(self, price_db_path: str, output_db_path: str):
        self.price_db_path = price_db_path
        self.output_db_path = output_db_path
        self._initialize_output_database()

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI (AC2.1.2)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calculate MACD (AC2.1.3)"""
        ema_12 = prices.ewm(span=12, adjust=False).mean()
        ema_26 = prices.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        return {
            'macd_line': macd_line,
            'macd_signal': signal_line,
            'macd_histogram': histogram
        }

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands (AC2.1.4)"""
        middle_band = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        bb_percent_b = (prices - lower_band) / (upper_band - lower_band)
        return {
            'bb_upper': upper_band,
            'bb_middle': middle_band,
            'bb_lower': lower_band,
            'bb_percent_b': bb_percent_b
        }

    def calculate_volume_indicators(self, volume: pd.Series, period: int = 30) -> Dict[str, pd.Series]:
        """Calculate volume indicators (AC2.1.5)"""
        avg_volume = volume.rolling(window=period).mean()
        volume_ratio = volume / avg_volume
        volume_spike = (volume_ratio > 2.0).astype(int)
        return {
            'volume_ratio': volume_ratio,
            'volume_spike': volume_spike
        }

    def calculate_momentum(self, prices: pd.Series, periods: List[int] = [5, 10, 30]) -> Dict[str, pd.Series]:
        """Calculate price momentum (AC2.1.6)"""
        momentum = {}
        for period in periods:
            momentum[f'momentum_{period}d'] = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return momentum

    def extract_features_for_sample(self, bse_code: str, date: str, lookback_days: int = 60) -> TechnicalFeatures:
        """Extract technical features for a single sample (AC2.1.7)"""
        # Fetch historical price data
        conn = sqlite3.connect(self.price_db_path)
        query = """
            SELECT date, close, volume
            FROM price_movements
            WHERE bse_code = ? AND date <= ?
            ORDER BY date DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(bse_code, date, lookback_days))
        conn.close()

        if len(df) < 30:  # AC2.1.8: Insufficient data
            return TechnicalFeatures(None, None, None, None, None, None, None, None, None, None, None, None, None)

        df = df.sort_values('date')
        prices = df['close']
        volume = df['volume']

        # Calculate all indicators
        rsi = self.calculate_rsi(prices)
        macd = self.calculate_macd(prices)
        bb = self.calculate_bollinger_bands(prices)
        vol = self.calculate_volume_indicators(volume)
        mom = self.calculate_momentum(prices)

        # Get most recent values
        latest_idx = -1
        return TechnicalFeatures(
            rsi_14=rsi.iloc[latest_idx] if not rsi.empty else None,
            macd_line=macd['macd_line'].iloc[latest_idx],
            macd_signal=macd['macd_signal'].iloc[latest_idx],
            macd_histogram=macd['macd_histogram'].iloc[latest_idx],
            bb_upper=bb['bb_upper'].iloc[latest_idx],
            bb_middle=bb['bb_middle'].iloc[latest_idx],
            bb_lower=bb['bb_lower'].iloc[latest_idx],
            bb_percent_b=bb['bb_percent_b'].iloc[latest_idx],
            volume_ratio=vol['volume_ratio'].iloc[latest_idx],
            volume_spike=vol['volume_spike'].iloc[latest_idx],
            momentum_5d=mom['momentum_5d'].iloc[latest_idx],
            momentum_10d=mom['momentum_10d'].iloc[latest_idx],
            momentum_30d=mom['momentum_30d'].iloc[latest_idx]
        )

    def extract_features_batch(self, samples: List[Dict]) -> pd.DataFrame:
        """Extract features for multiple samples (AC2.1.7)"""
        # Vectorized batch processing for performance
        pass
```

### Test File: `tests/unit/test_technical_features.py`

**Test Cases**:
- Test RSI calculation: prices=[100, 102, 101, 103] → RSI ≈ 50-70
- Test MACD calculation: uptrend → MACD > 0, histogram > 0
- Test Bollinger Bands: price at middle → bb_percent_b ≈ 0.5
- Test volume spike detection: volume 3x avg → volume_spike = 1
- Test momentum calculation: 10% price increase over 5 days → momentum_5d ≈ 10%
- Test missing data handling: <30 days data → return NaN
- Test batch processing: 1000 samples in <5 seconds

---

## Performance Requirements

- **Batch processing**: 200K samples in <5 minutes (goal: <3 minutes)
- **Memory usage**: <2GB RAM for 200K samples
- **Vectorization**: Use pandas/numpy vectorized operations (no Python loops)

---

## Definition of Done

- [ ] Code implemented following TDD
- [ ] All 8 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Performance test: 10K samples in <30 seconds
- [ ] Integration test: Extract features for all 200K+ samples
- [ ] Missing data report: ≤5% missing values
- [ ] Feature dictionary documented
- [ ] Code review: Passes linter, type checking

---

**Author**: VCP Financial Research Team
**Created**: 2025-11-13

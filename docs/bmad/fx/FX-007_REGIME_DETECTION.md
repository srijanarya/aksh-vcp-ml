# FX-007: Regime Detection System

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-1 (Regime Detection & Optimal Strategy Discovery)
**Priority**: HIGH
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Regime Types](#regime-types)
5. [Feature Engineering](#feature-engineering)
6. [Technical Specification](#technical-specification)
7. [Training Process](#training-process)
8. [Test Cases](#test-cases)
9. [Performance Requirements](#performance-requirements)

---

## Overview

### Purpose

Detect the market "regime" (day type) at 9:15 AM and select the optimal trading strategy for that day.

### User Requirement

**User said**: *"Can we have a system that tries to figure out what would have made the most amount of money given the data or the movement of a particular day and then use a machine learning system to understand the regime"*

**Reference**: Frank Ochoa's "Pivot Boss" - Different day types require different strategies

### Why Regime Detection Matters

**Problem**: A single strategy doesn't work every day

- **Trending days**: ADX+DMA works great
- **Range-bound days**: Mean reversion works better
- **Volatile days**: Stay out or use wide stops
- **Expansion days**: Breakout strategies work
- **Contraction days**: Wait for setup

**Solution**: Detect day type in the morning → Select optimal strategy → Trade accordingly

---

## User Story

**As** the Portfolio Manager
**I want** to detect the market regime each morning
**So that** I use the strategy most likely to profit that day

### Success Criteria

1. Predict day type with >55% accuracy
2. Strategy selection improves returns vs single strategy
3. System learns from new data (weekly retraining)
4. Predictions made by 9:15 AM (before market fully opens)

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Extract morning features (gap, volume, VIX, ADX, sentiment) by 9:15 AM
✅ **AC-2**: Classify day into 5 types: expansion, contraction, trending, choppy, volatile
✅ **AC-3**: Train ML model (Random Forest or XGBoost) on historical data
✅ **AC-4**: Predict day type with >55% accuracy
✅ **AC-5**: Map day type to optimal strategy
✅ **AC-6**: Retrain model weekly with last week's data
✅ **AC-7**: Store predictions and actuals for validation

### Should Have

⭕ **AC-8**: Confidence score for predictions (0-1)
⭕ **AC-9**: Feature importance analysis (which features matter most)
⭕ **AC-10**: Fallback to conservative strategy if confidence < 50%

### Nice to Have

🔵 **AC-11**: Multi-model ensemble (combine predictions)
🔵 **AC-12**: Real-time regime change detection (intraday)
🔵 **AC-13**: Visualization of regime history

---

## Regime Types

### 1. Expansion Day

**Characteristics**:
- Gap up/down > 0.5%
- High volume (> 1.5× avg)
- High ADX (> 25)
- Directional move

**Best Strategy**: ADX+DMA (trend following)

**Example**: Nifty gaps up 1.2%, rallies all day

---

### 2. Contraction Day

**Characteristics**:
- Small gap (< 0.3%)
- Low volume (< 0.8× avg)
- Low ADX (< 15)
- Narrow range

**Best Strategy**: Wait / No trade (low opportunity)

**Example**: Nifty flat, drifts in 50-point range

---

### 3. Trending Day

**Characteristics**:
- Moderate gap (0.3-0.7%)
- Normal volume (0.8-1.5× avg)
- High ADX (> 20)
- Sustained direction

**Best Strategy**: ADX+DMA or Moving Average crossover

**Example**: Nifty opens flat, trends up steadily

---

### 4. Choppy Day

**Characteristics**:
- Mixed signals
- Low ADX (< 15)
- High intraday reversals
- Wide range but no direction

**Best Strategy**: Mean reversion or stay out

**Example**: Nifty swings +100, -100, +50, -75 (no net move)

---

### 5. Volatile Day

**Characteristics**:
- VIX > 25
- Large intraday swings
- News-driven
- Unpredictable

**Best Strategy**: Reduce position size or stay out

**Example**: Budget announcement, large swings both directions

---

## Feature Engineering

### Morning Features (Available by 9:15 AM)

#### F1: Gap Percentage

**Definition**: (Open - Previous Close) / Previous Close

**Example**:
- Prev Close: 22,000
- Open: 22,150
- Gap: (22,150 - 22,000) / 22,000 = 0.68% (gap up)

**Range**: -5% to +5%

---

#### F2: Pre-Market Volume Ratio

**Definition**: (9:00-9:15 volume) / (Average first 15 min volume)

**Example**:
- Pre-market volume: 5M shares
- Avg 9:00-9:15 volume: 3M shares
- Ratio: 5M / 3M = 1.67 (high interest)

**Range**: 0.5 to 3.0

---

#### F3: VIX Level

**Definition**: India VIX at 9:15 AM

**Categories**:
- Low: < 12
- Normal: 12-18
- Elevated: 18-25
- High: 25-35
- Extreme: > 35

**Range**: 10 to 50

---

#### F4: Nifty ADX (Previous Day Close)

**Definition**: ADX calculated from previous day's close

**Interpretation**:
- ADX > 25: Strong trend likely continues
- ADX 15-25: Developing trend
- ADX < 15: No trend, expect range-bound

**Range**: 0 to 100

---

#### F5: Overnight Sentiment Score

**Definition**: Sentiment from news (8 PM - 9 AM)

**Calculation**:
1. Fetch news articles (Trium Finance API)
2. LLM scores each article: -1 (bearish) to +1 (bullish)
3. Average score

**Example**:
- 5 positive articles: +0.8, +0.6, +0.7, +0.9, +0.5
- Avg: +0.70 (bullish sentiment)

**Range**: -1 to +1

---

#### F6: Global Cues

**Definition**: S&P 500 / Dow Jones overnight performance

**Example**:
- S&P 500 overnight: +0.8%
- Dow Jones: +1.1%
- Avg: +0.95% (positive global cue)

**Range**: -3% to +3%

---

#### F7: Nifty ATR (14-day)

**Definition**: Average True Range (volatility measure)

**Interpretation**:
- High ATR: Expect large moves
- Low ATR: Expect small moves

**Range**: 100 to 500 (points)

---

### Summary: Feature Vector

```python
features = {
    "gap_pct": 0.68,  # Gap up 0.68%
    "volume_ratio": 1.67,  # High pre-market volume
    "vix": 18.5,  # Elevated
    "nifty_adx": 28,  # Strong trend
    "sentiment": 0.70,  # Bullish
    "global_cues": 0.95,  # Positive
    "nifty_atr": 220,  # Moderate volatility
}
```

**Day Type Prediction**: Likely EXPANSION (gap + volume + trend)

---

## Technical Specification

### Class: `RegimeDetector`

```python
# intelligence/regime_detector.py
from dataclasses import dataclass
from datetime import datetime, date
from typing import Literal
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb
import pickle
import logging

@dataclass
class RegimePrediction:
    """Regime prediction result"""
    date: date
    predicted_regime: str
    confidence: float
    features: dict
    strategy: str  # Optimal strategy for this regime

RegimeType = Literal["expansion", "contraction", "trending", "choppy", "volatile"]

class RegimeDetector:
    """
    Detect market regime at 9:15 AM

    Uses ML model trained on historical data to predict day type
    """

    def __init__(self, model_path: str = None, db_path: str = "regime_training.db"):
        """
        Initialize regime detector

        Args:
            model_path: Path to trained model (pickle file)
            db_path: Path to training data database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path

        # Load model if exists
        if model_path and os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.logger.info(f"Loaded model from {model_path}")
        else:
            self.model = None
            self.logger.warning("No model loaded. Train first.")

        # Strategy mapping
        self.strategy_map = {
            "expansion": "ADX_DMA",
            "trending": "ADX_DMA",
            "contraction": "NO_TRADE",
            "choppy": "MEAN_REVERSION",
            "volatile": "REDUCE_SIZE",
        }

    def predict_regime(
        self,
        current_date: date,
        gap_pct: float,
        volume_ratio: float,
        vix: float,
        nifty_adx: float,
        sentiment: float,
        global_cues: float,
        nifty_atr: float,
    ) -> RegimePrediction:
        """
        Predict regime for today

        Args:
            current_date: Today's date
            gap_pct: Gap percentage
            volume_ratio: Pre-market volume ratio
            vix: India VIX
            nifty_adx: Nifty ADX (previous close)
            sentiment: Overnight sentiment (-1 to +1)
            global_cues: Global markets performance
            nifty_atr: Nifty 14-day ATR

        Returns:
            RegimePrediction object
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Create feature vector
        features = {
            "gap_pct": gap_pct,
            "volume_ratio": volume_ratio,
            "vix": vix,
            "nifty_adx": nifty_adx,
            "sentiment": sentiment,
            "global_cues": global_cues,
            "nifty_atr": nifty_atr,
        }

        X = pd.DataFrame([features])

        # Predict
        predicted_regime = self.model.predict(X)[0]

        # Get confidence (probability of predicted class)
        probabilities = self.model.predict_proba(X)[0]
        predicted_idx = self.model.classes_.tolist().index(predicted_regime)
        confidence = probabilities[predicted_idx]

        # Map regime to strategy
        strategy = self.strategy_map.get(predicted_regime, "ADX_DMA")

        self.logger.info(
            f"{current_date}: Predicted regime = {predicted_regime} "
            f"(confidence: {confidence:.2%}), Strategy = {strategy}"
        )

        return RegimePrediction(
            date=current_date,
            predicted_regime=predicted_regime,
            confidence=confidence,
            features=features,
            strategy=strategy,
        )

    def train(self, start_date: str, end_date: str) -> dict:
        """
        Train regime detection model

        Args:
            start_date: Training start date (YYYY-MM-DD)
            end_date: Training end date (YYYY-MM-DD)

        Returns:
            Training metrics dict
        """
        # Load labeled data from database
        df = self._load_training_data(start_date, end_date)

        if len(df) < 100:
            raise ValueError(
                f"Insufficient training data: {len(df)} days. Need at least 100."
            )

        # Split features and labels
        feature_cols = [
            "gap_pct", "volume_ratio", "vix", "nifty_adx",
            "sentiment", "global_cues", "nifty_atr"
        ]
        X = df[feature_cols]
        y = df["regime_label"]

        # Train-test split (80-20)
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            random_state=42,
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        train_accuracy = self.model.score(X_train, y_train)
        test_accuracy = self.model.score(X_test, y_test)

        self.logger.info(
            f"Model trained: Train accuracy = {train_accuracy:.2%}, "
            f"Test accuracy = {test_accuracy:.2%}"
        )

        # Feature importance
        feature_importance = dict(zip(
            feature_cols,
            self.model.feature_importances_
        ))

        # Save model
        model_path = f"models/regime_detector_{end_date}.pkl"
        os.makedirs("models", exist_ok=True)
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)

        self.logger.info(f"Model saved to {model_path}")

        return {
            "train_accuracy": train_accuracy,
            "test_accuracy": test_accuracy,
            "feature_importance": feature_importance,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }

    def _load_training_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load labeled training data from database"""
        import sqlite3

        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            date,
            gap_pct,
            volume_ratio,
            vix,
            nifty_adx,
            sentiment,
            global_cues,
            nifty_atr,
            regime_label  -- Labeled by analyze_historical_day()
        FROM regime_labels
        WHERE date >= ? AND date <= ?
        ORDER BY date
        """

        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()

        return df

    def extract_morning_features(self, current_date: date) -> dict:
        """
        Extract features at 9:15 AM

        This runs LIVE every morning at 9:15 AM

        Returns:
            Feature dict
        """
        # 1. Gap percentage
        gap_pct = self._calculate_gap()

        # 2. Pre-market volume ratio
        volume_ratio = self._calculate_volume_ratio()

        # 3. VIX
        vix = self._fetch_vix()

        # 4. Nifty ADX (previous close)
        nifty_adx = self._calculate_nifty_adx()

        # 5. Overnight sentiment
        sentiment = self._calculate_overnight_sentiment(current_date)

        # 6. Global cues
        global_cues = self._fetch_global_cues()

        # 7. Nifty ATR
        nifty_atr = self._calculate_nifty_atr()

        return {
            "gap_pct": gap_pct,
            "volume_ratio": volume_ratio,
            "vix": vix,
            "nifty_adx": nifty_adx,
            "sentiment": sentiment,
            "global_cues": global_cues,
            "nifty_atr": nifty_atr,
        }

    def _calculate_gap(self) -> float:
        """Calculate gap % (open vs prev close)"""
        # Fetch Nifty previous close and current open
        import yfinance as yf
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="2d")

        prev_close = hist['Close'].iloc[-2]
        current_open = hist['Open'].iloc[-1]

        gap_pct = (current_open - prev_close) / prev_close
        return gap_pct

    def _calculate_volume_ratio(self) -> float:
        """Calculate pre-market volume ratio"""
        # Fetch 9:00-9:15 volume vs historical avg
        # (Simplified: Use first hour volume ratio as proxy)
        import yfinance as yf
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1mo", interval="1h")

        # Today's first hour volume
        today_volume = hist['Volume'].iloc[-1]

        # Avg first hour volume (last 20 days)
        avg_first_hour = hist['Volume'].head(20).mean()

        volume_ratio = today_volume / avg_first_hour if avg_first_hour > 0 else 1.0
        return volume_ratio

    def _fetch_vix(self) -> float:
        """Fetch India VIX"""
        import yfinance as yf
        vix = yf.Ticker("^INDIAVIX")
        current_vix = vix.history(period="1d")['Close'].iloc[-1]
        return current_vix

    def _calculate_nifty_adx(self) -> float:
        """Calculate Nifty ADX from previous close"""
        from signals.adx_dma_scanner import ADXDMAScanner

        scanner = ADXDMAScanner(output_db_path=":memory:")
        nifty_data = scanner.fetch_stock_data("^NSEI", period="3mo")

        adx = scanner.calculate_adx(
            nifty_data['high'],
            nifty_data['low'],
            nifty_data['close']
        )

        return adx.iloc[-1]

    def _calculate_overnight_sentiment(self, current_date: date) -> float:
        """Calculate overnight sentiment from news"""
        from intelligence.sentiment_analyzer import SentimentAnalyzer

        analyzer = SentimentAnalyzer()

        # Fetch news from 8 PM yesterday to 9 AM today
        yesterday = current_date - timedelta(days=1)
        news_start = datetime.combine(yesterday, time(20, 0))
        news_end = datetime.combine(current_date, time(9, 0))

        sentiment_score = analyzer.analyze_news_period(
            start_time=news_start,
            end_time=news_end,
            symbols=["NIFTY", "INDIA"],  # General market news
        )

        return sentiment_score

    def _fetch_global_cues(self) -> float:
        """Fetch overnight performance of S&P 500 / Dow"""
        import yfinance as yf

        sp500 = yf.Ticker("^GSPC")
        sp500_hist = sp500.history(period="2d")
        sp500_return = (
            sp500_hist['Close'].iloc[-1] - sp500_hist['Close'].iloc[-2]
        ) / sp500_hist['Close'].iloc[-2]

        return sp500_return

    def _calculate_nifty_atr(self) -> float:
        """Calculate Nifty 14-day ATR"""
        import yfinance as yf

        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1mo")

        # ATR calculation
        high_low = hist['High'] - hist['Low']
        high_close = abs(hist['High'] - hist['Close'].shift())
        low_close = abs(hist['Low'] - hist['Close'].shift())

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=14).mean().iloc[-1]

        return atr
```

---

## Training Process

### Step 1: Label Historical Days

For each historical day, determine which strategy would have been most profitable:

```python
# intelligence/regime_labeler.py
def label_historical_day(date: str) -> str:
    """
    Analyze historical day and label regime

    Process:
    1. Run ADX+DMA strategy → PnL_A
    2. Run mean reversion strategy → PnL_B
    3. Run breakout strategy → PnL_C
    4. Best strategy → Regime label
    """

    results = {}

    # Test ADX+DMA
    results["ADX_DMA"] = backtest_strategy("ADX_DMA", date, date)

    # Test Mean Reversion
    results["MEAN_REVERSION"] = backtest_strategy("MEAN_REVERSION", date, date)

    # Test No Trade
    results["NO_TRADE"] = 0.0

    # Find best
    best_strategy = max(results, key=results.get)

    # Map strategy to regime
    if best_strategy == "ADX_DMA" and gap > 0.5 and volume > 1.5:
        return "expansion"
    elif best_strategy == "ADX_DMA":
        return "trending"
    elif best_strategy == "MEAN_REVERSION":
        return "choppy"
    elif best_strategy == "NO_TRADE":
        return "contraction"
    else:
        return "volatile"
```

### Step 2: Build Training Dataset

```sql
-- regime_training.db
CREATE TABLE regime_labels (
    date DATE PRIMARY KEY,
    gap_pct REAL,
    volume_ratio REAL,
    vix REAL,
    nifty_adx REAL,
    sentiment REAL,
    global_cues REAL,
    nifty_atr REAL,
    regime_label TEXT,  -- expansion, contraction, trending, choppy, volatile
    best_strategy TEXT,  -- ADX_DMA, MEAN_REVERSION, NO_TRADE
    pnl REAL  -- Actual PnL achieved by best strategy
);
```

### Step 3: Train Model

```python
detector = RegimeDetector()

# Train on 2 years of data
metrics = detector.train(
    start_date="2023-01-01",
    end_date="2024-12-31"
)

print(f"Test Accuracy: {metrics['test_accuracy']:.2%}")
print(f"Feature Importance: {metrics['feature_importance']}")
```

### Step 4: Weekly Retraining

```python
# Scheduled every Monday at 8:00 AM
def retrain_regime_model():
    detector = RegimeDetector()

    # Train on last 2 years
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=730)

    metrics = detector.train(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )

    logger.info(f"Model retrained. Accuracy: {metrics['test_accuracy']:.2%}")
```

---

## Test Cases

### TC-001: Predict Expansion Day

```python
def test_predict_expansion_day():
    detector = RegimeDetector(model_path="models/regime_detector.pkl")

    # Features for typical expansion day
    prediction = detector.predict_regime(
        current_date=date(2025, 11, 19),
        gap_pct=1.2,  # Large gap
        volume_ratio=2.0,  # High volume
        vix=18,  # Moderate VIX
        nifty_adx=28,  # Strong trend
        sentiment=0.7,  # Bullish
        global_cues=0.8,  # Positive
        nifty_atr=220,
    )

    assert prediction.predicted_regime == "expansion"
    assert prediction.strategy == "ADX_DMA"
    assert prediction.confidence > 0.50
```

### TC-002: Predict Contraction Day

```python
def test_predict_contraction_day():
    detector = RegimeDetector(model_path="models/regime_detector.pkl")

    prediction = detector.predict_regime(
        current_date=date(2025, 11, 19),
        gap_pct=0.1,  # Small gap
        volume_ratio=0.6,  # Low volume
        vix=12,  # Low VIX
        nifty_adx=10,  # Weak trend
        sentiment=0.0,  # Neutral
        global_cues=0.1,  # Flat
        nifty_atr=150,
    )

    assert prediction.predicted_regime == "contraction"
    assert prediction.strategy == "NO_TRADE"
```

### TC-003: Model Accuracy >55%

```python
def test_model_accuracy():
    detector = RegimeDetector()

    metrics = detector.train(
        start_date="2023-01-01",
        end_date="2024-12-31"
    )

    assert metrics["test_accuracy"] > 0.55  # > 55%
```

---

## Performance Requirements

### PR-1: Prediction Latency

**Requirement**: Predict regime in < 100ms (excluding feature extraction)

### PR-2: Feature Extraction Latency

**Requirement**: Extract all features in < 5 seconds at 9:15 AM

---

## Implementation Checklist

- [ ] Create `intelligence/regime_detector.py`
- [ ] Create `intelligence/regime_labeler.py`
- [ ] Label 500+ historical days
- [ ] Train initial model (>55% accuracy)
- [ ] Write 10 unit tests
- [ ] Implement weekly retraining
- [ ] Integrate with strategy selector
- [ ] Validate on out-of-sample data
- [ ] Document feature importance
- [ ] Performance test (<100ms prediction)

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: FX-008 (Sentiment Analyzer)

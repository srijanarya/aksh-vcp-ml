"""
Sentiment Feature Extractor - Story 2.3

Extracts sentiment and reaction features from price/volume data around earnings announcements.
Features capture market reaction, investor sentiment, and momentum around earnings events.

Features Extracted (8 total):
1. Pre-announcement momentum (5-day, 10-day)
2. Day 0/1 reaction (announcement day and next day price changes)
3. Volume behavior (spike ratio, pre-announcement trend)
4. Post-announcement volatility (5-day std dev)

Author: VCP Financial Research Team
Date: 2025-11-13
Story: 2.3
Epic: 2 (Feature Engineering)
"""

import sqlite3
import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SentimentFeatures:
    """Dataclass representing sentiment features for a single earnings announcement sample"""

    bse_code: str
    date: str  # Earnings announcement date (YYYY-MM-DD)

    # Pre-announcement momentum (2 features)
    pre_momentum_5d: Optional[float] = None  # 5-day price momentum before announcement (%)
    pre_momentum_10d: Optional[float] = None  # 10-day price momentum before announcement (%)

    # Day 1 reaction (3 features)
    day0_reaction: Optional[float] = None  # Announcement day price change (%)
    day1_reaction: Optional[float] = None  # Next trading day price change (%)
    cumulative_reaction_2d: Optional[float] = None  # Day 0 + Day 1 combined (%)

    # Volume behavior (2 features)
    volume_spike_ratio: Optional[float] = None  # Announcement volume / 20-day avg volume
    pre_volume_trend: Optional[float] = None  # 5-day avg volume / 20-day avg volume

    # Post-announcement volatility (1 feature)
    post_volatility_5d: Optional[float] = None  # Std dev of 5-day returns after announcement

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SentimentFeatureExtractor:
    """
    Extracts sentiment features from price/volume data around earnings announcements.

    Requires:
    - historical_prices.db (from Story 1.3)
    - upper_circuit_labels.db (from Story 1.2)

    Produces:
    - sentiment_features.db with 8 features per sample
    """

    def __init__(
        self,
        price_db_path: str,
        labels_db_path: str,
        output_db_path: str
    ):
        """
        Initialize SentimentFeatureExtractor

        Args:
            price_db_path: Path to historical_prices.db (Story 1.3)
            labels_db_path: Path to upper_circuit_labels.db (Story 1.2)
            output_db_path: Path to output sentiment_features.db
        """
        self.price_db_path = price_db_path
        self.labels_db_path = labels_db_path
        self.output_db_path = output_db_path

        # Create output database and schema
        self._create_database_schema()

        logger.info(f"SentimentFeatureExtractor initialized")
        logger.info(f"Price DB: {price_db_path}")
        logger.info(f"Output DB: {output_db_path}")

    def _create_database_schema(self):
        """Create sentiment_features table with proper schema and indexes"""
        conn = sqlite3.connect(self.output_db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_features (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                date DATE NOT NULL,

                -- Pre-announcement momentum
                pre_momentum_5d REAL,
                pre_momentum_10d REAL,

                -- Day 1 reaction
                day0_reaction REAL,
                day1_reaction REAL,
                cumulative_reaction_2d REAL,

                -- Volume behavior
                volume_spike_ratio REAL,
                pre_volume_trend REAL,

                -- Post-announcement volatility
                post_volatility_5d REAL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, date) ON CONFLICT REPLACE
            )
        """)

        # Create indexes for fast lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentiment_sample_id
            ON sentiment_features(feature_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sentiment_bse_date
            ON sentiment_features(bse_code, date)
        """)

        conn.commit()
        conn.close()

        logger.info("Database schema created successfully")

    def _load_price_data(
        self,
        bse_code: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Load price data for a given date range

        Args:
            bse_code: BSE company code
            start_date: Start date for price data
            end_date: End date for price data

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        conn = sqlite3.connect(self.price_db_path)

        query = """
            SELECT date, open, high, low, close, volume
            FROM historical_prices
            WHERE bse_code = ?
              AND date >= ?
              AND date <= ?
            ORDER BY date ASC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(bse_code, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )

        conn.close()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def calculate_pre_momentum(
        self,
        prices: pd.DataFrame,
        announcement_date: datetime
    ) -> Dict[str, Optional[float]]:
        """
        Calculate pre-announcement momentum features

        Args:
            prices: DataFrame with price data
            announcement_date: Earnings announcement date

        Returns:
            Dict with 'momentum_5d' and 'momentum_10d' keys
        """
        result = {
            'momentum_5d': None,
            'momentum_10d': None
        }

        if prices.empty:
            return result

        # Filter to only pre-announcement data
        pre_prices = prices[prices['date'] < announcement_date].copy()

        if pre_prices.empty:
            return result

        pre_prices = pre_prices.sort_values('date', ascending=False).reset_index(drop=True)
        closes = pre_prices['close'].values

        # Calculate 5-day momentum (Day -5 vs Day -1)
        # Need 6 prices: Day -1, Day -2, Day -3, Day -4, Day -5 relative to announcement
        if len(closes) >= 6:
            day_1_close = closes[0]  # Most recent (Day -1)
            day_5_close = closes[5]  # 6th most recent (Day -5)

            if day_5_close > 0:
                result['momentum_5d'] = ((day_1_close - day_5_close) / day_5_close) * 100

        # Calculate 10-day momentum (Day -10 vs Day -1)
        # Need 11 prices: Day -1, Day -2, ..., Day -10
        if len(closes) >= 11:
            day_1_close = closes[0]
            day_10_close = closes[10]  # 11th most recent (Day -10)

            if day_10_close > 0:
                result['momentum_10d'] = ((day_1_close - day_10_close) / day_10_close) * 100

        return result

    def calculate_day_reaction(
        self,
        prices: pd.DataFrame,
        announcement_date: datetime
    ) -> Dict[str, Optional[float]]:
        """
        Calculate day 0 and day 1 reaction features

        Args:
            prices: DataFrame with price data
            announcement_date: Earnings announcement date

        Returns:
            Dict with 'day0_reaction', 'day1_reaction', 'cumulative_2d' keys
        """
        result = {
            'day0_reaction': None,
            'day1_reaction': None,
            'cumulative_2d': None
        }

        if prices.empty:
            return result

        # Get Day 0 data (announcement day)
        day0 = prices[prices['date'] == announcement_date]

        if day0.empty:
            logger.warning(f"No price data on announcement date {announcement_date}")
            return result

        day0 = day0.iloc[0]

        # Calculate Day 0 reaction (open to close)
        if day0['open'] > 0:
            result['day0_reaction'] = ((day0['close'] - day0['open']) / day0['open']) * 100

        # Get Day 1 data (next trading day)
        post_prices = prices[prices['date'] > announcement_date].sort_values('date')

        if len(post_prices) >= 1:
            day1 = post_prices.iloc[0]

            # Calculate Day 1 reaction (Day 0 close to Day 1 close)
            if day0['close'] > 0:
                result['day1_reaction'] = ((day1['close'] - day0['close']) / day0['close']) * 100

            # Calculate cumulative 2-day reaction (Day 0 open to Day 1 close)
            if day0['open'] > 0:
                result['cumulative_2d'] = ((day1['close'] - day0['open']) / day0['open']) * 100

        return result

    def calculate_volume_features(
        self,
        prices: pd.DataFrame,
        announcement_date: datetime
    ) -> Dict[str, Optional[float]]:
        """
        Calculate volume behavior features

        Args:
            prices: DataFrame with price data
            announcement_date: Earnings announcement date

        Returns:
            Dict with 'volume_spike_ratio' and 'pre_volume_trend' keys
        """
        result = {
            'volume_spike_ratio': None,
            'pre_volume_trend': None
        }

        if prices.empty or 'volume' not in prices.columns:
            return result

        # Get announcement day volume
        day0 = prices[prices['date'] == announcement_date]

        if day0.empty:
            return result

        announcement_volume = day0.iloc[0]['volume']

        # Get pre-announcement data
        pre_prices = prices[prices['date'] < announcement_date].copy()

        if pre_prices.empty:
            return result

        pre_prices = pre_prices.sort_values('date', ascending=False).reset_index(drop=True)
        volumes = pre_prices['volume'].values

        # Calculate 20-day average volume
        if len(volumes) >= 20:
            avg_20d_volume = np.mean(volumes[:20])

            if avg_20d_volume > 0:
                result['volume_spike_ratio'] = announcement_volume / avg_20d_volume

        # Calculate pre-announcement volume trend (5-day avg vs 20-day avg)
        # Use days 1-5 (most recent) vs days 6-20 for clearer trend
        if len(volumes) >= 20:
            avg_5d_volume = np.mean(volumes[0:5])  # Days -1 to -5
            avg_20d_volume = np.mean(volumes[5:20])  # Days -6 to -20 (for comparison)

            if avg_20d_volume > 0:
                result['pre_volume_trend'] = avg_5d_volume / avg_20d_volume

        return result

    def calculate_post_volatility(
        self,
        prices: pd.DataFrame,
        announcement_date: datetime
    ) -> Dict[str, Optional[float]]:
        """
        Calculate post-announcement volatility

        Args:
            prices: DataFrame with price data
            announcement_date: Earnings announcement date

        Returns:
            Dict with 'post_volatility_5d' key
        """
        result = {
            'post_volatility_5d': None
        }

        if prices.empty:
            return result

        # Get post-announcement data (Days +1 to +5)
        # Include Day 0 as base for Day 1 return calculation
        post_prices = prices[prices['date'] >= announcement_date].copy()

        if post_prices.empty:
            return result

        post_prices = post_prices.sort_values('date').reset_index(drop=True)

        # Need at least 6 prices (Day 0 + Days 1-5) for 5 daily returns
        if len(post_prices) < 6:
            return result

        # Calculate daily returns for days +1 to +5
        closes = post_prices['close'].values[:6]
        returns = []

        for i in range(1, 6):
            if closes[i-1] > 0:
                daily_return = ((closes[i] - closes[i-1]) / closes[i-1]) * 100
                returns.append(daily_return)

        if len(returns) >= 5:
            result['post_volatility_5d'] = float(np.std(returns))

        return result

    def extract_features_for_sample(
        self,
        bse_code: str,
        date: str
    ) -> SentimentFeatures:
        """
        Extract all sentiment features for a single sample

        Args:
            bse_code: BSE company code
            date: Earnings announcement date (YYYY-MM-DD)

        Returns:
            SentimentFeatures object with all features
        """
        announcement_date = datetime.strptime(date, '%Y-%m-%d')

        # Load price data (30 days before to 10 days after)
        start_date = announcement_date - timedelta(days=30)
        end_date = announcement_date + timedelta(days=10)

        prices = self._load_price_data(bse_code, start_date, end_date)

        if prices.empty:
            logger.warning(f"No price data for {bse_code} around {date}")
            return SentimentFeatures(bse_code=bse_code, date=date)

        # Calculate all feature groups
        momentum = self.calculate_pre_momentum(prices, announcement_date)
        reaction = self.calculate_day_reaction(prices, announcement_date)
        volume = self.calculate_volume_features(prices, announcement_date)
        volatility = self.calculate_post_volatility(prices, announcement_date)

        # Combine into SentimentFeatures object
        features = SentimentFeatures(
            bse_code=bse_code,
            date=date,
            pre_momentum_5d=momentum.get('momentum_5d'),
            pre_momentum_10d=momentum.get('momentum_10d'),
            day0_reaction=reaction.get('day0_reaction'),
            day1_reaction=reaction.get('day1_reaction'),
            cumulative_reaction_2d=reaction.get('cumulative_2d'),
            volume_spike_ratio=volume.get('volume_spike_ratio'),
            pre_volume_trend=volume.get('pre_volume_trend'),
            post_volatility_5d=volatility.get('post_volatility_5d')
        )

        return features

    def extract_features_batch(
        self,
        samples: List[Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Extract sentiment features for multiple samples in batch

        Args:
            samples: List of dicts with 'bse_code' and 'date' keys

        Returns:
            DataFrame with all features
        """
        logger.info(f"Starting batch extraction for {len(samples)} samples")

        features_list = []

        for i, sample in enumerate(samples):
            if i % 100 == 0 and i > 0:
                logger.info(f"Processed {i}/{len(samples)} samples")

            features = self.extract_features_for_sample(
                bse_code=sample['bse_code'],
                date=sample['date']
            )

            features_list.append(asdict(features))

        df = pd.DataFrame(features_list)

        # Store in database
        self._store_features(df)

        logger.info(f"Batch extraction complete: {len(df)} samples")

        return df

    def _store_features(self, df: pd.DataFrame):
        """
        Store features in sentiment_features.db

        Args:
            df: DataFrame with sentiment features
        """
        conn = sqlite3.connect(self.output_db_path)

        # Store using INSERT OR REPLACE for idempotency
        for _, row in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO sentiment_features (
                    bse_code, date,
                    pre_momentum_5d, pre_momentum_10d,
                    day0_reaction, day1_reaction, cumulative_reaction_2d,
                    volume_spike_ratio, pre_volume_trend,
                    post_volatility_5d
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['bse_code'], row['date'],
                row.get('pre_momentum_5d'), row.get('pre_momentum_10d'),
                row.get('day0_reaction'), row.get('day1_reaction'), row.get('cumulative_reaction_2d'),
                row.get('volume_spike_ratio'), row.get('pre_volume_trend'),
                row.get('post_volatility_5d')
            ))

        conn.commit()
        conn.close()

        logger.info(f"Stored {len(df)} feature records in database")


if __name__ == "__main__":
    # Example usage
    extractor = SentimentFeatureExtractor(
        price_db_path="data/historical_prices.db",
        labels_db_path="data/upper_circuit_labels.db",
        output_db_path="data/sentiment_features.db"
    )

    # Extract features for a single sample
    features = extractor.extract_features_for_sample(
        bse_code="500325",
        date="2024-01-10"
    )

    print(f"Sentiment Features for {features.bse_code} on {features.date}:")
    print(f"Pre-momentum (5d): {features.pre_momentum_5d:.2f}%" if features.pre_momentum_5d else "N/A")
    print(f"Day 0 reaction: {features.day0_reaction:.2f}%" if features.day0_reaction else "N/A")
    print(f"Volume spike ratio: {features.volume_spike_ratio:.2f}x" if features.volume_spike_ratio else "N/A")

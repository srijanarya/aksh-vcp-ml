"""
Seasonality Feature Extractor - Story 2.4

Extracts seasonality features to capture quarterly patterns, fiscal year effects,
and historical upper circuit rates by quarter.

Features Extracted (6 total):
1. Quarter indicators (Q1-Q4 one-hot encoding) - 4 features
2. Month indicator (1-12) - 1 feature
3. Historical circuit rate by quarter - 1 feature

Author: VCP Financial Research Team
Date: 2025-11-13
Story: 2.4
Epic: 2 (Feature Engineering)
"""

import sqlite3
import pandas as pd
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SeasonalityFeatures:
    """Dataclass representing seasonality features for a single earnings announcement sample"""

    bse_code: str
    date: str  # Earnings announcement date (YYYY-MM-DD)

    # Quarter indicators (4 one-hot features)
    is_q1: int = 0  # 1 if Q1 (Apr-Jun), 0 otherwise
    is_q2: int = 0  # 1 if Q2 (Jul-Sep), 0 otherwise
    is_q3: int = 0  # 1 if Q3 (Oct-Dec), 0 otherwise
    is_q4: int = 0  # 1 if Q4 (Jan-Mar), 0 otherwise

    # Month indicator (1 feature)
    announcement_month: int = 0  # 1-12

    # Historical circuit rate (1 feature)
    historical_circuit_rate_quarter: Optional[float] = None  # % of upper circuits in this quarter historically

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class SeasonalityFeatureExtractor:
    """
    Extracts seasonality features from announcement dates and historical upper circuit labels.

    Requires:
    - upper_circuit_labels.db (from Story 1.2)

    Produces:
    - seasonality_features.db with 6 features per sample
    """

    # Indian fiscal year quarter mapping
    MONTH_TO_QUARTER = {
        1: 'Q4', 2: 'Q4', 3: 'Q4',  # Jan-Mar
        4: 'Q1', 5: 'Q1', 6: 'Q1',  # Apr-Jun
        7: 'Q2', 8: 'Q2', 9: 'Q2',  # Jul-Sep
        10: 'Q3', 11: 'Q3', 12: 'Q3'  # Oct-Dec
    }

    QUARTER_TO_MONTHS = {
        'Q1': [4, 5, 6],
        'Q2': [7, 8, 9],
        'Q3': [10, 11, 12],
        'Q4': [1, 2, 3]
    }

    def __init__(
        self,
        labels_db_path: str,
        output_db_path: str
    ):
        """
        Initialize SeasonalityFeatureExtractor

        Args:
            labels_db_path: Path to upper_circuit_labels.db (Story 1.2)
            output_db_path: Path to output seasonality_features.db
        """
        self.labels_db_path = labels_db_path
        self.output_db_path = output_db_path

        # Cache for historical circuit rates (key: (bse_code, quarter, end_date))
        self._circuit_rate_cache = {}

        # Create output database and schema
        self._create_database_schema()

        logger.info(f"SeasonalityFeatureExtractor initialized")
        logger.info(f"Labels DB: {labels_db_path}")
        logger.info(f"Output DB: {output_db_path}")

    def _create_database_schema(self):
        """Create seasonality_features table with proper schema and indexes"""
        conn = sqlite3.connect(self.output_db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS seasonality_features (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                date DATE NOT NULL,

                -- Quarter indicators (one-hot)
                is_q1 INTEGER,
                is_q2 INTEGER,
                is_q3 INTEGER,
                is_q4 INTEGER,

                -- Month indicator
                announcement_month INTEGER,

                -- Historical circuit rate
                historical_circuit_rate_quarter REAL,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, date) ON CONFLICT REPLACE
            )
        """)

        # Create indexes for fast lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_seasonality_sample_id
            ON seasonality_features(feature_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_seasonality_bse_date
            ON seasonality_features(bse_code, date)
        """)

        conn.commit()
        conn.close()

        logger.info("Database schema created successfully")

    def get_quarter_from_date(self, date_str: str) -> str:
        """
        Get quarter (Q1-Q4) from date string

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Quarter string ('Q1', 'Q2', 'Q3', or 'Q4')
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month = date_obj.month
        return self.MONTH_TO_QUARTER[month]

    def get_month_from_date(self, date_str: str) -> int:
        """
        Get month (1-12) from date string

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Month as integer (1-12)
        """
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.month

    def get_quarter_one_hot(self, date_str: str) -> Dict[str, int]:
        """
        Get one-hot encoded quarter features

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Dict with is_q1, is_q2, is_q3, is_q4 keys (1 or 0)
        """
        quarter = self.get_quarter_from_date(date_str)

        result = {
            'is_q1': 0,
            'is_q2': 0,
            'is_q3': 0,
            'is_q4': 0
        }

        if quarter == 'Q1':
            result['is_q1'] = 1
        elif quarter == 'Q2':
            result['is_q2'] = 1
        elif quarter == 'Q3':
            result['is_q3'] = 1
        elif quarter == 'Q4':
            result['is_q4'] = 1

        return result

    def calculate_historical_circuit_rate(
        self,
        bse_code: str,
        date: str
    ) -> float:
        """
        Calculate historical upper circuit rate for same quarter over last 3 years

        Args:
            bse_code: BSE company code
            date: Current announcement date (YYYY-MM-DD)

        Returns:
            Historical circuit rate (0.0 to 1.0), or 0.0 if no historical data
        """
        # Get current quarter
        quarter = self.get_quarter_from_date(date)
        current_date = datetime.strptime(date, '%Y-%m-%d')

        # Check cache
        cache_key = (bse_code, quarter, date)
        if cache_key in self._circuit_rate_cache:
            return self._circuit_rate_cache[cache_key]

        # Get months for this quarter
        quarter_months = self.QUARTER_TO_MONTHS[quarter]

        # Load historical data for this company and quarter (last 3 years)
        start_date = current_date - timedelta(days=3*365)

        conn = sqlite3.connect(self.labels_db_path)

        query = """
            SELECT earnings_date as date, label as upper_circuit
            FROM upper_circuit_labels
            WHERE bse_code = ?
              AND earnings_date >= ?
              AND earnings_date < ?
            ORDER BY earnings_date ASC
        """

        df = pd.read_sql_query(
            query,
            conn,
            params=(bse_code, start_date.strftime('%Y-%m-%d'), date)
        )

        conn.close()

        if df.empty:
            logger.warning(f"No historical data for {bse_code}")
            self._circuit_rate_cache[cache_key] = 0.0
            return 0.0

        # Filter to same quarter
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month

        quarter_df = df[df['month'].isin(quarter_months)]

        if quarter_df.empty:
            logger.warning(f"No historical data for {bse_code} in {quarter}")
            self._circuit_rate_cache[cache_key] = 0.0
            return 0.0

        # Calculate circuit rate
        total_announcements = len(quarter_df)
        upper_circuits = quarter_df['upper_circuit'].sum()

        if total_announcements < 3:
            logger.warning(f"Sparse historical data for {bse_code} in {quarter}: {total_announcements} announcements")

        rate = upper_circuits / total_announcements if total_announcements > 0 else 0.0

        # Cache result
        self._circuit_rate_cache[cache_key] = float(rate)

        return float(rate)

    def extract_features_for_sample(
        self,
        bse_code: str,
        date: str
    ) -> SeasonalityFeatures:
        """
        Extract all seasonality features for a single sample

        Args:
            bse_code: BSE company code
            date: Earnings announcement date (YYYY-MM-DD)

        Returns:
            SeasonalityFeatures object with all features
        """
        # Get quarter one-hot encoding
        quarter_one_hot = self.get_quarter_one_hot(date)

        # Get month
        month = self.get_month_from_date(date)

        # Calculate historical circuit rate
        historical_rate = self.calculate_historical_circuit_rate(bse_code, date)

        # Combine into SeasonalityFeatures object
        features = SeasonalityFeatures(
            bse_code=bse_code,
            date=date,
            is_q1=quarter_one_hot['is_q1'],
            is_q2=quarter_one_hot['is_q2'],
            is_q3=quarter_one_hot['is_q3'],
            is_q4=quarter_one_hot['is_q4'],
            announcement_month=month,
            historical_circuit_rate_quarter=historical_rate
        )

        return features

    def extract_features_batch(
        self,
        samples: List[Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Extract seasonality features for multiple samples in batch

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
        Store features in seasonality_features.db

        Args:
            df: DataFrame with seasonality features
        """
        conn = sqlite3.connect(self.output_db_path)

        # Store using INSERT OR REPLACE for idempotency
        for _, row in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO seasonality_features (
                    bse_code, date,
                    is_q1, is_q2, is_q3, is_q4,
                    announcement_month,
                    historical_circuit_rate_quarter
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['bse_code'], row['date'],
                row['is_q1'], row['is_q2'], row['is_q3'], row['is_q4'],
                row['announcement_month'],
                row.get('historical_circuit_rate_quarter')
            ))

        conn.commit()
        conn.close()

        logger.info(f"Stored {len(df)} feature records in database")


if __name__ == "__main__":
    # Example usage
    extractor = SeasonalityFeatureExtractor(
        labels_db_path="data/upper_circuit_labels.db",
        output_db_path="data/seasonality_features.db"
    )

    # Extract features for a single sample
    features = extractor.extract_features_for_sample(
        bse_code="500325",
        date="2024-04-15"
    )

    print(f"Seasonality Features for {features.bse_code} on {features.date}:")
    print(f"Quarter: Q1={features.is_q1}, Q2={features.is_q2}, Q3={features.is_q3}, Q4={features.is_q4}")
    print(f"Month: {features.announcement_month}")
    print(f"Historical circuit rate: {features.historical_circuit_rate_quarter:.2%}" if features.historical_circuit_rate_quarter else "N/A")

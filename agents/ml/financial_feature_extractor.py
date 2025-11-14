"""
Story 2.2: Financial Feature Extractor

Extracts financial features (revenue growth, profit growth, margins, EPS, earnings quality)
from quarterly financial data. Target: 15 financial features per sample for 200K+ samples.

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FinancialFeatures:
    """Container for 15 financial features (AC2.2.1)"""
    bse_code: str
    date: str  # Earnings announcement date

    # Revenue growth features (3)
    revenue_growth_qoq: Optional[float] = None  # Quarter-over-quarter (%)
    revenue_growth_yoy: Optional[float] = None  # Year-over-year (%)
    revenue_growth_avg_4q: Optional[float] = None  # 4-quarter moving average

    # Profit growth features (3)
    pat_growth_qoq: Optional[float] = None
    pat_growth_yoy: Optional[float] = None
    pat_growth_avg_4q: Optional[float] = None

    # Margin features (4)
    operating_margin: Optional[float] = None  # Current quarter OPM (%)
    net_profit_margin: Optional[float] = None  # Current quarter NPM (%)
    margin_expansion_qoq: Optional[float] = None  # NPM delta vs prev quarter
    avg_margin_4q: Optional[float] = None  # 4-quarter average NPM

    # EPS features (3)
    eps_growth_qoq: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    eps_consistency: Optional[float] = None  # Std dev over 4 quarters

    # Earnings quality features (2)
    consecutive_growth_quarters: Optional[int] = None  # Growth streak
    earnings_surprise: Optional[int] = None  # Binary: 1 if >20% growth QoQ

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class FinancialFeatureExtractor:
    """
    Extracts financial features from quarterly financial data.

    Supports:
    - Revenue growth (QoQ, YoY, 4Q average)
    - Profit growth (PAT QoQ, YoY, 4Q average)
    - Margins (OPM, NPM, expansion, 4Q average)
    - EPS features (QoQ, YoY, consistency)
    - Earnings quality (growth streaks, surprises)

    Performance: Processes 200K+ samples in <35 minutes using efficient SQL queries.
    """

    # Quarter ordering for proper sorting
    QUARTER_ORDER = {'Q1': 1, 'Q2': 2, 'Q3': 3, 'Q4': 4}

    def __init__(self, financials_db_path: str, output_db_path: str):
        """
        Initialize extractor with database paths (AC2.2.1)

        Args:
            financials_db_path: Path to historical_financials.db (input)
            output_db_path: Path to financial_features.db (output)
        """
        self.financials_db_path = financials_db_path
        self.output_db_path = output_db_path
        self._initialize_database()
        logger.info(f"FinancialFeatureExtractor initialized: financials_db={financials_db_path}, output_db={output_db_path}")

    def _initialize_database(self):
        """AC2.2.1: Create financial_features table with indexes"""
        conn = sqlite3.connect(self.output_db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_features (
                feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                date DATE NOT NULL,

                -- Revenue growth features
                revenue_growth_qoq REAL,
                revenue_growth_yoy REAL,
                revenue_growth_avg_4q REAL,

                -- Profit growth features
                pat_growth_qoq REAL,
                pat_growth_yoy REAL,
                pat_growth_avg_4q REAL,

                -- Margin features
                operating_margin REAL,
                net_profit_margin REAL,
                margin_expansion_qoq REAL,
                avg_margin_4q REAL,

                -- EPS features
                eps_growth_qoq REAL,
                eps_growth_yoy REAL,
                eps_consistency REAL,

                -- Earnings quality features
                consecutive_growth_quarters INTEGER,
                earnings_surprise INTEGER,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, date) ON CONFLICT REPLACE
            )
        """)

        # Create indexes for query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_sample_id ON financial_features(feature_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_bse_date ON financial_features(bse_code, date)")

        conn.commit()
        conn.close()
        logger.info("Database schema initialized with indexes")

    def _sort_financials(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort financials by year and quarter (most recent first)

        Args:
            df: DataFrame with 'quarter' and 'year' columns

        Returns:
            Sorted DataFrame (Q4 2024, Q3 2024, Q2 2024, ...)
        """
        if df.empty:
            return df

        # Add quarter order for sorting
        df['quarter_order'] = df['quarter'].map(self.QUARTER_ORDER)

        # Sort by year DESC, then quarter_order DESC
        df = df.sort_values(['year', 'quarter_order'], ascending=[False, False])

        # Drop temporary column
        df = df.drop('quarter_order', axis=1)

        return df.reset_index(drop=True)

    def calculate_revenue_growth(self, financials: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate revenue growth features (AC2.2.2)

        Args:
            financials: DataFrame with columns ['quarter', 'year', 'revenue']
                       Sorted most recent first (Q0, Q-1, Q-2, ...)

        Returns:
            Dict with keys 'qoq', 'yoy', 'avg_4q'
        """
        result = {'qoq': None, 'yoy': None, 'avg_4q': None}

        if len(financials) < 2:
            return result

        # Sort to ensure proper ordering
        financials = self._sort_financials(financials.copy())

        # Get revenue values
        revenues = financials['revenue'].values

        # Check for negative/zero revenue (invalid)
        if revenues[0] <= 0 or pd.isna(revenues[0]):
            logger.warning(f"Invalid current revenue: {revenues[0]}")
            return result

        # Calculate QoQ growth (Q0 vs Q-1)
        if len(revenues) >= 2 and revenues[1] > 0:
            result['qoq'] = ((revenues[0] - revenues[1]) / revenues[1]) * 100

        # Calculate YoY growth (Q0 vs Q-4)
        if len(revenues) >= 5 and revenues[4] > 0:
            result['yoy'] = ((revenues[0] - revenues[4]) / revenues[4]) * 100

        # Calculate 4Q average growth (need at least 4 quarters for 3 growth calculations)
        if len(revenues) >= 4:
            qoq_growths = []
            for i in range(min(4, len(revenues) - 1)):
                if revenues[i] > 0 and revenues[i + 1] > 0:
                    growth = ((revenues[i] - revenues[i + 1]) / revenues[i + 1]) * 100
                    qoq_growths.append(growth)

            if qoq_growths:
                result['avg_4q'] = np.mean(qoq_growths)

        return result

    def calculate_profit_growth(self, financials: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate profit growth features (AC2.2.3)

        Args:
            financials: DataFrame with columns ['quarter', 'year', 'pat']
                       Sorted most recent first

        Returns:
            Dict with keys 'qoq', 'yoy', 'avg_4q'

        Note:
            Handles loss-to-profit turnarounds and profit-to-loss scenarios.
        """
        result = {'qoq': None, 'yoy': None, 'avg_4q': None}

        if len(financials) < 2:
            return result

        # Sort to ensure proper ordering
        financials = self._sort_financials(financials.copy())

        # Get PAT values
        pats = financials['pat'].values

        # Check for invalid current PAT
        if pd.isna(pats[0]):
            return result

        # Calculate QoQ growth with special handling for losses
        if len(pats) >= 2 and not pd.isna(pats[1]):
            if pats[1] == 0:
                result['qoq'] = None  # Undefined
            elif pats[1] < 0:
                # Loss to profit/loss: calculate as turnaround
                result['qoq'] = ((pats[0] - pats[1]) / abs(pats[1])) * 100
            else:
                # Normal growth calculation
                result['qoq'] = ((pats[0] - pats[1]) / pats[1]) * 100

        # Calculate YoY growth
        if len(pats) >= 5 and not pd.isna(pats[4]):
            if pats[4] == 0:
                result['yoy'] = None
            elif pats[4] < 0:
                result['yoy'] = ((pats[0] - pats[4]) / abs(pats[4])) * 100
            else:
                result['yoy'] = ((pats[0] - pats[4]) / pats[4]) * 100

        # Calculate 4Q average growth
        if len(pats) >= 5:
            qoq_growths = []
            for i in range(4):
                if not pd.isna(pats[i]) and not pd.isna(pats[i + 1]):
                    if pats[i + 1] == 0:
                        continue
                    elif pats[i + 1] < 0:
                        growth = ((pats[i] - pats[i + 1]) / abs(pats[i + 1])) * 100
                    else:
                        growth = ((pats[i] - pats[i + 1]) / pats[i + 1]) * 100
                    qoq_growths.append(growth)

            if qoq_growths:
                result['avg_4q'] = np.mean(qoq_growths)

        return result

    def calculate_margins(self, financials: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate margin features (AC2.2.4)

        Args:
            financials: DataFrame with columns ['quarter', 'year', 'revenue', 'pat', 'operating_profit']

        Returns:
            Dict with keys 'operating_margin', 'net_profit_margin', 'expansion_qoq', 'avg_4q'
        """
        result = {
            'operating_margin': None,
            'net_profit_margin': None,
            'expansion_qoq': None,
            'avg_4q': None
        }

        if len(financials) < 1:
            return result

        # Sort to ensure proper ordering
        financials = self._sort_financials(financials.copy())

        # Get current quarter data
        current = financials.iloc[0]

        # Calculate current quarter margins
        if current['revenue'] > 0:
            if 'operating_profit' in financials.columns and not pd.isna(current.get('operating_profit')):
                result['operating_margin'] = (current['operating_profit'] / current['revenue']) * 100

            if 'pat' in financials.columns and not pd.isna(current.get('pat')):
                result['net_profit_margin'] = (current['pat'] / current['revenue']) * 100

        # Calculate margin expansion QoQ
        if len(financials) >= 2 and 'pat' in financials.columns:
            prev = financials.iloc[1]
            if current['revenue'] > 0 and prev['revenue'] > 0:
                current_npm = (current['pat'] / current['revenue']) * 100 if not pd.isna(current.get('pat')) else None
                prev_npm = (prev['pat'] / prev['revenue']) * 100 if not pd.isna(prev.get('pat')) else None

                if current_npm is not None and prev_npm is not None:
                    result['expansion_qoq'] = current_npm - prev_npm

        # Calculate 4Q average NPM
        if len(financials) >= 4 and 'pat' in financials.columns:
            margins = []
            for i in range(4):
                row = financials.iloc[i]
                if row['revenue'] > 0 and not pd.isna(row.get('pat')):
                    npm = (row['pat'] / row['revenue']) * 100
                    margins.append(npm)

            if margins:
                result['avg_4q'] = np.mean(margins)

        return result

    def calculate_eps_features(self, financials: pd.DataFrame) -> Dict[str, Optional[float]]:
        """
        Calculate EPS features (AC2.2.5)

        Args:
            financials: DataFrame with columns ['quarter', 'year', 'eps']

        Returns:
            Dict with keys 'qoq_growth', 'yoy_growth', 'consistency'
        """
        result = {'qoq_growth': None, 'yoy_growth': None, 'consistency': None}

        if len(financials) < 2:
            return result

        # Sort to ensure proper ordering
        financials = self._sort_financials(financials.copy())

        # Get EPS values
        eps_values = financials['eps'].values

        # Check for invalid current EPS
        if pd.isna(eps_values[0]) or eps_values[0] <= 0:
            return result

        # Calculate QoQ growth
        if len(eps_values) >= 2 and eps_values[1] > 0 and not pd.isna(eps_values[1]):
            result['qoq_growth'] = ((eps_values[0] - eps_values[1]) / eps_values[1]) * 100

        # Calculate YoY growth
        if len(eps_values) >= 5 and eps_values[4] > 0 and not pd.isna(eps_values[4]):
            result['yoy_growth'] = ((eps_values[0] - eps_values[4]) / eps_values[4]) * 100

        # Calculate consistency (std dev over 4 quarters)
        if len(eps_values) >= 4:
            recent_eps = eps_values[:4]
            # Filter out NaN values
            recent_eps = recent_eps[~pd.isna(recent_eps)]
            if len(recent_eps) >= 4:
                result['consistency'] = float(np.std(recent_eps))

        return result

    def calculate_earnings_quality(self, financials: pd.DataFrame) -> Dict[str, Optional[int]]:
        """
        Calculate earnings quality features (AC2.2.6)

        Args:
            financials: DataFrame with columns ['quarter', 'year', 'revenue', 'pat']

        Returns:
            Dict with keys 'consecutive_growth_quarters', 'earnings_surprise'
        """
        result = {'consecutive_growth_quarters': None, 'earnings_surprise': None}

        if len(financials) < 2:
            return result

        # Sort to ensure proper ordering
        financials = self._sort_financials(financials.copy())

        # Calculate consecutive growth quarters
        consecutive = 0
        for i in range(len(financials) - 1):
            current = financials.iloc[i]
            prev = financials.iloc[i + 1]

            # Check if both revenue and PAT are growing
            revenue_growing = False
            pat_growing = False

            if current['revenue'] > 0 and prev['revenue'] > 0:
                revenue_growing = current['revenue'] > prev['revenue']

            if not pd.isna(current['pat']) and not pd.isna(prev['pat']):
                if prev['pat'] < 0:
                    # Turnaround counts as growth
                    pat_growing = current['pat'] > prev['pat']
                elif prev['pat'] > 0:
                    pat_growing = current['pat'] > prev['pat']

            if revenue_growing and pat_growing:
                consecutive += 1
            else:
                break  # Streak broken

        result['consecutive_growth_quarters'] = consecutive

        # Calculate earnings surprise (>20% QoQ growth)
        if len(financials) >= 2:
            current = financials.iloc[0]
            prev = financials.iloc[1]

            surprise = False

            # Check revenue surprise
            if current['revenue'] > 0 and prev['revenue'] > 0:
                revenue_growth = ((current['revenue'] - prev['revenue']) / prev['revenue']) * 100
                if revenue_growth > 20.0:
                    surprise = True

            # Check PAT surprise
            if not pd.isna(current['pat']) and not pd.isna(prev['pat']):
                if prev['pat'] > 0:
                    pat_growth = ((current['pat'] - prev['pat']) / prev['pat']) * 100
                    if pat_growth > 20.0:
                        surprise = True
                elif prev['pat'] < 0 and current['pat'] > 0:
                    # Turnaround from loss to profit is always a surprise
                    surprise = True

            result['earnings_surprise'] = 1 if surprise else 0

        return result

    def _load_financial_data(self, bse_code: str) -> Optional[pd.DataFrame]:
        """
        Load historical financial data for a company (AC2.2.7)

        Args:
            bse_code: BSE company code

        Returns:
            DataFrame with columns ['quarter', 'year', 'revenue', 'pat', 'operating_profit', 'eps']
            or None if no data found
        """
        conn = sqlite3.connect(self.financials_db_path)

        query = """
            SELECT quarter, year, revenue, pat, operating_profit, eps
            FROM historical_financials
            WHERE bse_code = ?
            ORDER BY year DESC, quarter DESC
            LIMIT 12
        """

        try:
            df = pd.read_sql_query(query, conn, params=(bse_code,))
            conn.close()

            if df.empty:
                logger.warning(f"No financial data found for {bse_code}")
                return None

            return df

        except Exception as e:
            logger.error(f"Error loading financial data for {bse_code}: {e}")
            conn.close()
            return None

    def extract_features_for_sample(self, bse_code: str, date: str) -> FinancialFeatures:
        """
        Extract all financial features for a single sample (AC2.2.7)

        Args:
            bse_code: BSE company code
            date: Earnings announcement date (YYYY-MM-DD)

        Returns:
            FinancialFeatures object with 15 features (or None values if insufficient data)
        """
        # Load financial data
        financials = self._load_financial_data(bse_code)

        if financials is None or len(financials) < 2:
            logger.warning(f"Insufficient financial data for {bse_code} on {date}: returning NaN features")
            return FinancialFeatures(bse_code=bse_code, date=date)

        # Calculate all feature groups
        revenue_growth = self.calculate_revenue_growth(financials)
        profit_growth = self.calculate_profit_growth(financials)
        margins = self.calculate_margins(financials)
        eps_features = self.calculate_eps_features(financials)
        quality = self.calculate_earnings_quality(financials)

        return FinancialFeatures(
            bse_code=bse_code,
            date=date,
            revenue_growth_qoq=revenue_growth['qoq'],
            revenue_growth_yoy=revenue_growth['yoy'],
            revenue_growth_avg_4q=revenue_growth['avg_4q'],
            pat_growth_qoq=profit_growth['qoq'],
            pat_growth_yoy=profit_growth['yoy'],
            pat_growth_avg_4q=profit_growth['avg_4q'],
            operating_margin=margins['operating_margin'],
            net_profit_margin=margins['net_profit_margin'],
            margin_expansion_qoq=margins['expansion_qoq'],
            avg_margin_4q=margins['avg_4q'],
            eps_growth_qoq=eps_features['qoq_growth'],
            eps_growth_yoy=eps_features['yoy_growth'],
            eps_consistency=eps_features['consistency'],
            consecutive_growth_quarters=quality['consecutive_growth_quarters'],
            earnings_surprise=quality['earnings_surprise']
        )

    def extract_features_batch(self, samples: List[Dict]) -> pd.DataFrame:
        """
        Extract features for multiple samples (AC2.2.7)

        Args:
            samples: List of dicts with keys 'sample_id', 'bse_code', 'date'

        Returns:
            DataFrame with all features for each sample

        Performance:
            - Target: 1000 samples in <10 seconds (100 samples/second)
            - Uses efficient single-pass extraction
        """
        logger.info(f"Starting batch financial feature extraction for {len(samples)} samples")

        features_list = []
        for sample in samples:
            bse_code = sample['bse_code']
            date = sample['date']
            sample_id = sample.get('sample_id')

            features = self.extract_features_for_sample(bse_code, date)
            feature_dict = asdict(features)
            if sample_id is not None:
                feature_dict['sample_id'] = sample_id
            features_list.append(feature_dict)

        # Convert to DataFrame
        df = pd.DataFrame(features_list)

        # Bulk insert into database
        conn = sqlite3.connect(self.output_db_path)
        cursor = conn.cursor()

        for features_dict in features_list:
            cursor.execute("""
                INSERT OR REPLACE INTO financial_features (
                    bse_code, date,
                    revenue_growth_qoq, revenue_growth_yoy, revenue_growth_avg_4q,
                    pat_growth_qoq, pat_growth_yoy, pat_growth_avg_4q,
                    operating_margin, net_profit_margin, margin_expansion_qoq, avg_margin_4q,
                    eps_growth_qoq, eps_growth_yoy, eps_consistency,
                    consecutive_growth_quarters, earnings_surprise,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                features_dict['bse_code'], features_dict['date'],
                features_dict['revenue_growth_qoq'], features_dict['revenue_growth_yoy'], features_dict['revenue_growth_avg_4q'],
                features_dict['pat_growth_qoq'], features_dict['pat_growth_yoy'], features_dict['pat_growth_avg_4q'],
                features_dict['operating_margin'], features_dict['net_profit_margin'],
                features_dict['margin_expansion_qoq'], features_dict['avg_margin_4q'],
                features_dict['eps_growth_qoq'], features_dict['eps_growth_yoy'], features_dict['eps_consistency'],
                features_dict['consecutive_growth_quarters'], features_dict['earnings_surprise'],
                features_dict['created_at']
            ))

        conn.commit()
        conn.close()

        logger.info(f"Batch financial feature extraction complete: {len(features_list)} samples processed")
        return df

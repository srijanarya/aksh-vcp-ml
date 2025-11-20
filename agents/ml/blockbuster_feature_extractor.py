#!/usr/bin/env python3
"""
ML BLOCKBUSTER FEATURE EXTRACTOR

This agent extracts blockbuster-related features for ML training.
It bridges the gap between blockbuster detection and ML pipeline.

Features extracted:
1. is_blockbuster - Binary flag (0/1)
2. blockbuster_score - Composite score (0-100)
3. revenue_yoy_growth - YoY revenue growth %
4. pat_yoy_growth - YoY PAT growth %
5. revenue_qoq_growth - QoQ revenue growth %
6. pat_qoq_growth - QoQ PAT growth %
7. momentum_score - Acceleration/deceleration indicator
8. consecutive_growth_quarters - Number of consecutive growth quarters
9. percentile_rank - Stock's rank among all stocks (0-100)
10. combined_growth_score - Weighted YoY + QoQ score
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLBlockbusterFeatureExtractor:
    def __init__(self):
        self.data_dir = Path("data")
        self.features_dir = self.data_dir / "features"
        self.features_dir.mkdir(parents=True, exist_ok=True)

        # Input databases
        self.blockbuster_alerts_db = self.data_dir / "blockbuster_alerts.db"
        self.accurate_blockbusters_db = self.data_dir / "accurate_blockbusters.db"
        self.complete_quarterly_db = self.data_dir / "complete_quarterly_analysis.db"

        # Output database
        self.output_db = self.features_dir / "blockbuster_features.db"

        self._init_output_database()

    def _init_output_database(self):
        """Initialize the blockbuster features database"""
        conn = sqlite3.connect(self.output_db)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS blockbuster_features (
                symbol TEXT,
                date DATE,

                -- Core blockbuster indicators
                is_blockbuster INTEGER DEFAULT 0,
                blockbuster_score REAL DEFAULT 0,

                -- YoY Growth metrics
                revenue_yoy_growth REAL,
                pat_yoy_growth REAL,
                eps_yoy_growth REAL,

                -- QoQ Growth metrics
                revenue_qoq_growth REAL,
                pat_qoq_growth REAL,
                eps_qoq_growth REAL,

                -- Momentum indicators
                momentum_score REAL,
                revenue_momentum TEXT,
                pat_momentum TEXT,

                -- Consistency metrics
                consecutive_growth_quarters INTEGER DEFAULT 0,
                quarters_since_last_blockbuster INTEGER,

                -- Relative performance
                percentile_rank REAL,
                sector_relative_score REAL,

                -- Combined scores
                combined_growth_score REAL,
                yoy_score REAL,
                qoq_score REAL,

                -- Trend indicators
                trend_strength TEXT,
                growth_acceleration REAL,

                -- Metadata
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (symbol, date)
            )
        """)

        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_date ON blockbuster_features(symbol, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_is_blockbuster ON blockbuster_features(is_blockbuster)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_blockbuster_score ON blockbuster_features(blockbuster_score DESC)")

        conn.commit()
        conn.close()

    def extract_from_blockbuster_alerts(self) -> pd.DataFrame:
        """Extract features from the original blockbuster_alerts database"""
        if not self.blockbuster_alerts_db.exists():
            logger.warning(f"Blockbuster alerts database not found at {self.blockbuster_alerts_db}")
            return pd.DataFrame()

        conn = sqlite3.connect(self.blockbuster_alerts_db)

        query = """
            SELECT
                COALESCE(nse_symbol, bse_code) as symbol,
                announcement_date as date,
                is_blockbuster,
                blockbuster_score,
                revenue_yoy_growth,
                pat_yoy_growth,
                eps_growth as eps_yoy_growth,
                criteria_met
            FROM blockbuster_alerts
            WHERE symbol IS NOT NULL
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['data_source'] = 'blockbuster_alerts'
            logger.info(f"Extracted {len(df)} records from blockbuster_alerts.db")

        return df

    def extract_from_accurate_blockbusters(self) -> pd.DataFrame:
        """Extract features from the accurate blockbusters database"""
        if not self.accurate_blockbusters_db.exists():
            logger.warning(f"Accurate blockbusters database not found at {self.accurate_blockbusters_db}")
            return pd.DataFrame()

        conn = sqlite3.connect(self.accurate_blockbusters_db)

        query = """
            SELECT
                symbol,
                quarter_date as date,
                revenue_yoy,
                pat_yoy,
                composite_score as blockbuster_score,
                CASE WHEN composite_score > 50 THEN 1 ELSE 0 END as is_blockbuster
            FROM quarterly_results
            WHERE symbol IS NOT NULL
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['data_source'] = 'accurate_blockbusters'
            df.rename(columns={
                'revenue_yoy': 'revenue_yoy_growth',
                'pat_yoy': 'pat_yoy_growth'
            }, inplace=True)
            logger.info(f"Extracted {len(df)} records from accurate_blockbusters.db")

        return df

    def extract_from_complete_quarterly(self) -> pd.DataFrame:
        """Extract features from the complete quarterly analysis database"""
        if not self.complete_quarterly_db.exists():
            logger.warning(f"Complete quarterly database not found at {self.complete_quarterly_db}")
            return pd.DataFrame()

        conn = sqlite3.connect(self.complete_quarterly_db)

        query = """
            SELECT
                symbol,
                quarter_date as date,

                -- YoY metrics
                revenue_yoy as revenue_yoy_growth,
                pat_yoy as pat_yoy_growth,
                eps_yoy as eps_yoy_growth,
                yoy_score,

                -- QoQ metrics
                revenue_qoq as revenue_qoq_growth,
                pat_qoq as pat_qoq_growth,
                eps_qoq as eps_qoq_growth,
                qoq_score,

                -- Combined and momentum
                combined_score,
                revenue_momentum,
                pat_momentum,

                -- Consistency
                quarters_of_growth as consecutive_growth_quarters,
                trend_strength,

                -- Determine blockbuster status
                CASE WHEN combined_score > 100 THEN 1 ELSE 0 END as is_blockbuster,
                combined_score as blockbuster_score

            FROM quarterly_analysis
            WHERE symbol IS NOT NULL
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            df['data_source'] = 'complete_quarterly'
            df['combined_growth_score'] = df['combined_score']
            logger.info(f"Extracted {len(df)} records from complete_quarterly_analysis.db")

        return df

    def calculate_momentum_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate momentum score based on growth acceleration"""
        df = df.sort_values(['symbol', 'date'])

        # Calculate momentum score
        df['momentum_score'] = 0.0

        for symbol in df['symbol'].unique():
            mask = df['symbol'] == symbol
            symbol_df = df[mask].copy()

            if len(symbol_df) > 1:
                # Calculate growth acceleration
                symbol_df['revenue_acceleration'] = symbol_df['revenue_yoy_growth'].diff()
                symbol_df['pat_acceleration'] = symbol_df['pat_yoy_growth'].diff()

                # Momentum score: weighted acceleration
                symbol_df['momentum_score'] = (
                    symbol_df['revenue_acceleration'].fillna(0) * 0.3 +
                    symbol_df['pat_acceleration'].fillna(0) * 0.7
                )

                df.loc[mask, 'momentum_score'] = symbol_df['momentum_score']
                df.loc[mask, 'growth_acceleration'] = symbol_df['pat_acceleration']

        return df

    def calculate_percentile_ranks(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate percentile ranks for each date"""
        df['percentile_rank'] = 0.0

        for date in df['date'].unique():
            mask = df['date'] == date
            date_df = df[mask].copy()

            if len(date_df) > 1:
                # Calculate percentile rank based on blockbuster score
                date_df['percentile_rank'] = date_df['blockbuster_score'].rank(pct=True) * 100
                df.loc[mask, 'percentile_rank'] = date_df['percentile_rank']

        return df

    def calculate_quarters_since_blockbuster(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate quarters since last blockbuster for each symbol"""
        df = df.sort_values(['symbol', 'date'])
        df['quarters_since_last_blockbuster'] = None

        for symbol in df['symbol'].unique():
            mask = df['symbol'] == symbol
            symbol_df = df[mask].copy()

            last_blockbuster_idx = None
            for i, row in symbol_df.iterrows():
                if row['is_blockbuster'] == 1:
                    last_blockbuster_idx = i
                    df.loc[i, 'quarters_since_last_blockbuster'] = 0
                elif last_blockbuster_idx is not None:
                    quarters_diff = (pd.to_datetime(row['date']) -
                                   pd.to_datetime(df.loc[last_blockbuster_idx, 'date'])).days // 90
                    df.loc[i, 'quarters_since_last_blockbuster'] = quarters_diff

        return df

    def merge_and_deduplicate(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge multiple dataframes and handle duplicates"""
        if not dfs:
            return pd.DataFrame()

        # Concatenate all dataframes
        combined = pd.concat(dfs, ignore_index=True)

        if combined.empty:
            return combined

        # Priority order for data sources (higher priority overwrites lower)
        source_priority = {
            'complete_quarterly': 3,
            'accurate_blockbusters': 2,
            'blockbuster_alerts': 1
        }

        combined['priority'] = combined['data_source'].map(source_priority).fillna(0)

        # Sort by priority and keep the highest priority record for each symbol-date
        combined = combined.sort_values(['symbol', 'date', 'priority'], ascending=[True, True, False])
        combined = combined.groupby(['symbol', 'date']).first().reset_index()

        # Drop the priority column
        combined = combined.drop('priority', axis=1)

        return combined

    def extract_all_features(self) -> pd.DataFrame:
        """Extract features from all available sources"""
        logger.info("Starting blockbuster feature extraction...")

        # Extract from different sources
        dfs = []

        # 1. Original blockbuster alerts
        df1 = self.extract_from_blockbuster_alerts()
        if not df1.empty:
            dfs.append(df1)

        # 2. Accurate blockbusters
        df2 = self.extract_from_accurate_blockbusters()
        if not df2.empty:
            dfs.append(df2)

        # 3. Complete quarterly analysis
        df3 = self.extract_from_complete_quarterly()
        if not df3.empty:
            dfs.append(df3)

        if not dfs:
            logger.warning("No data found in any source database")
            return pd.DataFrame()

        # Merge and deduplicate
        df = self.merge_and_deduplicate(dfs)

        # Calculate additional features
        df = self.calculate_momentum_score(df)
        df = self.calculate_percentile_ranks(df)
        df = self.calculate_quarters_since_blockbuster(df)

        # Fill missing values
        df['is_blockbuster'] = df['is_blockbuster'].fillna(0).astype(int)
        df['blockbuster_score'] = df['blockbuster_score'].fillna(0)
        df['consecutive_growth_quarters'] = df['consecutive_growth_quarters'].fillna(0).astype(int)

        # Ensure date format
        df['date'] = pd.to_datetime(df['date'])

        logger.info(f"Extracted total {len(df)} feature records")
        logger.info(f"Blockbusters found: {df['is_blockbuster'].sum()}")
        logger.info(f"Average blockbuster score: {df['blockbuster_score'].mean():.2f}")

        return df

    def save_features(self, df: pd.DataFrame):
        """Save features to the database"""
        if df.empty:
            logger.warning("No features to save")
            return

        conn = sqlite3.connect(self.output_db)

        # Save to database
        df.to_sql('blockbuster_features', conn, if_exists='replace', index=False)

        # Get statistics
        stats = pd.read_sql("""
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                SUM(is_blockbuster) as total_blockbusters,
                AVG(blockbuster_score) as avg_score,
                MAX(blockbuster_score) as max_score
            FROM blockbuster_features
        """, conn)

        conn.close()

        logger.info("="*80)
        logger.info("BLOCKBUSTER FEATURES EXTRACTION COMPLETE")
        logger.info("="*80)
        logger.info(f"Total records: {stats['total_records'].iloc[0]:,}")
        logger.info(f"Unique symbols: {stats['unique_symbols'].iloc[0]:,}")
        logger.info(f"Total blockbusters: {stats['total_blockbusters'].iloc[0]:,}")
        logger.info(f"Average score: {stats['avg_score'].iloc[0]:.2f}")
        logger.info(f"Max score: {stats['max_score'].iloc[0]:.2f}")
        logger.info(f"Output saved to: {self.output_db}")
        logger.info("="*80)

    def run(self):
        """Main execution method"""
        # Extract all features
        df = self.extract_all_features()

        # Save to database
        self.save_features(df)

        return df


def main():
    """Main execution function"""
    extractor = MLBlockbusterFeatureExtractor()
    features_df = extractor.run()

    if not features_df.empty:
        # Show top blockbusters
        top_blockbusters = features_df[features_df['is_blockbuster'] == 1].nlargest(10, 'blockbuster_score')

        if not top_blockbusters.empty:
            print("\nTOP 10 BLOCKBUSTERS BY SCORE:")
            print("="*80)
            for _, row in top_blockbusters.iterrows():
                print(f"{row['symbol']}: Score {row['blockbuster_score']:.1f}, "
                      f"Revenue YoY {row['revenue_yoy_growth']:.1f}%, "
                      f"PAT YoY {row['pat_yoy_growth']:.1f}%")


if __name__ == "__main__":
    main()
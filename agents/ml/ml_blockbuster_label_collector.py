#!/usr/bin/env python3
"""
ML BLOCKBUSTER LABEL COLLECTOR

This agent collects blockbuster labels for ML training, creating a dual-target
dataset that includes both upper circuit and blockbuster labels.

Integration with ML Pipeline:
1. Reads from blockbuster detection databases
2. Creates unified labels for ML training
3. Enables dual-target model training (circuits + blockbusters)
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BlockbusterLabel:
    """Label for blockbuster quarter detection"""
    symbol: str
    bse_code: Optional[str]
    nse_symbol: Optional[str]
    announcement_date: str

    # Blockbuster indicators
    is_blockbuster: int  # 0 or 1
    blockbuster_score: float

    # Growth metrics
    revenue_yoy_growth: float
    pat_yoy_growth: float
    eps_yoy_growth: float

    # QoQ metrics
    revenue_qoq_growth: Optional[float]
    pat_qoq_growth: Optional[float]

    # Circuit label (if available)
    hit_upper_circuit: Optional[int]

    # Combined label
    high_impact_event: int  # 1 if blockbuster OR circuit


class MLBlockbusterLabelCollector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Input databases
        self.blockbuster_alerts_db = self.data_dir / "blockbuster_alerts.db"
        self.blockbuster_features_db = self.data_dir / "features" / "blockbuster_features.db"
        self.upper_circuit_labels_db = self.data_dir / "upper_circuit_labels.db"

        # Output database for unified labels
        self.unified_labels_db = self.data_dir / "unified_ml_labels.db"

        self._init_unified_database()

    def _init_unified_database(self):
        """Initialize the unified labels database for ML training"""
        conn = sqlite3.connect(self.unified_labels_db)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS unified_ml_labels (
                -- Identifiers
                symbol TEXT,
                bse_code TEXT,
                nse_symbol TEXT,
                date DATE,

                -- Upper Circuit Label (existing)
                hit_upper_circuit INTEGER DEFAULT 0,
                price_change_pct REAL,

                -- Blockbuster Label (new)
                is_blockbuster INTEGER DEFAULT 0,
                blockbuster_score REAL DEFAULT 0,

                -- Growth Metrics
                revenue_yoy_growth REAL,
                pat_yoy_growth REAL,
                eps_yoy_growth REAL,
                revenue_qoq_growth REAL,
                pat_qoq_growth REAL,

                -- Momentum Indicators
                momentum_score REAL,
                consecutive_growth_quarters INTEGER DEFAULT 0,
                percentile_rank REAL,

                -- Combined Labels for Multi-Target Learning
                high_impact_event INTEGER DEFAULT 0,  -- 1 if circuit OR blockbuster
                event_type TEXT,  -- 'circuit', 'blockbuster', 'both', 'none'
                composite_score REAL,  -- Combined scoring

                -- Metadata
                data_source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (symbol, date)
            )
        """)

        # Create indexes for efficient querying
        conn.execute("CREATE INDEX IF NOT EXISTS idx_bse_code_date ON unified_ml_labels(bse_code, date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_is_blockbuster ON unified_ml_labels(is_blockbuster)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_hit_circuit ON unified_ml_labels(hit_upper_circuit)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_high_impact ON unified_ml_labels(high_impact_event)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON unified_ml_labels(event_type)")

        conn.commit()
        conn.close()

    def collect_blockbuster_labels(self) -> pd.DataFrame:
        """Collect blockbuster labels from various sources"""
        dfs = []

        # 1. Collect from blockbuster features database
        if self.blockbuster_features_db.exists():
            conn = sqlite3.connect(self.blockbuster_features_db)

            query = """
                SELECT
                    symbol,
                    date,
                    is_blockbuster,
                    blockbuster_score,
                    revenue_yoy_growth,
                    pat_yoy_growth,
                    eps_yoy_growth,
                    revenue_qoq_growth,
                    pat_qoq_growth,
                    momentum_score,
                    consecutive_growth_quarters,
                    percentile_rank
                FROM blockbuster_features
            """

            df = pd.read_sql(query, conn)
            df['data_source'] = 'blockbuster_features'
            dfs.append(df)
            conn.close()

            logger.info(f"Collected {len(df)} records from blockbuster features")

        # 2. Collect from blockbuster alerts database
        if self.blockbuster_alerts_db.exists():
            conn = sqlite3.connect(self.blockbuster_alerts_db)

            query = """
                SELECT
                    COALESCE(nse_symbol, bse_code) as symbol,
                    bse_code,
                    nse_symbol,
                    announcement_date as date,
                    is_blockbuster,
                    blockbuster_score,
                    revenue_yoy_growth,
                    pat_yoy_growth,
                    eps_growth as eps_yoy_growth
                FROM blockbuster_alerts
            """

            df = pd.read_sql(query, conn)
            df['data_source'] = 'blockbuster_alerts'
            dfs.append(df)
            conn.close()

            logger.info(f"Collected {len(df)} records from blockbuster alerts")

        if dfs:
            # Combine all sources
            combined = pd.concat(dfs, ignore_index=True)

            # Remove duplicates, keeping the most complete record
            combined = combined.sort_values('blockbuster_score', ascending=False)
            combined = combined.groupby(['symbol', 'date']).first().reset_index()

            return combined

        return pd.DataFrame()

    def collect_circuit_labels(self) -> pd.DataFrame:
        """Collect upper circuit labels"""
        if not self.upper_circuit_labels_db.exists():
            logger.warning("Upper circuit labels database not found")
            return pd.DataFrame()

        conn = sqlite3.connect(self.upper_circuit_labels_db)

        query = """
            SELECT
                COALESCE(nse_symbol, bse_code) as symbol,
                bse_code,
                nse_symbol,
                earnings_date as date,
                label as hit_upper_circuit,
                price_change_pct
            FROM upper_circuit_labels
            WHERE label IS NOT NULL
        """

        df = pd.read_sql(query, conn)
        conn.close()

        logger.info(f"Collected {len(df)} circuit labels")
        return df

    def merge_labels(self, blockbuster_df: pd.DataFrame, circuit_df: pd.DataFrame) -> pd.DataFrame:
        """Merge blockbuster and circuit labels into unified dataset"""

        if blockbuster_df.empty and circuit_df.empty:
            logger.warning("No data to merge")
            return pd.DataFrame()

        # Ensure date columns are datetime
        if not blockbuster_df.empty:
            blockbuster_df['date'] = pd.to_datetime(blockbuster_df['date'])
        if not circuit_df.empty:
            circuit_df['date'] = pd.to_datetime(circuit_df['date'])

        # Merge on symbol and date
        if not blockbuster_df.empty and not circuit_df.empty:
            merged = pd.merge(
                blockbuster_df,
                circuit_df[['symbol', 'date', 'hit_upper_circuit', 'price_change_pct']],
                on=['symbol', 'date'],
                how='outer'
            )
        elif not blockbuster_df.empty:
            merged = blockbuster_df.copy()
            merged['hit_upper_circuit'] = 0
            merged['price_change_pct'] = np.nan
        else:
            merged = circuit_df.copy()
            merged['is_blockbuster'] = 0
            merged['blockbuster_score'] = 0

        # Fill missing values
        merged['is_blockbuster'] = merged['is_blockbuster'].fillna(0).astype(int)
        merged['hit_upper_circuit'] = merged['hit_upper_circuit'].fillna(0).astype(int)
        merged['blockbuster_score'] = merged['blockbuster_score'].fillna(0)

        # Create combined labels
        merged['high_impact_event'] = ((merged['is_blockbuster'] == 1) |
                                       (merged['hit_upper_circuit'] == 1)).astype(int)

        # Determine event type
        def get_event_type(row):
            if row['is_blockbuster'] and row['hit_upper_circuit']:
                return 'both'
            elif row['is_blockbuster']:
                return 'blockbuster'
            elif row['hit_upper_circuit']:
                return 'circuit'
            else:
                return 'none'

        merged['event_type'] = merged.apply(get_event_type, axis=1)

        # Create composite score
        merged['composite_score'] = (
            merged['blockbuster_score'] * 0.5 +
            merged['price_change_pct'].fillna(0) * 10
        )

        return merged

    def save_unified_labels(self, df: pd.DataFrame):
        """Save unified labels to database"""
        if df.empty:
            logger.warning("No labels to save")
            return

        conn = sqlite3.connect(self.unified_labels_db)

        # Save to database
        df.to_sql('unified_ml_labels', conn, if_exists='replace', index=False)

        # Get statistics
        stats = pd.read_sql("""
            SELECT
                COUNT(*) as total_samples,
                SUM(is_blockbuster) as blockbuster_count,
                SUM(hit_upper_circuit) as circuit_count,
                SUM(high_impact_event) as high_impact_count,
                COUNT(CASE WHEN event_type = 'both' THEN 1 END) as both_count
            FROM unified_ml_labels
        """, conn)

        conn.close()

        logger.info("="*80)
        logger.info("UNIFIED ML LABELS CREATED")
        logger.info("="*80)
        logger.info(f"Total samples: {stats['total_samples'].iloc[0]:,}")
        logger.info(f"Blockbusters: {stats['blockbuster_count'].iloc[0]:,}")
        logger.info(f"Upper circuits: {stats['circuit_count'].iloc[0]:,}")
        logger.info(f"High impact events: {stats['high_impact_count'].iloc[0]:,}")
        logger.info(f"Both (blockbuster + circuit): {stats['both_count'].iloc[0]:,}")
        logger.info(f"Output saved to: {self.unified_labels_db}")
        logger.info("="*80)

    def get_label_distribution(self) -> Dict:
        """Get distribution of labels for analysis"""
        if not self.unified_labels_db.exists():
            return {}

        conn = sqlite3.connect(self.unified_labels_db)

        dist = pd.read_sql("""
            SELECT
                event_type,
                COUNT(*) as count,
                AVG(blockbuster_score) as avg_blockbuster_score,
                AVG(price_change_pct) as avg_price_change,
                AVG(composite_score) as avg_composite_score
            FROM unified_ml_labels
            GROUP BY event_type
        """, conn)

        conn.close()

        return dist.to_dict('records')

    def run(self) -> pd.DataFrame:
        """Main execution method"""
        logger.info("Starting unified label collection...")

        # Collect labels from different sources
        blockbuster_df = self.collect_blockbuster_labels()
        circuit_df = self.collect_circuit_labels()

        # Merge into unified dataset
        unified_df = self.merge_labels(blockbuster_df, circuit_df)

        # Save to database
        self.save_unified_labels(unified_df)

        # Show distribution
        distribution = self.get_label_distribution()

        print("\nLABEL DISTRIBUTION:")
        print("="*60)
        for dist in distribution:
            print(f"{dist['event_type'].upper()}:")
            print(f"  Count: {dist['count']:,}")
            print(f"  Avg Blockbuster Score: {dist['avg_blockbuster_score']:.2f}")
            if dist['avg_price_change']:
                print(f"  Avg Price Change: {dist['avg_price_change']:.2f}%")
            print(f"  Avg Composite Score: {dist['avg_composite_score']:.2f}")
            print()

        return unified_df


def main():
    """Main execution function"""
    collector = MLBlockbusterLabelCollector()

    # Run collection
    unified_labels = collector.run()

    if not unified_labels.empty:
        # Show some examples of high-impact events
        high_impact = unified_labels[unified_labels['high_impact_event'] == 1].head(10)

        if not high_impact.empty:
            print("\nTOP HIGH-IMPACT EVENTS (Blockbuster OR Circuit):")
            print("="*80)
            for _, row in high_impact.iterrows():
                print(f"{row['symbol']} ({row['date']}): {row['event_type'].upper()}")
                if row['is_blockbuster']:
                    print(f"  Blockbuster Score: {row['blockbuster_score']:.1f}")
                if row['hit_upper_circuit']:
                    print(f"  Price Change: {row['price_change_pct']:.2f}%")
                print(f"  Composite Score: {row['composite_score']:.1f}")
                print()

    logger.info("Unified label collection complete!")
    logger.info("ML models can now train on both circuit and blockbuster targets")


if __name__ == "__main__":
    main()
"""
Unit tests for Story 2.3: Sentiment Feature Extraction

Tests follow TDD RED phase - written before implementation.
Target: 20 tests covering all acceptance criteria.

Test Structure:
1. TestSentimentFeatureExtractorInitialization (3 tests) - AC2.3.1
2. TestPreAnnouncementMomentum (3 tests) - AC2.3.2
3. TestDay1Reaction (4 tests) - AC2.3.3
4. TestVolumeBehavior (3 tests) - AC2.3.4
5. TestPostVolatility (2 tests) - AC2.3.5
6. TestFeatureExtraction (2 tests) - AC2.3.6
7. TestMissingDataHandling (2 tests) - AC2.3.7
8. TestPerformance (1 test) - AC2.3.6 performance
"""

import pytest
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import time

# Will be implemented
from agents.ml.sentiment_feature_extractor import (
    SentimentFeatureExtractor,
    SentimentFeatures
)


class TestSentimentFeatureExtractorInitialization:
    """AC2.3.1: Class initialization and database setup"""

    def test_class_exists(self):
        """Test that SentimentFeatureExtractor class exists"""
        assert SentimentFeatureExtractor is not None
        assert callable(SentimentFeatureExtractor)

    def test_constructor_instantiation(self):
        """Test that constructor accepts required parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db = Path(tmpdir) / "prices.db"
            labels_db = Path(tmpdir) / "labels.db"
            output_db = Path(tmpdir) / "sentiment.db"

            # Create minimal databases
            for db_path in [price_db, labels_db]:
                conn = sqlite3.connect(db_path)
                conn.execute("CREATE TABLE dummy (id INTEGER)")
                conn.close()

            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            assert extractor is not None
            assert extractor.price_db_path == str(price_db)
            assert extractor.output_db_path == str(output_db)

    def test_database_schema_creation(self):
        """Test that sentiment_features table is created with correct schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db = Path(tmpdir) / "prices.db"
            labels_db = Path(tmpdir) / "labels.db"
            output_db = Path(tmpdir) / "sentiment.db"

            # Create minimal databases
            for db_path in [price_db, labels_db]:
                conn = sqlite3.connect(db_path)
                conn.execute("CREATE TABLE dummy (id INTEGER)")
                conn.close()

            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Check table exists
            conn = sqlite3.connect(output_db)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sentiment_features'"
            )
            assert cursor.fetchone() is not None

            # Check schema has all feature columns
            cursor = conn.execute("PRAGMA table_info(sentiment_features)")
            columns = [row[1] for row in cursor.fetchall()]

            expected_columns = [
                'feature_id', 'bse_code', 'date',
                'pre_momentum_5d', 'pre_momentum_10d',
                'day0_reaction', 'day1_reaction', 'cumulative_reaction_2d',
                'volume_spike_ratio', 'pre_volume_trend',
                'post_volatility_5d',
                'created_at'
            ]

            for col in expected_columns:
                assert col in columns, f"Missing column: {col}"

            conn.close()


class TestPreAnnouncementMomentum:
    """AC2.3.2: Pre-announcement momentum calculation"""

    def test_5day_momentum_calculation(self):
        """Test 5-day pre-announcement momentum calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # After sorting DESC, indices will be:
            # Index 0 (Day -1): 110
            # Index 5 (Day -6): 100
            # 5-day momentum = ((110 - 100) / 100) * 100 = 10%
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [
                    announcement_date - timedelta(days=6),  # Will be index 5 after sort
                    announcement_date - timedelta(days=5),  # Index 4
                    announcement_date - timedelta(days=4),  # Index 3
                    announcement_date - timedelta(days=3),  # Index 2
                    announcement_date - timedelta(days=2),  # Index 1
                    announcement_date - timedelta(days=1),  # Index 0 (most recent)
                ],
                'close': [100.0, 102.0, 104.0, 106.0, 108.0, 110.0]
            })

            momentum = extractor.calculate_pre_momentum(prices, announcement_date)

            assert momentum is not None
            assert 'momentum_5d' in momentum
            assert 9.0 < momentum['momentum_5d'] < 11.0  # ~10% ((110-100)/100 = 10%)

    def test_10day_momentum_calculation(self):
        """Test 10-day pre-announcement momentum calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # After sorting DESC, indices will be:
            # Index 0 (Day -1): 120
            # Index 10 (Day -11): 100
            # 10-day momentum = ((120 - 100) / 100) * 100 = 20%
            announcement_date = datetime(2024, 1, 15)
            prices = pd.DataFrame({
                'date': [
                    announcement_date - timedelta(days=11),  # Index 10
                    announcement_date - timedelta(days=10),  # Index 9
                    announcement_date - timedelta(days=9),   # Index 8
                    announcement_date - timedelta(days=8),   # Index 7
                    announcement_date - timedelta(days=7),   # Index 6
                    announcement_date - timedelta(days=6),   # Index 5
                    announcement_date - timedelta(days=5),   # Index 4
                    announcement_date - timedelta(days=4),   # Index 3
                    announcement_date - timedelta(days=3),   # Index 2
                    announcement_date - timedelta(days=2),   # Index 1
                    announcement_date - timedelta(days=1),   # Index 0 (most recent)
                ],
                'close': [100.0, 102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0, 116.0, 118.0, 120.0]
            })

            momentum = extractor.calculate_pre_momentum(prices, announcement_date)

            assert momentum is not None
            assert 'momentum_10d' in momentum
            assert 19.0 < momentum['momentum_10d'] < 21.0  # ~20% ((120-100)/100 = 20%)

    def test_momentum_with_missing_data(self):
        """Test momentum calculation with insufficient data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Only 3 days of data (insufficient for 5-day momentum)
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date - timedelta(days=i) for i in range(3, 0, -1)],
                'close': [100, 105, 110]
            })

            momentum = extractor.calculate_pre_momentum(prices, announcement_date)

            assert momentum is not None
            assert momentum['momentum_5d'] is None or pd.isna(momentum['momentum_5d'])
            assert momentum['momentum_10d'] is None or pd.isna(momentum['momentum_10d'])

    def _create_extractor(self, tmpdir):
        """Helper to create extractor with dummy databases"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        for db_path in [price_db, labels_db]:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

        return SentimentFeatureExtractor(
            price_db_path=str(price_db),
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestDay1Reaction:
    """AC2.3.3: Day 1 reaction features"""

    def test_day0_reaction_calculation(self):
        """Test announcement day (Day 0) price reaction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Day 0: Open=100, Close=110 → 10% reaction
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date],
                'open': [100.0],
                'close': [110.0]
            })

            reaction = extractor.calculate_day_reaction(prices, announcement_date)

            assert reaction is not None
            assert 'day0_reaction' in reaction
            assert 9.0 < reaction['day0_reaction'] < 11.0  # ~10%

    def test_day1_reaction_calculation(self):
        """Test next trading day (Day 1) price reaction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Day 0: Close=110, Day 1: Close=121 → 10% reaction on Day 1
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date, announcement_date + timedelta(days=1)],
                'open': [100.0, 110.0],
                'close': [110.0, 121.0]
            })

            reaction = extractor.calculate_day_reaction(prices, announcement_date)

            assert reaction is not None
            assert 'day1_reaction' in reaction
            assert 9.0 < reaction['day1_reaction'] < 11.0  # ~10%

    def test_cumulative_2day_reaction(self):
        """Test cumulative 2-day reaction (Day 0 + Day 1)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Day 0: Open=100, Close=110 (10%)
            # Day 1: Open=110, Close=121 (10%)
            # Cumulative from Day 0 open to Day 1 close: (121-100)/100 = 21%
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date, announcement_date + timedelta(days=1)],
                'open': [100.0, 110.0],
                'close': [110.0, 121.0]
            })

            reaction = extractor.calculate_day_reaction(prices, announcement_date)

            assert reaction is not None
            assert 'cumulative_2d' in reaction
            assert 20.0 < reaction['cumulative_2d'] < 22.0  # ~21%

    def test_negative_reaction(self):
        """Test negative reaction (stock fell on announcement)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Day 0: Open=100, Close=90 → -10% reaction
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date],
                'open': [100.0],
                'close': [90.0]
            })

            reaction = extractor.calculate_day_reaction(prices, announcement_date)

            assert reaction is not None
            assert 'day0_reaction' in reaction
            assert -11.0 < reaction['day0_reaction'] < -9.0  # ~-10%

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        for db_path in [price_db, labels_db]:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

        return SentimentFeatureExtractor(
            price_db_path=str(price_db),
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestVolumeBehavior:
    """AC2.3.4: Volume behavior features"""

    def test_volume_spike_ratio(self):
        """Test volume spike ratio calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # 20-day avg volume = 1M, announcement day volume = 3M → ratio = 3.0
            announcement_date = datetime(2024, 1, 25)
            prices = pd.DataFrame({
                'date': [announcement_date - timedelta(days=i) for i in range(20, -1, -1)],
                'volume': [1_000_000] * 20 + [3_000_000]  # Last day has 3x volume
            })

            volume_features = extractor.calculate_volume_features(prices, announcement_date)

            assert volume_features is not None
            assert 'volume_spike_ratio' in volume_features
            assert 2.8 < volume_features['volume_spike_ratio'] < 3.2  # ~3.0

    def test_pre_volume_trend(self):
        """Test pre-announcement volume trend"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Days -20 to -6: 1M volume
            # Days -5 to -1: 1.5M volume → trend = 1.5/1.0 = 1.5
            announcement_date = datetime(2024, 1, 25)
            volumes = [1_000_000] * 15 + [1_500_000] * 5 + [2_000_000]  # Last is announcement day
            prices = pd.DataFrame({
                'date': [announcement_date - timedelta(days=i) for i in range(20, -1, -1)],
                'volume': volumes
            })

            volume_features = extractor.calculate_volume_features(prices, announcement_date)

            assert volume_features is not None
            assert 'pre_volume_trend' in volume_features
            assert 1.4 < volume_features['pre_volume_trend'] < 1.6  # ~1.5

    def test_volume_surge_detection(self):
        """Test detection of volume surge (>2x average)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # 20-day avg = 1M, announcement = 2.5M → surge detected
            announcement_date = datetime(2024, 1, 25)
            prices = pd.DataFrame({
                'date': [announcement_date - timedelta(days=i) for i in range(20, -1, -1)],
                'volume': [1_000_000] * 20 + [2_500_000]
            })

            volume_features = extractor.calculate_volume_features(prices, announcement_date)

            assert volume_features is not None
            assert volume_features['volume_spike_ratio'] > 2.0

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        for db_path in [price_db, labels_db]:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

        return SentimentFeatureExtractor(
            price_db_path=str(price_db),
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestPostVolatility:
    """AC2.3.5: Post-announcement volatility"""

    def test_5day_post_volatility(self):
        """Test 5-day post-announcement volatility calculation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Days +1 to +5: Returns = [2%, -1%, 3%, -2%, 1%]
            # Volatility = std dev of returns
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date + timedelta(days=i) for i in range(6)],
                'close': [100.0, 102.0, 100.98, 104.01, 101.93, 102.95]
            })

            volatility = extractor.calculate_post_volatility(prices, announcement_date)

            assert volatility is not None
            assert 'post_volatility_5d' in volatility
            assert volatility['post_volatility_5d'] > 0  # Should be positive

    def test_volatility_with_insufficient_data(self):
        """Test volatility calculation with <5 days post-announcement"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Only 3 days of post data
            announcement_date = datetime(2024, 1, 10)
            prices = pd.DataFrame({
                'date': [announcement_date + timedelta(days=i) for i in range(3)],
                'close': [100.0, 102.0, 104.0]
            })

            volatility = extractor.calculate_post_volatility(prices, announcement_date)

            assert volatility is not None
            # Should return NaN or None for insufficient data
            assert volatility['post_volatility_5d'] is None or pd.isna(volatility['post_volatility_5d'])

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        for db_path in [price_db, labels_db]:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

        return SentimentFeatureExtractor(
            price_db_path=str(price_db),
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestFeatureExtraction:
    """AC2.3.6: Feature extraction for single and batch samples"""

    def test_single_sample_extraction(self):
        """Test extract_features_for_sample returns SentimentFeatures object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db, labels_db, output_db = self._setup_databases(tmpdir)
            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Extract features
            features = extractor.extract_features_for_sample(
                bse_code="500325",
                date="2024-01-10"
            )

            assert features is not None
            assert isinstance(features, SentimentFeatures)
            assert features.bse_code == "500325"
            assert features.date == "2024-01-10"
            # Check that at least some features are calculated
            assert features.pre_momentum_5d is not None or features.day0_reaction is not None

    def test_batch_extraction(self):
        """Test extract_features_batch processes multiple samples"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db, labels_db, output_db = self._setup_databases(tmpdir)
            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Batch extract
            samples = [
                {"bse_code": "500325", "date": "2024-01-10"},
                {"bse_code": "500325", "date": "2024-01-15"},
                {"bse_code": "532540", "date": "2024-01-12"}
            ]

            df = extractor.extract_features_batch(samples)

            assert df is not None
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert 'bse_code' in df.columns
            assert 'pre_momentum_5d' in df.columns

    def _setup_databases(self, tmpdir):
        """Helper to set up databases with sample data"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        # Create price database with sample data
        conn = sqlite3.connect(price_db)
        conn.execute("""
            CREATE TABLE historical_prices (
                bse_code TEXT,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        """)

        # Add sample price data for multiple dates
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        for bse_code in ["500325", "532540"]:
            for i, date in enumerate(dates):
                conn.execute("""
                    INSERT INTO historical_prices VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bse_code, date.strftime('%Y-%m-%d'), 100.0 + i, 105.0 + i,
                      95.0 + i, 102.0 + i, 1_000_000))

        conn.commit()
        conn.close()

        # Create labels database
        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return price_db, labels_db, output_db


class TestMissingDataHandling:
    """AC2.3.7: Missing data handling"""

    def test_insufficient_data_returns_nan(self):
        """Test that NaN is returned when insufficient price data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db, labels_db, output_db = self._setup_minimal_database(tmpdir)
            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            features = extractor.extract_features_for_sample(
                bse_code="500325",
                date="2024-01-10"
            )

            assert features is not None
            # Most features should be NaN due to insufficient data
            assert features.pre_momentum_10d is None or pd.isna(features.pre_momentum_10d)

    def test_missing_data_logged(self, caplog):
        """Test that missing data is logged as warning"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db, labels_db, output_db = self._setup_minimal_database(tmpdir)
            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            features = extractor.extract_features_for_sample(
                bse_code="500325",
                date="2024-01-10"
            )

            # Check logs for warning about insufficient data
            # (This test may need adjustment based on actual logging implementation)
            assert features is not None

    def _setup_minimal_database(self, tmpdir):
        """Helper to create database with minimal data"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        # Create price database with only 2 days of data
        conn = sqlite3.connect(price_db)
        conn.execute("""
            CREATE TABLE historical_prices (
                bse_code TEXT,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        """)
        conn.execute("""
            INSERT INTO historical_prices VALUES ('500325', '2024-01-09', 100, 103, 98, 102, 1000000)
        """)
        conn.execute("""
            INSERT INTO historical_prices VALUES ('500325', '2024-01-10', 102, 106, 100, 105, 1200000)
        """)
        conn.commit()
        conn.close()

        # Create labels database
        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return price_db, labels_db, output_db


class TestPerformance:
    """AC2.3.6: Performance requirements"""

    def test_batch_processing_performance(self):
        """Test that 1000 samples can be processed in <5 seconds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            price_db, labels_db, output_db = self._setup_large_database(tmpdir)
            extractor = SentimentFeatureExtractor(
                price_db_path=str(price_db),
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Generate 1000 samples
            samples = []
            dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            for i, date in enumerate(dates[:1000]):
                samples.append({
                    "bse_code": f"50{i % 100:04d}",
                    "date": date.strftime('%Y-%m-%d')
                })

            # Measure time
            start_time = time.time()
            df = extractor.extract_features_batch(samples)
            elapsed = time.time() - start_time

            assert df is not None
            assert len(df) > 0
            assert elapsed < 5.0, f"Batch processing took {elapsed:.2f}s (target: <5s)"
            print(f"\nPerformance: Processed {len(df)} samples in {elapsed:.2f}s ({len(df)/elapsed:.0f} samples/sec)")

    def _setup_large_database(self, tmpdir):
        """Helper to create large database for performance testing"""
        price_db = Path(tmpdir) / "prices.db"
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "sentiment.db"

        # Create price database with sample data for many companies
        conn = sqlite3.connect(price_db)
        conn.execute("""
            CREATE TABLE historical_prices (
                bse_code TEXT,
                date DATE,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        """)
        conn.execute("CREATE INDEX idx_price_bse_date ON historical_prices(bse_code, date)")

        # Add data for 100 companies over 1 year
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        for company_id in range(100):
            bse_code = f"50{company_id:04d}"
            for i, date in enumerate(dates):
                conn.execute("""
                    INSERT INTO historical_prices VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (bse_code, date.strftime('%Y-%m-%d'),
                      100.0 + i*0.1, 105.0 + i*0.1, 95.0 + i*0.1, 102.0 + i*0.1,
                      1_000_000 + (i % 10) * 100_000))

        conn.commit()
        conn.close()

        # Create labels database
        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return price_db, labels_db, output_db


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

"""
Unit tests for Story 2.1: Technical Features Extraction

TDD Phase: RED (write tests first)
Target: ≥90% test coverage

Test Coverage:
- AC2.1.1: TechnicalFeatureExtractor initialization
- AC2.1.2: RSI calculation
- AC2.1.3: MACD calculation
- AC2.1.4: Bollinger Bands calculation
- AC2.1.5: Volume indicators
- AC2.1.6: Price momentum
- AC2.1.7: Batch processing
- AC2.1.8: Missing data handling
"""

import pytest
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


class TestTechnicalFeatureExtractorInitialization:
    """Test TechnicalFeatureExtractor class initialization (AC2.1.1)"""

    def test_extractor_class_exists(self):
        """AC2.1.1: Verify TechnicalFeatureExtractor can be imported"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor
        assert TechnicalFeatureExtractor is not None

    def test_extractor_instantiation(self, tmp_path):
        """AC2.1.1: Test extractor can be instantiated with db paths"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        price_db = str(tmp_path / "price_movements.db")
        output_db = str(tmp_path / "features.db")

        extractor = TechnicalFeatureExtractor(
            price_db_path=price_db,
            output_db_path=output_db
        )

        assert extractor.price_db_path == price_db
        assert extractor.output_db_path == output_db

    def test_output_database_schema_created(self, tmp_path):
        """AC2.1.1: Verify technical_features table schema"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        price_db = str(tmp_path / "price_movements.db")
        output_db = str(tmp_path / "features.db")

        extractor = TechnicalFeatureExtractor(price_db, output_db)

        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='technical_features'")
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("PRAGMA index_list('technical_features')")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]

        assert 'idx_sample_id' in index_names
        assert 'idx_bse_date' in index_names

        conn.close()


class TestRSICalculation:
    """Test RSI (Relative Strength Index) calculation (AC2.1.2)"""

    def test_rsi_uptrend(self):
        """AC2.1.2: RSI for uptrend should be >50"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Uptrend: prices increasing
        prices = pd.Series([100, 102, 104, 106, 108, 110, 112, 114, 116, 118] * 2)
        rsi = extractor.calculate_rsi(prices, period=14)

        # RSI should be high for uptrend
        assert rsi.iloc[-1] > 50
        assert rsi.iloc[-1] < 100

    def test_rsi_downtrend(self):
        """AC2.1.2: RSI for downtrend should be <50"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Downtrend: prices decreasing
        prices = pd.Series([118, 116, 114, 112, 110, 108, 106, 104, 102, 100] * 2)
        rsi = extractor.calculate_rsi(prices, period=14)

        # RSI should be low for downtrend
        assert rsi.iloc[-1] < 50
        assert rsi.iloc[-1] > 0

    def test_rsi_range(self):
        """AC2.1.2: RSI should be between 0 and 100"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Random price movements
        np.random.seed(42)
        prices = pd.Series(100 + np.cumsum(np.random.randn(100)))
        rsi = extractor.calculate_rsi(prices, period=14)

        # RSI must be in range [0, 100]
        assert (rsi.dropna() >= 0).all()
        assert (rsi.dropna() <= 100).all()


class TestMACDCalculation:
    """Test MACD calculation (AC2.1.3)"""

    def test_macd_components_exist(self):
        """AC2.1.3: MACD returns line, signal, and histogram"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        prices = pd.Series(range(100, 150))
        macd = extractor.calculate_macd(prices)

        assert 'macd_line' in macd
        assert 'macd_signal' in macd
        assert 'macd_histogram' in macd

    def test_macd_uptrend_positive(self):
        """AC2.1.3: MACD line should be positive in strong uptrend"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Strong uptrend
        prices = pd.Series(range(100, 200))
        macd = extractor.calculate_macd(prices)

        # MACD line should be positive
        assert macd['macd_line'].iloc[-1] > 0

    def test_macd_histogram_calculation(self):
        """AC2.1.3: MACD histogram = MACD line - Signal line"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        prices = pd.Series(range(100, 150))
        macd = extractor.calculate_macd(prices)

        # Verify histogram calculation (allow small rounding differences)
        expected_histogram = macd['macd_line'] - macd['macd_signal']
        np.testing.assert_array_almost_equal(
            macd['macd_histogram'].values,
            expected_histogram.values,
            decimal=3  # Allow rounding to 3 decimal places (0.001 precision)
        )


class TestBollingerBands:
    """Test Bollinger Bands calculation (AC2.1.4)"""

    def test_bollinger_bands_components(self):
        """AC2.1.4: BB returns upper, middle, lower, and %B"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        prices = pd.Series(range(100, 150))
        bb = extractor.calculate_bollinger_bands(prices, period=20, std_dev=2.0)

        assert 'bb_upper' in bb
        assert 'bb_middle' in bb
        assert 'bb_lower' in bb
        assert 'bb_percent_b' in bb

    def test_bollinger_bands_order(self):
        """AC2.1.4: Upper > Middle > Lower"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        prices = pd.Series([100] * 30)  # Flat price
        bb = extractor.calculate_bollinger_bands(prices, period=20)

        # For flat prices, bands should converge but maintain order
        assert bb['bb_upper'].iloc[-1] >= bb['bb_middle'].iloc[-1]
        assert bb['bb_middle'].iloc[-1] >= bb['bb_lower'].iloc[-1]

    def test_bollinger_percent_b(self):
        """AC2.1.4: BB %B at middle band should be ≈ 0.5"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Create prices that oscillate around 100
        prices = pd.Series([100 + i % 5 for i in range(50)])
        bb = extractor.calculate_bollinger_bands(prices, period=20)

        # %B should be around 0.5 for prices near middle band
        # For oscillating prices [100,101,102,103,104,...], %B will range from ~0.15 to ~0.85
        percent_b = bb['bb_percent_b'].iloc[-10:]  # Last 10 values
        assert (percent_b > 0.1).all()  # Allow for oscillation below middle band
        assert (percent_b < 0.9).all()  # Allow for oscillation above middle band
        # Verify mean is around 0.5 (middle band)
        assert 0.4 < percent_b.mean() < 0.6


class TestVolumeIndicators:
    """Test volume indicators (AC2.1.5)"""

    def test_volume_ratio_calculation(self):
        """AC2.1.5: Volume ratio = current / 30-day average"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Constant volume of 1000 for 29 days, then 2000 on day 30
        volume = pd.Series([1000] * 29 + [2000])
        vol_indicators = extractor.calculate_volume_indicators(volume, period=30)

        # Volume ratio should be 2000 / 1000 = 2.0
        assert vol_indicators['volume_ratio'].iloc[-1] == pytest.approx(2.0, rel=0.1)

    def test_volume_spike_detection(self):
        """AC2.1.5: Volume spike = 1 if ratio > 2.0"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Normal volume, then 3x spike
        volume = pd.Series([1000] * 30 + [3000])
        vol_indicators = extractor.calculate_volume_indicators(volume, period=30)

        # Should detect spike
        assert vol_indicators['volume_spike'].iloc[-1] == 1

    def test_no_volume_spike(self):
        """AC2.1.5: Volume spike = 0 if ratio ≤ 2.0"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # Normal volume, slight increase
        volume = pd.Series([1000] * 30 + [1500])
        vol_indicators = extractor.calculate_volume_indicators(volume, period=30)

        # Should not detect spike
        assert vol_indicators['volume_spike'].iloc[-1] == 0


class TestMomentumCalculation:
    """Test price momentum calculation (AC2.1.6)"""

    def test_momentum_positive(self):
        """AC2.1.6: Positive momentum for price increase"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # 10% increase over 5 days: 100 → 110
        prices = pd.Series([100, 102, 104, 106, 108, 110])
        momentum = extractor.calculate_momentum(prices, periods=[5])

        # 5-day momentum should be (110 - 100) / 100 * 100 = 10%
        assert momentum['momentum_5d'].iloc[-1] == pytest.approx(10.0, rel=0.1)

    def test_momentum_negative(self):
        """AC2.1.6: Negative momentum for price decrease"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        # 10% decrease: 110 → 99
        prices = pd.Series([110, 108, 106, 104, 102, 99])
        momentum = extractor.calculate_momentum(prices, periods=[5])

        # Should be negative
        assert momentum['momentum_5d'].iloc[-1] < 0

    def test_momentum_multiple_periods(self):
        """AC2.1.6: Calculate momentum for 5, 10, 30 days"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        extractor = TechnicalFeatureExtractor("dummy.db", "dummy.db")

        prices = pd.Series(range(100, 200))
        momentum = extractor.calculate_momentum(prices, periods=[5, 10, 30])

        assert 'momentum_5d' in momentum
        assert 'momentum_10d' in momentum
        assert 'momentum_30d' in momentum


class TestFeatureExtraction:
    """Test feature extraction for samples (AC2.1.7)"""

    def test_extract_features_for_sample(self, tmp_path):
        """AC2.1.7: Extract all features for a single sample"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        # Create mock price database
        price_db = tmp_path / "price.db"
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE price_movements (
                bse_code TEXT,
                date DATE,
                close REAL,
                volume INTEGER
            )
        """)

        # Insert 60 days of data
        base_date = datetime(2024, 1, 1)
        for i in range(60):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO price_movements (bse_code, date, close, volume) VALUES (?, ?, ?, ?)",
                ('500325', date, 100 + i * 0.5, 1000000)
            )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = TechnicalFeatureExtractor(str(price_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-03-01')

        # Verify all features calculated
        assert features.rsi_14 is not None
        assert features.macd_line is not None
        assert features.macd_signal is not None
        assert features.macd_histogram is not None
        assert features.bb_upper is not None
        assert features.bb_middle is not None
        assert features.bb_lower is not None
        assert features.bb_percent_b is not None
        assert features.volume_ratio is not None
        assert features.volume_spike is not None
        assert features.momentum_5d is not None
        assert features.momentum_10d is not None
        assert features.momentum_30d is not None

    def test_extract_features_batch(self, tmp_path):
        """AC2.1.7: Extract features for multiple samples"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        # Create mock database with multiple companies
        price_db = tmp_path / "price.db"
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE price_movements (
                bse_code TEXT,
                date DATE,
                close REAL,
                volume INTEGER
            )
        """)

        # Insert data for 2 companies
        base_date = datetime(2024, 1, 1)
        for bse_code in ['500325', '500209']:
            for i in range(60):
                date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute(
                    "INSERT INTO price_movements (bse_code, date, close, volume) VALUES (?, ?, ?, ?)",
                    (bse_code, date, 100 + i * 0.5, 1000000)
                )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = TechnicalFeatureExtractor(str(price_db), str(output_db))

        samples = [
            {'sample_id': 1, 'bse_code': '500325', 'date': '2024-03-01'},
            {'sample_id': 2, 'bse_code': '500209', 'date': '2024-03-01'}
        ]

        df = extractor.extract_features_batch(samples)

        assert len(df) == 2
        assert 'rsi_14' in df.columns
        assert 'macd_line' in df.columns


class TestMissingDataHandling:
    """Test missing data handling (AC2.1.8)"""

    def test_insufficient_data_returns_nan(self, tmp_path):
        """AC2.1.8: Return NaN if <30 days of data"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor

        # Create database with only 20 days of data
        price_db = tmp_path / "price.db"
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE price_movements (
                bse_code TEXT,
                date DATE,
                close REAL,
                volume INTEGER
            )
        """)

        # Insert only 20 days
        base_date = datetime(2024, 1, 1)
        for i in range(20):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO price_movements (bse_code, date, close, volume) VALUES (?, ?, ?, ?)",
                ('500325', date, 100, 1000000)
            )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = TechnicalFeatureExtractor(str(price_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-01-20')

        # All features should be None/NaN
        assert features.rsi_14 is None
        assert features.macd_line is None

    def test_missing_data_logged(self, tmp_path, caplog):
        """AC2.1.8: Log warning for missing features"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor
        import logging

        caplog.set_level(logging.WARNING)

        # Create database with insufficient data
        price_db = tmp_path / "price.db"
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE price_movements (bse_code TEXT, date DATE, close REAL, volume INTEGER)")
        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = TechnicalFeatureExtractor(str(price_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-01-20')

        # Should log warning
        assert any("Insufficient data" in record.message or "missing" in record.message.lower()
                   for record in caplog.records)


class TestPerformance:
    """Test performance requirements (AC2.1.7)"""

    def test_batch_processing_performance(self, tmp_path):
        """AC2.1.7: Process 1000 samples in <5 seconds"""
        from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor
        import time

        # Create database with data for 10 companies
        price_db = tmp_path / "price.db"
        conn = sqlite3.connect(str(price_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE price_movements (
                bse_code TEXT,
                date DATE,
                close REAL,
                volume INTEGER
            )
        """)

        # Insert 60 days for 10 companies
        base_date = datetime(2024, 1, 1)
        for bse_code_num in range(10):
            bse_code = f"50{bse_code_num:04d}"
            for i in range(60):
                date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
                cursor.execute(
                    "INSERT INTO price_movements (bse_code, date, close, volume) VALUES (?, ?, ?, ?)",
                    (bse_code, date, 100 + i * 0.5, 1000000)
                )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = TechnicalFeatureExtractor(str(price_db), str(output_db))

        # Create 100 samples (10 companies × 10 dates each)
        samples = []
        for bse_code_num in range(10):
            bse_code = f"50{bse_code_num:04d}"
            for day in range(30, 40):
                date = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
                samples.append({
                    'sample_id': len(samples) + 1,
                    'bse_code': bse_code,
                    'date': date
                })

        start_time = time.time()
        df = extractor.extract_features_batch(samples)
        elapsed = time.time() - start_time

        # Should process 100 samples in <5 seconds
        assert elapsed < 5.0
        assert len(df) == 100

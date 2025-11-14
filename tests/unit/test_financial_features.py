"""
Unit tests for Story 2.2: Financial Features Extraction

Tests cover all 8 acceptance criteria with 26 comprehensive tests.
Following TDD approach: Write tests first (RED), then implement (GREEN).

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import pytest
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


class TestFinancialFeatureExtractorInitialization:
    """Test initialization and database setup (AC2.2.1)"""

    def test_extractor_class_exists(self):
        """AC2.2.1: FinancialFeatureExtractor class exists"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        assert FinancialFeatureExtractor is not None

    def test_extractor_instantiation(self, tmp_path):
        """AC2.2.1: Constructor accepts database paths"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        financials_db = str(tmp_path / "financials.db")
        output_db = str(tmp_path / "features.db")

        extractor = FinancialFeatureExtractor(financials_db, output_db)

        assert extractor.financials_db_path == financials_db
        assert extractor.output_db_path == output_db

    def test_output_database_schema_created(self, tmp_path):
        """AC2.2.1: Creates financial_features table with indexes"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        financials_db = str(tmp_path / "financials.db")
        output_db = str(tmp_path / "features.db")

        FinancialFeatureExtractor(financials_db, output_db)

        # Verify table exists
        conn = sqlite3.connect(output_db)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='financial_features'")
        assert cursor.fetchone() is not None

        # Check indexes exist
        cursor.execute("PRAGMA index_list('financial_features')")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]

        assert 'idx_financial_sample_id' in index_names
        assert 'idx_financial_bse_date' in index_names

        conn.close()


class TestRevenueGrowthCalculation:
    """Test revenue growth features (AC2.2.2)"""

    def test_qoq_revenue_growth_positive(self):
        """AC2.2.2: Calculate positive QoQ revenue growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Revenue: Q0=120 Cr, Q-1=100 Cr → 20% growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'revenue': [120.0, 100.0]
        })

        growth = extractor.calculate_revenue_growth(financials)

        assert growth['qoq'] == pytest.approx(20.0, rel=0.01)

    def test_yoy_revenue_growth(self):
        """AC2.2.2: Calculate YoY revenue growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Revenue: Q1 2024=150 Cr, Q1 2023=100 Cr → 50% YoY growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2024, 2023, 2023, 2023, 2023],
            'revenue': [150.0, 140.0, 130.0, 120.0, 100.0]
        })

        growth = extractor.calculate_revenue_growth(financials)

        assert growth['yoy'] == pytest.approx(50.0, rel=0.01)

    def test_revenue_growth_4q_average(self):
        """AC2.2.2: Calculate 4-quarter average revenue growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Revenue growth QoQ: 10%, 8.7%, 4.55% → Average ≈ 7.75%
        financials = pd.DataFrame({
            'quarter': ['Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2023, 2023, 2023, 2023],
            'revenue': [137.5, 125.0, 115.0, 110.0]
        })

        growth = extractor.calculate_revenue_growth(financials)

        assert growth['avg_4q'] is not None
        assert 7.0 < growth['avg_4q'] < 8.5  # Average of 3 QoQ growths

    def test_negative_revenue_handling(self):
        """AC2.2.2: Handle negative revenue gracefully"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Negative revenue (accounting adjustment)
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'revenue': [-50.0, 100.0]
        })

        growth = extractor.calculate_revenue_growth(financials)

        # Should return NaN for invalid data
        assert pd.isna(growth['qoq'])


class TestProfitGrowthCalculation:
    """Test profit growth features (AC2.2.3)"""

    def test_qoq_pat_growth_positive(self):
        """AC2.2.3: Calculate positive QoQ PAT growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # PAT: Q0=60 Cr, Q-1=50 Cr → 20% growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'pat': [60.0, 50.0]
        })

        growth = extractor.calculate_profit_growth(financials)

        assert growth['qoq'] == pytest.approx(20.0, rel=0.01)

    def test_yoy_pat_growth(self):
        """AC2.2.3: Calculate YoY PAT growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # PAT: Q1 2024=75 Cr, Q1 2023=50 Cr → 50% YoY growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2024, 2023, 2023, 2023, 2023],
            'pat': [75.0, 70.0, 65.0, 60.0, 50.0]
        })

        growth = extractor.calculate_profit_growth(financials)

        assert growth['yoy'] == pytest.approx(50.0, rel=0.01)

    def test_loss_to_profit_turnaround(self):
        """AC2.2.3: Detect loss-to-profit turnaround"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # PAT: Q0=+50 Cr, Q-1=-100 Cr → Turnaround
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'pat': [50.0, -100.0]
        })

        growth = extractor.calculate_profit_growth(financials)

        # Turnaround: (50 - (-100)) / abs(-100) = 150%
        assert growth['qoq'] == pytest.approx(150.0, rel=0.01)

    def test_profit_to_loss(self):
        """AC2.2.3: Detect profit-to-loss scenario"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # PAT: Q0=-50 Cr, Q-1=+100 Cr → Loss
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'pat': [-50.0, 100.0]
        })

        growth = extractor.calculate_profit_growth(financials)

        # Should be large negative growth
        assert growth['qoq'] < -100.0


class TestMarginCalculation:
    """Test margin features (AC2.2.4)"""

    def test_operating_margin_calculation(self):
        """AC2.2.4: Calculate operating profit margin"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # OPM = (40 / 200) * 100 = 20%
        financials = pd.DataFrame({
            'quarter': ['Q1'],
            'year': [2024],
            'revenue': [200.0],
            'operating_profit': [40.0]
        })

        margins = extractor.calculate_margins(financials)

        assert margins['operating_margin'] == pytest.approx(20.0, rel=0.01)

    def test_net_profit_margin_calculation(self):
        """AC2.2.4: Calculate net profit margin"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # NPM = (30 / 200) * 100 = 15%
        financials = pd.DataFrame({
            'quarter': ['Q1'],
            'year': [2024],
            'revenue': [200.0],
            'pat': [30.0]
        })

        margins = extractor.calculate_margins(financials)

        assert margins['net_profit_margin'] == pytest.approx(15.0, rel=0.01)

    def test_margin_expansion(self):
        """AC2.2.4: Calculate margin expansion QoQ"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # NPM Q0 = 15%, NPM Q-1 = 10% → Expansion = +5%
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'revenue': [200.0, 200.0],
            'pat': [30.0, 20.0]  # 15% vs 10%
        })

        margins = extractor.calculate_margins(financials)

        assert margins['expansion_qoq'] == pytest.approx(5.0, rel=0.01)

    def test_avg_margin_4q(self):
        """AC2.2.4: Calculate 4-quarter average margin"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # NPM: 10%, 12%, 14%, 16% → Average = 13%
        financials = pd.DataFrame({
            'quarter': ['Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2023, 2023, 2023, 2023],
            'revenue': [100.0, 100.0, 100.0, 100.0],
            'pat': [16.0, 14.0, 12.0, 10.0]
        })

        margins = extractor.calculate_margins(financials)

        assert margins['avg_4q'] == pytest.approx(13.0, rel=0.01)


class TestEPSFeatures:
    """Test EPS features (AC2.2.5)"""

    def test_qoq_eps_growth(self):
        """AC2.2.5: Calculate QoQ EPS growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # EPS: Q0=12, Q-1=10 → 20% growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'eps': [12.0, 10.0]
        })

        eps_features = extractor.calculate_eps_features(financials)

        assert eps_features['qoq_growth'] == pytest.approx(20.0, rel=0.01)

    def test_yoy_eps_growth(self):
        """AC2.2.5: Calculate YoY EPS growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # EPS: Q1 2024=15, Q1 2023=10 → 50% YoY growth
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2024, 2023, 2023, 2023, 2023],
            'eps': [15.0, 14.0, 13.0, 12.0, 10.0]
        })

        eps_features = extractor.calculate_eps_features(financials)

        assert eps_features['yoy_growth'] == pytest.approx(50.0, rel=0.01)

    def test_eps_consistency(self):
        """AC2.2.5: Calculate EPS consistency (std dev)"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Consistent EPS: 10, 11, 10, 11 → Low std dev
        financials_consistent = pd.DataFrame({
            'quarter': ['Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2023, 2023, 2023, 2023],
            'eps': [11.0, 10.0, 11.0, 10.0]
        })

        eps_features = extractor.calculate_eps_features(financials_consistent)

        assert eps_features['consistency'] < 1.0  # Low std dev = consistent


class TestEarningsQuality:
    """Test earnings quality features (AC2.2.6)"""

    def test_consecutive_growth_quarters(self):
        """AC2.2.6: Calculate consecutive growth quarters"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # 3 consecutive quarters of revenue + PAT growth
        financials = pd.DataFrame({
            'quarter': ['Q4', 'Q3', 'Q2', 'Q1'],
            'year': [2023, 2023, 2023, 2023],
            'revenue': [140.0, 130.0, 120.0, 110.0],  # Growing
            'pat': [14.0, 13.0, 12.0, 11.0]  # Growing
        })

        quality = extractor.calculate_earnings_quality(financials)

        assert quality['consecutive_growth_quarters'] == 3

    def test_earnings_surprise_detection(self):
        """AC2.2.6: Detect earnings surprise (>20% growth)"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Revenue growth QoQ = 25% (surprise!)
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'revenue': [125.0, 100.0],  # 25% growth
            'pat': [20.0, 20.0]
        })

        quality = extractor.calculate_earnings_quality(financials)

        assert quality['earnings_surprise'] == 1

    def test_no_earnings_surprise(self):
        """AC2.2.6: No surprise for modest growth"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        extractor = FinancialFeatureExtractor("dummy.db", "dummy.db")

        # Revenue growth QoQ = 10% (normal)
        financials = pd.DataFrame({
            'quarter': ['Q1', 'Q4'],
            'year': [2024, 2023],
            'revenue': [110.0, 100.0],  # 10% growth
            'pat': [20.0, 20.0]
        })

        quality = extractor.calculate_earnings_quality(financials)

        assert quality['earnings_surprise'] == 0


class TestFeatureExtraction:
    """Test feature extraction methods (AC2.2.7)"""

    def test_extract_features_for_sample(self, tmp_path):
        """AC2.2.7: Extract all features for a single sample"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        # Create test database with financial data
        financials_db = tmp_path / "financials.db"
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER,
                revenue REAL,
                pat REAL,
                operating_profit REAL,
                eps REAL
            )
        """)

        # Insert 8 quarters of data for company 500325
        quarters = ['Q4', 'Q3', 'Q2', 'Q1', 'Q4', 'Q3', 'Q2', 'Q1']
        years = [2023, 2023, 2023, 2023, 2022, 2022, 2022, 2022]
        revenues = [140.0, 130.0, 120.0, 110.0, 135.0, 125.0, 115.0, 105.0]

        for q, y, r in zip(quarters, years, revenues):
            cursor.execute(
                "INSERT INTO historical_financials (bse_code, quarter, year, revenue, pat, operating_profit, eps) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ('500325', q, y, r, r * 0.1, r * 0.15, r * 0.001)
            )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = FinancialFeatureExtractor(str(financials_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-01-15')

        # Verify all features are present
        assert features.bse_code == '500325'
        assert features.revenue_growth_qoq is not None
        assert features.pat_growth_qoq is not None
        assert features.net_profit_margin is not None

    def test_extract_features_batch(self, tmp_path):
        """AC2.2.7: Extract features for multiple samples"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        # Create test database
        financials_db = tmp_path / "financials.db"
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER,
                revenue REAL,
                pat REAL,
                operating_profit REAL,
                eps REAL
            )
        """)

        # Insert data for 2 companies
        for bse_code in ['500325', '500209']:
            for i, (q, y) in enumerate([('Q4', 2023), ('Q3', 2023), ('Q2', 2023), ('Q1', 2023)]):
                cursor.execute(
                    "INSERT INTO historical_financials (bse_code, quarter, year, revenue, pat, operating_profit, eps) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (bse_code, q, y, 100.0 + i * 10, 10.0 + i, 15.0 + i, 1.0 + i * 0.1)
                )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = FinancialFeatureExtractor(str(financials_db), str(output_db))

        samples = [
            {'sample_id': 1, 'bse_code': '500325', 'date': '2024-01-15'},
            {'sample_id': 2, 'bse_code': '500209', 'date': '2024-01-15'}
        ]

        df = extractor.extract_features_batch(samples)

        assert len(df) == 2
        assert 'revenue_growth_qoq' in df.columns
        assert 'pat_growth_qoq' in df.columns


class TestMissingDataHandling:
    """Test missing data handling (AC2.2.8)"""

    def test_insufficient_data_returns_nan(self, tmp_path):
        """AC2.2.8: Return NaN if <4 quarters of data"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        # Create database with only 2 quarters
        financials_db = tmp_path / "financials.db"
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER,
                revenue REAL,
                pat REAL,
                operating_profit REAL,
                eps REAL
            )
        """)

        # Insert only 2 quarters
        for i, (q, y) in enumerate([('Q1', 2024), ('Q4', 2023)]):
            cursor.execute(
                "INSERT INTO historical_financials (bse_code, quarter, year, revenue, pat, operating_profit, eps) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ('500325', q, y, 100.0, 10.0, 15.0, 1.0)
            )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = FinancialFeatureExtractor(str(financials_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-02-01')

        # YoY and 4Q averages should be NaN
        assert pd.isna(features.revenue_growth_yoy)
        assert pd.isna(features.revenue_growth_avg_4q)

    def test_missing_data_logged(self, tmp_path, caplog):
        """AC2.2.8: Log warning when insufficient data"""
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        # Empty database
        financials_db = tmp_path / "financials.db"
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER,
                revenue REAL,
                pat REAL,
                operating_profit REAL,
                eps REAL
            )
        """)

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = FinancialFeatureExtractor(str(financials_db), str(output_db))

        features = extractor.extract_features_for_sample('500325', '2024-02-01')

        # Should log warning
        assert "Insufficient data" in caplog.text or "No financial data" in caplog.text


class TestPerformance:
    """Test performance requirements (AC2.2.7)"""

    def test_batch_processing_performance(self, tmp_path):
        """AC2.2.7: Process 1000 samples in <10 seconds"""
        import time
        from agents.ml.financial_feature_extractor import FinancialFeatureExtractor

        # Create test database with data for 100 companies
        financials_db = tmp_path / "financials.db"
        conn = sqlite3.connect(str(financials_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE historical_financials (
                bse_code TEXT,
                quarter TEXT,
                year INTEGER,
                revenue REAL,
                pat REAL,
                operating_profit REAL,
                eps REAL
            )
        """)

        # Insert data for 100 companies (10 samples per company)
        for company_idx in range(100):
            bse_code = f"50{company_idx:04d}"
            for q, y in [('Q4', 2023), ('Q3', 2023), ('Q2', 2023), ('Q1', 2023)]:
                cursor.execute(
                    "INSERT INTO historical_financials (bse_code, quarter, year, revenue, pat, operating_profit, eps) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (bse_code, q, y, 100.0, 10.0, 15.0, 1.0)
                )

        conn.commit()
        conn.close()

        output_db = tmp_path / "features.db"
        extractor = FinancialFeatureExtractor(str(financials_db), str(output_db))

        # Create 1000 samples (10 per company)
        samples = []
        for company_idx in range(100):
            bse_code = f"50{company_idx:04d}"
            for sample_idx in range(10):
                samples.append({
                    'sample_id': company_idx * 10 + sample_idx,
                    'bse_code': bse_code,
                    'date': '2024-01-15'
                })

        # Time the batch processing
        start_time = time.time()
        df = extractor.extract_features_batch(samples)
        elapsed_time = time.time() - start_time

        assert len(df) == 1000
        assert elapsed_time < 10.0  # Target: <10 seconds

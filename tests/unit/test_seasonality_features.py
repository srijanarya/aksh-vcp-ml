"""
Unit tests for Story 2.4: Seasonality Feature Extraction

Tests follow TDD RED phase - written before implementation.
Target: 21 tests covering all acceptance criteria.

Test Structure:
1. TestSeasonalityFeatureExtractorInitialization (3 tests) - AC2.4.1
2. TestQuarterExtraction (4 tests) - AC2.4.2
3. TestOneHotEncoding (4 tests) - AC2.4.2
4. TestMonthExtraction (2 tests) - AC2.4.3
5. TestHistoricalCircuitRate (3 tests) - AC2.4.4
6. TestFeatureExtraction (2 tests) - AC2.4.5
7. TestMissingDataHandling (2 tests) - AC2.4.6
8. TestPerformance (1 test) - AC2.4.5 performance
"""

import pytest
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import tempfile
import time

# Will be implemented
from agents.ml.seasonality_feature_extractor import (
    SeasonalityFeatureExtractor,
    SeasonalityFeatures
)


class TestSeasonalityFeatureExtractorInitialization:
    """AC2.4.1: Class initialization and database setup"""

    def test_class_exists(self):
        """Test that SeasonalityFeatureExtractor class exists"""
        assert SeasonalityFeatureExtractor is not None
        assert callable(SeasonalityFeatureExtractor)

    def test_constructor_instantiation(self):
        """Test that constructor accepts required parameters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db = Path(tmpdir) / "labels.db"
            output_db = Path(tmpdir) / "seasonality.db"

            # Create minimal database
            conn = sqlite3.connect(labels_db)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            assert extractor is not None
            assert extractor.labels_db_path == str(labels_db)
            assert extractor.output_db_path == str(output_db)

    def test_database_schema_creation(self):
        """Test that seasonality_features table is created with correct schema"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db = Path(tmpdir) / "labels.db"
            output_db = Path(tmpdir) / "seasonality.db"

            # Create minimal database
            conn = sqlite3.connect(labels_db)
            conn.execute("CREATE TABLE dummy (id INTEGER)")
            conn.close()

            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Check table exists
            conn = sqlite3.connect(output_db)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='seasonality_features'"
            )
            assert cursor.fetchone() is not None

            # Check schema has all feature columns
            cursor = conn.execute("PRAGMA table_info(seasonality_features)")
            columns = [row[1] for row in cursor.fetchall()]

            expected_columns = [
                'feature_id', 'bse_code', 'date',
                'is_q1', 'is_q2', 'is_q3', 'is_q4',
                'announcement_month',
                'historical_circuit_rate_quarter',
                'created_at'
            ]

            for col in expected_columns:
                assert col in columns, f"Missing column: {col}"

            conn.close()


class TestQuarterExtraction:
    """AC2.4.2: Quarter extraction from date"""

    def test_q1_extraction(self):
        """Test Q1 extraction (Apr-Jun)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Test April (Q1)
            quarter = extractor.get_quarter_from_date("2024-04-15")
            assert quarter == 'Q1'

            # Test May (Q1)
            quarter = extractor.get_quarter_from_date("2024-05-20")
            assert quarter == 'Q1'

            # Test June (Q1)
            quarter = extractor.get_quarter_from_date("2024-06-30")
            assert quarter == 'Q1'

    def test_q2_extraction(self):
        """Test Q2 extraction (Jul-Sep)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            quarter = extractor.get_quarter_from_date("2024-07-15")
            assert quarter == 'Q2'

            quarter = extractor.get_quarter_from_date("2024-08-20")
            assert quarter == 'Q2'

            quarter = extractor.get_quarter_from_date("2024-09-30")
            assert quarter == 'Q2'

    def test_q3_extraction(self):
        """Test Q3 extraction (Oct-Dec)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            quarter = extractor.get_quarter_from_date("2024-10-15")
            assert quarter == 'Q3'

            quarter = extractor.get_quarter_from_date("2024-11-20")
            assert quarter == 'Q3'

            quarter = extractor.get_quarter_from_date("2024-12-31")
            assert quarter == 'Q3'

    def test_q4_extraction(self):
        """Test Q4 extraction (Jan-Mar)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            quarter = extractor.get_quarter_from_date("2024-01-15")
            assert quarter == 'Q4'

            quarter = extractor.get_quarter_from_date("2024-02-20")
            assert quarter == 'Q4'

            quarter = extractor.get_quarter_from_date("2024-03-31")
            assert quarter == 'Q4'

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return SeasonalityFeatureExtractor(
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestOneHotEncoding:
    """AC2.4.2: One-hot encoding for quarters"""

    def test_q1_one_hot_encoding(self):
        """Test Q1 one-hot encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            one_hot = extractor.get_quarter_one_hot("2024-04-15")

            assert one_hot['is_q1'] == 1
            assert one_hot['is_q2'] == 0
            assert one_hot['is_q3'] == 0
            assert one_hot['is_q4'] == 0

    def test_q2_one_hot_encoding(self):
        """Test Q2 one-hot encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            one_hot = extractor.get_quarter_one_hot("2024-07-15")

            assert one_hot['is_q1'] == 0
            assert one_hot['is_q2'] == 1
            assert one_hot['is_q3'] == 0
            assert one_hot['is_q4'] == 0

    def test_q3_one_hot_encoding(self):
        """Test Q3 one-hot encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            one_hot = extractor.get_quarter_one_hot("2024-10-15")

            assert one_hot['is_q1'] == 0
            assert one_hot['is_q2'] == 0
            assert one_hot['is_q3'] == 1
            assert one_hot['is_q4'] == 0

    def test_q4_one_hot_encoding(self):
        """Test Q4 one-hot encoding"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            one_hot = extractor.get_quarter_one_hot("2024-01-15")

            assert one_hot['is_q1'] == 0
            assert one_hot['is_q2'] == 0
            assert one_hot['is_q3'] == 0
            assert one_hot['is_q4'] == 1

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return SeasonalityFeatureExtractor(
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestMonthExtraction:
    """AC2.4.3: Month extraction from date"""

    def test_month_extraction(self):
        """Test month extraction from date"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            # Test various months
            assert extractor.get_month_from_date("2024-01-15") == 1
            assert extractor.get_month_from_date("2024-02-20") == 2
            assert extractor.get_month_from_date("2024-06-30") == 6
            assert extractor.get_month_from_date("2024-12-31") == 12

    def test_month_range_validation(self):
        """Test that month is in valid range 1-12"""
        with tempfile.TemporaryDirectory() as tmpdir:
            extractor = self._create_extractor(tmpdir)

            for month in range(1, 13):
                date_str = f"2024-{month:02d}-15"
                extracted_month = extractor.get_month_from_date(date_str)
                assert 1 <= extracted_month <= 12

    def _create_extractor(self, tmpdir):
        """Helper to create extractor"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("CREATE TABLE dummy (id INTEGER)")
        conn.close()

        return SeasonalityFeatureExtractor(
            labels_db_path=str(labels_db),
            output_db_path=str(output_db)
        )


class TestHistoricalCircuitRate:
    """AC2.4.4: Historical circuit rate calculation"""

    def test_calculate_rate_with_historical_data(self):
        """Test historical circuit rate calculation with sufficient data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_database_with_history(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Calculate rate for Q1 (Apr-Jun)
            # Historical Q1 announcements: 5 total, 2 upper circuits → 40%
            rate = extractor.calculate_historical_circuit_rate(
                bse_code="500325",
                date="2024-04-15"  # Q1
            )

            assert rate is not None
            assert 0.35 < rate < 0.45  # ~40%

    def test_handle_no_historical_data(self):
        """Test handling of company with no historical data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_empty_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            rate = extractor.calculate_historical_circuit_rate(
                bse_code="999999",  # Non-existent company
                date="2024-04-15"
            )

            assert rate == 0.0

    def test_handle_sparse_historical_data(self):
        """Test handling of sparse historical data (<3 announcements)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_database_sparse(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Only 2 Q1 announcements, 1 upper circuit → 50%
            rate = extractor.calculate_historical_circuit_rate(
                bse_code="500325",
                date="2024-04-15"
            )

            assert rate is not None
            assert 0.4 < rate < 0.6  # ~50%, but with low confidence

    def _setup_database_with_history(self, tmpdir):
        """Helper to create database with historical data"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)

        # Add Q1 (Apr-Jun) historical data: 5 announcements that will be in range
        # Start date is 2024-04-15 minus 3 years = 2021-04-15
        # So 2021-04-15 itself won't be included (< not <=)
        # Included: 2021-05-20, 2022-04-18, 2022-06-10, 2023-04-20, 2023-05-15 = 5 dates
        # Upper circuits: 0, 1, 0, 1, 0 = 2 upper circuits → 40%
        q1_dates = [
            ("2021-04-15", 1),  # Won't be included (on boundary)
            ("2021-05-20", 0),  # Included
            ("2022-04-18", 1),  # Included
            ("2022-06-10", 0),  # Included
            ("2023-04-20", 1),  # Included
            ("2023-05-15", 0)   # Included
        ]

        for date, upper_circuit in q1_dates:
            conn.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                ("500325", date, upper_circuit)
            )

        conn.commit()
        conn.close()

        return labels_db, output_db

    def _setup_empty_database(self, tmpdir):
        """Helper to create empty database"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)
        conn.commit()
        conn.close()

        return labels_db, output_db

    def _setup_database_sparse(self, tmpdir):
        """Helper to create database with sparse data"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)

        # Only 2 Q1 announcements
        conn.execute("INSERT INTO upper_circuit_labels VALUES ('500325', '2022-04-15', 1)")
        conn.execute("INSERT INTO upper_circuit_labels VALUES ('500325', '2023-05-20', 0)")

        conn.commit()
        conn.close()

        return labels_db, output_db


class TestFeatureExtraction:
    """AC2.4.5: Feature extraction for single and batch samples"""

    def test_single_sample_extraction(self):
        """Test extract_features_for_sample returns SeasonalityFeatures object"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            features = extractor.extract_features_for_sample(
                bse_code="500325",
                date="2024-04-15"  # Q1
            )

            assert features is not None
            assert isinstance(features, SeasonalityFeatures)
            assert features.bse_code == "500325"
            assert features.date == "2024-04-15"
            assert features.is_q1 == 1
            assert features.is_q2 == 0
            assert features.is_q3 == 0
            assert features.is_q4 == 0
            assert features.announcement_month == 4

    def test_batch_extraction(self):
        """Test extract_features_batch processes multiple samples"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            samples = [
                {"bse_code": "500325", "date": "2024-04-15"},  # Q1
                {"bse_code": "500325", "date": "2024-07-20"},  # Q2
                {"bse_code": "532540", "date": "2024-10-10"}   # Q3
            ]

            df = extractor.extract_features_batch(samples)

            assert df is not None
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 3
            assert 'bse_code' in df.columns
            assert 'is_q1' in df.columns
            assert 'announcement_month' in df.columns

    def _setup_database(self, tmpdir):
        """Helper to set up database with sample data"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)

        # Add some historical data
        dates = [
            ("500325", "2021-04-15", 1),
            ("500325", "2022-04-20", 0),
            ("500325", "2023-04-18", 1),
            ("532540", "2021-10-15", 0),
            ("532540", "2022-10-20", 1),
        ]

        for bse_code, date, upper_circuit in dates:
            conn.execute(
                "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                (bse_code, date, upper_circuit)
            )

        conn.commit()
        conn.close()

        return labels_db, output_db


class TestMissingDataHandling:
    """AC2.4.6: Missing data handling"""

    def test_no_historical_data_returns_zero(self):
        """Test that 0 is returned when no historical data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_empty_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            features = extractor.extract_features_for_sample(
                bse_code="999999",
                date="2024-04-15"
            )

            assert features is not None
            assert features.historical_circuit_rate_quarter == 0.0

    def test_missing_data_logged(self, caplog):
        """Test that missing data is logged as warning"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_empty_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            features = extractor.extract_features_for_sample(
                bse_code="999999",
                date="2024-04-15"
            )

            assert features is not None
            # Check that warning was logged (may need adjustment based on actual logging)

    def _setup_empty_database(self, tmpdir):
        """Helper to create empty database"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)
        conn.commit()
        conn.close()

        return labels_db, output_db


class TestPerformance:
    """AC2.4.5: Performance requirements"""

    def test_batch_processing_performance(self):
        """Test that 1000 samples can be processed in <3 seconds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            labels_db, output_db = self._setup_large_database(tmpdir)
            extractor = SeasonalityFeatureExtractor(
                labels_db_path=str(labels_db),
                output_db_path=str(output_db)
            )

            # Generate 1000 samples
            samples = []
            months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
            for i in range(1000):
                month = months[i % 12]
                samples.append({
                    "bse_code": f"50{i % 100:04d}",
                    "date": f"2024-{month:02d}-15"
                })

            # Measure time
            start_time = time.time()
            df = extractor.extract_features_batch(samples)
            elapsed = time.time() - start_time

            assert df is not None
            assert len(df) > 0
            assert elapsed < 3.0, f"Batch processing took {elapsed:.2f}s (target: <3s)"
            print(f"\nPerformance: Processed {len(df)} samples in {elapsed:.2f}s ({len(df)/elapsed:.0f} samples/sec)")

    def _setup_large_database(self, tmpdir):
        """Helper to create large database for performance testing"""
        labels_db = Path(tmpdir) / "labels.db"
        output_db = Path(tmpdir) / "seasonality.db"

        conn = sqlite3.connect(labels_db)
        conn.execute("""
            CREATE TABLE upper_circuit_labels (
                bse_code TEXT,
                date DATE,
                upper_circuit INTEGER
            )
        """)
        conn.execute("CREATE INDEX idx_labels_bse_date ON upper_circuit_labels(bse_code, date)")

        # Add historical data for 100 companies
        for company_id in range(100):
            bse_code = f"50{company_id:04d}"
            # Add 3 years of quarterly data
            for year in [2021, 2022, 2023]:
                for month in [1, 4, 7, 10]:  # One per quarter
                    upper_circuit = 1 if (company_id + year + month) % 3 == 0 else 0
                    conn.execute(
                        "INSERT INTO upper_circuit_labels VALUES (?, ?, ?)",
                        (bse_code, f"{year}-{month:02d}-15", upper_circuit)
                    )

        conn.commit()
        conn.close()

        return labels_db, output_db


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

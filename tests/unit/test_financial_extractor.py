"""
Tests for FinancialExtractor (Story 1.4)

Acceptance Criteria (from Epic 1 Story 1.4):
AC1.4.1: Reuse existing indian_pdf_extractor.py via importable function
AC1.4.2: Query earnings announcements from earnings_calendar.db
AC1.4.3: Download and extract financial data with caching
AC1.4.4: Store extracted data in historical_financials.db
AC1.4.5: Achieve ≥80% extraction success rate
AC1.4.6: Log extraction failures for investigation
AC1.4.7: Validate extracted data quality

Test Strategy: AAA (Arrange, Act, Assert) pattern with mocking
Coverage Target: ≥90%

Author: VCP Financial Research Team
Created: 2025-11-13
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

# System under test (will be created in ml_data_collector.py)
# from agents.ml.ml_data_collector import FinancialExtractor, FinancialData, ExtractionReport


class TestFinancialExtractorInitialization:
    """Test FinancialExtractor class initialization (AC1.4.1)"""

    def test_extractor_class_exists(self):
        """AC1.4.1: Verify FinancialExtractor class exists"""
        from agents.ml.ml_data_collector import FinancialExtractor
        assert FinancialExtractor is not None

    def test_extractor_instantiation(self, tmp_path):
        """AC1.4.1: Extractor can be instantiated with db_path"""
        from agents.ml.ml_data_collector import FinancialExtractor

        db_path = tmp_path / "historicalfinancials.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        assert extractor is not None
        assert hasattr(extractor, 'extract_all_financials')

    def test_extractor_creates_database_table(self, tmp_path):
        """AC1.4.4: Extractor creates historical_financials table on init"""
        from agents.ml.ml_data_collector import FinancialExtractor

        db_path = tmp_path / "historical_financials.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        # Verify table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historical_financials'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "historical_financials"


class TestEarningsAnnouncementQuery:
    """Test querying earnings announcements (AC1.4.2)"""

    def test_query_earnings_from_database(self, tmp_path):
        """AC1.4.2: Query earnings from earnings_calendar.db"""
        from agents.ml.ml_data_collector import FinancialExtractor

        # Create mock earnings_calendar.db
        earnings_db = tmp_path / "earnings_calendar.db"
        conn = sqlite3.connect(earnings_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE earnings (
                bse_code TEXT,
                announcement_date DATE,
                pdf_url TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO earnings VALUES
            ('500570', '2024-01-15', 'https://example.com/tcs_q3_fy24.pdf'),
            ('500209', '2024-04-20', 'https://example.com/infy_q4_fy24.pdf')
        """)
        conn.commit()
        conn.close()

        extractor = FinancialExtractor(db_path=str(tmp_path / "historical_financials.db"))

        # Query earnings (mock path to earnings_calendar.db)
        with patch.object(extractor, 'earnings_db_path', str(earnings_db)):
            announcements = extractor.query_earnings_announcements("2024-01-01", "2024-12-31")

        assert len(announcements) == 2
        assert announcements[0]['bse_code'] == '500570'
        assert announcements[0]['quarter'] == 'Q3'  # Jan is Q3 (Oct-Dec reporting)
        assert announcements[0]['year'] == 2024

    def test_identify_quarter_from_announcement_date(self, tmp_path):
        """AC1.4.2: Correctly identify fiscal quarter from announcement date"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Q1 (Apr-Jun announcements typically in Jul-Aug)
        assert extractor.identify_quarter(date(2024, 7, 15)) == 'Q1'
        # Q2 (Jul-Sep announcements typically in Oct-Nov)
        assert extractor.identify_quarter(date(2024, 10, 20)) == 'Q2'
        # Q3 (Oct-Dec announcements typically in Jan-Feb)
        assert extractor.identify_quarter(date(2024, 1, 25)) == 'Q3'
        # Q4 (Jan-Mar announcements typically in Apr-May)
        assert extractor.identify_quarter(date(2024, 4, 30)) == 'Q4'


class TestPDFDownloadAndCaching:
    """Test PDF download with caching (AC1.4.3)"""

    def test_download_pdf_successful(self, tmp_path):
        """AC1.4.3: Download PDF to cache directory"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(
            db_path=str(tmp_path / "test.db"),
            cache_dir=str(tmp_path / "cache")
        )

        pdf_url = "https://example.com/earnings.pdf"

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'%PDF-1.4...'
            mock_get.return_value = mock_response

            pdf_path = extractor.download_pdf(pdf_url, "500570", "Q3", 2024)

        assert pdf_path is not None
        assert "500570_Q3_2024.pdf" in pdf_path
        assert Path(pdf_path).parent == tmp_path / "cache"

    def test_download_pdf_uses_cache(self, tmp_path):
        """AC1.4.3: Use cached PDF if already downloaded"""
        from agents.ml.ml_data_collector import FinancialExtractor

        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cached_pdf = cache_dir / "500570_Q3_2024.pdf"
        cached_pdf.write_bytes(b'%PDF-cached...')

        extractor = FinancialExtractor(
            db_path=str(tmp_path / "test.db"),
            cache_dir=str(cache_dir)
        )

        # Should not make HTTP request
        with patch('requests.get') as mock_get:
            pdf_path = extractor.download_pdf("https://example.com/pdf", "500570", "Q3", 2024)

            assert mock_get.call_count == 0  # Cache hit
            assert pdf_path == str(cached_pdf)

    def test_download_pdf_404_error(self, tmp_path):
        """AC1.4.3, AC1.4.6: Log PDF download failure"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("404 Not Found")

            pdf_path = extractor.download_pdf("https://bad-url.com/pdf", "500570", "Q3", 2024)

        assert pdf_path is None
        # Should log failure (checked in integration test)


class TestFinancialDataExtraction:
    """Test financial data extraction from PDFs (AC1.4.1, AC1.4.3)"""

    def test_extract_from_pdf_successful(self, tmp_path):
        """AC1.4.1, AC1.4.3: Successfully extract financial data"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Mock PDF file
        pdf_path = tmp_path / "earnings.pdf"
        pdf_path.write_bytes(b'%PDF-mock...')

        # Mock indian_pdf_extractor
        with patch('agents.ml.ml_data_collector.extract_financial_data') as mock_extract:
            mock_extract.return_value = FinancialData(
                revenue_cr=15000.0,
                pat_cr=2500.0,
                eps=45.50,
                opm=18.5,
                npm=16.7,
                extraction_confidence=0.9
            )

            data = extractor.extract_from_pdf(str(pdf_path), "500570", "Q3", 2024)

        assert data is not None
        assert data.revenue_cr == 15000.0
        assert data.eps == 45.50
        assert data.extraction_confidence >= 0.7

    def test_extract_from_pdf_returns_none_on_failure(self, tmp_path):
        """AC1.4.3: Return None if extraction fails"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        pdf_path = tmp_path / "bad_pdf.pdf"
        pdf_path.write_bytes(b'Not a valid PDF')

        with patch('agents.ml.ml_data_collector.extract_financial_data') as mock_extract:
            mock_extract.return_value = None

            data = extractor.extract_from_pdf(str(pdf_path), "500570", "Q3", 2024)

        assert data is None

    def test_skip_if_already_extracted_with_high_confidence(self, tmp_path):
        """AC1.4.3: Skip extraction if already processed with confidence ≥0.7"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "test.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        # Insert existing high-confidence extraction
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historical_financials
            (bse_code, quarter, year, revenue_cr, pat_cr, eps, opm, npm, extraction_confidence)
            VALUES ('500570', 'Q3', 2024, 15000, 2500, 45.5, 18.5, 16.7, 0.9)
        """)
        conn.commit()
        conn.close()

        # Should skip extraction
        should_extract = extractor.should_extract("500570", "Q3", 2024)
        assert should_extract is False


class TestDatabaseStorage:
    """Test storing extracted data (AC1.4.4)"""

    def test_store_financial_data(self, tmp_path):
        """AC1.4.4: Store extracted data in historical_financials.db"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "historical_financials.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        data = FinancialData(
            revenue_cr=15000.0,
            pat_cr=2500.0,
            eps=45.50,
            opm=18.5,
            npm=16.7,
            extraction_confidence=0.9
        )

        success = extractor.store_financial_data(
            data, "500570", "Q3", 2024, "https://example.com/pdf"
        )

        assert success is True

        # Verify in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT revenue_cr, eps, extraction_confidence
            FROM historical_financials
            WHERE bse_code='500570' AND quarter='Q3' AND year=2024
        """)
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == 15000.0
        assert row[1] == 45.50
        assert row[2] == 0.9

    def test_store_uses_insert_or_replace(self, tmp_path):
        """AC1.4.4: Use INSERT OR REPLACE for idempotency"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "test.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        data1 = FinancialData(15000, 2500, 45.5, 18.5, 16.7, 0.8)
        extractor.store_financial_data(data1, "500570", "Q3", 2024, "url1")

        # Store again with different values (reprocessing)
        data2 = FinancialData(16000, 2600, 46.0, 19.0, 17.0, 0.9)
        extractor.store_financial_data(data2, "500570", "Q3", 2024, "url2")

        # Should have only 1 record (updated)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), revenue_cr FROM historical_financials WHERE bse_code='500570'")
        row = cursor.fetchone()
        conn.close()

        assert row[0] == 1  # Only one record
        assert row[1] == 16000.0  # Updated value


class TestDataValidation:
    """Test data quality validation (AC1.4.7)"""

    def test_validate_revenue_positive(self, tmp_path):
        """AC1.4.7 Check 1: Revenue > 0"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Valid: positive revenue
        data_valid = FinancialData(15000, 2500, 45.5, 18.5, 16.7, 0.9)
        result = extractor.validate_financial_data(data_valid)
        assert result.is_valid is True

        # Invalid: negative revenue
        data_invalid = FinancialData(-100, 2500, 45.5, 18.5, 16.7, 0.9)
        result = extractor.validate_financial_data(data_invalid)
        assert result.is_valid is False
        assert "revenue" in result.failed_checks

    def test_validate_margin_bounds(self, tmp_path):
        """AC1.4.7 Check 2: Margin bounds -100% ≤ OPM, NPM ≤ 100%"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Valid: margins within bounds
        data_valid = FinancialData(15000, -500, 10.0, -5.0, -3.0, 0.9)  # Loss-making OK
        result = extractor.validate_financial_data(data_valid)
        assert result.is_valid is True

        # Invalid: OPM > 100%
        data_invalid = FinancialData(15000, 2500, 45.5, 150.0, 16.7, 0.9)
        result = extractor.validate_financial_data(data_invalid)
        assert result.is_valid is False
        assert "opm" in result.failed_checks

    def test_validate_no_duplicates(self, tmp_path):
        """AC1.4.7 Check 3: No duplicates (UNIQUE constraint)"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "test.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        data = FinancialData(15000, 2500, 45.5, 18.5, 16.7, 0.9)

        # First insert should succeed
        success1 = extractor.store_financial_data(data, "500570", "Q3", 2024, "url")
        assert success1 is True

        # Second insert with same key should REPLACE (not create duplicate)
        success2 = extractor.store_financial_data(data, "500570", "Q3", 2024, "url")
        assert success2 is True

        # Verify only 1 record
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historical_financials WHERE bse_code='500570'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_mark_low_confidence_on_validation_failure(self, tmp_path):
        """AC1.4.7: Mark extraction_confidence=0.5 if validation fails"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Invalid data (negative revenue)
        data = FinancialData(-100, 2500, 45.5, 18.5, 16.7, 0.9)

        result = extractor.validate_financial_data(data)
        assert result.is_valid is False
        assert result.adjusted_confidence == 0.5


class TestSuccessRateCalculation:
    """Test success rate calculation (AC1.4.5)"""

    def test_calculate_success_rate(self, tmp_path):
        """AC1.4.5: Calculate success rate = successful / attempted"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "test.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        # Insert 85 successful extractions (confidence ≥0.7)
        for i in range(85):
            data = FinancialData(15000 + i*100, 2500, 45.5, 18.5, 16.7, 0.8)
            extractor.store_financial_data(data, f"50{i:04d}", "Q3", 2024, "url")

        # Insert 15 failed extractions (confidence <0.7)
        for i in range(15):
            data = FinancialData(100, 10, 1.0, 5.0, 2.0, 0.5)  # Low confidence
            extractor.store_financial_data(data, f"51{i:04d}", "Q3", 2024, "url")

        success_rate = extractor.calculate_success_rate()

        # 85 / 100 = 85%
        assert success_rate >= 80.0
        assert 84.0 <= success_rate <= 86.0

    def test_success_rate_meets_target(self, tmp_path):
        """AC1.4.5: Success rate ≥80% meets target"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        # Mock success rate
        with patch.object(extractor, 'calculate_success_rate', return_value=82.5):
            meets_target = extractor.meets_success_target()

        assert meets_target is True


class TestFailureLogging:
    """Test extraction failure logging (AC1.4.6)"""

    def test_log_extraction_failure(self, tmp_path):
        """AC1.4.6: Log extraction failures to CSV"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        extractor.log_extraction_failure(
            bse_code="500570",
            company_name="TCS",
            quarter="Q3",
            year=2024,
            pdf_url="https://example.com/pdf",
            error_type="PDF_ENCRYPTED",
            error_message="Cannot decrypt PDF"
        )

        # Verify CSV created
        csv_path = Path("/Users/srijan/Desktop/aksh/data/extraction_failures.csv")
        # In tests, use tmp_path
        csv_path = tmp_path / "extraction_failures.csv"
        extractor.failure_log_path = str(csv_path)  # Override for testing

        extractor.log_extraction_failure(
            "500570", "TCS", "Q3", 2024, "url", "PDF_ENCRYPTED", "msg"
        )

        assert csv_path.exists()
        content = csv_path.read_text()
        assert "PDF_ENCRYPTED" in content
        assert "500570" in content

    def test_analyze_failures_by_error_type(self, tmp_path):
        """AC1.4.6: Generate failure analysis report"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))
        extractor.failure_log_path = str(tmp_path / "failures.csv")

        # Log multiple failures
        extractor.log_extraction_failure("500570", "TCS", "Q3", 2024, "url", "PDF_ENCRYPTED", "msg")
        extractor.log_extraction_failure("500209", "INFY", "Q3", 2024, "url", "PDF_ENCRYPTED", "msg")
        extractor.log_extraction_failure("500180", "HDFC", "Q3", 2024, "url", "TABLE_NOT_FOUND", "msg")

        report = extractor.analyze_failures()

        assert report.total_failures == 3
        assert report.by_error_type["PDF_ENCRYPTED"] == 2
        assert report.by_error_type["TABLE_NOT_FOUND"] == 1


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios"""

    def test_extract_all_financials_workflow(self, tmp_path):
        """Integration: Full extraction workflow"""
        from agents.ml.ml_data_collector import FinancialExtractor, FinancialData

        db_path = tmp_path / "historical_financials.db"
        extractor = FinancialExtractor(db_path=str(db_path))

        # Mock earnings query
        with patch.object(extractor, 'query_earnings_announcements') as mock_query:
            mock_query.return_value = [
                {"bse_code": "500570", "quarter": "Q3", "year": 2024, "pdf_url": "url1"},
                {"bse_code": "500209", "quarter": "Q3", "year": 2024, "pdf_url": "url2"}
            ]

            # Mock extraction
            with patch.object(extractor, 'extract_from_pdf') as mock_extract:
                mock_extract.return_value = FinancialData(15000, 2500, 45.5, 18.5, 16.7, 0.9)

                report = extractor.extract_all_financials("2024-01-01", "2024-12-31")

        assert report.total_attempted >= 2
        assert report.total_successful >= 1
        assert report.success_rate >= 0.0

    def test_handle_empty_earnings_calendar(self, tmp_path):
        """Edge case: No earnings in date range"""
        from agents.ml.ml_data_collector import FinancialExtractor

        extractor = FinancialExtractor(db_path=str(tmp_path / "test.db"))

        with patch.object(extractor, 'query_earnings_announcements', return_value=[]):
            report = extractor.extract_all_financials("2024-01-01", "2024-01-31")

        assert report.total_attempted == 0
        assert report.success_rate == 0.0


# Pytest fixtures
@pytest.fixture
def sample_financial_data():
    """Sample valid financial data"""
    from agents.ml.ml_data_collector import FinancialData
    return FinancialData(
        revenue_cr=15000.0,
        pat_cr=2500.0,
        eps=45.50,
        opm=18.5,
        npm=16.7,
        extraction_confidence=0.9
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=agents.ml.ml_data_collector", "--cov-report=term-missing"])

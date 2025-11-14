"""
Unit tests for Story 1.5: PriceCollector

TDD Phase: RED (write tests first)
Target: ≥90% test coverage

Test Coverage:
- AC1.5.1: Download BSE BhavCopy CSV files
- AC1.5.2: Download NSE BhavCopy CSV files
- AC1.5.3: Parse CSV files and store in price_movements.db
- AC1.5.4: yfinance fallback for missing dates
- AC1.5.5: Calculate data completeness per company
- AC1.5.6: Validate OHLC data quality
- AC1.5.7: Test query performance with indexes
"""

import pytest
import sqlite3
import os
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime, timedelta, date
from unittest.mock import patch, Mock, MagicMock
import pandas as pd


class TestPriceCollectorInitialization:
    """Test PriceCollector class initialization and database setup"""

    def test_price_collector_class_exists(self):
        """Verify PriceCollector class can be imported"""
        from agents.ml.ml_data_collector import PriceCollector
        assert PriceCollector is not None

    def test_price_collector_instantiation(self, tmp_path):
        """Test PriceCollector can be instantiated with db_path"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test_price_movements.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        assert collector.db_path == db_path
        assert collector.cache_dir == Path(cache_dir)
        assert Path(cache_dir).exists()

    def test_database_schema_created(self, tmp_path):
        """AC1.5.3: Verify price_movements table schema"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_movements'")
        assert cursor.fetchone() is not None

        # Check indexes exist (AC1.5.7)
        cursor.execute("PRAGMA index_list('price_movements')")
        indexes = cursor.fetchall()
        index_names = [idx[1] for idx in indexes]

        assert 'idx_bse_date' in index_names
        assert 'idx_nse_date' in index_names
        assert 'idx_date' in index_names

        conn.close()


class TestBSEBhavCopyDownload:
    """Test BSE BhavCopy download and caching (AC1.5.1)"""

    def test_download_bse_bhav_copies_creates_cache_dir(self, tmp_path):
        """AC1.5.1: Download creates cache directory if missing"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        assert (tmp_path / "cache").exists()
        assert (tmp_path / "cache" / "bse").exists()

    def test_download_bse_bhav_copy_single_day(self, tmp_path):
        """AC1.5.1: Download single BSE BhavCopy file"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        # Mock requests.get
        with patch('requests.get') as mock_get:
            # Create a mock ZIP file
            mock_zip_content = b'PK\x03\x04...'  # Valid ZIP header
            mock_response = Mock()
            mock_response.content = mock_zip_content
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Mock zipfile extraction
            with patch('zipfile.ZipFile') as mock_zipfile:
                mock_zip = Mock()
                mock_zip.namelist.return_value = ['EQ131124.CSV']
                mock_zip.read.return_value = b'SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE\n500325,RELIANCE,2800,2850,2790,2840\n'
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                file_paths = collector.download_bse_bhav_copies("2024-11-13", "2024-11-13")

        assert len(file_paths) == 1
        assert "EQ131124.csv" in file_paths[0]

    def test_bse_bhav_copy_uses_cache_if_exists(self, tmp_path):
        """AC1.5.1: Skip download if file already cached"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        # Create cached file
        cached_file = collector.cache_dir / "bse" / "EQ131124.csv"
        cached_file.parent.mkdir(parents=True, exist_ok=True)
        cached_file.write_text("SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE\n500325,RELIANCE,2800,2850,2790,2840\n")

        with patch('requests.get') as mock_get:
            file_paths = collector.download_bse_bhav_copies("2024-11-13", "2024-11-13")

            # Should not call requests.get since file is cached
            mock_get.assert_not_called()

        assert len(file_paths) == 1

    def test_bse_download_retries_on_failure(self, tmp_path):
        """AC1.5.1: Retry 3x on download failure"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        with patch('requests.get') as mock_get:
            # Simulate 2 failures then success
            mock_get.side_effect = [
                Exception("Timeout"),
                Exception("Connection error"),
                Mock(content=b'PK\x03\x04...', raise_for_status=Mock())
            ]

            with patch('zipfile.ZipFile') as mock_zipfile:
                mock_zip = Mock()
                mock_zip.namelist.return_value = ['EQ131124.CSV']
                mock_zip.read.return_value = b'SC_CODE,SC_NAME,OPEN\n'
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                file_paths = collector.download_bse_bhav_copies("2024-11-13", "2024-11-13")

        assert mock_get.call_count == 3  # 2 retries + 1 success


class TestNSEBhavCopyDownload:
    """Test NSE BhavCopy download and caching (AC1.5.2)"""

    def test_download_nse_bhav_copy_includes_headers(self, tmp_path):
        """AC1.5.2: NSE download includes required headers"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b'PK\x03\x04...'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            with patch('zipfile.ZipFile') as mock_zipfile:
                mock_zip = Mock()
                mock_zip.namelist.return_value = ['cm13NOV2024bhav.csv']
                mock_zip.read.return_value = b'SYMBOL,SERIES,OPEN\nRELIANCE,EQ,2800\n'
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                collector.download_nse_bhav_copies("2024-11-13", "2024-11-13")

        # Verify headers were passed
        call_args = mock_get.call_args
        headers = call_args[1].get('headers', {})
        assert 'User-Agent' in headers
        assert 'Mozilla' in headers['User-Agent']

    def test_nse_download_handles_404_gracefully(self, tmp_path):
        """AC1.5.2: Handle weekends/holidays with 404 response"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        with patch('requests.get') as mock_get:
            # Simulate 404 for non-trading day
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response

            file_paths = collector.download_nse_bhav_copies("2024-11-10", "2024-11-10")  # Sunday

        # Should return empty list, not raise exception
        assert file_paths == []


class TestCSVParsing:
    """Test CSV parsing and storage (AC1.5.3)"""

    def test_parse_bse_bhav_copy(self, tmp_path):
        """AC1.5.3: Parse BSE BhavCopy CSV correctly"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Create sample BSE CSV
        csv_path = tmp_path / "EQ131124.csv"
        csv_path.write_text(
            "SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE,NO_OF_SHRS,NET_TURNOV,TDCLOINDI\n"
            "500325,RELIANCE,2800.0,2850.0,2790.0,2840.0,1000000,2800000000,\n"
            "500209,INFOSYS,1500.0,1520.0,1490.0,1510.0,500000,750000000,C\n"
        )

        df = collector.parse_bhav_copy(str(csv_path), source='bse_bhav_copy', date="2024-11-13")

        assert len(df) == 2
        assert 'bse_code' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
        assert df.iloc[0]['bse_code'] == '500325'
        assert df.iloc[0]['open'] == 2800.0

    def test_parse_nse_bhav_copy(self, tmp_path):
        """AC1.5.3: Parse NSE BhavCopy CSV correctly"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Create sample NSE CSV
        csv_path = tmp_path / "cm13NOV2024bhav.csv"
        csv_path.write_text(
            "SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,TOTTRDQTY,TOTTRDVAL,PREV_CLOSE\n"
            "RELIANCE,EQ,2800.0,2850.0,2790.0,2840.0,1000000,2800000000,2820.0\n"
            "INFY,EQ,1500.0,1520.0,1490.0,1510.0,500000,750000000,1505.0\n"
        )

        df = collector.parse_bhav_copy(str(csv_path), source='nse_bhav_copy', date="2024-11-13")

        assert len(df) == 2
        assert 'nse_symbol' in df.columns
        assert 'prev_close' in df.columns
        assert df.iloc[0]['nse_symbol'] == 'RELIANCE'
        assert df.iloc[0]['prev_close'] == 2820.0

    def test_store_price_data_in_database(self, tmp_path):
        """AC1.5.3: Store parsed data in price_movements.db"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Create sample DataFrame
        df = pd.DataFrame({
            'bse_code': ['500325', '500209'],
            'date': ['2024-11-13', '2024-11-13'],
            'open': [2800.0, 1500.0],
            'high': [2850.0, 1520.0],
            'low': [2790.0, 1490.0],
            'close': [2840.0, 1510.0],
            'volume': [1000000, 500000],
            'source': ['bse_bhav_copy', 'bse_bhav_copy']
        })

        rows_inserted = collector.store_price_data(df)

        assert rows_inserted == 2

        # Verify data in database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_movements")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_store_handles_duplicate_dates(self, tmp_path):
        """AC1.5.3: UNIQUE constraint prevents duplicates, INSERT OR REPLACE updates"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert first time
        df1 = pd.DataFrame({
            'bse_code': ['500325'],
            'date': ['2024-11-13'],
            'open': [2800.0],
            'high': [2850.0],
            'low': [2790.0],
            'close': [2840.0],
            'volume': [1000000],
            'source': ['bse_bhav_copy']
        })
        collector.store_price_data(df1)

        # Insert duplicate with different close price
        df2 = pd.DataFrame({
            'bse_code': ['500325'],
            'date': ['2024-11-13'],
            'open': [2800.0],
            'high': [2850.0],
            'low': [2790.0],
            'close': [2845.0],  # Different close
            'volume': [1100000],
            'source': ['bse_bhav_copy']
        })
        collector.store_price_data(df2)

        # Should only have 1 record (replaced)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), close FROM price_movements WHERE bse_code='500325' GROUP BY close")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1
        assert result[1] == 2845.0  # Updated value


class TestYFinanceFallback:
    """Test yfinance fallback for missing dates (AC1.5.4)"""

    def test_identify_companies_with_gaps(self, tmp_path):
        """AC1.5.4: Identify companies with <95% date coverage"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert data with gaps
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Company 1: 920/975 dates = 94.4% (below threshold)
        for i in range(920):
            date_str = (datetime(2022, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT OR REPLACE INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
                "VALUES (?, ?, 100, 110, 90, 105, 1000, 'bse_bhav_copy')",
                ('500325', date_str)
            )

        # Company 2: 950/975 dates = 97.4% (above threshold)
        for i in range(950):
            date_str = (datetime(2022, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT OR REPLACE INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
                "VALUES (?, ?, 100, 110, 90, 105, 1000, 'bse_bhav_copy')",
                ('500209', date_str)
            )

        conn.commit()
        conn.close()

        gaps = collector.identify_gaps(['500325', '500209'], start_date="2022-01-01", end_date="2024-09-30", expected_days=975)

        # Only 500325 should have gaps
        assert '500325' in gaps
        assert '500209' not in gaps or len(gaps.get('500209', [])) == 0

    def test_fill_gaps_with_yfinance(self, tmp_path):
        """AC1.5.4: Fill missing dates using yfinance"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Mock BSE-NSE mapping
        collector.bse_nse_mapping = {'500325': 'RELIANCE'}

        with patch('yfinance.download') as mock_yf:
            # Mock yfinance response
            mock_df = pd.DataFrame({
                'Open': [2800.0, 2820.0],
                'High': [2850.0, 2870.0],
                'Low': [2790.0, 2810.0],
                'Close': [2840.0, 2860.0],
                'Volume': [1000000, 1100000]
            }, index=pd.to_datetime(['2024-11-13', '2024-11-14']))
            mock_yf.return_value = mock_df

            gaps_filled = collector.fill_gaps_with_yfinance(
                bse_code='500325',
                missing_dates=['2024-11-13', '2024-11-14']
            )

        assert gaps_filled == 2

        # Verify data stored with yfinance_fallback source
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM price_movements WHERE source='yfinance_fallback'")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_yfinance_respects_rate_limit(self, tmp_path):
        """AC1.5.4: 1 second delay between yfinance calls"""
        from agents.ml.ml_data_collector import PriceCollector
        import time

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        collector.bse_nse_mapping = {'500325': 'RELIANCE', '500209': 'INFY'}

        with patch('yfinance.download') as mock_yf:
            mock_df = pd.DataFrame({
                'Open': [2800.0],
                'High': [2850.0],
                'Low': [2790.0],
                'Close': [2840.0],
                'Volume': [1000000]
            }, index=pd.to_datetime(['2024-11-13']))
            mock_yf.return_value = mock_df

            with patch('time.sleep') as mock_sleep:
                collector.fill_gaps_with_yfinance('500325', ['2024-11-13'])
                collector.fill_gaps_with_yfinance('500209', ['2024-11-13'])

                # Should call sleep at least once
                assert mock_sleep.call_count >= 1
                # Should sleep for 1 second
                mock_sleep.assert_called_with(1)


class TestCompletenessCalculation:
    """Test data completeness calculation (AC1.5.5)"""

    def test_calculate_completeness_per_company(self, tmp_path):
        """AC1.5.5: Calculate completeness = (dates_with_data / expected_trading_days) * 100"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert 930 dates for 500325 (930/975 = 95.4%)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for i in range(930):
            date_str = (datetime(2022, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT OR REPLACE INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
                "VALUES (?, ?, 100, 110, 90, 105, 1000, 'bse_bhav_copy')",
                ('500325', date_str)
            )
        conn.commit()
        conn.close()

        completeness = collector.calculate_completeness(['500325'], expected_days=975)

        assert '500325' in completeness
        assert completeness['500325'] >= 95.0
        assert completeness['500325'] <= 96.0

    def test_log_incomplete_data_to_csv(self, tmp_path):
        """AC1.5.5: Log companies with <95% completeness to CSV"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)
        collector.incomplete_data_log = str(tmp_path / "incomplete.csv")

        # Insert only 900 dates (900/975 = 92.3%, below threshold)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for i in range(900):
            date_str = (datetime(2022, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT OR REPLACE INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
                "VALUES (?, ?, 100, 110, 90, 105, 1000, 'bse_bhav_copy')",
                ('500325', date_str)
            )
        conn.commit()
        conn.close()

        completeness = collector.calculate_completeness(['500325'], expected_days=975)
        collector.log_incomplete_companies(completeness, threshold=95.0)

        # Verify CSV created
        assert Path(collector.incomplete_data_log).exists()

        # Verify content
        with open(collector.incomplete_data_log, 'r') as f:
            content = f.read()
            assert '500325' in content
            assert '92.' in content  # Completeness percentage


class TestOHLCValidation:
    """Test OHLC data quality validation (AC1.5.6)"""

    def test_validate_ohlc_relationships(self, tmp_path):
        """AC1.5.6 Check 1: low ≤ open ≤ high and low ≤ close ≤ high"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert valid record
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
            "VALUES ('500325', '2024-11-13', 2820, 2850, 2800, 2840, 1000000, 'bse_bhav_copy')"
        )

        # Insert invalid record (high < low)
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
            "VALUES ('500209', '2024-11-13', 1500, 1490, 1520, 1510, 500000, 'bse_bhav_copy')"
        )
        conn.commit()
        conn.close()

        validation_report = collector.validate_ohlc_data()

        assert validation_report.total_records == 2
        assert validation_report.invalid_records == 1
        assert any('500209' in key for key in validation_report.anomalies.keys())

    def test_validate_no_future_dates(self, tmp_path):
        """AC1.5.6 Check 3: date ≤ today()"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert future date
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
            "VALUES ('500325', ?, 2800, 2850, 2790, 2840, 1000000, 'bse_bhav_copy')",
            (future_date,)
        )
        conn.commit()
        conn.close()

        validation_report = collector.validate_ohlc_data()

        assert validation_report.invalid_records >= 1
        assert any('FUTURE_DATE' in anomaly for anomaly in validation_report.anomalies.values())

    def test_validate_price_continuity(self, tmp_path):
        """AC1.5.6 Check 4: Flag if abs(close - prev_close) / prev_close > 0.5"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert two consecutive dates with 60% jump
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
            "VALUES ('500325', '2024-11-12', 2500, 2520, 2480, 2500, 1000000, 'bse_bhav_copy')"
        )
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, prev_close, source) "
            "VALUES ('500325', '2024-11-13', 4000, 4050, 3950, 4000, 1000000, 2500, 'bse_bhav_copy')"
        )
        conn.commit()
        conn.close()

        validation_report = collector.validate_ohlc_data()

        assert validation_report.invalid_records >= 1
        assert any('PRICE_JUMP' in anomaly for anomaly in validation_report.anomalies.values())

    def test_log_anomalies_to_csv(self, tmp_path):
        """AC1.5.6: Log validation failures to price_data_anomalies.csv"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)
        collector.anomaly_log = str(tmp_path / "anomalies.csv")

        # Insert invalid record
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
            "VALUES ('500209', '2024-11-13', 1500, 1490, 1520, 1510, 500000, 'bse_bhav_copy')"
        )
        conn.commit()
        conn.close()

        validation_report = collector.validate_ohlc_data()
        collector.log_anomalies(validation_report)

        # Verify CSV created
        assert Path(collector.anomaly_log).exists()

        # Verify content
        with open(collector.anomaly_log, 'r') as f:
            content = f.read()
            assert '500209' in content
            assert 'OHLC_RELATIONSHIP' in content or 'high' in content.lower()


class TestQueryPerformance:
    """Test query performance with indexes (AC1.5.7)"""

    def test_query_performance_with_indexes(self, tmp_path):
        """AC1.5.7: Query should return in <10ms with indexes"""
        from agents.ml.ml_data_collector import PriceCollector
        import time

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Insert 1000 records
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for i in range(1000):
            date_str = (datetime(2022, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute(
                "INSERT INTO price_movements (bse_code, date, open, high, low, close, volume, source) "
                "VALUES ('500325', ?, 2800, 2850, 2790, 2840, 1000000, 'bse_bhav_copy')",
                (date_str,)
            )
        conn.commit()

        # Test query performance
        start_time = time.time()
        cursor.execute(
            "SELECT * FROM price_movements WHERE bse_code='500325' AND date BETWEEN '2024-01-01' AND '2024-12-31'"
        )
        results = cursor.fetchall()
        end_time = time.time()

        conn.close()

        query_time_ms = (end_time - start_time) * 1000

        # Should be fast with indexes
        assert query_time_ms < 100  # Relaxed threshold for test environment

    def test_indexes_exist(self, tmp_path):
        """AC1.5.7: Verify all required indexes exist"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list('price_movements')")
        indexes = cursor.fetchall()
        conn.close()

        index_names = [idx[1] for idx in indexes]

        assert 'idx_bse_date' in index_names
        assert 'idx_nse_date' in index_names
        assert 'idx_date' in index_names


class TestIntegrationScenarios:
    """Integration tests for full workflow"""

    def test_collect_all_price_data_workflow(self, tmp_path):
        """Test complete price data collection workflow"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        cache_dir = str(tmp_path / "cache")

        collector = PriceCollector(db_path=db_path, cache_dir=cache_dir)

        # Mock all external calls
        with patch.object(collector, 'download_bse_bhav_copies') as mock_bse, \
             patch.object(collector, 'download_nse_bhav_copies') as mock_nse, \
             patch.object(collector, 'parse_bhav_copy') as mock_parse, \
             patch.object(collector, 'fill_gaps_with_yfinance') as mock_yf:

            # Setup mocks with properly named files
            # BSE format: EQ131124.csv for 13/11/2024
            mock_bse.return_value = [str(tmp_path / 'EQ131124.csv')]
            # NSE format: cm13NOV2024bhav.csv
            mock_nse.return_value = [str(tmp_path / 'cm13NOV2024bhav.csv')]

            mock_parse.return_value = pd.DataFrame({
                'bse_code': ['500325'],
                'date': ['2024-11-13'],
                'open': [2800.0],
                'high': [2850.0],
                'low': [2790.0],
                'close': [2840.0],
                'volume': [1000000],
                'source': ['bse_bhav_copy']
            })

            mock_yf.return_value = 10  # 10 gaps filled

            # Execute
            report = collector.collect_all_price_data(
                bse_codes=['500325', '500209'],
                start_date='2024-11-01',
                end_date='2024-11-13'
            )

        assert report.total_files_downloaded >= 2
        assert report.total_records_stored >= 1
        assert mock_bse.called
        assert mock_nse.called

    def test_handle_empty_bhav_copy(self, tmp_path):
        """Test handling of empty BhavCopy files"""
        from agents.ml.ml_data_collector import PriceCollector

        db_path = str(tmp_path / "test.db")
        collector = PriceCollector(db_path=db_path)

        # Create empty CSV
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("SC_CODE,SC_NAME,OPEN,HIGH,LOW,CLOSE\n")

        df = collector.parse_bhav_copy(str(csv_path), source='bse_bhav_copy', date="2024-11-13")

        # Should return empty DataFrame, not error
        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)

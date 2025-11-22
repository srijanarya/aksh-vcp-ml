#!/usr/bin/env python3
"""
Unit Tests for Cache Management Tools

Tests HistoricalBackfillTool, IncrementalUpdateTool, and CacheHealthMonitorTool
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import sqlite3
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from agents.cache.tools.historical_backfill_tool import HistoricalBackfillTool
from agents.cache.tools.incremental_update_tool import IncrementalUpdateTool
from agents.cache.tools.cache_health_monitor_tool import CacheHealthMonitorTool


class TestHistoricalBackfillTool:
    """Test Historical Backfill Tool"""

    def test_initialization(self, tmp_path):
        """Test tool initializes correctly"""
        checkpoint = tmp_path / "checkpoint.json"
        tool = HistoricalBackfillTool(
            checkpoint_file=str(checkpoint),
            batch_size=5
        )

        assert tool.batch_size == 5
        assert tool.checkpoint_file == checkpoint

    def test_save_checkpoint(self, tmp_path):
        """Test saving checkpoint"""
        checkpoint = tmp_path / "checkpoint.json"
        tool = HistoricalBackfillTool(checkpoint_file=str(checkpoint))

        tool._save_checkpoint(
            remaining_symbols=['TCS', 'INFY'],
            completed=1,
            failed=0,
            failed_symbols=[]
        )

        assert checkpoint.exists()

        with open(checkpoint) as f:
            data = json.load(f)

        assert data['completed'] == 1
        assert data['failed'] == 0
        assert len(data['remaining_symbols']) == 2

    def test_load_checkpoint(self, tmp_path):
        """Test loading checkpoint"""
        checkpoint = tmp_path / "checkpoint.json"
        tool = HistoricalBackfillTool(checkpoint_file=str(checkpoint))

        # Save checkpoint
        tool._save_checkpoint(
            remaining_symbols=['TCS'],
            completed=2,
            failed=1,
            failed_symbols=['BADSTOCK']
        )

        # Load checkpoint
        loaded = tool._load_checkpoint()

        assert loaded is not None
        assert loaded['completed'] == 2
        assert loaded['failed'] == 1
        assert loaded['remaining_symbols'] == ['TCS']

    def test_load_checkpoint_not_found(self, tmp_path):
        """Test loading non-existent checkpoint returns None"""
        checkpoint = tmp_path / "nonexistent.json"
        tool = HistoricalBackfillTool(checkpoint_file=str(checkpoint))

        loaded = tool._load_checkpoint()
        assert loaded is None

    def test_clear_checkpoint(self, tmp_path):
        """Test clearing checkpoint"""
        checkpoint = tmp_path / "checkpoint.json"
        tool = HistoricalBackfillTool(checkpoint_file=str(checkpoint))

        # Create checkpoint
        tool._save_checkpoint(['TCS'], 1, 0, [])
        assert checkpoint.exists()

        # Clear it
        tool._clear_checkpoint()
        assert not checkpoint.exists()

    def test_get_progress(self, tmp_path):
        """Test getting backfill progress"""
        tool = HistoricalBackfillTool(checkpoint_file=str(tmp_path / "checkpoint.json"))

        tool.stats['total_symbols'] = 10
        tool.stats['completed_symbols'] = 7
        tool.stats['failed_symbols'] = 1

        progress = tool.get_progress()

        assert progress['total_symbols'] == 10
        assert progress['completed'] == 7
        assert progress['failed'] == 1
        assert progress['remaining'] == 2
        assert progress['progress_pct'] == 80.0  # (7+1)/10 * 100


class TestIncrementalUpdateTool:
    """Test Incremental Update Tool"""

    def test_initialization(self, tmp_path):
        """Test tool initializes correctly"""
        cache_db = tmp_path / "cache.db"
        tool = IncrementalUpdateTool(
            cache_db_path=str(cache_db),
            lookback_days=2
        )

        assert tool.lookback_days == 2
        assert tool.cache_db_path == cache_db

    def test_get_last_cached_date_no_db(self, tmp_path):
        """Test getting last cached date when DB doesn't exist"""
        cache_db = tmp_path / "nonexistent.db"
        tool = IncrementalUpdateTool(cache_db_path=str(cache_db))

        last_date = tool._get_last_cached_date('RELIANCE', 'NSE', 'ONE_DAY')
        assert last_date is None

    def test_get_last_cached_date(self, tmp_path):
        """Test getting last cached date"""
        cache_db = tmp_path / "cache.db"

        # Create test database
        conn = sqlite3.connect(str(cache_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE ohlcv_data (
                symbol TEXT,
                exchange TEXT,
                interval TEXT,
                timestamp TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER
            )
        """)

        # Insert test data
        test_date = datetime(2024, 11, 20)
        cursor.execute("""
            INSERT INTO ohlcv_data (symbol, exchange, interval, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('RELIANCE', 'NSE', 'ONE_DAY', test_date.isoformat(), 100, 105, 99, 103, 1000000))

        conn.commit()
        conn.close()

        # Test retrieval
        tool = IncrementalUpdateTool(cache_db_path=str(cache_db))
        last_date = tool._get_last_cached_date('RELIANCE', 'NSE', 'ONE_DAY')

        assert last_date is not None
        assert last_date.date() == test_date.date()

    def test_get_all_cached_symbols(self, tmp_path):
        """Test getting all cached symbols"""
        cache_db = tmp_path / "cache.db"

        # Create test database
        conn = sqlite3.connect(str(cache_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE ohlcv_data (
                symbol TEXT,
                exchange TEXT,
                interval TEXT,
                timestamp TEXT
            )
        """)

        # Insert test data
        for symbol in ['RELIANCE', 'TCS', 'INFY']:
            cursor.execute("""
                INSERT INTO ohlcv_data (symbol, exchange, interval, timestamp)
                VALUES (?, ?, ?, ?)
            """, (symbol, 'NSE', 'ONE_DAY', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        # Test retrieval
        tool = IncrementalUpdateTool(cache_db_path=str(cache_db))
        symbols = tool._get_all_cached_symbols('NSE', 'ONE_DAY')

        assert len(symbols) == 3
        assert 'RELIANCE' in symbols
        assert 'TCS' in symbols
        assert 'INFY' in symbols

    def test_get_update_status_no_data(self, tmp_path):
        """Test getting update status for symbol with no data"""
        cache_db = tmp_path / "cache.db"
        tool = IncrementalUpdateTool(cache_db_path=str(cache_db))

        status = tool.get_update_status('RELIANCE')

        assert status['symbol'] == 'RELIANCE'
        assert status['has_data'] == False
        assert status['needs_update'] == True

    def test_get_update_status_with_data(self, tmp_path):
        """Test getting update status for symbol with data"""
        cache_db = tmp_path / "cache.db"

        # Create test database with old data
        conn = sqlite3.connect(str(cache_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE ohlcv_data (
                symbol TEXT,
                exchange TEXT,
                interval TEXT,
                timestamp TEXT
            )
        """)

        old_date = datetime.now() - timedelta(days=5)
        cursor.execute("""
            INSERT INTO ohlcv_data (symbol, exchange, interval, timestamp)
            VALUES (?, ?, ?, ?)
        """, ('RELIANCE', 'NSE', 'ONE_DAY', old_date.isoformat()))

        conn.commit()
        conn.close()

        # Test status
        tool = IncrementalUpdateTool(cache_db_path=str(cache_db))
        status = tool.get_update_status('RELIANCE')

        assert status['has_data'] == True
        assert status['days_stale'] == 5
        assert status['needs_update'] == True  # >1 day old


class TestCacheHealthMonitorTool:
    """Test Cache Health Monitor Tool"""

    def test_initialization(self, tmp_path):
        """Test tool initializes correctly"""
        cache_db = tmp_path / "cache.db"
        monitor = CacheHealthMonitorTool(
            cache_db_path=str(cache_db),
            freshness_threshold_days=2
        )

        assert monitor.freshness_threshold_days == 2
        assert monitor.cache_db_path == cache_db

    def test_generate_health_report_no_db(self, tmp_path):
        """Test health report when DB doesn't exist"""
        cache_db = tmp_path / "nonexistent.db"
        monitor = CacheHealthMonitorTool(cache_db_path=str(cache_db))

        report = monitor.generate_health_report()

        assert report['status'] == 'ERROR'
        assert 'not found' in report['message'].lower()

    def test_calculate_health_status_healthy(self):
        """Test health status calculation - healthy"""
        monitor = CacheHealthMonitorTool()

        metrics = {
            'freshness': {'freshness_rate': 95.0},
            'quality': {'symbols_with_gaps': 0},
            'coverage': {'total_symbols': 50}
        }

        status = monitor._calculate_health_status(metrics)
        assert status == "HEALTHY"

    def test_calculate_health_status_warning(self):
        """Test health status calculation - warning"""
        monitor = CacheHealthMonitorTool()

        metrics = {
            'freshness': {'freshness_rate': 75.0},  # Low freshness
            'quality': {'symbols_with_gaps': 0},
            'coverage': {'total_symbols': 50}
        }

        status = monitor._calculate_health_status(metrics)
        assert status == "WARNING"

    def test_calculate_health_status_critical(self):
        """Test health status calculation - critical"""
        monitor = CacheHealthMonitorTool()

        metrics = {
            'freshness': {'freshness_rate': 70.0},  # Low freshness
            'quality': {'symbols_with_gaps': 5},  # Has gaps
            'coverage': {'total_symbols': 50}
        }

        status = monitor._calculate_health_status(metrics)
        assert status == "CRITICAL"

    def test_identify_issues(self):
        """Test identifying issues from metrics"""
        monitor = CacheHealthMonitorTool()

        metrics = {
            'freshness': {'stale_symbols': 10},
            'quality': {'symbols_with_gaps': 5},
            'coverage': {'total_symbols': 50}
        }

        issues = monitor._identify_issues(metrics)

        assert len(issues) == 2
        assert any('stale' in issue.lower() for issue in issues)
        assert any('gaps' in issue.lower() for issue in issues)

    def test_generate_recommendations(self):
        """Test generating recommendations"""
        monitor = CacheHealthMonitorTool()

        metrics = {
            'freshness': {'stale_symbols': 5},
            'quality': {'symbols_with_gaps': 0},
            'coverage': {'total_symbols': 50},
            'database': {'size_mb': 50}
        }

        recommendations = monitor._generate_recommendations(metrics)

        assert len(recommendations) > 0
        assert any('incremental update' in rec.lower() for rec in recommendations)

    def test_check_symbol_health_no_data(self, tmp_path):
        """Test checking symbol health with no data"""
        cache_db = tmp_path / "cache.db"

        # Create empty database
        conn = sqlite3.connect(str(cache_db))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE ohlcv_data (
                symbol TEXT,
                exchange TEXT,
                interval TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

        monitor = CacheHealthMonitorTool(cache_db_path=str(cache_db))
        health = monitor.check_symbol_health('RELIANCE')

        assert health['status'] == 'NO_DATA'

    def test_check_symbol_health_with_data(self, tmp_path):
        """Test checking symbol health with data"""
        cache_db = tmp_path / "cache.db"

        # Create test database
        conn = sqlite3.connect(str(cache_db))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE ohlcv_data (
                symbol TEXT,
                exchange TEXT,
                interval TEXT,
                timestamp TEXT
            )
        """)

        # Insert recent data (healthy)
        recent_date = datetime.now() - timedelta(days=1)
        for i in range(250):  # 250 rows = ~1 year
            cursor.execute("""
                INSERT INTO ohlcv_data (symbol, exchange, interval, timestamp)
                VALUES (?, ?, ?, ?)
            """, ('RELIANCE', 'NSE', 'ONE_DAY', (recent_date - timedelta(days=i)).isoformat()))

        conn.commit()
        conn.close()

        monitor = CacheHealthMonitorTool(cache_db_path=str(cache_db))
        health = monitor.check_symbol_health('RELIANCE')

        assert health['status'] == 'HEALTHY'
        assert health['is_fresh'] == True
        assert health['has_gaps'] == False


if __name__ == "__main__":
    pytest.main([__file__, '-v'])

#!/usr/bin/env python3
"""
Unit Tests for BSE Filtering Agent System

Tests BSEFilteringAgent, BSEEarningsCalendarTool, and StockFilterByEarningsTool
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from agents.filtering.bse_filtering_agent import BSEFilteringAgent
from agents.filtering.tools.bse_earnings_calendar_tool import BSEEarningsCalendarTool
from agents.filtering.tools.stock_filter_by_earnings_tool import StockFilterByEarningsTool


class TestBSEEarningsCalendarTool:
    """Test BSE Earnings Calendar Tool"""

    def test_initialization(self, tmp_path):
        """Test tool initializes correctly"""
        db_path = tmp_path / "test_earnings.db"
        tool = BSEEarningsCalendarTool(db_path=str(db_path))

        assert tool.db_path.exists()
        assert tool.session is not None

        # Verify database schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'earnings_calendar' in tables
        conn.close()

    def test_cache_announcements(self, tmp_path):
        """Test caching announcements works"""
        db_path = tmp_path / "test_earnings.db"
        tool = BSEEarningsCalendarTool(db_path=str(db_path))

        announcements = [
            {
                'bse_code': '500325',
                'company_name': 'Reliance',
                'announcement_type': 'RESULT',
                'announcement_date': '2024-11-25',
                'details': 'Q2 Results'
            }
        ]

        tool._cache_announcements(announcements)

        # Verify cached
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM earnings_calendar")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_get_cached_announcements(self, tmp_path):
        """Test retrieving cached announcements"""
        db_path = tmp_path / "test_earnings.db"
        tool = BSEEarningsCalendarTool(db_path=str(db_path))

        # Cache some data
        announcements = [
            {
                'bse_code': '500325',
                'company_name': 'Reliance',
                'announcement_type': 'RESULT',
                'announcement_date': datetime.now().strftime('%Y-%m-%d'),
                'details': 'Q2 Results'
            }
        ]
        tool._cache_announcements(announcements)

        # Retrieve
        cached = tool._get_cached_announcements(
            from_date=datetime.now(),
            to_date=datetime.now()
        )

        assert cached is not None
        assert len(cached) == 1
        assert cached[0]['bse_code'] == '500325'

    def test_get_cached_announcements_stale(self, tmp_path):
        """Test stale cache returns None"""
        db_path = tmp_path / "test_earnings.db"
        tool = BSEEarningsCalendarTool(db_path=str(db_path))

        # Cache old data
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        old_date = datetime.now() - timedelta(days=2)
        cursor.execute("""
            INSERT INTO earnings_calendar
            (bse_code, company_name, announcement_type, announcement_date, details, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('500325', 'Test', 'RESULT', old_date.strftime('%Y-%m-%d'), 'Test', old_date.isoformat()))

        conn.commit()
        conn.close()

        # Try to retrieve (should be None - stale)
        cached = tool._get_cached_announcements(
            from_date=datetime.now(),
            to_date=datetime.now()
        )

        assert cached is None  # Stale cache

    def test_cleanup_old_data(self, tmp_path):
        """Test cleanup removes old announcements"""
        db_path = tmp_path / "test_earnings.db"
        tool = BSEEarningsCalendarTool(db_path=str(db_path))

        # Insert old data
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        old_date = datetime.now() - timedelta(days=100)
        cursor.execute("""
            INSERT INTO earnings_calendar
            (bse_code, company_name, announcement_type, announcement_date, details, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('500325', 'Test', 'RESULT', old_date.strftime('%Y-%m-%d'), 'Test', old_date.isoformat()))

        conn.commit()
        conn.close()

        # Cleanup (keep 90 days)
        tool.cleanup_old_data(days_to_keep=90)

        # Verify deleted
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM earnings_calendar")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0


class TestStockFilterByEarningsTool:
    """Test Stock Filter By Earnings Tool"""

    def test_initialization(self, tmp_path):
        """Test tool initializes correctly"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        assert tool.mapping_db_path.exists()

        # Verify schema
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert 'bse_nse_mapping' in tables
        conn.close()

    def test_add_mapping(self, tmp_path):
        """Test adding BSE-NSE mapping"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        tool.add_mapping(
            bse_code='500325',
            nse_symbol='RELIANCE',
            company_name='Reliance Industries'
        )

        # Verify added
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT nse_symbol FROM bse_nse_mapping WHERE bse_code = '500325'")
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == 'RELIANCE'

    def test_add_mappings_bulk(self, tmp_path):
        """Test bulk mapping addition"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        mappings = [
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE'},
            {'bse_code': '532540', 'nse_symbol': 'TCS'},
        ]

        tool.add_mappings_bulk(mappings)

        # Verify
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bse_nse_mapping")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_get_nse_symbol(self, tmp_path):
        """Test getting NSE symbol for BSE code"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        tool.add_mapping(bse_code='500325', nse_symbol='RELIANCE')

        nse_symbol = tool.get_nse_symbol('500325')
        assert nse_symbol == 'RELIANCE'

        # Test non-existent
        nse_symbol = tool.get_nse_symbol('999999')
        assert nse_symbol is None

    def test_get_bse_code(self, tmp_path):
        """Test getting BSE code for NSE symbol"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        tool.add_mapping(bse_code='500325', nse_symbol='RELIANCE')

        bse_code = tool.get_bse_code('RELIANCE')
        assert bse_code == '500325'

        # Test non-existent
        bse_code = tool.get_bse_code('NONEXISTENT')
        assert bse_code is None

    def test_map_bse_to_nse(self, tmp_path):
        """Test mapping list of BSE codes to NSE symbols"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        # Add mappings
        mappings = [
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE'},
            {'bse_code': '532540', 'nse_symbol': 'TCS'},
        ]
        tool.add_mappings_bulk(mappings)

        # Map
        bse_codes = ['500325', '532540', '999999']
        result = tool.map_bse_to_nse(bse_codes)

        assert len(result) == 2  # Only 2 mapped
        assert result['500325'] == 'RELIANCE'
        assert result['532540'] == 'TCS'
        assert tool.stats['unmapped_codes'] == 1

    def test_filter_universe(self, tmp_path):
        """Test filtering universe by earnings"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        # Add mappings
        mappings = [
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE'},
            {'bse_code': '532540', 'nse_symbol': 'TCS'},
        ]
        tool.add_mappings_bulk(mappings)

        # Original universe
        original_universe = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK']

        # BSE codes with earnings
        bse_codes_with_earnings = ['500325']  # Only RELIANCE

        # Filter
        filtered = tool.filter_universe(original_universe, bse_codes_with_earnings)

        assert len(filtered) == 1
        assert 'RELIANCE' in filtered
        assert tool.stats['filter_efficiency'] == 75.0  # 3/4 removed

    def test_get_whitelist(self, tmp_path):
        """Test getting earnings whitelist"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        # Add mappings
        tool.add_mappings_bulk([
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE'},
            {'bse_code': '532540', 'nse_symbol': 'TCS'},
        ])

        # Get whitelist
        whitelist = tool.get_whitelist(['500325', '532540'])

        assert isinstance(whitelist, set)
        assert len(whitelist) == 2
        assert 'RELIANCE' in whitelist
        assert 'TCS' in whitelist

    def test_get_mapping_coverage(self, tmp_path):
        """Test getting mapping coverage statistics"""
        db_path = tmp_path / "test_mapping.db"
        tool = StockFilterByEarningsTool(mapping_db_path=str(db_path))

        tool.add_mappings_bulk([
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE'},
            {'bse_code': '532540', 'nse_symbol': 'TCS'},
        ])

        coverage = tool.get_mapping_coverage()

        assert coverage['total_mappings'] == 2
        assert coverage['unique_nse_symbols'] == 2
        assert coverage['unique_bse_codes'] == 2


class TestBSEFilteringAgent:
    """Test BSE Filtering Agent"""

    def test_initialization(self, tmp_path):
        """Test agent initializes correctly"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db),
            default_lookforward_days=7
        )

        assert agent.earnings_tool is not None
        assert agent.filter_tool is not None
        assert agent.default_lookforward_days == 7

    def test_initialize_mappings(self, tmp_path):
        """Test initializing Nifty 50 mappings"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db)
        )

        agent.initialize_mappings()

        # Verify mappings loaded
        coverage = agent.filter_tool.get_mapping_coverage()
        assert coverage['total_mappings'] > 0

    @patch('agents.filtering.tools.bse_earnings_calendar_tool.BSEEarningsCalendarTool.get_stocks_with_upcoming_earnings')
    def test_filter_universe_by_earnings(self, mock_get_stocks, tmp_path):
        """Test filtering universe by earnings"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db)
        )

        # Initialize mappings
        agent.initialize_mappings()

        # Mock BSE earnings
        mock_get_stocks.return_value = ['500325']  # RELIANCE BSE code

        # Filter
        original_universe = ['RELIANCE', 'TCS', 'INFY']
        result = agent.filter_universe_by_earnings(
            original_universe=original_universe,
            lookforward_days=7
        )

        assert result['original_size'] == 3
        assert result['filtered_size'] == 1
        assert 'RELIANCE' in result['filtered_universe']
        assert result['reduction_pct'] > 0

    @patch('agents.filtering.tools.bse_earnings_calendar_tool.BSEEarningsCalendarTool.get_stocks_with_upcoming_earnings')
    def test_get_earnings_whitelist(self, mock_get_stocks, tmp_path):
        """Test getting earnings whitelist"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db)
        )

        agent.initialize_mappings()
        mock_get_stocks.return_value = ['500325', '532540']  # RELIANCE, TCS

        whitelist = agent.get_earnings_whitelist(lookforward_days=7)

        assert len(whitelist) == 2
        assert 'RELIANCE' in whitelist
        assert 'TCS' in whitelist

    @patch('agents.filtering.tools.bse_earnings_calendar_tool.BSEEarningsCalendarTool.get_stocks_with_upcoming_earnings')
    def test_should_analyze_stock(self, mock_get_stocks, tmp_path):
        """Test checking if stock should be analyzed"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db)
        )

        agent.initialize_mappings()
        mock_get_stocks.return_value = ['500325']  # RELIANCE

        assert agent.should_analyze_stock('RELIANCE', lookforward_days=7)
        assert not agent.should_analyze_stock('TCS', lookforward_days=7)

    def test_get_stats(self, tmp_path):
        """Test getting agent statistics"""
        earnings_db = tmp_path / "earnings.db"
        mapping_db = tmp_path / "mapping.db"

        agent = BSEFilteringAgent(
            earnings_db_path=str(earnings_db),
            mapping_db_path=str(mapping_db)
        )

        stats = agent.get_stats()

        assert 'total_runs' in stats
        assert 'average_reduction' in stats
        assert stats['total_runs'] == 0  # No runs yet


if __name__ == "__main__":
    pytest.main([__file__, '-v'])

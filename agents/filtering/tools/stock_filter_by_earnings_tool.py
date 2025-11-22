#!/usr/bin/env python3
"""
Stock Filter By Earnings Tool

Maps BSE codes to NSE symbols and filters stock universe for backtesting.

Goal: 70% universe reduction by only including stocks with upcoming earnings
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Set
import logging

logger = logging.getLogger(__name__)


class StockFilterByEarningsTool:
    """
    Tool to filter stock universe based on upcoming earnings

    Features:
    - Maps BSE codes to NSE symbols
    - Filters universe to stocks with upcoming earnings
    - Provides whitelist for backtest filtering
    - Tracks filtering statistics
    """

    def __init__(
        self,
        mapping_db_path: str = "data/bse_nse_mapping.db"
    ):
        """
        Initialize stock filter tool

        Args:
            mapping_db_path: Path to BSE-NSE mapping database
        """
        self.mapping_db_path = Path(mapping_db_path)
        self.mapping_db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_mapping_database()

        # Statistics
        self.stats = {
            'total_bse_codes': 0,
            'mapped_nse_symbols': 0,
            'unmapped_codes': 0,
            'filter_efficiency': 0.0
        }

    def _init_mapping_database(self):
        """Initialize BSE-NSE mapping database"""
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        # BSE-NSE mapping table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bse_nse_mapping (
                bse_code TEXT PRIMARY KEY,
                nse_symbol TEXT NOT NULL,
                company_name TEXT,
                isin TEXT,
                last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Index for fast NSE lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nse_symbol
            ON bse_nse_mapping(nse_symbol)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Mapping database initialized at {self.mapping_db_path}")

    def add_mapping(
        self,
        bse_code: str,
        nse_symbol: str,
        company_name: Optional[str] = None,
        isin: Optional[str] = None
    ):
        """
        Add or update BSE-NSE mapping

        Args:
            bse_code: BSE stock code
            nse_symbol: NSE symbol
            company_name: Company name (optional)
            isin: ISIN code (optional)
        """
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO bse_nse_mapping
            (bse_code, nse_symbol, company_name, isin, last_verified)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (bse_code, nse_symbol, company_name, isin))

        conn.commit()
        conn.close()

    def add_mappings_bulk(self, mappings: List[Dict]):
        """
        Add multiple mappings in bulk

        Args:
            mappings: List of mapping dictionaries with keys:
                      bse_code, nse_symbol, company_name, isin
        """
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        for mapping in mappings:
            cursor.execute("""
                INSERT OR REPLACE INTO bse_nse_mapping
                (bse_code, nse_symbol, company_name, isin, last_verified)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                mapping['bse_code'],
                mapping['nse_symbol'],
                mapping.get('company_name'),
                mapping.get('isin')
            ))

        conn.commit()
        conn.close()

        logger.info(f"Added {len(mappings)} BSE-NSE mappings")

    def get_nse_symbol(self, bse_code: str) -> Optional[str]:
        """
        Get NSE symbol for BSE code

        Args:
            bse_code: BSE stock code

        Returns:
            NSE symbol or None if not found
        """
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nse_symbol FROM bse_nse_mapping
            WHERE bse_code = ?
        """, (bse_code,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_bse_code(self, nse_symbol: str) -> Optional[str]:
        """
        Get BSE code for NSE symbol

        Args:
            nse_symbol: NSE symbol

        Returns:
            BSE code or None if not found
        """
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT bse_code FROM bse_nse_mapping
            WHERE nse_symbol = ?
        """, (nse_symbol,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def map_bse_to_nse(self, bse_codes: List[str]) -> Dict[str, str]:
        """
        Map list of BSE codes to NSE symbols

        Args:
            bse_codes: List of BSE stock codes

        Returns:
            Dictionary mapping BSE code to NSE symbol (only successful mappings)
        """
        mappings = {}

        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        for bse_code in bse_codes:
            cursor.execute("""
                SELECT nse_symbol FROM bse_nse_mapping
                WHERE bse_code = ?
            """, (bse_code,))

            result = cursor.fetchone()
            if result:
                mappings[bse_code] = result[0]

        conn.close()

        # Update statistics
        self.stats['total_bse_codes'] = len(bse_codes)
        self.stats['mapped_nse_symbols'] = len(mappings)
        self.stats['unmapped_codes'] = len(bse_codes) - len(mappings)

        logger.info(f"Mapped {len(mappings)}/{len(bse_codes)} BSE codes to NSE symbols")

        return mappings

    def filter_universe(
        self,
        original_universe: List[str],
        bse_codes_with_earnings: List[str]
    ) -> List[str]:
        """
        Filter stock universe to only stocks with upcoming earnings

        Args:
            original_universe: Original list of NSE symbols
            bse_codes_with_earnings: List of BSE codes with earnings

        Returns:
            Filtered list of NSE symbols
        """
        # Map BSE codes to NSE symbols
        bse_to_nse = self.map_bse_to_nse(bse_codes_with_earnings)
        nse_symbols_with_earnings = set(bse_to_nse.values())

        # Filter original universe
        filtered_universe = [
            symbol for symbol in original_universe
            if symbol in nse_symbols_with_earnings
        ]

        # Calculate filtering efficiency
        original_size = len(original_universe)
        filtered_size = len(filtered_universe)
        reduction = ((original_size - filtered_size) / original_size * 100) if original_size > 0 else 0

        self.stats['filter_efficiency'] = reduction

        logger.info(f"Filtered universe: {original_size} → {filtered_size} stocks ({reduction:.1f}% reduction)")

        return filtered_universe

    def get_whitelist(
        self,
        bse_codes_with_earnings: List[str]
    ) -> Set[str]:
        """
        Get set of NSE symbols with upcoming earnings (whitelist)

        Args:
            bse_codes_with_earnings: List of BSE codes with earnings

        Returns:
            Set of NSE symbols
        """
        bse_to_nse = self.map_bse_to_nse(bse_codes_with_earnings)
        return set(bse_to_nse.values())

    def get_stats(self) -> Dict:
        """
        Get filtering statistics

        Returns:
            Dictionary with statistics
        """
        return self.stats.copy()

    def load_nifty_mappings(self):
        """
        Pre-load BSE-NSE mappings for Nifty 50 stocks

        This is a convenience method to bootstrap the mapping database
        """
        # Hardcoded Nifty 50 BSE-NSE mappings (top 20 for demo)
        nifty_mappings = [
            {'bse_code': '500325', 'nse_symbol': 'RELIANCE', 'company_name': 'Reliance Industries'},
            {'bse_code': '532540', 'nse_symbol': 'TCS', 'company_name': 'Tata Consultancy Services'},
            {'bse_code': '500180', 'nse_symbol': 'HDFCBANK', 'company_name': 'HDFC Bank'},
            {'bse_code': '500209', 'nse_symbol': 'INFY', 'company_name': 'Infosys'},
            {'bse_code': '532174', 'nse_symbol': 'ICICIBANK', 'company_name': 'ICICI Bank'},
            {'bse_code': '500696', 'nse_symbol': 'HINDUNILVR', 'company_name': 'Hindustan Unilever'},
            {'bse_code': '500875', 'nse_symbol': 'ITC', 'company_name': 'ITC'},
            {'bse_code': '500112', 'nse_symbol': 'SBIN', 'company_name': 'State Bank of India'},
            {'bse_code': '532454', 'nse_symbol': 'BHARTIARTL', 'company_name': 'Bharti Airtel'},
            {'bse_code': '500247', 'nse_symbol': 'KOTAKBANK', 'company_name': 'Kotak Mahindra Bank'},
            {'bse_code': '500510', 'nse_symbol': 'LT', 'company_name': 'Larsen & Toubro'},
            {'bse_code': '532281', 'nse_symbol': 'HCLTECH', 'company_name': 'HCL Technologies'},
            {'bse_code': '532215', 'nse_symbol': 'AXISBANK', 'company_name': 'Axis Bank'},
            {'bse_code': '500820', 'nse_symbol': 'ASIANPAINT', 'company_name': 'Asian Paints'},
            {'bse_code': '532500', 'nse_symbol': 'MARUTI', 'company_name': 'Maruti Suzuki'},
            {'bse_code': '524715', 'nse_symbol': 'SUNPHARMA', 'company_name': 'Sun Pharmaceutical'},
            {'bse_code': '500114', 'nse_symbol': 'TITAN', 'company_name': 'Titan Company'},
            {'bse_code': '500034', 'nse_symbol': 'BAJFINANCE', 'company_name': 'Bajaj Finance'},
            {'bse_code': '532538', 'nse_symbol': 'ULTRACEMCO', 'company_name': 'UltraTech Cement'},
            {'bse_code': '500790', 'nse_symbol': 'NESTLEIND', 'company_name': 'Nestle India'},
        ]

        self.add_mappings_bulk(nifty_mappings)
        logger.info(f"Loaded {len(nifty_mappings)} Nifty mappings")

    def get_mapping_coverage(self) -> Dict:
        """
        Get statistics on mapping database coverage

        Returns:
            Dictionary with coverage statistics
        """
        conn = sqlite3.connect(str(self.mapping_db_path))
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM bse_nse_mapping")
        total_mappings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT nse_symbol) FROM bse_nse_mapping")
        unique_nse = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT bse_code) FROM bse_nse_mapping")
        unique_bse = cursor.fetchone()[0]

        conn.close()

        return {
            'total_mappings': total_mappings,
            'unique_nse_symbols': unique_nse,
            'unique_bse_codes': unique_bse
        }


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    filter_tool = StockFilterByEarningsTool()

    # Load Nifty mappings
    filter_tool.load_nifty_mappings()

    # Demo: Filter Nifty 50 universe
    nifty_50 = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
    bse_with_earnings = ['500325', '532540']  # RELIANCE, TCS

    filtered = filter_tool.filter_universe(nifty_50, bse_with_earnings)

    print(f"\nOriginal universe: {len(nifty_50)} stocks")
    print(f"Filtered universe: {len(filtered)} stocks")
    print(f"Reduction: {filter_tool.stats['filter_efficiency']:.1f}%")
    print(f"\nFiltered stocks: {filtered}")

    # Coverage statistics
    coverage = filter_tool.get_mapping_coverage()
    print(f"\nMapping database coverage:")
    print(f"  Total mappings: {coverage['total_mappings']}")
    print(f"  Unique NSE symbols: {coverage['unique_nse_symbols']}")
    print(f"  Unique BSE codes: {coverage['unique_bse_codes']}")

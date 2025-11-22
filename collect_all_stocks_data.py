#!/usr/bin/env python3
"""
Comprehensive Data Collector for ALL Indian Stocks

This script collects quarterly earnings for ALL 5,000+ Indian stocks
to identify the TRUE top 0.1-0.2% performers (real blockbusters).

True Blockbusters = Top 5-10 stocks out of 5,000+ (not 40% of stocks!)
"""

import yfinance as yf
import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveStockCollector:
    """Collect data for ALL Indian stocks to find true blockbusters"""

    def __init__(self):
        self.db_path = "data/all_indian_stocks_quarterly.db"
        Path("data").mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize comprehensive database"""
        conn = sqlite3.connect(self.db_path)

        # Main quarterly data table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_data (
                symbol TEXT,
                company_name TEXT,
                quarter TEXT,
                fiscal_year INTEGER,
                announcement_date DATE,

                -- Absolute numbers (in Crores)
                revenue REAL,
                pat REAL,
                ebitda REAL,
                eps REAL,

                -- Growth metrics
                revenue_yoy REAL,
                pat_yoy REAL,
                ebitda_yoy REAL,
                eps_yoy REAL,

                -- Composite scoring
                composite_score REAL,
                revenue_rank INTEGER,
                pat_rank INTEGER,
                overall_rank INTEGER,
                percentile REAL,

                -- Metadata
                data_source TEXT DEFAULT 'yahoo',
                collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (symbol, quarter, fiscal_year)
            )
        """)

        # Symbol universe table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS symbol_universe (
                symbol TEXT PRIMARY KEY,
                exchange TEXT,
                status TEXT,
                quarters_available INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_composite_score ON quarterly_data(composite_score DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_quarter_year ON quarterly_data(quarter, fiscal_year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rankings ON quarterly_data(overall_rank)")

        conn.commit()
        conn.close()

    def load_all_indian_symbols(self) -> list:
        """Load ALL Indian stock symbols from multiple sources"""
        symbols = set()

        # 1. Load from comprehensive symbol files
        symbol_files = [
            "agents/backtesting/symbol_lists/nse_bse_all_stocks.txt",
            "data/master_stock_list.csv",
            "tools/all_indian_stocks.txt"
        ]

        for file_path in symbol_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            symbol = line.strip().replace('.NS', '').replace('.BO', '')
                            if symbol and not symbol.startswith('#'):
                                symbols.add(symbol)
                    logger.info(f"Loaded {len(lines)} symbols from {file_path}")
                except Exception as e:
                    logger.warning(f"Error loading {file_path}: {e}")

        # 2. Get NSE stocks from official list
        nse_stocks = self.fetch_nse_stocks()
        symbols.update(nse_stocks)

        # 3. Get BSE stocks
        bse_stocks = self.fetch_bse_stocks()
        symbols.update(bse_stocks)

        # Remove invalid symbols
        symbols = {s for s in symbols if s and len(s) > 0 and s.isalnum()}

        logger.info(f"Total unique symbols loaded: {len(symbols)}")
        return list(symbols)

    def fetch_nse_stocks(self) -> set:
        """Fetch all NSE listed stocks"""
        try:
            # NSE provides a CSV of all listed securities
            import requests

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Try to get NSE equity list
            urls = [
                "https://www1.nseindia.com/content/equities/EQUITY_L.csv",
                "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            ]

            for url in urls:
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        # Parse CSV content
                        lines = response.text.split('\n')
                        symbols = set()
                        for line in lines[1:]:  # Skip header
                            if ',' in line:
                                parts = line.split(',')
                                if len(parts) > 0:
                                    symbol = parts[0].strip()
                                    if symbol:
                                        symbols.add(symbol)
                        logger.info(f"Fetched {len(symbols)} NSE symbols")
                        return symbols
                except:
                    continue

        except Exception as e:
            logger.warning(f"Could not fetch NSE stocks: {e}")

        return set()

    def fetch_bse_stocks(self) -> set:
        """Fetch all BSE listed stocks"""
        # For now, return empty set - can be implemented later
        return set()

    def collect_stock_quarterly_data(self, symbol: str, max_quarters: int = 20) -> list:
        """Collect quarterly data for a single stock"""
        results = []

        try:
            # Try NSE first, then BSE
            for suffix in ['.NS', '.BO']:
                ticker = yf.Ticker(f"{symbol}{suffix}")
                income_stmt = ticker.quarterly_income_stmt

                if not income_stmt.empty:
                    break

            if income_stmt.empty:
                return []

            # Process each quarter
            for i, date in enumerate(income_stmt.columns[:max_quarters]):
                try:
                    quarter_data = {
                        'symbol': symbol,
                        'announcement_date': date.strftime('%Y-%m-%d'),
                        'quarter': self._get_quarter(date),
                        'fiscal_year': self._get_fiscal_year(date)
                    }

                    # Extract financial metrics
                    metrics = {
                        'Total Revenue': 'revenue',
                        'Net Income': 'pat',
                        'EBITDA': 'ebitda',
                        'Basic EPS': 'eps'
                    }

                    for yahoo_field, db_field in metrics.items():
                        if yahoo_field in income_stmt.index:
                            value = income_stmt.loc[yahoo_field, date]
                            if pd.notna(value):
                                # Convert to Crores for revenue/pat/ebitda
                                if db_field in ['revenue', 'pat', 'ebitda']:
                                    quarter_data[db_field] = value / 10000000
                                else:
                                    quarter_data[db_field] = value

                    # Calculate YoY growth (compare with same quarter last year)
                    if i + 4 < len(income_stmt.columns):
                        yoy_date = income_stmt.columns[i + 4]

                        for yahoo_field, db_field in metrics.items():
                            if yahoo_field in income_stmt.index and db_field in quarter_data:
                                yoy_value = income_stmt.loc[yahoo_field, yoy_date]
                                if pd.notna(yoy_value) and yoy_value != 0:
                                    current = quarter_data[db_field]
                                    if db_field in ['revenue', 'pat', 'ebitda']:
                                        yoy_value = yoy_value / 10000000
                                    growth = ((current - yoy_value) / abs(yoy_value)) * 100
                                    quarter_data[f'{db_field}_yoy'] = growth

                    # Calculate composite score (weighted average of growth rates)
                    rev_yoy = quarter_data.get('revenue_yoy', 0) or 0
                    pat_yoy = quarter_data.get('pat_yoy', 0) or 0

                    # Weight: 35% revenue growth, 65% profit growth
                    # (Profit growth is more important for true blockbusters)
                    quarter_data['composite_score'] = (rev_yoy * 0.35) + (pat_yoy * 0.65)

                    results.append(quarter_data)

                except Exception as e:
                    continue

        except Exception as e:
            logger.debug(f"Error collecting {symbol}: {e}")

        return results

    def collect_all_stocks(self, limit: int = None, batch_size: int = 100):
        """Collect data for ALL stocks"""
        symbols = self.load_all_indian_symbols()

        if limit:
            symbols = symbols[:limit]

        logger.info(f"\n{'='*80}")
        logger.info(f"COLLECTING DATA FOR {len(symbols)} STOCKS")
        logger.info(f"Goal: Find the TRUE top 0.1-0.2% performers")
        logger.info(f"{'='*80}\n")

        conn = sqlite3.connect(self.db_path)

        total_collected = 0
        total_quarters = 0

        # Process in batches for better progress tracking
        for batch_start in range(0, len(symbols), batch_size):
            batch_end = min(batch_start + batch_size, len(symbols))
            batch = symbols[batch_start:batch_end]

            batch_num = (batch_start // batch_size) + 1
            total_batches = (len(symbols) + batch_size - 1) // batch_size

            logger.info(f"\nBatch {batch_num}/{total_batches}: Processing {len(batch)} stocks...")

            for symbol in batch:
                quarters = self.collect_stock_quarterly_data(symbol)

                if quarters:
                    for q in quarters:
                        try:
                            # Insert quarterly data
                            conn.execute("""
                                INSERT OR REPLACE INTO quarterly_data
                                (symbol, quarter, fiscal_year, announcement_date,
                                 revenue, pat, ebitda, eps,
                                 revenue_yoy, pat_yoy, ebitda_yoy, eps_yoy,
                                 composite_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                q.get('symbol'),
                                q.get('quarter'),
                                q.get('fiscal_year'),
                                q.get('announcement_date'),
                                q.get('revenue'),
                                q.get('pat'),
                                q.get('ebitda'),
                                q.get('eps'),
                                q.get('revenue_yoy'),
                                q.get('pat_yoy'),
                                q.get('ebitda_yoy'),
                                q.get('eps_yoy'),
                                q.get('composite_score')
                            ))
                        except:
                            continue

                    # Update symbol status
                    conn.execute("""
                        INSERT OR REPLACE INTO symbol_universe
                        (symbol, status, quarters_available)
                        VALUES (?, 'collected', ?)
                    """, (symbol, len(quarters)))

                    total_collected += 1
                    total_quarters += len(quarters)

                # Rate limiting
                time.sleep(0.15)

            conn.commit()

            # Progress update
            progress_pct = (batch_end / len(symbols)) * 100
            logger.info(f"Progress: {progress_pct:.1f}% | Collected: {total_collected} | Quarters: {total_quarters}")

        conn.close()

        logger.info(f"\n{'='*80}")
        logger.info("DATA COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Stocks with data: {total_collected}/{len(symbols)}")
        logger.info(f"📊 Total quarters: {total_quarters}")
        logger.info(f"📈 Avg quarters/stock: {total_quarters/total_collected if total_collected else 0:.1f}")

        # Now find the TRUE blockbusters
        self.find_true_blockbusters()

    def find_true_blockbusters(self, quarter: str = 'Q2', fiscal_year: int = 2024, top_n: int = 10):
        """
        Find the ACTUAL top performers - the true 0.1-0.2% of the market
        """
        conn = sqlite3.connect(self.db_path)

        # First, get total count of companies with data for this quarter
        count_query = """
            SELECT COUNT(DISTINCT symbol) as total
            FROM quarterly_data
            WHERE quarter = ? AND fiscal_year = ?
            AND revenue IS NOT NULL AND pat IS NOT NULL
        """

        total_stocks = pd.read_sql(count_query, conn, params=(quarter, fiscal_year))
        total_count = total_stocks.iloc[0]['total'] if not total_stocks.empty else 0

        if total_count == 0:
            logger.warning(f"No data found for {quarter} FY{fiscal_year}")
            conn.close()
            return

        # Get ALL stocks for this quarter and rank them
        query = """
            SELECT
                symbol,
                quarter,
                fiscal_year,
                revenue,
                pat,
                eps,
                COALESCE(revenue_yoy, 0) as revenue_yoy,
                COALESCE(pat_yoy, 0) as pat_yoy,
                COALESCE(composite_score, 0) as composite_score
            FROM quarterly_data
            WHERE quarter = ? AND fiscal_year = ?
            AND revenue IS NOT NULL AND pat IS NOT NULL
            ORDER BY composite_score DESC
        """

        df = pd.read_sql(query, conn, params=(quarter, fiscal_year))
        conn.close()

        if df.empty:
            return

        # Add rankings
        df['rank'] = range(1, len(df) + 1)
        df['percentile'] = ((len(df) - df['rank'] + 1) / len(df)) * 100

        # Get only the TRUE top performers
        true_blockbusters = df.head(top_n)

        # Calculate what percentile these represent
        top_percentile = (top_n / total_count) * 100

        print(f"\n{'='*100}")
        print(f"🏆 TRUE BLOCKBUSTERS - TOP {top_n} out of {total_count} stocks ({top_percentile:.2f}%)")
        print(f"Quarter: {quarter} FY{fiscal_year}")
        print(f"{'='*100}\n")

        for idx, row in true_blockbusters.iterrows():
            rank = row['rank']
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"

            print(f"{emoji} RANK #{rank}: {row['symbol']}")
            print(f"   📈 Revenue Growth: {row['revenue_yoy']:+.1f}%")
            print(f"   💰 PAT Growth: {row['pat_yoy']:+.1f}%")
            print(f"   🎯 Composite Score: {row['composite_score']:.1f}")
            print(f"   📊 Percentile: Top {row['percentile']:.2f}%")
            print(f"   💵 Revenue: ₹{row['revenue']:.0f} Cr | PAT: ₹{row['pat']:.0f} Cr")
            print()

        # Show the minimum thresholds to be a true blockbuster
        min_revenue_growth = true_blockbusters['revenue_yoy'].min()
        min_pat_growth = true_blockbusters['pat_yoy'].min()
        min_score = true_blockbusters['composite_score'].min()

        print(f"{'='*100}")
        print("📊 TRUE BLOCKBUSTER CRITERIA (Based on Actual Data):")
        print(f"{'='*100}")
        print(f"To be in the TOP {top_n} ({top_percentile:.2f}% of market), you need AT LEAST:")
        print(f"   • Minimum Revenue Growth: {min_revenue_growth:+.1f}%")
        print(f"   • Minimum PAT Growth: {min_pat_growth:+.1f}%")
        print(f"   • Minimum Composite Score: {min_score:.1f}")
        print()
        print(f"❌ Our old criteria (Rev>15%, PAT>20%) would have selected {len(df[(df['revenue_yoy'] > 15) & (df['pat_yoy'] > 20)])} stocks")
        print(f"✅ True blockbuster approach selects exactly {top_n} stocks (top {top_percentile:.2f}%)")

    def _get_quarter(self, date) -> str:
        """Get Indian fiscal quarter"""
        month = date.month
        if month in [4, 5, 6]:
            return 'Q1'
        elif month in [7, 8, 9]:
            return 'Q2'
        elif month in [10, 11, 12]:
            return 'Q3'
        else:
            return 'Q4'

    def _get_fiscal_year(self, date) -> int:
        """Get Indian fiscal year"""
        if date.month >= 4:
            return date.year + 1
        else:
            return date.year


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Collect ALL Indian stocks data')
    parser.add_argument('--limit', type=int, help='Limit number of stocks (for testing)')
    parser.add_argument('--batch', type=int, default=100, help='Batch size')
    parser.add_argument('--find-only', action='store_true', help='Only find blockbusters from existing data')

    args = parser.parse_args()

    collector = ComprehensiveStockCollector()

    if args.find_only:
        # Just find blockbusters from existing data
        collector.find_true_blockbusters()
    else:
        # Collect data for all stocks
        collector.collect_all_stocks(limit=args.limit, batch_size=args.batch)
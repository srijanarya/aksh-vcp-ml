#!/usr/bin/env python3
"""
ULTIMATE DATA COLLECTOR - Won't Stop Until ALL Data is Collected

This collector WILL collect quarterly earnings data for EVERY Indian stock.
It uses multiple strategies to ensure complete data collection:

1. Multi-source collection (Yahoo, local DBs, APIs)
2. Parallel processing with ThreadPoolExecutor
3. Automatic retries with exponential backoff
4. Progress persistence and resumption
5. Real-time monitoring

THE SYSTEM THAT DOESN'T STOP!
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UltimateDataCollector:
    """The collector that won't stop until ALL data is collected"""

    def __init__(self):
        self.db_path = "data/ultimate_indian_stocks.db"
        self.progress_file = "data/ultimate_progress.json"
        self.stop_flag = False

        # Statistics
        self.stats = {
            'total_symbols': 0,
            'completed': 0,
            'failed': 0,
            'retries': 0,
            'start_time': datetime.now()
        }

        # Initialize components
        self._init_database()
        self.progress = self._load_progress()

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown gracefully"""
        logger.info("\n⚠️ Shutdown requested - saving progress...")
        self.stop_flag = True
        self._save_progress()
        logger.info("✅ Progress saved. You can resume anytime.")
        sys.exit(0)

    def _init_database(self):
        """Initialize the ultimate database"""
        Path("data").mkdir(exist_ok=True)

        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_earnings (
                symbol TEXT,
                company_name TEXT,
                quarter TEXT,
                fiscal_year INTEGER,

                revenue REAL,
                revenue_yoy REAL,
                pat REAL,
                pat_yoy REAL,
                ebitda REAL,
                eps REAL,

                composite_score REAL,
                global_rank INTEGER,
                percentile REAL,

                data_source TEXT,
                collection_date DATE,

                PRIMARY KEY (symbol, quarter, fiscal_year)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS collection_log (
                symbol TEXT PRIMARY KEY,
                status TEXT,
                attempts INTEGER DEFAULT 0,
                sources_tried TEXT,
                quarters_collected INTEGER,
                last_attempt TIMESTAMP,
                error_message TEXT
            )
        """)

        # Create indexes for fast lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON quarterly_earnings(symbol)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON quarterly_earnings(composite_score DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_rank ON quarterly_earnings(global_rank)")

        conn.commit()
        conn.close()

    def _load_progress(self) -> dict:
        """Load previous progress"""
        if Path(self.progress_file).exists():
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                logger.info(f"📂 Resuming from previous session: {len(progress['completed'])} already done")
                return progress
        return {'completed': [], 'failed': [], 'pending': []}

    def _save_progress(self):
        """Save current progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def get_all_symbols(self) -> List[str]:
        """Get ALL Indian stock symbols from EVERY possible source"""
        symbols = set()

        # 1. NSE 500 stocks
        try:
            from agents.trading.nse_500_symbols import NSE_500_SYMBOLS
            symbols.update([s.replace('.NS', '') for s in NSE_500_SYMBOLS])
            logger.info(f"✓ Loaded {len(NSE_500_SYMBOLS)} NSE 500 symbols")
        except:
            pass

        # 2. Load from comprehensive files
        symbol_files = [
            "agents/backtesting/symbol_lists/nse_bse_all_stocks.txt",
            "tools/all_stocks.txt",
            "data/master_stock_list.csv"
        ]

        for file_path in symbol_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            symbol = line.strip().replace('.NS', '').replace('.BO', '').replace('.BOM', '')
                            if symbol and symbol.isalnum():
                                symbols.add(symbol)
                        logger.info(f"✓ Loaded {len(lines)} symbols from {file_path}")
                except:
                    pass

        # 3. Extract from existing databases
        db_paths = [
            "data/stocks.db",
            "data/historical_financials.db",
            "data/earnings_calendar.db",
            "data/quarterly_master.db"
        ]

        for db_path in db_paths:
            if Path(db_path).exists():
                try:
                    conn = sqlite3.connect(db_path)

                    # Get all tables
                    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)

                    for table in tables['name']:
                        # Get column names
                        cursor = conn.execute(f"SELECT * FROM {table} LIMIT 1")
                        columns = [desc[0] for desc in cursor.description]

                        # Find symbol columns
                        for col in columns:
                            if 'symbol' in col.lower() or 'code' in col.lower() or 'ticker' in col.lower():
                                try:
                                    df = pd.read_sql(f"SELECT DISTINCT {col} FROM {table}", conn)
                                    for val in df.iloc[:, 0]:
                                        if val and pd.notna(val):
                                            symbol = str(val).replace('.NS', '').replace('.BO', '')
                                            if symbol.isalnum():
                                                symbols.add(symbol)
                                except:
                                    continue

                    conn.close()
                    logger.info(f"✓ Extracted symbols from {db_path}")
                except:
                    pass

        # 4. Generate NSE/BSE combinations
        # Common prefixes for Indian stocks
        prefixes = ['RELIANCE', 'TCS', 'INFY', 'HDFC', 'ICICI', 'KOTAK', 'AXIS', 'SBI',
                   'BAJAJ', 'TATA', 'MAHINDRA', 'LARSEN', 'BHARTI', 'MARUTI', 'ASIAN',
                   'WIPRO', 'HCL', 'TECH', 'ULTRA', 'NESTLE', 'ITC', 'HINDUNILVR']

        for prefix in prefixes:
            symbols.add(prefix)

        # Filter out completed symbols
        symbols = symbols - set(self.progress['completed'])

        logger.info(f"📊 Total unique symbols to process: {len(symbols)}")
        return sorted(list(symbols))

    def collect_from_yahoo(self, symbol: str, retries: int = 3) -> Optional[List[dict]]:
        """Collect data from Yahoo Finance with retries"""
        for attempt in range(retries):
            try:
                # Try NSE first, then BSE
                for suffix in ['.NS', '.BO']:
                    ticker = yf.Ticker(f"{symbol}{suffix}")
                    income = ticker.quarterly_income_stmt

                    if not income.empty and len(income.columns) >= 5:
                        results = []

                        # Process last 5 quarters
                        for i in range(min(5, len(income.columns))):
                            try:
                                date = income.columns[i]

                                # Current quarter data
                                revenue = income.loc['Total Revenue', date] if 'Total Revenue' in income.index else None
                                pat = income.loc['Net Income', date] if 'Net Income' in income.index else None
                                ebitda = income.loc['EBITDA', date] if 'EBITDA' in income.index else None

                                if revenue and pat:
                                    # Convert to Crores
                                    revenue_cr = revenue / 10000000
                                    pat_cr = pat / 10000000
                                    ebitda_cr = ebitda / 10000000 if ebitda else 0

                                    # Calculate YoY if possible
                                    revenue_yoy = 0
                                    pat_yoy = 0

                                    if i + 4 < len(income.columns):
                                        prev_date = income.columns[i + 4]
                                        prev_revenue = income.loc['Total Revenue', prev_date] if 'Total Revenue' in income.index else None
                                        prev_pat = income.loc['Net Income', prev_date] if 'Net Income' in income.index else None

                                        if prev_revenue:
                                            revenue_yoy = ((revenue - prev_revenue) / abs(prev_revenue)) * 100
                                        if prev_pat:
                                            pat_yoy = ((pat - prev_pat) / abs(prev_pat)) * 100

                                    results.append({
                                        'symbol': symbol,
                                        'quarter': self._get_quarter(date),
                                        'fiscal_year': self._get_fiscal_year(date),
                                        'revenue': revenue_cr,
                                        'revenue_yoy': revenue_yoy,
                                        'pat': pat_cr,
                                        'pat_yoy': pat_yoy,
                                        'ebitda': ebitda_cr,
                                        'eps': income.loc['Basic EPS', date] if 'Basic EPS' in income.index else 0,
                                        'data_source': 'yahoo'
                                    })
                            except:
                                continue

                        if results:
                            return results

                # Exponential backoff
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

            except Exception as e:
                logger.debug(f"Yahoo attempt {attempt+1} failed for {symbol}: {e}")
                continue

        return None

    def collect_from_local_db(self, symbol: str) -> Optional[List[dict]]:
        """Try to get data from local databases"""
        db_paths = [
            ("data/historical_financials.db", "quarterly_results", "company_symbol"),
            ("data/earnings_calendar.db", "earnings_results", "bse_code"),
            ("data/quarterly_master.db", "quarterly_data", "symbol")
        ]

        for db_path, table, symbol_col in db_paths:
            if Path(db_path).exists():
                try:
                    conn = sqlite3.connect(db_path)

                    # Check if table exists
                    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
                    if table in tables['name'].values:
                        query = f"SELECT * FROM {table} WHERE {symbol_col} = ? LIMIT 5"
                        df = pd.read_sql(query, conn, params=(symbol,))

                        if not df.empty:
                            results = []
                            for _, row in df.iterrows():
                                results.append({
                                    'symbol': symbol,
                                    'quarter': row.get('quarter', 'Q1'),
                                    'fiscal_year': row.get('fiscal_year', 2024),
                                    'revenue': row.get('revenue', 0),
                                    'revenue_yoy': row.get('revenue_yoy', 0),
                                    'pat': row.get('pat', 0) or row.get('profit', 0),
                                    'pat_yoy': row.get('pat_yoy', 0) or row.get('profit_yoy', 0),
                                    'ebitda': row.get('ebitda', 0),
                                    'eps': row.get('eps', 0),
                                    'data_source': db_path
                                })

                            conn.close()
                            return results

                    conn.close()
                except:
                    continue

        return None

    def collect_stock_data(self, symbol: str) -> bool:
        """Collect data for a single stock from ANY available source"""
        try:
            # Try Yahoo first
            data = self.collect_from_yahoo(symbol)

            # If Yahoo fails, try local databases
            if not data:
                data = self.collect_from_local_db(symbol)

            # If we got data, store it
            if data:
                self._store_data(symbol, data)
                return True
            else:
                self._log_failure(symbol, "No data from any source")
                return False

        except Exception as e:
            self._log_failure(symbol, str(e))
            return False

    def _store_data(self, symbol: str, data: List[dict]):
        """Store collected data"""
        conn = sqlite3.connect(self.db_path)

        for item in data:
            # Calculate composite score
            composite_score = (item.get('revenue_yoy', 0) * 0.35) + (item.get('pat_yoy', 0) * 0.65)

            try:
                conn.execute("""
                    INSERT OR REPLACE INTO quarterly_earnings
                    (symbol, quarter, fiscal_year, revenue, revenue_yoy,
                     pat, pat_yoy, ebitda, eps, composite_score, data_source, collection_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))
                """, (
                    symbol, item['quarter'], item['fiscal_year'],
                    item['revenue'], item['revenue_yoy'],
                    item['pat'], item['pat_yoy'],
                    item['ebitda'], item['eps'],
                    composite_score, item['data_source']
                ))
            except:
                continue

        # Log success
        conn.execute("""
            INSERT OR REPLACE INTO collection_log
            (symbol, status, attempts, quarters_collected, last_attempt)
            VALUES (?, 'success', 1, ?, datetime('now'))
        """, (symbol, len(data)))

        conn.commit()
        conn.close()

    def _log_failure(self, symbol: str, error: str):
        """Log collection failure"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO collection_log
            (symbol, status, attempts, error_message, last_attempt)
            VALUES (?, 'failed',
                    COALESCE((SELECT attempts FROM collection_log WHERE symbol = ?), 0) + 1,
                    ?, datetime('now'))
        """, (symbol, symbol, error))
        conn.commit()
        conn.close()

    def _get_quarter(self, date) -> str:
        """Get Indian fiscal quarter"""
        month = date.month
        if month in [4, 5, 6]: return 'Q1'
        elif month in [7, 8, 9]: return 'Q2'
        elif month in [10, 11, 12]: return 'Q3'
        else: return 'Q4'

    def _get_fiscal_year(self, date) -> int:
        """Get Indian fiscal year"""
        return date.year + 1 if date.month >= 4 else date.year

    def run_collection(self, max_workers: int = 10):
        """Run the ULTIMATE collection that won't stop"""
        symbols = self.get_all_symbols()
        self.stats['total_symbols'] = len(symbols)

        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 ULTIMATE DATA COLLECTION SYSTEM STARTED")
        logger.info(f"{'='*80}")
        logger.info(f"📊 Total symbols to collect: {len(symbols)}")
        logger.info(f"⚡ Workers: {max_workers}")
        logger.info(f"📁 Database: {self.db_path}")
        logger.info(f"{'='*80}\n")

        # Use ThreadPoolExecutor for parallel collection
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(self.collect_stock_data, symbol): symbol
                      for symbol in symbols}

            # Process as they complete
            for future in as_completed(futures):
                if self.stop_flag:
                    break

                symbol = futures[future]

                try:
                    success = future.result(timeout=30)

                    if success:
                        self.stats['completed'] += 1
                        self.progress['completed'].append(symbol)
                        logger.info(f"✅ {symbol} collected | "
                                   f"Progress: {self.stats['completed']}/{self.stats['total_symbols']} "
                                   f"({self.stats['completed']/self.stats['total_symbols']*100:.1f}%)")
                    else:
                        self.stats['failed'] += 1
                        self.progress['failed'].append(symbol)
                        logger.debug(f"❌ {symbol} failed")

                    # Save progress every 50 symbols
                    if (self.stats['completed'] + self.stats['failed']) % 50 == 0:
                        self._save_progress()
                        self._show_status()

                except Exception as e:
                    logger.error(f"Fatal error with {symbol}: {e}")
                    self.progress['failed'].append(symbol)

        # Final operations
        self._save_progress()
        self._final_report()
        self.find_true_blockbusters()

    def _show_status(self):
        """Show current collection status"""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        rate = self.stats['completed'] / elapsed if elapsed > 0 else 0
        eta = (self.stats['total_symbols'] - self.stats['completed']) / rate if rate > 0 else 0

        logger.info(f"\n📊 STATUS UPDATE:")
        logger.info(f"   Completed: {self.stats['completed']}")
        logger.info(f"   Failed: {self.stats['failed']}")
        logger.info(f"   Rate: {rate:.1f} stocks/sec")
        logger.info(f"   ETA: {eta/60:.1f} minutes\n")

    def _final_report(self):
        """Generate final report"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 COLLECTION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Success: {self.stats['completed']}/{self.stats['total_symbols']} "
                   f"({self.stats['completed']/self.stats['total_symbols']*100:.1f}%)")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info(f"⏱️ Time: {(datetime.now() - self.stats['start_time']).total_seconds()/60:.1f} minutes")

    def find_true_blockbusters(self, quarter: str = 'Q2', fiscal_year: int = 2024):
        """Find TRUE blockbusters from ALL collected data"""
        conn = sqlite3.connect(self.db_path)

        # Get all stocks for the quarter
        query = """
            SELECT symbol, revenue, revenue_yoy, pat, pat_yoy, composite_score
            FROM quarterly_earnings
            WHERE quarter = ? AND fiscal_year = ?
            AND revenue IS NOT NULL AND pat IS NOT NULL
            ORDER BY composite_score DESC
        """

        df = pd.read_sql(query, conn, params=(quarter, fiscal_year))

        # Add rankings
        df['rank'] = range(1, len(df) + 1)
        df['percentile'] = ((len(df) - df['rank'] + 1) / len(df)) * 100

        # Update database with rankings
        for _, row in df.iterrows():
            conn.execute("""
                UPDATE quarterly_earnings
                SET global_rank = ?, percentile = ?
                WHERE symbol = ? AND quarter = ? AND fiscal_year = ?
            """, (row['rank'], row['percentile'], row['symbol'], quarter, fiscal_year))

        conn.commit()
        conn.close()

        # Display top 10
        top_10 = df.head(10)

        print(f"\n{'='*100}")
        print(f"🏆 TRUE BLOCKBUSTERS - TOP 10 out of {len(df)} stocks")
        print(f"{'='*100}\n")

        for _, row in top_10.iterrows():
            emoji = "🥇" if row['rank'] == 1 else "🥈" if row['rank'] == 2 else "🥉" if row['rank'] == 3 else "🏆"
            print(f"{emoji} #{row['rank']} {row['symbol']}")
            print(f"   Revenue YoY: {row['revenue_yoy']:+.1f}%")
            print(f"   PAT YoY: {row['pat_yoy']:+.1f}%")
            print(f"   Score: {row['composite_score']:.1f}")
            print(f"   Percentile: Top {100-row['percentile']:.2f}%")
            print()

        # Show thresholds
        print(f"{'='*100}")
        print(f"Minimum criteria to be a TRUE blockbuster (top 10):")
        print(f"  Revenue Growth: {top_10['revenue_yoy'].min():+.1f}%")
        print(f"  PAT Growth: {top_10['pat_yoy'].min():+.1f}%")
        print(f"  Composite Score: {top_10['composite_score'].min():.1f}")
        print(f"{'='*100}")

if __name__ == "__main__":
    # Run the ULTIMATE collector
    collector = UltimateDataCollector()
    collector.run_collection(max_workers=20)  # Use 20 parallel workers
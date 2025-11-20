#!/usr/bin/env python3
"""
ACCURATE BLOCKBUSTER FINDER

This script correctly collects and calculates YoY growth from Yahoo Finance
to find the TRUE top performers in the Indian stock market.
"""

import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AccurateBlockbusterFinder:
    def __init__(self):
        self.db_path = "data/accurate_blockbusters.db"
        Path("data").mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database with correct schema"""
        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_results (
                symbol TEXT,
                quarter_date DATE,
                revenue REAL,
                revenue_yoy REAL,
                pat REAL,
                pat_yoy REAL,
                composite_score REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, quarter_date)
            )
        """)

        conn.commit()
        conn.close()

    def collect_accurate_data(self, symbols=None):
        """Collect accurate data with proper YoY calculations"""

        if symbols is None:
            # Default to major Indian stocks
            symbols = [
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
                'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT',
                'HINDUNILVR', 'AXISBANK', 'BAJFINANCE', 'MARUTI', 'HCLTECH',
                'ASIANPAINT', 'NESTLEIND', 'WIPRO', 'TATAMOTORS', 'ULTRACEMCO',
                'TECHM', 'TITAN', 'ONGC', 'JSWSTEEL', 'SUNPHARMA',
                'ADANIENT', 'ADANIPORTS', 'POWERGRID', 'NTPC', 'COALINDIA',
                'BAJAJFINSV', 'DRREDDY', 'HDFC', 'M&M', 'TATASTEEL'
            ]

            # Try to load more from files
            try:
                from agents.trading.nse_500_symbols import NSE_500_SYMBOLS
                symbols.extend([s.replace('.NS', '') for s in NSE_500_SYMBOLS])
            except:
                pass

        # Remove duplicates
        symbols = list(set(symbols))

        logger.info(f"Collecting accurate data for {len(symbols)} stocks...")

        conn = sqlite3.connect(self.db_path)
        successful = 0

        for i, symbol in enumerate(symbols, 1):
            try:
                # Try NSE first
                ticker = yf.Ticker(f"{symbol}.NS")
                quarterly = ticker.quarterly_income_stmt

                if quarterly.empty:
                    # Try BSE
                    ticker = yf.Ticker(f"{symbol}.BO")
                    quarterly = ticker.quarterly_income_stmt

                if not quarterly.empty and len(quarterly.columns) >= 5:
                    # Get latest quarter and YoY comparison
                    latest = quarterly.columns[0]
                    yoy = quarterly.columns[4]  # Same quarter last year

                    # Extract metrics
                    revenue = quarterly.loc['Total Revenue', latest] if 'Total Revenue' in quarterly.index else None
                    revenue_yoy_val = quarterly.loc['Total Revenue', yoy] if 'Total Revenue' in quarterly.index else None
                    pat = quarterly.loc['Net Income', latest] if 'Net Income' in quarterly.index else None
                    pat_yoy_val = quarterly.loc['Net Income', yoy] if 'Net Income' in quarterly.index else None

                    if all([revenue, revenue_yoy_val, pat, pat_yoy_val]):
                        # Calculate YoY growth
                        revenue_growth = ((revenue - revenue_yoy_val) / abs(revenue_yoy_val)) * 100
                        pat_growth = ((pat - pat_yoy_val) / abs(pat_yoy_val)) * 100

                        # Composite score (35% revenue, 65% profit)
                        composite = (revenue_growth * 0.35) + (pat_growth * 0.65)

                        # Store in database
                        conn.execute("""
                            INSERT OR REPLACE INTO quarterly_results
                            (symbol, quarter_date, revenue, revenue_yoy, pat, pat_yoy, composite_score)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            symbol,
                            latest.strftime('%Y-%m-%d'),
                            revenue / 10000000,  # Convert to Crores
                            revenue_growth,
                            pat / 10000000,  # Convert to Crores
                            pat_growth,
                            composite
                        ))

                        successful += 1

                        if pat_growth > 100:  # Log exceptional performers
                            logger.info(f"✓ {symbol}: PAT Growth {pat_growth:.1f}%, Score {composite:.1f}")

                # Progress update
                if i % 10 == 0:
                    conn.commit()
                    logger.info(f"Progress: {i}/{len(symbols)} ({successful} successful)")

                # Rate limiting
                time.sleep(0.2)

            except Exception as e:
                logger.debug(f"Error with {symbol}: {e}")
                continue

        conn.commit()
        conn.close()

        logger.info(f"Collection complete: {successful}/{len(symbols)} stocks with data")

        return successful

    def find_true_blockbusters(self):
        """Find the ACTUAL top performers with accurate data"""

        conn = sqlite3.connect(self.db_path)

        # Get all stocks ordered by composite score
        query = """
            SELECT symbol, revenue, revenue_yoy, pat, pat_yoy, composite_score
            FROM quarterly_results
            WHERE revenue_yoy IS NOT NULL AND pat_yoy IS NOT NULL
            ORDER BY composite_score DESC
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            logger.warning("No data found in database")
            return

        total_stocks = len(df)

        print("\n" + "="*100)
        print(f"🏆 TRUE BLOCKBUSTERS - TOP 10 out of {total_stocks} stocks (Based on ACCURATE Data)")
        print("="*100 + "\n")

        for i, row in df.head(10).iterrows():
            rank = i + 1
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"

            print(f"{emoji} RANK #{rank}: {row['symbol']}")
            print(f"   📈 Revenue: ₹{row['revenue']:.0f} Cr (Growth: {row['revenue_yoy']:+.1f}%)")
            print(f"   💰 PAT: ₹{row['pat']:.0f} Cr (Growth: {row['pat_yoy']:+.1f}%)")
            print(f"   🎯 Composite Score: {row['composite_score']:.1f}")
            print(f"   📊 Percentile: Top {(rank/total_stocks)*100:.2f}%")
            print()

        # Statistics
        top_10 = df.head(10)

        print("="*100)
        print("📊 TRUE BLOCKBUSTER CRITERIA (From Actual Data):")
        print("="*100)
        print(f"To be in the TOP 10 ({(10/total_stocks)*100:.1f}% of market):")
        print(f"   • Minimum Revenue Growth: {top_10['revenue_yoy'].min():+.1f}%")
        print(f"   • Minimum PAT Growth: {top_10['pat_yoy'].min():+.1f}%")
        print(f"   • Minimum Composite Score: {top_10['composite_score'].min():.1f}")
        print()
        print(f"Average of Top 10:")
        print(f"   • Avg Revenue Growth: {top_10['revenue_yoy'].mean():+.1f}%")
        print(f"   • Avg PAT Growth: {top_10['pat_yoy'].mean():+.1f}%")
        print()

        # Compare with old criteria
        old_criteria = df[(df['revenue_yoy'] > 15) & (df['pat_yoy'] > 20)]
        print(f"Old criteria (Rev>15%, PAT>20%) would select: {len(old_criteria)} stocks")
        print(f"True blockbuster approach selects: 10 stocks")

        if len(old_criteria) > 10:
            print(f"\nThat's {len(old_criteria)/10:.1f}x too many 'blockbusters'!")

        return df

def main():
    finder = AccurateBlockbusterFinder()

    # Collect accurate data
    logger.info("Starting accurate data collection...")
    stocks_collected = finder.collect_accurate_data()

    # Find true blockbusters
    if stocks_collected > 0:
        finder.find_true_blockbusters()

if __name__ == "__main__":
    main()
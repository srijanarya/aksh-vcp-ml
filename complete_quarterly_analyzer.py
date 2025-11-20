#!/usr/bin/env python3
"""
COMPLETE QUARTERLY ANALYZER - YoY and QoQ Analysis

This script performs comprehensive quarterly analysis:
1. Year-over-Year (YoY) - Same quarter last year
2. Quarter-on-Quarter (QoQ) - Previous quarter sequential
3. Momentum tracking - Acceleration/deceleration
4. Trend analysis - Multiple quarter patterns
"""

import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteQuarterlyAnalyzer:
    def __init__(self):
        self.db_path = "data/complete_quarterly_analysis.db"
        Path("data").mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database with comprehensive schema"""
        conn = sqlite3.connect(self.db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_analysis (
                symbol TEXT,
                quarter_date DATE,

                -- Absolute values (in Crores)
                revenue REAL,
                pat REAL,
                ebitda REAL,
                eps REAL,

                -- YoY Growth (Year-over-Year)
                revenue_yoy REAL,
                pat_yoy REAL,
                ebitda_yoy REAL,
                eps_yoy REAL,

                -- QoQ Growth (Quarter-on-Quarter)
                revenue_qoq REAL,
                pat_qoq REAL,
                ebitda_qoq REAL,
                eps_qoq REAL,

                -- Momentum indicators
                revenue_momentum TEXT,  -- accelerating/decelerating/stable
                pat_momentum TEXT,

                -- Composite scores
                yoy_score REAL,
                qoq_score REAL,
                combined_score REAL,

                -- Trend analysis
                quarters_of_growth INTEGER,
                trend_strength TEXT,  -- strong/moderate/weak/negative

                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, quarter_date)
            )
        """)

        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_yoy_score ON quarterly_analysis(yoy_score DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_qoq_score ON quarterly_analysis(qoq_score DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_combined ON quarterly_analysis(combined_score DESC)")

        conn.commit()
        conn.close()

    def analyze_stock(self, symbol: str, suffix: str = '.NS'):
        """Perform complete quarterly analysis for a stock"""
        try:
            ticker = yf.Ticker(f"{symbol}{suffix}")
            quarterly = ticker.quarterly_income_stmt

            if quarterly.empty:
                # Try BSE if NSE fails
                ticker = yf.Ticker(f"{symbol}.BO")
                quarterly = ticker.quarterly_income_stmt

            if quarterly.empty or len(quarterly.columns) < 5:
                return None

            results = []

            # Analyze each quarter
            for i in range(min(8, len(quarterly.columns))):  # Last 8 quarters
                quarter_date = quarterly.columns[i]

                # Extract current quarter metrics
                revenue = quarterly.loc['Total Revenue', quarter_date] if 'Total Revenue' in quarterly.index else None
                pat = quarterly.loc['Net Income', quarter_date] if 'Net Income' in quarterly.index else None
                ebitda = quarterly.loc['EBITDA', quarter_date] if 'EBITDA' in quarterly.index else None
                eps = quarterly.loc['Basic EPS', quarter_date] if 'Basic EPS' in quarterly.index else None

                if not (revenue and pat):
                    continue

                quarter_data = {
                    'symbol': symbol,
                    'quarter_date': quarter_date.strftime('%Y-%m-%d'),
                    'revenue': revenue / 10000000,  # Convert to Crores
                    'pat': pat / 10000000,
                    'ebitda': ebitda / 10000000 if ebitda else 0,
                    'eps': eps if eps else 0
                }

                # Calculate YoY (Year-over-Year)
                if i + 4 < len(quarterly.columns):
                    yoy_date = quarterly.columns[i + 4]

                    yoy_revenue = quarterly.loc['Total Revenue', yoy_date] if 'Total Revenue' in quarterly.index else None
                    yoy_pat = quarterly.loc['Net Income', yoy_date] if 'Net Income' in quarterly.index else None

                    if yoy_revenue:
                        quarter_data['revenue_yoy'] = ((revenue - yoy_revenue) / abs(yoy_revenue)) * 100
                    if yoy_pat:
                        quarter_data['pat_yoy'] = ((pat - yoy_pat) / abs(yoy_pat)) * 100

                    # YoY Score (35% revenue, 65% profit)
                    quarter_data['yoy_score'] = (
                        quarter_data.get('revenue_yoy', 0) * 0.35 +
                        quarter_data.get('pat_yoy', 0) * 0.65
                    )

                # Calculate QoQ (Quarter-on-Quarter)
                if i + 1 < len(quarterly.columns):
                    qoq_date = quarterly.columns[i + 1]

                    qoq_revenue = quarterly.loc['Total Revenue', qoq_date] if 'Total Revenue' in quarterly.index else None
                    qoq_pat = quarterly.loc['Net Income', qoq_date] if 'Net Income' in quarterly.index else None

                    if qoq_revenue:
                        quarter_data['revenue_qoq'] = ((revenue - qoq_revenue) / abs(qoq_revenue)) * 100
                    if qoq_pat:
                        quarter_data['pat_qoq'] = ((pat - qoq_pat) / abs(qoq_pat)) * 100

                    # QoQ Score
                    quarter_data['qoq_score'] = (
                        quarter_data.get('revenue_qoq', 0) * 0.35 +
                        quarter_data.get('pat_qoq', 0) * 0.65
                    )

                # Calculate momentum (comparing QoQ growth rates)
                if i + 2 < len(quarterly.columns) and 'revenue_qoq' in quarter_data:
                    prev_qoq_date = quarterly.columns[i + 2]
                    prev_revenue = quarterly.loc['Total Revenue', prev_qoq_date] if 'Total Revenue' in quarterly.index else None

                    if prev_revenue and qoq_revenue:
                        prev_qoq_growth = ((qoq_revenue - prev_revenue) / abs(prev_revenue)) * 100

                        # Determine momentum
                        if quarter_data['revenue_qoq'] > prev_qoq_growth + 5:
                            quarter_data['revenue_momentum'] = 'accelerating'
                        elif quarter_data['revenue_qoq'] < prev_qoq_growth - 5:
                            quarter_data['revenue_momentum'] = 'decelerating'
                        else:
                            quarter_data['revenue_momentum'] = 'stable'

                # Combined score (60% YoY, 40% QoQ)
                quarter_data['combined_score'] = (
                    quarter_data.get('yoy_score', 0) * 0.6 +
                    quarter_data.get('qoq_score', 0) * 0.4
                )

                # Count consecutive quarters of growth
                growth_count = 0
                for j in range(i, min(i + 4, len(quarterly.columns) - 1)):
                    curr = quarterly.loc['Net Income', quarterly.columns[j]] if 'Net Income' in quarterly.index else 0
                    prev = quarterly.loc['Net Income', quarterly.columns[j + 1]] if 'Net Income' in quarterly.index else 0
                    if curr and prev and curr > prev:
                        growth_count += 1
                    else:
                        break
                quarter_data['quarters_of_growth'] = growth_count

                # Determine trend strength
                if quarter_data.get('yoy_score', 0) > 50 and quarter_data.get('qoq_score', 0) > 10:
                    quarter_data['trend_strength'] = 'strong'
                elif quarter_data.get('yoy_score', 0) > 20 and quarter_data.get('qoq_score', 0) > 0:
                    quarter_data['trend_strength'] = 'moderate'
                elif quarter_data.get('yoy_score', 0) > 0 or quarter_data.get('qoq_score', 0) > 0:
                    quarter_data['trend_strength'] = 'weak'
                else:
                    quarter_data['trend_strength'] = 'negative'

                results.append(quarter_data)

            return results

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def collect_and_analyze(self, symbols=None):
        """Collect and analyze multiple stocks"""

        if symbols is None:
            # Default major stocks
            symbols = [
                'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'TATAMOTORS',
                'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'WIPRO',
                'BAJFINANCE', 'MARUTI', 'HCLTECH', 'ASIANPAINT',
                'ULTRACEMCO', 'TECHM', 'TITAN', 'JSWSTEEL', 'HINDPETRO',
                'ESCORTS', 'LAURUSLABS', 'BIOCON', 'NAUKRI', 'TATASTEEL'
            ]

        conn = sqlite3.connect(self.db_path)
        successful = 0

        logger.info(f"Analyzing {len(symbols)} stocks with YoY and QoQ...")

        for symbol in symbols:
            results = self.analyze_stock(symbol)

            if results:
                for data in results:
                    try:
                        # Insert into database
                        columns = ', '.join(data.keys())
                        placeholders = ', '.join(['?' for _ in data])
                        query = f"INSERT OR REPLACE INTO quarterly_analysis ({columns}) VALUES ({placeholders})"
                        conn.execute(query, list(data.values()))
                    except Exception as e:
                        logger.debug(f"Error storing {symbol}: {e}")

                successful += 1
                latest = results[0]  # Most recent quarter

                # Log exceptional performers
                if latest.get('yoy_score', 0) > 100:
                    logger.info(f"🚀 {symbol}: YoY Score {latest['yoy_score']:.1f}, QoQ Score {latest.get('qoq_score', 0):.1f}")
                elif latest.get('qoq_score', 0) > 20:
                    logger.info(f"📈 {symbol}: Strong QoQ momentum {latest['qoq_score']:.1f}%")

        conn.commit()
        conn.close()

        logger.info(f"Analysis complete: {successful}/{len(symbols)} stocks analyzed")

        return successful

    def find_blockbusters(self, criteria='combined'):
        """Find top performers based on different criteria"""

        conn = sqlite3.connect(self.db_path)

        # Get latest quarter for each stock
        query = """
            WITH latest_quarters AS (
                SELECT symbol, MAX(quarter_date) as latest_date
                FROM quarterly_analysis
                GROUP BY symbol
            )
            SELECT qa.*
            FROM quarterly_analysis qa
            JOIN latest_quarters lq ON qa.symbol = lq.symbol AND qa.quarter_date = lq.latest_date
            WHERE qa.revenue_yoy IS NOT NULL AND qa.pat_yoy IS NOT NULL
        """

        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            logger.warning("No data found")
            return

        # Sort based on criteria
        if criteria == 'yoy':
            df = df.sort_values('yoy_score', ascending=False)
            score_col = 'yoy_score'
            title = "TOP PERFORMERS - Year-over-Year (YoY)"
        elif criteria == 'qoq':
            df = df.sort_values('qoq_score', ascending=False)
            score_col = 'qoq_score'
            title = "TOP PERFORMERS - Quarter-on-Quarter (QoQ)"
        else:  # combined
            df = df.sort_values('combined_score', ascending=False)
            score_col = 'combined_score'
            title = "TOP PERFORMERS - Combined (YoY + QoQ)"

        print("\n" + "="*100)
        print(f"🏆 {title}")
        print("="*100 + "\n")

        for i, row in df.head(10).iterrows():
            rank = i + 1
            emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"

            print(f"{emoji} RANK #{rank}: {row['symbol']}")
            print(f"   📈 YoY: Revenue {row['revenue_yoy']:+.1f}%, PAT {row['pat_yoy']:+.1f}% (Score: {row['yoy_score']:.1f})")

            if pd.notna(row['revenue_qoq']) and pd.notna(row['pat_qoq']):
                print(f"   📊 QoQ: Revenue {row['revenue_qoq']:+.1f}%, PAT {row['pat_qoq']:+.1f}% (Score: {row.get('qoq_score', 0):.1f})")

            print(f"   🎯 Combined Score: {row['combined_score']:.1f}")

            if pd.notna(row['revenue_momentum']):
                print(f"   🔄 Momentum: Revenue {row['revenue_momentum']}")

            if row['quarters_of_growth'] > 0:
                print(f"   📉 Consecutive Growth: {row['quarters_of_growth']} quarters")

            print(f"   💪 Trend: {row['trend_strength'].upper()}")
            print()

        # Show different perspectives
        print("="*100)
        print("📊 DIFFERENT PERSPECTIVES:")
        print("="*100)

        # Best QoQ momentum
        qoq_best = df.nlargest(3, 'qoq_score')
        print("\n🚀 Best QoQ Momentum (Sequential Growth):")
        for _, row in qoq_best.iterrows():
            print(f"   • {row['symbol']}: QoQ Score {row.get('qoq_score', 0):.1f} (Rev {row['revenue_qoq']:+.1f}%, PAT {row['pat_qoq']:+.1f}%)")

        # Most consistent (high quarters of growth)
        consistent = df.nlargest(3, 'quarters_of_growth')
        print("\n📈 Most Consistent (Consecutive Growth):")
        for _, row in consistent.iterrows():
            print(f"   • {row['symbol']}: {row['quarters_of_growth']} quarters of growth")

        # Accelerating momentum
        accelerating = df[df['revenue_momentum'] == 'accelerating'].head(3)
        if not accelerating.empty:
            print("\n⚡ Accelerating Momentum:")
            for _, row in accelerating.iterrows():
                print(f"   • {row['symbol']}: Revenue momentum accelerating")

        return df

def main():
    analyzer = CompleteQuarterlyAnalyzer()

    # Collect and analyze
    logger.info("Starting comprehensive quarterly analysis...")
    analyzer.collect_and_analyze()

    # Show results from different perspectives
    print("\n" + "="*100)
    print("COMPLETE QUARTERLY ANALYSIS - YoY AND QoQ")
    print("="*100)

    # Show combined top performers
    analyzer.find_blockbusters('combined')

    # Show YoY leaders
    print("\n")
    analyzer.find_blockbusters('yoy')

    # Show QoQ momentum leaders
    print("\n")
    analyzer.find_blockbusters('qoq')

if __name__ == "__main__":
    main()
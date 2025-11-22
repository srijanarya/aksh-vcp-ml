#!/usr/bin/env python3
"""
Simple Quarterly Earnings Collector

Collects quarterly earnings data for all Indian stocks to find true blockbusters.
"""

import yfinance as yf
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_quarterly_data():
    """Collect quarterly earnings for top 100 stocks"""
    
    # Create database
    Path("data").mkdir(exist_ok=True)
    conn = sqlite3.connect("data/quarterly_master.db")
    
    # Create table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quarterly_data (
            symbol TEXT,
            quarter TEXT,
            fiscal_year INTEGER,
            revenue REAL,
            revenue_yoy REAL,
            pat REAL,
            pat_yoy REAL,
            composite_score REAL,
            PRIMARY KEY (symbol, quarter, fiscal_year)
        )
    """)
    
    # Sample of top Indian stocks
    stocks = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT",
        "HINDUNILVR", "AXISBANK", "BAJFINANCE", "MARUTI", "HCLTECH",
        "ASIANPAINT", "NESTLEIND", "WIPRO", "TATAMOTORS", "ULTRACEMCO",
        "TECHM", "TITAN", "ONGC", "JSWSTEEL", "SUNPHARMA"
    ]
    
    logger.info(f"Collecting data for {len(stocks)} stocks...")
    
    collected = 0
    for symbol in stocks:
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            income = ticker.quarterly_income_stmt
            
            if not income.empty and len(income.columns) >= 5:
                # Get latest quarter
                latest_date = income.columns[0]
                yoy_date = income.columns[4]  # Same quarter last year
                
                # Extract metrics
                if 'Total Revenue' in income.index and 'Net Income' in income.index:
                    revenue = income.loc['Total Revenue', latest_date]
                    pat = income.loc['Net Income', latest_date]
                    prev_revenue = income.loc['Total Revenue', yoy_date]
                    prev_pat = income.loc['Net Income', yoy_date]
                    
                    if all(pd.notna([revenue, pat, prev_revenue, prev_pat])):
                        # Convert to Crores
                        revenue_cr = revenue / 10000000
                        pat_cr = pat / 10000000
                        
                        # Calculate YoY
                        revenue_yoy = ((revenue - prev_revenue) / abs(prev_revenue)) * 100
                        pat_yoy = ((pat - prev_pat) / abs(prev_pat)) * 100
                        
                        # Composite score
                        score = (revenue_yoy * 0.4) + (pat_yoy * 0.6)
                        
                        # Store in database
                        conn.execute("""
                            INSERT OR REPLACE INTO quarterly_data
                            VALUES (?, 'Q2', 2024, ?, ?, ?, ?, ?)
                        """, (symbol, revenue_cr, revenue_yoy, pat_cr, pat_yoy, score))
                        
                        collected += 1
                        logger.info(f"✓ {symbol}: Rev YoY {revenue_yoy:.1f}%, PAT YoY {pat_yoy:.1f}%")
            
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            logger.debug(f"✗ {symbol}: {e}")
    
    conn.commit()
    
    # Find top performers
    logger.info(f"\n{'='*60}")
    logger.info("TOP 10 TRUE BLOCKBUSTERS (Q2 FY2024)")
    logger.info(f"{'='*60}")
    
    df = pd.read_sql("""
        SELECT * FROM quarterly_data
        ORDER BY composite_score DESC
        LIMIT 10
    """, conn)
    
    for i, row in df.iterrows():
        emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏆"
        print(f"\n{emoji} #{i+1} {row['symbol']}")
        print(f"   Revenue Growth: {row['revenue_yoy']:+.1f}%")
        print(f"   PAT Growth: {row['pat_yoy']:+.1f}%")
        print(f"   Score: {row['composite_score']:.1f}")
    
    conn.close()
    logger.info(f"\n✅ Collected data for {collected}/{len(stocks)} stocks")

if __name__ == "__main__":
    collect_quarterly_data()

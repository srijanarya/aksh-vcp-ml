import logging
import time
import sqlite3
import pandas as pd
from tools.screener_client import ScreenerClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BSE Code to NSE Symbol mapping (from backfill_angel_one_data.py)
BSE_CODES = [
    '500325', '500112', '532540', '500209', '500180', 
    '532174', '500696', '500010', '532215', '500820',
    '532504', '500410', '532281', '507815', '500440',
    '532712', '532483', '532977', '500034', '532454',
    '500387', '500570', '532555', '500547', '532868'
]

def backfill_financials():
    client = ScreenerClient()
    conn = sqlite3.connect("data/historical_financials.db")
    cursor = conn.cursor()
    
    # Ensure table exists (it should, but just in case)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_financials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bse_code TEXT NOT NULL,
            year INTEGER,
            quarter TEXT,
            revenue REAL,
            pat REAL,
            operating_profit REAL,
            eps REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(bse_code, year, quarter) ON CONFLICT REPLACE
        )
    """)
    
    success_count = 0
    
    for bse_code in BSE_CODES:
        logger.info(f"Processing {bse_code}...")
        
        # 1. Search for company to get URL slug
        company = client.search_company(bse_code)
        if not company:
            logger.warning(f"Could not find company for {bse_code}")
            continue
            
        # Extract slug correctly
        # URL format: /company/RELIANCE/ or /company/RELIANCE/consolidated/
        raw_url = company['url']
        logger.info(f"Raw URL: {raw_url}")
        
        if '/company/' in raw_url:
            parts = raw_url.split('/company/')[1].split('/')
            url_slug = parts[0]
        else:
            logger.warning(f"Unexpected URL format: {raw_url}")
            continue
            
        logger.info(f"Found {company['name']} ({url_slug})")
        
        # 2. Fetch quarterly results (12 quarters = 3 years)
        time.sleep(1) # Polite delay
        df = client.get_quarterly_results(url_slug, num_quarters=12)
        
        if df.empty:
            logger.warning(f"No data for {bse_code}")
            continue
            
        # 3. Store in DB
        records_count = 0
        for _, row in df.iterrows():
            # Calculate operating_profit if only OPM is available
            # ScreenerClient returns 'opm'
            opm = row.get('opm', 0)
            revenue = row.get('revenue', 0)
            operating_profit = (opm / 100) * revenue if revenue else 0
            
            cursor.execute("""
                INSERT OR REPLACE INTO historical_financials 
                (bse_code, year, quarter, revenue, pat, operating_profit, eps)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                bse_code, 
                row['fy_year'], 
                row['quarter'], 
                row['revenue'], 
                row['pat'], 
                operating_profit, 
                row['eps']
            ))
            records_count += 1
            
        conn.commit()
        logger.info(f"Saved {records_count} quarters for {bse_code}")
        success_count += 1
        
    conn.close()
    logger.info(f"Backfill complete. Processed {success_count}/{len(BSE_CODES)} companies.")

if __name__ == "__main__":
    backfill_financials()

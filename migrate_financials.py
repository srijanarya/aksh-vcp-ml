import sqlite3
import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_financials():
    source_db = "data/earnings_calendar.db"
    target_db = "data/historical_financials.db"
    
    if not os.path.exists(source_db):
        logger.error(f"Source DB {source_db} not found")
        return
        
    # 1. Create target table
    conn_target = sqlite3.connect(target_db)
    cursor_target = conn_target.cursor()
    
    cursor_target.execute("DROP TABLE IF EXISTS historical_financials")
    
    cursor_target.execute("""
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
    conn_target.commit()
    
    # 2. Read from source
    conn_source = sqlite3.connect(source_db)
    query = """
        SELECT bse_code, fiscal_year, quarter, revenue, profit, eps 
        FROM earnings 
        WHERE revenue IS NOT NULL OR profit IS NOT NULL
    """
    df = pd.read_sql_query(query, conn_source)
    conn_source.close()
    
    logger.info(f"Read {len(df)} records from {source_db}")
    
    if df.empty:
        logger.warning("No financial records found to migrate")
        return

    # 3. Transform
    # Clean fiscal_year (e.g., "FY2025" -> 2025)
    def clean_year(y):
        if pd.isna(y): return None
        y_str = str(y).upper()
        if y_str.startswith('FY'):
            return int(y_str.replace('FY', ''))
        try:
            return int(y)
        except:
            return None
            
    df['year'] = df['fiscal_year'].apply(clean_year)
    
    # Rename columns
    df = df.rename(columns={'profit': 'pat'})
    
    # Add missing columns
    df['operating_profit'] = None # Not available in source
    
    # Select final columns
    final_df = df[['bse_code', 'year', 'quarter', 'revenue', 'pat', 'operating_profit', 'eps']]
    
    # 4. Write to target
    records = final_df.to_dict('records')
    
    cursor_target.executemany("""
        INSERT OR REPLACE INTO historical_financials 
        (bse_code, year, quarter, revenue, pat, operating_profit, eps)
        VALUES (:bse_code, :year, :quarter, :revenue, :pat, :operating_profit, :eps)
    """, records)
    
    conn_target.commit()
    conn_target.close()
    
    logger.info(f"Successfully migrated {len(records)} records to {target_db}")

if __name__ == "__main__":
    migrate_financials()

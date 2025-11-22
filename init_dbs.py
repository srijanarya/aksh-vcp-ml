"""
Initialize Database Schemas

This script creates the necessary SQLite tables for the ML system if they don't exist.
Useful for setting up the environment before running pipelines.
"""

import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_BASE_PATH = "/Users/srijan/Desktop/aksh/data"

def init_price_db():
    db_path = os.path.join(DB_BASE_PATH, "price_movements.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS price_movements (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bse_code TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            UNIQUE(bse_code, date)
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Initialized {db_path}")

def init_financials_db():
    db_path = os.path.join(DB_BASE_PATH, "historical_financials.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historical_financials (
            financial_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bse_code TEXT NOT NULL,
            quarter TEXT NOT NULL,
            year INTEGER NOT NULL,
            revenue_cr REAL,
            pat_cr REAL,
            eps REAL,
            opm REAL,
            npm REAL,
            extraction_confidence REAL,
            pdf_url TEXT,
            UNIQUE(bse_code, quarter, year)
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Initialized {db_path}")

def init_labels_db():
    db_path = os.path.join(DB_BASE_PATH, "upper_circuit_labels.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS upper_circuit_labels (
            label_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bse_code TEXT NOT NULL,
            date DATE NOT NULL,
            upper_circuit INTEGER,
            UNIQUE(bse_code, date)
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Initialized {db_path}")
    
def init_earnings_db():
    db_path = os.path.join(DB_BASE_PATH, "earnings_calendar.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS earnings (
            earnings_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bse_code TEXT NOT NULL,
            announcement_date DATE NOT NULL,
            pdf_url TEXT,
            UNIQUE(bse_code, announcement_date)
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"Initialized {db_path}")

def main():
    logger.info("Initializing databases...")
    init_price_db()
    init_financials_db()
    init_labels_db()
    init_earnings_db()
    logger.info("Database initialization complete.")

if __name__ == "__main__":
    main()

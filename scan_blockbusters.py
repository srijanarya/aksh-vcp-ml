#!/usr/bin/env python3
"""
True Blockbuster Scanner (0.01% Filter)

Scans for stocks that meet the strict "True Blockbuster" criteria:
1. Verified Fundamentals (Sales/Profit > 25%)
2. Technical Strength (Price > 200DMA, RSI > 50)
3. High Data Confidence
"""

import os
import sys
import logging
import sqlite3
import argparse
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.ml.true_blockbuster_detector import TrueBlockbusterDetector
from tools.telegram_bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("blockbuster_scan.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_recent_companies(db_path: str, days: int = 30) -> pd.DataFrame:
    """Fetch companies with recent earnings announcements"""
    try:
        conn = sqlite3.connect(db_path)
        query = f"""
            SELECT DISTINCT bse_code, company_name, announcement_date
            FROM earnings_results 
            WHERE extraction_status = 'extracted'
            AND announcement_date >= date('now', '-{days} days')
            ORDER BY announcement_date DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Database error: {e}")
        return pd.DataFrame()

def scan_market(days_back: int = 30):
    """
    Main scanning function using TrueBlockbusterDetector
    """
    logger.info(f"🚀 Starting True Blockbuster Scan (Last {days_back} days)...")
    
    detector = TrueBlockbusterDetector()
    bot = TelegramBot()
    
    db_path = "/Users/srijan/Desktop/aksh/data/earnings_calendar.db"
    if not os.path.exists(db_path):
        # Fallback for testing if DB doesn't exist
        logger.warning(f"Database not found at {db_path}, using local path")
        db_path = "data/earnings_calendar.db"
    
    companies = get_recent_companies(db_path, days_back)
    
    if companies.empty:
        logger.warning("No recent earnings found to scan.")
        return

    logger.info(f"Scanning {len(companies)} companies...")
    
    blockbusters_found = 0
    
    for _, row in companies.iterrows():
        bse_code = row['bse_code']
        name = row['company_name']
        
        try:
            result = detector.analyze_stock(bse_code, name)
            
            if result['is_blockbuster']:
                blockbusters_found += 1
                logger.info(f"🌟 BLOCKBUSTER FOUND: {name} ({bse_code})")
                
                # Send Telegram Alert
                message = (
                    f"🌟 *TRUE BLOCKBUSTER DETECTED* 🌟\n\n"
                    f"🏢 *{name}* ({bse_code})\n"
                    f"📊 Score: {result['score']}/100\n\n"
                    f"✅ *Why it qualifies:*\n"
                )
                for reason in result['reasons']:
                    message += f"• {reason}\n"
                
                message += f"\n⚠️ *Confidence:* Verified by Data Validator"
                
                bot.send_message(message)
                
            else:
                logger.info(f"   {name}: Score {result['score']} - {', '.join(result['failures'][:1])}")
                    
        except Exception as e:
            logger.error(f"Error analyzing {name}: {e}")
            continue
            
    logger.info(f"Scan complete. Found {blockbusters_found} True Blockbusters.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='True Blockbuster Scanner')
    parser.add_argument('--days', type=int, default=30, help='Days to look back')
    args = parser.parse_args()
    
    scan_market(args.days)

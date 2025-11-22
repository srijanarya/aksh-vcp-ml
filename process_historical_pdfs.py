#!/usr/bin/env python3
"""
Process Historical PDFs with OCR

This script:
1. Fetches PDF URLs from earnings_calendar.db (earnings table)
2. Downloads them using tools.pdf_downloader
3. Extracts data using the OCR-enhanced IndianFinancialPDFExtractor
4. Updates the database with extracted results
"""

import os
import sys
import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from indian_pdf_extractor import IndianFinancialPDFExtractor
from tools.pdf_downloader import download_pdf_with_retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("historical_pdf_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_PATH = "data/earnings_calendar.db"
PDF_CACHE_DIR = "data/cache/pdfs"

def setup_db():
    """Ensure database has necessary columns for extraction status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist, if not add them (idempotent check)
    # We'll use extraction_status to track progress
    
    conn.commit()
    conn.close()

def process_historical_pdfs():
    """Main processing loop"""
    logger.info("🚀 Starting Historical PDF Processing with OCR...")
    
    # Ensure cache dir exists
    Path(PDF_CACHE_DIR).mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch records with PDFs
    cursor.execute("""
        SELECT id, company_name, bse_code, pdf_url, extraction_status 
        FROM earnings 
        WHERE pdf_url IS NOT NULL 
        AND pdf_url != ''
        AND (extraction_status IS NULL OR extraction_status != 'extracted')
    """)
    
    records = cursor.fetchall()
    logger.info(f"Found {len(records)} PDFs to process")
    
    extractor = IndianFinancialPDFExtractor()
    
    success_count = 0
    
    for row in records:
        record_id = row['id']
        company = row['company_name']
        url = row['pdf_url']
        
        logger.info(f"\nProcessing {company} (ID: {record_id})...")
        logger.info(f"URL: {url}")
        
        try:
            # 1. Download PDF
            pdf_path = Path(PDF_CACHE_DIR) / f"{record_id}.pdf"
            
            if not pdf_path.exists():
                downloaded_path = download_pdf_with_retry(
                    url, 
                    save_path=pdf_path,
                    max_retries=2
                )
                if not downloaded_path:
                    logger.error(f"Failed to download PDF for {company}")
                    cursor.execute("UPDATE earnings SET extraction_status = 'download_failed' WHERE id = ?", (record_id,))
                    conn.commit()
                    continue
            else:
                logger.info("Using cached PDF")
            
            # 2. Extract Data (with OCR fallback)
            result = extractor.extract_from_pdf(str(pdf_path))
            
            if result['status'] == 'success':
                data = result['data']
                logger.info(f"✅ Extraction Success for {company}")
                logger.info(f"   Revenue: {data.get('revenue', {}).get('current_quarter_cr')}")
                logger.info(f"   Profit: {data.get('profit', {}).get('current_quarter_cr')}")
                
                # 3. Update Database
                # We update the 'earnings' table directly with extracted values
                # Note: The schema might need adjustment if we want to store strict YoY/QoQ
                
                rev = data.get('revenue', {}).get('current_quarter_cr')
                pat = data.get('profit', {}).get('current_quarter_cr')
                eps = data.get('eps', {}).get('current_quarter_cr')
                
                cursor.execute("""
                    UPDATE earnings 
                    SET revenue = ?, 
                        profit = ?, 
                        eps = ?,
                        extraction_status = 'extracted',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (rev, pat, eps, record_id))
                
                success_count += 1
                
            else:
                logger.warning(f"❌ Extraction Failed for {company}: {result.get('error')}")
                cursor.execute("UPDATE earnings SET extraction_status = 'extraction_failed' WHERE id = ?", (record_id,))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error processing {company}: {e}")
            continue
            
    conn.close()
    logger.info(f"\nProcessing Complete. Successfully extracted {success_count}/{len(records)} PDFs.")

if __name__ == "__main__":
    process_historical_pdfs()

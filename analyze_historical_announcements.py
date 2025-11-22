#!/usr/bin/env python3
"""
Historical Announcement Analysis

Process historical announcements from earnings_calendar.db and identify
the best performers in the current quarter based on extracted intelligence.
"""

import sqlite3
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.intelligence.intelligence_extractor import IntelligenceExtractor
from src.intelligence.announcement_classifier import AnnouncementClassifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoricalAnnouncementAnalyzer:
    """
    Analyzes historical announcements to find top quarterly performers
    """
    
    def __init__(self):
        self.extractor = IntelligenceExtractor()
        self.classifier = AnnouncementClassifier()
        self.earnings_db = "data/earnings_calendar.db"
        self.intelligence_db = "data/historical_intelligence.db"
        self._init_db()
    
    def _init_db(self):
        """Create database for historical intelligence"""
        conn = sqlite3.connect(self.intelligence_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_announcements (
                id INTEGER PRIMARY KEY,
                bse_code TEXT,
                company_name TEXT,
                announcement_date TEXT,
                pdf_url TEXT,
                category TEXT,
                extraction_status TEXT,
                intelligence_data JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_rankings (
                quarter TEXT,
                year INTEGER,
                rank INTEGER,
                bse_code TEXT,
                company_name TEXT,
                revenue_growth_yoy REAL,
                profit_growth_yoy REAL,
                revenue_cr REAL,
                profit_cr REAL,
                score REAL,
                PRIMARY KEY (quarter, year, bse_code)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def process_historical_announcements(self, limit=100):
        """
        Process historical announcements from earnings_calendar.db
        """
        logger.info(f"Processing up to {limit} historical announcements...")
        
        # Connect to earnings DB
        earnings_conn = sqlite3.connect(self.earnings_db)
        earnings_conn.row_factory = sqlite3.Row
        earnings_cursor = earnings_conn.cursor()
        
        # Get announcements with PDFs
        earnings_cursor.execute("""
            SELECT bse_code, company_name, announcement_date, pdf_url
            FROM earnings
            WHERE pdf_url IS NOT NULL
            AND pdf_url != ''
            ORDER BY announcement_date DESC
            LIMIT ?
        """, (limit,))
        
        announcements = earnings_cursor.fetchall()
        earnings_conn.close()
        
        logger.info(f"Found {len(announcements)} announcements with PDFs")
        
        # Process each
        processed = 0
        for ann in announcements:
            try:
                # Check if already processed
                if self._is_processed(ann['bse_code'], ann['announcement_date']):
                    continue
                
                # Classify
                mock_ann = {
                    'title': 'Financial Results',
                    'category': 'Results',
                    'description': 'Quarterly results'
                }
                category = self.classifier.classify(mock_ann)
                
                # Extract intelligence (only for EARNINGS)
                intelligence_data = {}
                status = 'skipped'
                
                if category == self.classifier.CAT_EARNINGS:
                    # Download and extract
                    pdf_path = Path("data/cache/pdfs") / f"{ann['bse_code']}_{ann['announcement_date']}.pdf"
                    
                    from tools.pdf_downloader import download_pdf_with_retry
                    if download_pdf_with_retry(ann['pdf_url'], pdf_path):
                        result = self.extractor.extract_intelligence(
                            {'id': ann['bse_code'], 'pdf_url': ann['pdf_url']},
                            category
                        )
                        intelligence_data = result.get('extracted_data', {})
                        status = result.get('status', 'failed')
                
                # Store
                self._store_intelligence(ann, category, status, intelligence_data)
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed} announcements...")
                    
            except Exception as e:
                logger.error(f"Error processing {ann['company_name']}: {e}")
                continue
        
        logger.info(f"✅ Processed {processed} announcements")
        return processed
    
    def _is_processed(self, bse_code, date):
        """Check if already processed"""
        conn = sqlite3.connect(self.intelligence_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM historical_announcements WHERE bse_code = ? AND announcement_date = ?",
            (bse_code, date)
        )
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def _store_intelligence(self, ann, category, status, intelligence_data):
        """Store intelligence"""
        conn = sqlite3.connect(self.intelligence_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO historical_announcements
            (bse_code, company_name, announcement_date, pdf_url, category, extraction_status, intelligence_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ann['bse_code'],
            ann['company_name'],
            ann['announcement_date'],
            ann['pdf_url'],
            category,
            status,
            json.dumps(intelligence_data)
        ))
        
        conn.commit()
        conn.close()
    
    def find_top_quarterly_performers(self, quarter='Q3', year=2024, top_n=10):
        """
        Find top performers in a specific quarter based on growth
        """
        logger.info(f"Finding top {top_n} performers for {quarter} {year}...")
        
        conn = sqlite3.connect(self.intelligence_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all successful extractions
        cursor.execute("""
            SELECT * FROM historical_announcements
            WHERE extraction_status = 'success'
            AND intelligence_data IS NOT NULL
        """)
        
        companies = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row['intelligence_data'])
                
                # Calculate score based on available metrics
                score = 0
                revenue_growth = 0
                profit_growth = 0
                revenue_cr = 0
                profit_cr = 0
                
                # Extract growth metrics
                if 'revenue' in data:
                    rev = data['revenue']
                    if 'current_quarter_cr' in rev:
                        revenue_cr = rev['current_quarter_cr']
                    if 'yoy_quarter_cr' in rev and 'current_quarter_cr' in rev:
                        if rev['yoy_quarter_cr'] > 0:
                            revenue_growth = ((rev['current_quarter_cr'] - rev['yoy_quarter_cr']) / rev['yoy_quarter_cr'] * 100)
                            score += revenue_growth * 0.4  # 40% weight
                
                if 'profit' in data:
                    prof = data['profit']
                    if 'current_quarter_cr' in prof:
                        profit_cr = prof['current_quarter_cr']
                    if 'yoy_quarter_cr' in prof and 'current_quarter_cr' in prof:
                        if prof['yoy_quarter_cr'] > 0:
                            profit_growth = ((prof['current_quarter_cr'] - prof['yoy_quarter_cr']) / prof['yoy_quarter_cr'] * 100)
                            score += profit_growth * 0.6  # 60% weight
                
                if score > 0:  # Only include companies with positive growth
                    companies.append({
                        'bse_code': row['bse_code'],
                        'company_name': row['company_name'],
                        'revenue_growth': revenue_growth,
                        'profit_growth': profit_growth,
                        'revenue_cr': revenue_cr,
                        'profit_cr': profit_cr,
                        'score': score
                    })
            except Exception as e:
                logger.warning(f"Error parsing data for {row['company_name']}: {e}")
                continue
        
        conn.close()
        
        # Sort by score
        companies.sort(key=lambda x: x['score'], reverse=True)
        top_performers = companies[:top_n]
        
        # Store rankings
        self._store_rankings(quarter, year, top_performers)
        
        return top_performers
    
    def _store_rankings(self, quarter, year, performers):
        """Store quarterly rankings"""
        conn = sqlite3.connect(self.intelligence_db)
        cursor = conn.cursor()
        
        for i, perf in enumerate(performers, 1):
            cursor.execute("""
                INSERT OR REPLACE INTO quarterly_rankings
                (quarter, year, rank, bse_code, company_name, revenue_growth_yoy, profit_growth_yoy, revenue_cr, profit_cr, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                quarter, year, i,
                perf['bse_code'],
                perf['company_name'],
                perf['revenue_growth'],
                perf['profit_growth'],
                perf['revenue_cr'],
                perf['profit_cr'],
                perf['score']
            ))
        
        conn.commit()
        conn.close()

if __name__ == "__main__":
    analyzer = HistoricalAnnouncementAnalyzer()
    
    # Process historical announcements
    print("=" * 80)
    print("HISTORICAL ANNOUNCEMENT ANALYSIS")
    print("=" * 80)
    
    processed = analyzer.process_historical_announcements(limit=50)
    
    # Find top performers
    print("\n" + "=" * 80)
    print("TOP QUARTERLY PERFORMERS")
    print("=" * 80)
    
    top = analyzer.find_top_quarterly_performers(top_n=10)
    
    print(f"\n{'Rank':<6} {'Company':<40} {'Revenue Gr%':<12} {'Profit Gr%':<12} {'Score':<8}")
    print("-" * 90)
    for i, company in enumerate(top, 1):
        print(f"{i:<6} {company['company_name'][:38]:<40} {company['revenue_growth']:>10.1f}% {company['profit_growth']:>10.1f}% {company['score']:>6.1f}")

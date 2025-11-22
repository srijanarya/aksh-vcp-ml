"""
Real-time Earnings Agent

This agent listens for BSE alerts, downloads the PDF, extracts financial data,
and determines if it's a "Blockbuster Result".
"""

import logging
import asyncio
import sqlite3
from datetime import datetime
from typing import Dict, Optional

from agents.ml.indian_pdf_extractor import IndianPDFExtractor

logger = logging.getLogger(__name__)

class RealtimeEarningsAgent:
    """Processes real-time earnings alerts"""
    
    def __init__(self, db_path: str = "data/earnings_calendar.db"):
        self.db_path = db_path
        self.pdf_extractor = IndianPDFExtractor()
        self._init_db()
        
    def _init_db(self):
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS earnings_analysis (
                bse_code TEXT,
                announcement_date DATETIME,
                revenue REAL,
                net_profit REAL,
                eps REAL,
                revenue_growth REAL,
                pat_growth REAL,
                is_blockbuster BOOLEAN,
                pdf_url TEXT,
                PRIMARY KEY (bse_code, announcement_date)
            )
        """)
        conn.commit()
        conn.close()
        
    async def process_alert(self, alert: Dict) -> Optional[Dict]:
        """
        Process a single alert from Telegram.
        
        Args:
            alert: Dict containing 'bse_code', 'pdf_url', 'subject'
            
        Returns:
            Dict with analysis results or None if failed
        """
        logger.info(f"Processing alert for {alert.get('bse_code')}")
        
        if not alert.get('pdf_url'):
            logger.warning("No PDF URL in alert")
            return None
            
        # 1. Extract Data from PDF
        financials = self.pdf_extractor.extract_financial_data(alert['pdf_url'])
        
        if not financials:
            logger.error("Failed to extract financials")
            return None
            
        # 2. Analyze for Blockbuster Status
        is_blockbuster = self._is_blockbuster(financials)
        
        # 3. Store Result
        self._store_result(alert['bse_code'], financials, is_blockbuster, alert['pdf_url'])
        
        # 4. Notify (Log for now)
        if is_blockbuster:
            logger.info(f"🚀 BLOCKBUSTER DETECTED: {alert['bse_code']} - Rev Growth: {financials['revenue_growth']}%, PAT Growth: {financials['pat_growth']}%")
        else:
            logger.info(f"Standard Result: {alert['bse_code']}")
            
        # 5. Return Result
        return {
            "bse_code": alert['bse_code'],
            "is_blockbuster": is_blockbuster,
            "financials": financials,
            "timestamp": datetime.now().isoformat()
        }
            
    def _is_blockbuster(self, financials: Dict) -> bool:
        """Determine if results are blockbuster"""
        # Criteria:
        # 1. Revenue Growth > 15%
        # 2. PAT Growth > 20%
        # 3. Positive EPS
        
        if (financials['revenue_growth'] > 15.0 and 
            financials['pat_growth'] > 20.0 and 
            financials['eps'] > 0):
            return True
        return False
        
    def _store_result(self, bse_code: str, financials: Dict, is_blockbuster: bool, pdf_url: str):
        """Save analysis to DB"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO earnings_analysis 
            (bse_code, announcement_date, revenue, net_profit, eps, revenue_growth, pat_growth, is_blockbuster, pdf_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bse_code, 
            datetime.now(),
            financials['revenue'],
            financials['net_profit'],
            financials['eps'],
            financials['revenue_growth'],
            financials['pat_growth'],
            is_blockbuster,
            pdf_url
        ))
        conn.commit()
        conn.close()

# Example usage (Simulated)
async def main():
    agent = RealtimeEarningsAgent()
    
    # Simulate an alert
    test_alert = {
        "bse_code": "500325",
        "pdf_url": "https://www.bseindia.com/xml-data/corpfiling/AttachLive/8d8d8d8d-8d8d-8d8d-8d8d-8d8d8d8d8d8d.pdf", # Fake URL
        "subject": "Financial Results"
    }
    
    # Note: This will fail to download the fake PDF, but shows the flow
    await agent.process_alert(test_alert)

if __name__ == "__main__":
    asyncio.run(main())

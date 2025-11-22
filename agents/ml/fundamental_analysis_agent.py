"""
Fundamental Analysis Agent

This agent orchestrates the collection and analysis of fundamental data:
1. Fetches announcements (Order wins, Results)
2. Parses PDF/Text content
3. Extracts key metrics (Revenue growth, Order book)
4. Computes sentiment scores
"""

import logging
import sqlite3
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.bse_announcement_fetcher import BSEAnnouncementFetcher
from agents.ml.indian_pdf_extractor import extract_financial_data

logger = logging.getLogger(__name__)

class FundamentalAnalysisAgent:
    """Analyzes fundamental data for stocks"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.fetcher = BSEAnnouncementFetcher()
        self._init_db()
        
    def _init_db(self):
        """Initialize database table"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fundamental_features (
                bse_code TEXT,
                date DATE,
                sentiment_score REAL,
                order_win_value REAL,
                revenue_growth_announced REAL,
                pat_growth_announced REAL,
                PRIMARY KEY (bse_code, date)
            )
        """)
        conn.commit()
        conn.close()
        
    def analyze_company(self, bse_code: str, start_date: str, end_date: str):
        """Analyze a company's announcements"""
        logger.info(f"Analyzing fundamentals for {bse_code}...")
        
        announcements = self.fetcher.fetch_announcements(bse_code, start_date, end_date)
        
        conn = sqlite3.connect(self.db_path)
        
        for ann in announcements:
            # Simple logic to extract metrics from text
            sentiment = 0.0
            order_value = 0.0
            rev_growth = 0.0
            pat_growth = 0.0
            
            text = ann['body'].lower()
            
            if "order worth" in text:
                sentiment = 0.8
                # Extract number (simplified)
                words = text.split()
                for i, w in enumerate(words):
                    if w == "rs." and i+1 < len(words):
                        try:
                            order_value = float(words[i+1])
                        except:
                            pass
                            
            if "revenue up" in text:
                sentiment = 0.6
                # Extract growth
                try:
                    rev_growth = float(text.split("revenue up")[1].split("%")[0])
                except:
                    pass
                    
            conn.execute("""
                INSERT OR REPLACE INTO fundamental_features 
                (bse_code, date, sentiment_score, order_win_value, revenue_growth_announced, pat_growth_announced)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (ann['bse_code'], ann['date'], sentiment, order_value, rev_growth, pat_growth))
            
        conn.commit()
        conn.close()
        logger.info(f"Analyzed {len(announcements)} announcements for {bse_code}")

if __name__ == "__main__":
    agent = FundamentalAnalysisAgent("data/features/fundamental_features.db")
    agent.analyze_company("500325", "2024-01-01", "2024-03-31")

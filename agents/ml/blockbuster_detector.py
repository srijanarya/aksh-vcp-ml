"""
Blockbuster Detector using VCP Earnings Database

Uses the earnings_results table which already contains quarterly financials
to detect blockbuster results based on YoY growth.
"""

import logging
import sqlite3
import sys
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

class BlockbusterDetector:
    """
    Detects blockbuster quarterly results using existing VCP earnings data
    
    Criteria:
    1. Revenue Growth YoY > 15%
    2. Profit (PAT) Growth YoY > 20%
    3. EPS > 0 and growing
    """
    
    def __init__(self, earnings_db_path: str = "/home/ubuntu/vcp/data/earnings_calendar.db"):
        self.earnings_db = earnings_db_path
        self._init_alerts_table()
    
    def _init_alerts_table(self):
        """Initialize table for storing blockbuster alerts"""
        conn = sqlite3.connect(self.earnings_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blockbuster_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT,
                bse_code TEXT,
                quarter TEXT,
                fiscal_year TEXT,
                announcement_date DATE,
                revenue REAL,
                profit REAL,
                eps REAL,
                revenue_yoy_growth REAL,
                profit_yoy_growth REAL,
                eps_growth REAL,
                is_blockbuster BOOLEAN,
                blockbuster_score INTEGER,
                criteria_met TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alerted BOOLEAN DEFAULT 0,
                UNIQUE(bse_code, quarter, fiscal_year)
            )
        """)
        conn.commit()
        conn.close()
    
    def analyze_company(self, bse_code: str, company_name: str = None) -> Tuple[bool, Dict]:
        """
        Analyze if a company's latest results are blockbuster
        
        Args:
            bse_code: BSE company code
            company_name: Optional company name
            
        Returns:
            (is_blockbuster, details_dict)
        """
        try:
            conn = sqlite3.connect(self.earnings_db)
            
            # Get last 5 quarters of data for this company
            df = pd.read_sql("""
                SELECT 
                    company_name,
                    bse_code,
                    quarter,
                    fiscal_year,
                    announcement_date,
                    revenue,
                    profit,
                    eps,
                    extraction_status
                FROM earnings_results
                WHERE bse_code = ?
                AND extraction_status = 'completed'
                AND revenue IS NOT NULL
                AND profit IS NOT NULL
                AND eps IS NOT NULL
                ORDER BY announcement_date DESC
                LIMIT 5
            """, conn, params=(bse_code,))
            
            conn.close()
            
            if len(df) < 5:
                logger.warning(f"Insufficient data for {bse_code}: only {len(df)} quarters with extracted data")
                return False, {'error': 'insufficient_data', 'quarters_found': len(df)}
            
            # Current quarter (most recent)
            current = df.iloc[0]
            # YoY comparison (same quarter last year)
            yoy = df.iloc[4]
            
            # Calculate YoY growth
            revenue_yoy = self._calculate_growth(current['revenue'], yoy['revenue'])
            profit_yoy = self._calculate_growth(current['profit'], yoy['profit'])
            eps_growth = self._calculate_growth(current['eps'], yoy['eps'])
            
            # Apply blockbuster criteria
            criteria_met = []
            is_blockbuster = True
            
            if revenue_yoy > 15.0:
                criteria_met.append(f"Revenue YoY {revenue_yoy:.1f}% > 15%")
            else:
                is_blockbuster = False
            
            if profit_yoy > 20.0:
                criteria_met.append(f"Profit YoY {profit_yoy:.1f}% > 20%")
            else:
                is_blockbuster = False
            
            if current['eps'] > 0:
                criteria_met.append(f"EPS ₹{current['eps']:.2f} > 0")
            else:
                is_blockbuster = False
            
            # Calculate blockbuster score (0-100)
            score = self._calculate_score(revenue_yoy, profit_yoy, current['eps'], eps_growth)
            
            result = {
                'company_name': current['company_name'],
                'bse_code': bse_code,
                'quarter': current['quarter'],
                'fiscal_year': current['fiscal_year'],
                'quarter_text': f"{current['quarter']} FY{current['fiscal_year']}",
                'announcement_date': current['announcement_date'],
                'revenue': current['revenue'],
                'pat': current['profit'],
                'eps': current['eps'],
                'revenue_yoy': revenue_yoy,
                'pat_yoy': profit_yoy,
                'eps_growth': eps_growth,
                'is_blockbuster': is_blockbuster,
                'blockbuster_score': score,
                'criteria_met': ' | '.join(criteria_met) if criteria_met else 'None',
                'quarters_analyzed': len(df)
            }
            
            # Store in database
            self._store_result(result)
            
            return is_blockbuster, result
            
        except Exception as e:
            logger.error(f"Error analyzing {bse_code}: {e}")
            return False, {'error': str(e)}
    
    def _calculate_growth(self, current: float, previous: float) -> float:
        """Calculate percentage growth"""
        if previous == 0 or pd.isna(previous) or pd.isna(current):
            return 0.0
        return ((current - previous) / abs(previous)) * 100
    
    def _calculate_score(self, revenue_yoy: float, profit_yoy: float, eps: float, eps_growth: float) -> int:
        """
        Calculate blockbuster score (0-100)
        
        Scoring:
        - Revenue YoY: up to 30 points (0-15% = 0, 15-50% = 30)
        - Profit YoY: up to 40 points (0-20% = 0, 20-60% = 40)
        - EPS: up to 20 points (based on absolute value)
        - EPS Growth: up to 10 points
        """
        score = 0
        
        # Revenue component (30 points)
        if revenue_yoy > 15:
            score += min(30, int((revenue_yoy - 15) / 35 * 30))
        
        # Profit component (40 points)
        if profit_yoy > 20:
            score += min(40, int((profit_yoy - 20) / 40 * 40))
        
        # EPS component (20 points)
        if eps > 0:
            score += min(20, int(eps / 100 * 20))  # Normalized by ₹100
        
        # EPS Growth component (10 points)
        if eps_growth > 0:
            score += min(10, int(eps_growth / 50 * 10))
        
        return min(100, score)
    
    def _store_result(self, result: Dict):
        """Store blockbuster analysis result"""
        conn = sqlite3.connect(self.earnings_db)
        conn.execute("""
            INSERT OR REPLACE INTO blockbuster_alerts
            (company_name, bse_code, quarter, fiscal_year, announcement_date,
             revenue, profit, eps, revenue_yoy_growth, profit_yoy_growth, eps_growth,
             is_blockbuster, blockbuster_score, criteria_met)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result['company_name'],
            result['bse_code'],
            result['quarter'],
            result['fiscal_year'],
            result.get('announcement_date'),
            result['revenue'],
            result['pat'],
            result['eps'],
            result['revenue_yoy'],
            result['pat_yoy'],
            result['eps_growth'],
            result['is_blockbuster'],
            result['blockbuster_score'],
            result['criteria_met']
        ))
        conn.commit()
        conn.close()
    
    def get_pending_alerts(self) -> pd.DataFrame:
        """Get blockbuster alerts that haven't been sent yet"""
        conn = sqlite3.connect(self.earnings_db)
        df = pd.read_sql("""
            SELECT * FROM blockbuster_alerts
            WHERE is_blockbuster = 1 AND alerted = 0
            ORDER BY blockbuster_score DESC, created_at DESC
        """, conn)
        conn.close()
        return df
    
    def mark_as_alerted(self, alert_id: int):
        """Mark an alert as sent"""
        conn = sqlite3.connect(self.earnings_db)
        conn.execute("UPDATE blockbuster_alerts SET alerted = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    detector = BlockbusterDetector("/home/ubuntu/vcp/data/earnings_calendar.db")
    
    # Test with a company that has data
    print("=" * 80)
    print("BLOCKBUSTER DETECTOR TEST (Using VCP Database)")
    print("=" * 80)
    
    # Get a few companies with recent earnings
    conn = sqlite3.connect("/home/ubuntu/vcp/data/earnings_calendar.db")
    recent_companies = pd.read_sql("""
        SELECT DISTINCT bse_code, company_name
        FROM earnings_results
        WHERE extraction_status = 'extracted'
        AND revenue IS NOT NULL
        LIMIT 5
    """, conn)
    conn.close()
    
    for _, row in recent_companies.iterrows():
        print(f"\n{'='*80}")
        print(f"Analyzing: {row['company_name']} ({row['bse_code']})")
        print(f"{'='*80}")
        
        is_blockbuster, result = detector.analyze_company(row['bse_code'], row['company_name'])
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue
        
        print(f"\nQuarter: {result['quarter_text']}")
        print(f"Revenue: ₹{result['revenue']:.0f} Cr ({result['revenue_yoy']:+.2f}% YoY)")
        print(f"Profit: ₹{result['pat']:.0f} Cr ({result['pat_yoy']:+.2f}% YoY)")
        print(f"EPS: ₹{result['eps']:.2f} ({result['eps_growth']:+.2f}% YoY)")
        print(f"\nBlockbuster Score: {result['blockbuster_score']}/100")
        print(f"Criteria Met: {result['criteria_met']}")
        
        if is_blockbuster:
            print(f"\n🚀 BLOCKBUSTER DETECTED!")
        else:
            print(f"\n📊 Standard Result")

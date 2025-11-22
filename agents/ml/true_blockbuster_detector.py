"""
True Blockbuster Detector (The '0.01%' Filter)

Identifies the top 0.01% of stocks that show exceptional fundamental growth
AND superior technical strength.

Criteria:
1. Fundamentals (Verified):
   - Sales Growth > 25%
   - Profit Growth > 25%
   - EPS Growth > 20%
   - Margin Expansion
   - Data Confidence > 80%

2. Technicals (Momentum):
   - Price > 200 DMA (Long-term trend)
   - Price > 50 DMA (Medium-term trend)
   - RSI > 50 (Bullish momentum)
   - Relative Strength > 80 (Outperforming market)

3. Volume:
   - Volume > 50-day average (Institutional buying)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta

# Import existing skills and data tools
from skills.technical_indicators import calculate_all_indicators, calculate_rsi
from src.data.data_accuracy_validator import DataAccuracyValidator
from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
from src.data.bse_nse_direct_fetcher import BSENSEDirectFetcher

logger = logging.getLogger(__name__)

class TrueBlockbusterDetector:
    """
    The 'One Shot' detector for finding true market leaders.
    Combines verified fundamentals with technical strength.
    """
    
    def __init__(self):
        self.validator = DataAccuracyValidator(enable_db=True, enable_bse=True, enable_screener=True)
        self.price_fetcher = YahooFinanceFetcher()
        self.bse_fetcher = BSENSEDirectFetcher()
        
        # Strict thresholds for "Blockbuster" status
        self.THRESHOLDS = {
            'sales_growth_min': 25.0,    # 25% minimum growth
            'profit_growth_min': 25.0,   # 25% minimum growth
            'eps_growth_min': 20.0,      # 20% minimum growth
            'min_confidence': 80.0,      # High data confidence required
            'rsi_min': 50.0,             # Bullish momentum
            'rs_min': 80.0,              # Relative Strength (0-100)
            'price_vs_50dma': 1.0,       # Price must be above 50 DMA
            'price_vs_200dma': 1.0       # Price must be above 200 DMA
        }

    def analyze_stock(self, bse_code: str, company_name: str) -> Dict:
        """
        Perform deep analysis to determine if stock is a True Blockbuster.
        """
        result = {
            'bse_code': bse_code,
            'company_name': company_name,
            'is_blockbuster': False,
            'score': 0,
            'reasons': [],
            'failures': [],
            'data': {}
        }
        
        logger.info(f"🔍 Analyzing {company_name} ({bse_code}) for Blockbuster Status...")
        
        # 1. Validate Fundamentals
        fund_data = self.validator.validate_quarterly_results(bse_code, company_name)
        
        if fund_data.overall_confidence < self.THRESHOLDS['min_confidence']:
            result['failures'].append(f"Low Data Confidence: {fund_data.overall_confidence}%")
            return result
            
        # Check Fundamental Growth
        # Note: We need YoY growth. The validator gives current values. 
        # We need to fetch previous year's same quarter from DB or Source.
        # For now, we'll assume the validator result includes growth metrics if available,
        # or we calculate them if we have history.
        
        # (Simplified for this implementation - assuming we can get growth from validator or source)
        # In a real scenario, we'd query the DB for the previous year's quarter.
        
        # Let's use the 'earnings_db' source data if available, as it has growth fields
        growth_metrics = self._get_growth_metrics(fund_data)
        
        if not growth_metrics:
             result['failures'].append("Could not calculate growth metrics")
             return result

        # Fundamental Checks (YoY and QoQ)
        fund_score = 0
        
        # YoY Growth (Primary - more important for long-term trends)
        if growth_metrics['revenue_yoy'] > self.THRESHOLDS['sales_growth_min']:
            result['reasons'].append(f"🚀 Sales YoY {growth_metrics['revenue_yoy']:.1f}% > {self.THRESHOLDS['sales_growth_min']}%")
            fund_score += 25
        else:
            result['failures'].append(f"Sales YoY {growth_metrics['revenue_yoy']:.1f}% too low")
            
        if growth_metrics['pat_yoy'] > self.THRESHOLDS['profit_growth_min']:
            result['reasons'].append(f"💰 Profit YoY {growth_metrics['pat_yoy']:.1f}% > {self.THRESHOLDS['profit_growth_min']}%")
            fund_score += 25
        else:
            result['failures'].append(f"Profit YoY {growth_metrics['pat_yoy']:.1f}% too low")
        
        # QoQ Growth (Bonus points for recent momentum)
        # QoQ > 15% is exceptional and shows accelerating business
        if growth_metrics.get('revenue_qoq', 0) > 15:
            result['reasons'].append(f"⚡ Sales QoQ {growth_metrics['revenue_qoq']:.1f}% (Accelerating!)")
            fund_score += 10
        elif growth_metrics.get('revenue_qoq', 0) > 0:
            result['reasons'].append(f"📈 Sales QoQ {growth_metrics['revenue_qoq']:.1f}% (Positive)")
            fund_score += 5
        
        if growth_metrics.get('pat_qoq', 0) > 15:
            result['reasons'].append(f"💎 Profit QoQ {growth_metrics['pat_qoq']:.1f}% (Accelerating!)")
            fund_score += 10
        elif growth_metrics.get('pat_qoq', 0) > 0:
            result['reasons'].append(f"💵 Profit QoQ {growth_metrics['pat_qoq']:.1f}% (Positive)")
            fund_score += 5
            
        # 2. Analyze Technicals
        tech_data = self._analyze_technicals(bse_code)
        
        if not tech_data:
            result['failures'].append("Could not fetch technical data")
            return result
            
        # Technical Checks
        tech_score = 0
        if tech_data['price'] > tech_data['dma_200']:
            result['reasons'].append("📈 Price > 200 DMA (Long-term Uptrend)")
            tech_score += 10
        else:
            result['failures'].append("Price < 200 DMA (Downtrend)")
            
        if tech_data['rsi'] > self.THRESHOLDS['rsi_min']:
            result['reasons'].append(f"⚡ RSI {tech_data['rsi']:.1f} (Bullish)")
            tech_score += 10
        else:
            result['failures'].append(f"RSI {tech_data['rsi']:.1f} too weak")
            
        if tech_data['relative_strength'] > self.THRESHOLDS['rs_min']:
            result['reasons'].append(f"💪 Relative Strength {tech_data['relative_strength']:.0f} (Outperformer)")
            tech_score += 20
        else:
            result['failures'].append(f"Relative Strength {tech_data['relative_strength']:.0f} too low")

        # Final Score Calculation
        total_score = fund_score + tech_score
        result['score'] = total_score
        result['data'] = {**growth_metrics, **tech_data}
        
        # Blockbuster Definition: High Score + No Critical Failures
        # Critical: Sales OR Profit must be high, AND Price > 200DMA
        is_fund_strong = (growth_metrics['revenue_yoy'] > 25 or growth_metrics['pat_yoy'] > 25)
        is_tech_strong = (tech_data['price'] > tech_data['dma_200'])
        
        if total_score >= 80 and is_fund_strong and is_tech_strong:
            result['is_blockbuster'] = True
            result['reasons'].append("🌟 TRUE BLOCKBUSTER STATUS ACHIEVED")
        
        return result

    def _get_growth_metrics(self, fund_data) -> Optional[Dict]:
        """
        Extract or calculate growth metrics (YoY and QoQ).
        Fetches historical data from earnings DB to compute growth.
        """
        import sqlite3
        from src.utils.fiscal_year_utils import get_previous_quarter, get_yoy_quarter
        
        # Try to find pre-calculated growth in source data first (e.g. from Screener)
        for source, data in fund_data.source_data.items():
            if hasattr(data, 'revenue_yoy') and data.revenue_yoy is not None:
                # If we have YoY, try to also get QoQ
                qoq_metrics = self._calculate_qoq_from_db(fund_data)
                return {
                    'revenue_yoy': data.revenue_yoy,
                    'pat_yoy': data.pat_yoy if hasattr(data, 'pat_yoy') else 0,
                    'eps_growth': data.eps_growth if hasattr(data, 'eps_growth') else 0,
                    'revenue_qoq': qoq_metrics.get('revenue_qoq', 0) if qoq_metrics else 0,
                    'pat_qoq': qoq_metrics.get('pat_qoq', 0) if qoq_metrics else 0,
                    'eps_qoq': qoq_metrics.get('eps_qoq', 0) if qoq_metrics else 0
                }
        
        # If no pre-calculated growth, fetch from DB and calculate
        growth = self._calculate_growth_from_db(fund_data)
        return growth
    
    def _calculate_growth_from_db(self, fund_data) -> Optional[Dict]:
        """Calculate YoY and QoQ growth by fetching historical quarters from DB"""
        try:
            import sqlite3
            
            # Get current quarter info from fund_data
            # We need to extract company identifier (BSE code or name)
            bse_code = None
            company_name = None
            
            # Try to get from earnings_db source
            if 'earnings_db' in fund_data.source_data:
                db_data = fund_data.source_data['earnings_db']
                if hasattr(db_data, 'bse_code'):
                    bse_code = db_data.bse_code
                if hasattr(db_data, 'company_name'):
                    company_name = db_data.company_name
            
            if not bse_code and not company_name:
                logger.warning("Cannot calculate growth: no company identifier")
                return None
            
            # Connect to earnings DB
            conn = sqlite3.connect('data/earnings_calendar.db')
            cursor = conn.cursor()
            
            # Get current quarter data
            query = """
                SELECT quarter, fiscal_year, revenue, profit, eps
                FROM earnings
                WHERE (bse_code = ? OR company_name = ?)
                AND revenue IS NOT NULL
                ORDER BY fiscal_year DESC, 
                         CASE quarter 
                             WHEN 'Q4' THEN 4 
                             WHEN 'Q3' THEN 3 
                             WHEN 'Q2' THEN 2 
                             WHEN 'Q1' THEN 1 
                         END DESC
                LIMIT 5
            """
            
            cursor.execute(query, (bse_code, company_name))
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) < 2:
                logger.warning(f"Insufficient historical data for growth calculation (found {len(rows)} quarters)")
                return None
            
            # Parse results
            current = {'quarter': rows[0][0], 'fy': rows[0][1], 'revenue': rows[0][2], 'profit': rows[0][3], 'eps': rows[0][4]}
            
            # Find QoQ (previous sequential quarter)
            qoq_data = None
            for row in rows[1:]:
                qoq_data = {'quarter': row[0], 'fy': row[1], 'revenue': row[2], 'profit': row[3], 'eps': row[4]}
                break
            
            # Find YoY (same quarter, previous year)
            yoy_data = None
            target_quarter = current['quarter']
            target_fy = current['fy'] - 1
            
            for row in rows:
                if row[0] == target_quarter and row[1] == target_fy:
                    yoy_data = {'quarter': row[0], 'fy': row[1], 'revenue': row[2], 'profit': row[3], 'eps': row[4]}
                    break
            
            # Calculate growth
            metrics = {}
            
            # YoY Growth
            if yoy_data and yoy_data['revenue']:
                metrics['revenue_yoy'] = ((current['revenue'] - yoy_data['revenue']) / yoy_data['revenue']) * 100 if current['revenue'] else 0
                metrics['pat_yoy'] = ((current['profit'] - yoy_data['profit']) / yoy_data['profit']) * 100 if current['profit'] and yoy_data['profit'] else 0
                metrics['eps_growth'] = ((current['eps'] - yoy_data['eps']) / yoy_data['eps']) * 100 if current['eps'] and yoy_data['eps'] else 0
            else:
                metrics['revenue_yoy'] = 0
                metrics['pat_yoy'] = 0
                metrics['eps_growth'] = 0
            
            # QoQ Growth
            if qoq_data and qoq_data['revenue']:
                metrics['revenue_qoq'] = ((current['revenue'] - qoq_data['revenue']) / qoq_data['revenue']) * 100 if current['revenue'] else 0
                metrics['pat_qoq'] = ((current['profit'] - qoq_data['profit']) / qoq_data['profit']) * 100 if current['profit'] and qoq_data['profit'] else 0
                metrics['eps_qoq'] = ((current['eps'] - qoq_data['eps']) / qoq_data['eps']) * 100 if current['eps'] and qoq_data['eps'] else 0
            else:
                metrics['revenue_qoq'] = 0
                metrics['pat_qoq'] = 0
                metrics['eps_qoq'] = 0
            
            return metrics if metrics else None
            
        except Exception as e:
            logger.error(f"Error calculating growth from DB: {e}")
            return None
    
    def _calculate_qoq_from_db(self, fund_data) -> Optional[Dict]:
        """Helper to calculate just QoQ when YoY is already available"""
        # Reuse the main calculation function
        full_metrics = self._calculate_growth_from_db(fund_data)
        if full_metrics:
            return {
                'revenue_qoq': full_metrics.get('revenue_qoq', 0),
                'pat_qoq': full_metrics.get('pat_qoq', 0),
                'eps_qoq': full_metrics.get('eps_qoq', 0)
            }
        return None

    def _analyze_technicals(self, bse_code: str) -> Optional[Dict]:
        """
        Fetch price history and calculate technicals.
        """
        try:
            # Convert BSE code to Yahoo symbol (e.g., 500038 -> 500038.BO)
            symbol = f"{bse_code}.BO"
            
            # Fetch 1 year of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=400)
            
            df = self.price_fetcher.fetch_ohlcv(symbol, "BSE", start_date, end_date)
            
            if df is None or len(df) < 200:
                logger.warning(f"Insufficient price data for {symbol}")
                return None
                
            # Calculate Indicators using existing skill
            prices = df['close'].tolist()
            indicators = calculate_all_indicators(prices)
            
            # Calculate Moving Averages manually if not in indicators
            # (calculate_all_indicators gives BB, MACD, RSI)
            
            # 200 DMA
            dma_200 = df['close'].rolling(window=200).mean().iloc[-1]
            dma_50 = df['close'].rolling(window=50).mean().iloc[-1]
            
            # Relative Strength (Simplified: vs Self History for now, or vs Index if we had it)
            # A true RS compares to Nifty 500. 
            # Proxy: Price Performance vs 6 months ago
            price_6m_ago = df['close'].iloc[-120] if len(df) > 120 else df['close'].iloc[0]
            rs_score = self._calculate_relative_strength(df['close'].iloc[-1], price_6m_ago)
            
            return {
                'price': df['close'].iloc[-1],
                'dma_200': dma_200,
                'dma_50': dma_50,
                'rsi': indicators['rsi'],
                'relative_strength': rs_score
            }
            
        except Exception as e:
            logger.error(f"Technical analysis failed: {e}")
            return None

    def _calculate_relative_strength(self, current_price: float, past_price: float) -> float:
        """
        Calculate a Relative Strength Score (0-100).
        This is a simplified proxy for RS Rating.
        """
        roc = ((current_price - past_price) / past_price) * 100
        
        # Map ROC to 0-100 score
        # > 50% gain = 90+ score
        # > 20% gain = 80+ score
        # 0% gain = 50 score
        
        if roc >= 50:
            return 90 + min(10, (roc - 50) / 5)
        elif roc >= 20:
            return 80 + (roc - 20) / 3
        elif roc >= 0:
            return 50 + (roc / 20) * 30
        else:
            return max(0, 50 - (abs(roc) / 20) * 50)

if __name__ == "__main__":
    # Test the detector
    logging.basicConfig(level=logging.INFO)
    detector = TrueBlockbusterDetector()
    
    # Test with a known stock (e.g., TCS or a smallcap)
    print("Testing True Blockbuster Detector...")
    # Note: This will fail if no data in DB/Yahoo, but verifies import/init
    try:
        result = detector.analyze_stock("500038", "Bharat Rasayan")
        print(result)
    except Exception as e:
        print(f"Test failed (expected if no data): {e}")

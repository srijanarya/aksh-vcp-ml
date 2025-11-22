#!/usr/bin/env python3
"""
Universal Blockbuster Scanner - Multi-Source with Format Normalization

This scanner combines multiple data sources with proper format handling:
1. Local databases (historical_financials, earnings_calendar)
2. Yahoo Finance API
3. Angel One API (for price data)

All data is normalized to a consistent format before analysis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import logging
import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataNormalizer:
    """Handles format inconsistencies across different data sources"""

    @staticmethod
    def normalize_number(value, source: str = 'unknown') -> float:
        """
        Normalize numbers from different sources
        - Screener: "1,234.56 Cr"
        - Yahoo: 1234560000 (in actual rupees)
        - Database: 1234.56 (in crores)
        - BSE/NSE: "1234.56"
        """
        if value is None or pd.isna(value):
            return 0.0

        # If already a number
        if isinstance(value, (int, float)):
            return float(value)

        # Convert string to number
        value_str = str(value).strip()

        # Remove currency symbols
        value_str = value_str.replace('₹', '').replace('Rs', '').replace('INR', '')

        # Remove commas
        value_str = value_str.replace(',', '')

        # Handle Cr (Crores) and L (Lakhs)
        multiplier = 1
        if 'Cr' in value_str or 'cr' in value_str:
            multiplier = 1  # Already in crores
            value_str = value_str.replace('Cr', '').replace('cr', '')
        elif 'L' in value_str or 'lakh' in value_str.lower():
            multiplier = 0.01  # Convert lakhs to crores
            value_str = value_str.replace('L', '').replace('lakh', '').replace('Lakh', '')
        elif 'M' in value_str or 'million' in value_str.lower():
            multiplier = 0.1  # Convert millions to crores
            value_str = value_str.replace('M', '').replace('million', '').replace('Million', '')
        elif 'B' in value_str or 'billion' in value_str.lower():
            multiplier = 100  # Convert billions to crores
            value_str = value_str.replace('B', '').replace('billion', '').replace('Billion', '')

        # Handle parentheses for negative numbers
        if '(' in value_str and ')' in value_str:
            value_str = '-' + value_str.replace('(', '').replace(')', '')

        try:
            # Convert to float
            number = float(value_str.strip())

            # Apply source-specific conversions
            if source == 'yahoo' and abs(number) > 1000000:
                # Yahoo returns in actual currency, convert to crores
                number = number / 10000000  # Convert to crores

            return number * multiplier
        except ValueError:
            logger.warning(f"Could not parse number: {value}")
            return 0.0

    @staticmethod
    def normalize_date(date_value, source: str = 'unknown') -> Optional[str]:
        """
        Normalize dates to YYYY-MM-DD format
        - Database: "2024-03-31"
        - BSE: "31/03/2024"
        - Yahoo: timestamp
        - Screener: "Mar 2024"
        """
        if date_value is None or pd.isna(date_value):
            return None

        try:
            # If already a datetime object
            if isinstance(date_value, (datetime, pd.Timestamp)):
                return date_value.strftime('%Y-%m-%d')

            date_str = str(date_value).strip()

            # Try different formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%d %b %Y', '%b %Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            # If timestamp (Unix epoch)
            try:
                if date_str.isdigit() and len(date_str) > 8:
                    dt = datetime.fromtimestamp(int(date_str))
                    return dt.strftime('%Y-%m-%d')
            except:
                pass

            logger.warning(f"Could not parse date: {date_value}")
            return None
        except Exception as e:
            logger.warning(f"Date parsing error: {e}")
            return None

    @staticmethod
    def normalize_quarter(quarter_value, source: str = 'unknown') -> Tuple[str, int]:
        """
        Normalize quarter formats
        Returns: (quarter, fiscal_year)
        - Database: "Q3", 2024
        - Screener: "Dec 2023"
        - Yahoo: "2023-12-31"
        - BSE: "Q3FY24"
        """
        if quarter_value is None or pd.isna(quarter_value):
            return ("Q1", datetime.now().year)

        quarter_str = str(quarter_value).strip()

        # Handle "Q3FY24" format
        if 'FY' in quarter_str:
            parts = quarter_str.split('FY')
            quarter = parts[0]
            year = 2000 + int(parts[1][:2]) if len(parts[1]) == 2 else int(parts[1][:4])
            return (quarter, year)

        # Handle "Dec 2023" format
        months_to_quarter = {
            'Mar': 'Q4', 'Apr': 'Q1', 'May': 'Q1', 'Jun': 'Q1',
            'Jul': 'Q2', 'Aug': 'Q2', 'Sep': 'Q2',
            'Oct': 'Q3', 'Nov': 'Q3', 'Dec': 'Q3',
            'Jan': 'Q4', 'Feb': 'Q4'
        }

        for month, quarter in months_to_quarter.items():
            if month in quarter_str:
                # Extract year
                year_parts = quarter_str.replace(month, '').strip().split()
                if year_parts:
                    year = int(year_parts[0])
                    # Adjust fiscal year (Apr-Mar)
                    if month in ['Jan', 'Feb', 'Mar']:
                        fiscal_year = year
                    else:
                        fiscal_year = year + 1
                    return (quarter, fiscal_year)

        # Handle date format "2023-12-31"
        try:
            dt = datetime.strptime(quarter_str[:10], '%Y-%m-%d')
            month = dt.month
            year = dt.year
            if month in [4, 5, 6]:
                return ('Q1', year + 1)
            elif month in [7, 8, 9]:
                return ('Q2', year + 1)
            elif month in [10, 11, 12]:
                return ('Q3', year + 1)
            else:  # Jan, Feb, Mar
                return ('Q4', year)
        except:
            pass

        # Default
        return ("Q1", datetime.now().year)

class MultiSourceDataFetcher:
    """Fetches data from multiple sources with fallback"""

    def __init__(self):
        self.normalizer = DataNormalizer()
        self.cache = {}

    def get_quarterly_financials(self, symbol: str, nse_symbol: str = None,
                                 bse_code: str = None) -> pd.DataFrame:
        """
        Get quarterly financials from multiple sources
        Returns normalized DataFrame with columns:
        quarter, fiscal_year, revenue, pat, eps, source
        """
        all_data = []

        # Try local database first
        if bse_code:
            db_data = self._fetch_from_database(bse_code)
            if not db_data.empty:
                db_data['source'] = 'database'
                all_data.append(db_data)

        # Try Yahoo Finance
        if nse_symbol:
            yahoo_data = self._fetch_from_yahoo(nse_symbol)
            if not yahoo_data.empty:
                yahoo_data['source'] = 'yahoo'
                all_data.append(yahoo_data)

        # Combine and deduplicate
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            # Remove duplicates, preferring database over yahoo
            combined = combined.sort_values('source').drop_duplicates(
                subset=['quarter', 'fiscal_year'], keep='first'
            )
            return combined.sort_values(['fiscal_year', 'quarter'], ascending=[False, False])

        return pd.DataFrame()

    def _fetch_from_database(self, bse_code: str) -> pd.DataFrame:
        """Fetch from local historical_financials database"""
        try:
            conn = sqlite3.connect('data/historical_financials.db')
            query = """
                SELECT quarter, year as fiscal_year,
                       revenue, pat, eps
                FROM historical_financials
                WHERE bse_code = ?
                AND revenue IS NOT NULL
                ORDER BY year DESC, quarter DESC
                LIMIT 8
            """
            df = pd.read_sql(query, conn, params=(bse_code,))
            conn.close()

            if df.empty:
                return df

            # Normalize data
            for col in ['revenue', 'pat', 'eps']:
                df[col] = df[col].apply(lambda x: self.normalizer.normalize_number(x, 'database'))

            return df

        except Exception as e:
            logger.error(f"Database fetch error for {bse_code}: {e}")
            return pd.DataFrame()

    def _fetch_from_yahoo(self, nse_symbol: str) -> pd.DataFrame:
        """Fetch from Yahoo Finance"""
        try:
            # Ensure .NS suffix
            if not nse_symbol.endswith('.NS'):
                nse_symbol = f"{nse_symbol}.NS"

            ticker = yf.Ticker(nse_symbol)

            # Get quarterly financials
            financials = ticker.quarterly_financials
            if financials is None or financials.empty:
                return pd.DataFrame()

            # Get quarterly earnings
            earnings = ticker.quarterly_earnings

            # Combine data
            quarters_data = []
            for date in financials.columns[:8]:  # Last 8 quarters
                quarter_data = {
                    'date': date,
                    'revenue': financials.loc['Total Revenue', date] if 'Total Revenue' in financials.index else 0,
                    'pat': financials.loc['Net Income', date] if 'Net Income' in financials.index else 0,
                    'eps': earnings.loc[date, 'Earnings'] if earnings is not None and date in earnings.index else 0
                }

                # Normalize quarter format
                q, fy = self.normalizer.normalize_quarter(date.strftime('%Y-%m-%d'), 'yahoo')
                quarter_data['quarter'] = q
                quarter_data['fiscal_year'] = fy

                # Normalize numbers (Yahoo returns in actual currency)
                quarter_data['revenue'] = self.normalizer.normalize_number(quarter_data['revenue'], 'yahoo')
                quarter_data['pat'] = self.normalizer.normalize_number(quarter_data['pat'], 'yahoo')
                quarter_data['eps'] = self.normalizer.normalize_number(quarter_data['eps'], 'yahoo')

                quarters_data.append(quarter_data)

            return pd.DataFrame(quarters_data)

        except Exception as e:
            logger.error(f"Yahoo fetch error for {nse_symbol}: {e}")
            return pd.DataFrame()

class UniversalBlockbusterScanner:
    """Scanner that works with multiple data sources"""

    def __init__(self):
        self.fetcher = MultiSourceDataFetcher()
        self.results_db = "data/universal_blockbuster_results.db"
        self._init_results_db()

    def _init_results_db(self):
        """Initialize results database"""
        conn = sqlite3.connect(self.results_db)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date DATE,
                company_name TEXT,
                nse_symbol TEXT,
                bse_code TEXT,
                blockbuster_score INTEGER,
                revenue_yoy REAL,
                pat_yoy REAL,
                eps REAL,
                is_blockbuster BOOLEAN,
                data_source TEXT,
                criteria_met TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def analyze_company(self, company_name: str, nse_symbol: str = None,
                       bse_code: str = None) -> Tuple[bool, Dict]:
        """
        Analyze company for blockbuster earnings
        Uses multiple data sources with fallback
        """
        # Get quarterly data from all available sources
        df = self.fetcher.get_quarterly_financials(
            symbol=company_name,
            nse_symbol=nse_symbol,
            bse_code=bse_code
        )

        if len(df) < 5:
            return False, {
                'error': 'insufficient_data',
                'available_quarters': len(df),
                'company_name': company_name
            }

        # Get current and YoY quarters
        current = df.iloc[0]

        # Find same quarter last year
        current_q = current['quarter']
        current_fy = current['fiscal_year']
        last_year_fy = current_fy - 1

        yoy_data = df[(df['quarter'] == current_q) & (df['fiscal_year'] == last_year_fy)]

        if yoy_data.empty:
            return False, {
                'error': 'no_yoy_comparison',
                'company_name': company_name
            }

        yoy = yoy_data.iloc[0]

        # Calculate YoY growth
        revenue_yoy = self._calculate_growth(current['revenue'], yoy['revenue'])
        pat_yoy = self._calculate_growth(current['pat'], yoy['pat'])
        eps_growth = self._calculate_growth(current['eps'], yoy['eps'])

        # Apply blockbuster criteria
        criteria_met = []
        is_blockbuster = True

        if revenue_yoy > 15.0:
            criteria_met.append(f"Revenue YoY {revenue_yoy:.1f}% > 15%")
        else:
            is_blockbuster = False

        if pat_yoy > 20.0:
            criteria_met.append(f"PAT YoY {pat_yoy:.1f}% > 20%")
        else:
            is_blockbuster = False

        if current['eps'] > 0:
            criteria_met.append(f"EPS ₹{current['eps']:.2f} > 0")
        else:
            is_blockbuster = False

        # Calculate score
        score = self._calculate_score(revenue_yoy, pat_yoy, current['eps'], eps_growth)

        result = {
            'company_name': company_name,
            'nse_symbol': nse_symbol,
            'bse_code': bse_code,
            'quarter': f"{current['quarter']} FY{current['fiscal_year']}",
            'revenue': current['revenue'],
            'pat': current['pat'],
            'eps': current['eps'],
            'revenue_yoy': revenue_yoy,
            'pat_yoy': pat_yoy,
            'eps_growth': eps_growth,
            'is_blockbuster': is_blockbuster,
            'blockbuster_score': score,
            'data_source': current.get('source', 'unknown'),
            'criteria_met': ' | '.join(criteria_met) if criteria_met else 'None'
        }

        # Store result
        self._store_result(result)

        return is_blockbuster, result

    def _calculate_growth(self, current: float, previous: float) -> float:
        """Calculate percentage growth"""
        if previous == 0 or pd.isna(previous) or pd.isna(current):
            return 0.0
        return ((current - previous) / abs(previous)) * 100

    def _calculate_score(self, revenue_yoy: float, pat_yoy: float,
                        eps: float, eps_growth: float) -> int:
        """Calculate blockbuster score (0-100)"""
        score = 0

        # Revenue component (30 points)
        if revenue_yoy > 15:
            score += min(30, int((revenue_yoy - 15) / 35 * 30))

        # PAT component (40 points)
        if pat_yoy > 20:
            score += min(40, int((pat_yoy - 20) / 40 * 40))

        # EPS component (20 points)
        if eps > 0:
            score += min(20, int(eps / 100 * 20))

        # EPS Growth component (10 points)
        if eps_growth > 0:
            score += min(10, int(eps_growth / 50 * 10))

        return min(100, score)

    def _store_result(self, result: Dict):
        """Store scan result"""
        conn = sqlite3.connect(self.results_db)
        conn.execute("""
            INSERT INTO scan_results
            (scan_date, company_name, nse_symbol, bse_code, blockbuster_score,
             revenue_yoy, pat_yoy, eps, is_blockbuster, data_source, criteria_met)
            VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result['company_name'],
            result.get('nse_symbol'),
            result.get('bse_code'),
            result['blockbuster_score'],
            result.get('revenue_yoy', 0),
            result.get('pat_yoy', 0),
            result.get('eps', 0),
            result['is_blockbuster'],
            result.get('data_source', 'unknown'),
            result.get('criteria_met', '')
        ))
        conn.commit()
        conn.close()

    def scan_companies(self, companies: List[Dict], max_companies: int = None) -> Tuple[List, List]:
        """
        Scan multiple companies
        Returns: (blockbusters, high_potential)
        """
        if max_companies:
            companies = companies[:max_companies]

        total = len(companies)
        print(f"\n{'='*80}")
        print(f"UNIVERSAL BLOCKBUSTER SCANNER - MULTI-SOURCE")
        print(f"{'='*80}")
        print(f"Total companies to scan: {total}")
        print(f"Data sources: Database → Yahoo Finance → Angel One")
        print(f"{'='*80}\n")

        blockbusters = []
        high_potential = []
        errors = 0

        for i, company in enumerate(companies):
            print(f"[{i+1}/{total}] Analyzing {company['name']}...")

            try:
                is_blockbuster, result = self.analyze_company(
                    company_name=company['name'],
                    nse_symbol=company.get('nse'),
                    bse_code=company.get('bse')
                )

                if 'error' in result:
                    errors += 1
                    print(f"  ⚠️  {result['error']}")
                    continue

                score = result['blockbuster_score']
                source = result.get('data_source', 'unknown')

                print(f"  📊 Score: {score}/100 (Source: {source})")
                print(f"  💰 Revenue YoY: {result['revenue_yoy']:+.1f}%")
                print(f"  💵 PAT YoY: {result['pat_yoy']:+.1f}%")

                if is_blockbuster:
                    blockbusters.append(result)
                    print(f"  🚀 **BLOCKBUSTER DETECTED!**")
                elif score >= 50:
                    high_potential.append(result)
                    print(f"  ⭐ High potential stock")

                # Small delay to respect APIs
                time.sleep(0.2)

            except Exception as e:
                errors += 1
                print(f"  ❌ Error: {e}")
                continue

        print(f"\n{'='*80}")
        print("SCAN COMPLETE")
        print(f"{'='*80}")
        print(f"Scanned: {total} | Errors: {errors}")
        print(f"Blockbusters: {len(blockbusters)} | High Potential: {len(high_potential)}")

        return blockbusters, high_potential

def load_companies_from_db() -> List[Dict]:
    """Load companies from local database"""
    companies = []

    # Try historical_financials first
    try:
        conn = sqlite3.connect('data/historical_financials.db')
        cursor = conn.execute("""
            SELECT DISTINCT bse_code
            FROM historical_financials
            WHERE revenue IS NOT NULL
        """)
        for row in cursor:
            companies.append({
                'name': row[0],
                'bse': row[0],
                'nse': None  # Will need mapping
            })
        conn.close()
    except Exception as e:
        logger.error(f"Could not load from database: {e}")

    return companies

def load_nse_500() -> List[Dict]:
    """Load NSE 500 companies"""
    try:
        from agents.trading.nse_500_symbols import NSE_500_SYMBOLS
        companies = []
        for symbol in NSE_500_SYMBOLS[:50]:  # Start with first 50
            company_name = symbol.replace('.NS', '')
            companies.append({
                'name': company_name,
                'nse': symbol,
                'bse': None  # Will need mapping
            })
        return companies
    except:
        return []

def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Universal Blockbuster Scanner')
    parser.add_argument('--source', choices=['db', 'nse500', 'both'], default='both',
                       help='Data source for companies')
    parser.add_argument('--max', type=int, help='Maximum companies to scan')

    args = parser.parse_args()

    # Load companies
    companies = []
    if args.source in ['db', 'both']:
        companies.extend(load_companies_from_db())
    if args.source in ['nse500', 'both']:
        companies.extend(load_nse_500())

    if not companies:
        print("No companies to scan!")
        return

    # Remove duplicates
    seen = set()
    unique_companies = []
    for company in companies:
        key = company['name']
        if key not in seen:
            seen.add(key)
            unique_companies.append(company)

    print(f"Loaded {len(unique_companies)} unique companies")

    # Run scan
    scanner = UniversalBlockbusterScanner()
    blockbusters, high_potential = scanner.scan_companies(
        unique_companies,
        max_companies=args.max
    )

    # Print summary
    if blockbusters:
        print(f"\n🚀 BLOCKBUSTERS ({len(blockbusters)}):")
        for b in sorted(blockbusters, key=lambda x: x['blockbuster_score'], reverse=True):
            print(f"  • {b['company_name']}: Score {b['blockbuster_score']}/100")
            print(f"    Revenue: {b['revenue_yoy']:+.1f}% | PAT: {b['pat_yoy']:+.1f}%")
            print(f"    Data Source: {b.get('data_source', 'unknown')}")

if __name__ == "__main__":
    main()
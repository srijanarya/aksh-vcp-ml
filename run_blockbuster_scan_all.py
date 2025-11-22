#!/usr/bin/env python3
"""
Enhanced Blockbuster Scanner - Full Market Coverage
Scans ALL NSE/BSE companies for blockbuster earnings patterns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.ml.blockbuster_detector import BlockbusterDetector
import logging
import time
from typing import List, Dict, Tuple
import json
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FullMarketScanner:
    """Enhanced scanner for all NSE/BSE companies"""

    def __init__(self, use_cache: bool = True):
        self.detector = BlockbusterDetector()
        self.use_cache = use_cache
        self.cache_file = "data/blockbuster_scan_cache.json"
        self.results_db = "data/blockbuster_scan_results.db"
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
                criteria_met TEXT,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def load_companies_from_file(self) -> List[Dict]:
        """Load NSE 500 equity stocks from curated list"""
        # Import the NSE 500 symbols
        try:
            from agents.trading.nse_500_symbols import NSE_500_SYMBOLS

            companies = []
            for symbol in NSE_500_SYMBOLS:
                # Remove .NS suffix for screener URL
                company_url = symbol.replace('.NS', '')
                companies.append({
                    'url': company_url,
                    'name': company_url,  # Will be updated from screener
                    'nse': symbol if '.NS' in symbol else company_url,
                    'bse': None  # Could be enhanced with BSE mapping
                })

            logger.info(f"Loaded {len(companies)} NSE 500 equity stocks")
            return companies

        except ImportError:
            logger.error("Could not import NSE_500_SYMBOLS")
            # Fallback to file if available
            symbol_file = Path("agents/backtesting/symbol_lists/nse_bse_all_stocks.txt")
            if not symbol_file.exists():
                logger.warning(f"Symbol file not found: {symbol_file}")
                return []

            with open(symbol_file, 'r') as f:
                content = f.read()

            # Parse symbols (assuming one per line)
            symbols = [line.strip() for line in content.split('\n') if line.strip()]

            companies = []
            for symbol in symbols:
                # Remove .NS or .BO suffix for screener URL
                company_url = symbol.replace('.NS', '').replace('.BO', '')
                companies.append({
                    'url': company_url,
                    'name': company_url,  # Will be updated from screener
                    'nse': symbol if '.NS' in symbol else company_url,
                    'bse': None  # Could be enhanced with BSE mapping
                })

            return companies

    def load_companies_from_db(self) -> List[Dict]:
        """Load companies from earnings database"""
        db_path = "data/earnings_calendar.db"

        if not Path(db_path).exists():
            logger.warning(f"Database not found: {db_path}")
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.execute("""
            SELECT DISTINCT
                company_name,
                nse_symbol,
                bse_code
            FROM earnings
            WHERE nse_symbol IS NOT NULL
            AND nse_symbol != ''
            GROUP BY nse_symbol
            ORDER BY company_name
        """)

        companies = []
        for row in cursor:
            companies.append({
                'url': row[1],  # NSE symbol as URL
                'name': row[0],
                'nse': row[1],
                'bse': row[2]
            })

        conn.close()
        return companies

    def load_top_liquid_companies(self) -> List[Dict]:
        """Load top liquid companies (Nifty 500 + more)"""
        # Start with a curated list of highly liquid stocks
        top_companies = [
            # Nifty 50 leaders
            {'url': 'TCS', 'name': 'Tata Consultancy Services', 'bse': '532540', 'nse': 'TCS'},
            {'url': 'RELIANCE', 'name': 'Reliance Industries', 'bse': '500325', 'nse': 'RELIANCE'},
            {'url': 'HDFCBANK', 'name': 'HDFC Bank', 'bse': '500180', 'nse': 'HDFCBANK'},
            {'url': 'INFY', 'name': 'Infosys', 'bse': '500209', 'nse': 'INFY'},
            {'url': 'ICICIBANK', 'name': 'ICICI Bank', 'bse': '532174', 'nse': 'ICICIBANK'},
            {'url': 'BAJFINANCE', 'name': 'Bajaj Finance', 'bse': '500034', 'nse': 'BAJFINANCE'},
            {'url': 'TATAMOTORS', 'name': 'Tata Motors', 'bse': '500570', 'nse': 'TATAMOTORS'},
            {'url': 'ADANIENT', 'name': 'Adani Enterprises', 'bse': '512599', 'nse': 'ADANIENT'},
            {'url': 'WIPRO', 'name': 'Wipro', 'bse': '507685', 'nse': 'WIPRO'},
            {'url': 'ITC', 'name': 'ITC Limited', 'bse': '500875', 'nse': 'ITC'},
            {'url': 'KOTAKBANK', 'name': 'Kotak Bank', 'bse': '500247', 'nse': 'KOTAKBANK'},
            {'url': 'LT', 'name': 'Larsen & Toubro', 'bse': '500510', 'nse': 'LT'},
            {'url': 'AXISBANK', 'name': 'Axis Bank', 'bse': '532215', 'nse': 'AXISBANK'},
            {'url': 'SBIN', 'name': 'State Bank of India', 'bse': '500112', 'nse': 'SBIN'},
            {'url': 'BHARTIARTL', 'name': 'Bharti Airtel', 'bse': '532454', 'nse': 'BHARTIARTL'},
            {'url': 'ASIANPAINT', 'name': 'Asian Paints', 'bse': '500820', 'nse': 'ASIANPAINT'},
            {'url': 'MARUTI', 'name': 'Maruti Suzuki', 'bse': '532500', 'nse': 'MARUTI'},
            {'url': 'HCLTECH', 'name': 'HCL Technologies', 'bse': '532281', 'nse': 'HCLTECH'},
            {'url': 'SUNPHARMA', 'name': 'Sun Pharma', 'bse': '524715', 'nse': 'SUNPHARMA'},
            {'url': 'TITAN', 'name': 'Titan Company', 'bse': '500114', 'nse': 'TITAN'},

            # Add more mid-cap winners
            {'url': 'ZOMATO', 'name': 'Zomato', 'bse': '543320', 'nse': 'ZOMATO'},
            {'url': 'PAYTM', 'name': 'Paytm', 'bse': '543396', 'nse': 'PAYTM'},
            {'url': 'DMART', 'name': 'Avenue Supermarts', 'bse': '540376', 'nse': 'DMART'},
            {'url': 'ADANIGREEN', 'name': 'Adani Green Energy', 'bse': '541450', 'nse': 'ADANIGREEN'},
            {'url': 'PIDILITIND', 'name': 'Pidilite Industries', 'bse': '500331', 'nse': 'PIDILITIND'},
        ]

        return top_companies

    def scan_companies(self, companies: List[Dict], batch_size: int = 10,
                       delay: float = 0.5, max_companies: int = None) -> Tuple[List[Dict], List[Dict]]:
        """
        Scan companies in batches with progress tracking

        Args:
            companies: List of company dicts
            batch_size: Number of companies per batch
            delay: Delay between companies (rate limiting)
            max_companies: Maximum companies to scan (None for all)

        Returns:
            (blockbusters, high_potential) tuple of lists
        """
        if max_companies:
            companies = companies[:max_companies]

        total = len(companies)
        print("\n" + "="*80)
        print(f"ENHANCED BLOCKBUSTER SCANNER - FULL MARKET COVERAGE")
        print("="*80)
        print(f"Total companies to scan: {total}")
        print(f"Batch size: {batch_size}")
        print(f"Estimated time: {(total * delay / 60):.1f} minutes")
        print("="*80 + "\n")

        blockbusters = []
        high_potential = []
        errors = []

        for i in range(0, total, batch_size):
            batch = companies[i:i + batch_size]
            batch_end = min(i + batch_size, total)

            print(f"\n{'='*60}")
            print(f"BATCH {i//batch_size + 1}: Processing companies {i+1}-{batch_end} of {total}")
            print(f"Progress: {(i/total*100):.1f}%")
            print('='*60)

            for j, company in enumerate(batch):
                current = i + j + 1
                print(f"\n[{current}/{total}] Analyzing {company['name']} ({company.get('nse', company['url'])})...")

                try:
                    is_blockbuster, result = self.detector.analyze_company(
                        company_url=company['url'],
                        company_name=company['name'],
                        bse_code=company.get('bse'),
                        nse_symbol=company.get('nse')
                    )

                    if 'error' in result:
                        errors.append(company)
                        print(f"  ⚠️  {result['error']}")
                        continue

                    score = result['blockbuster_score']
                    revenue_yoy = result.get('revenue_yoy', 0)
                    pat_yoy = result.get('pat_yoy', 0)

                    # Store in database
                    self._store_result(result)

                    # Display results
                    print(f"  📊 Score: {score}/100")
                    print(f"  💰 Revenue YoY: {revenue_yoy:+.1f}%")
                    print(f"  💵 PAT YoY: {pat_yoy:+.1f}%")

                    if is_blockbuster:
                        blockbusters.append(result)
                        print(f"  🚀 **BLOCKBUSTER DETECTED!**")
                    elif score >= 50:
                        high_potential.append(result)
                        print(f"  ⭐ High potential stock")
                    else:
                        print(f"  📈 Standard performance")

                    # Rate limiting
                    if delay > 0 and j < len(batch) - 1:
                        time.sleep(delay)

                except Exception as e:
                    errors.append(company)
                    print(f"  ❌ Error: {e}")
                    continue

            # Batch summary
            print(f"\n{'='*60}")
            print(f"Batch complete: {len(blockbusters)} blockbusters, {len(high_potential)} high potential")
            print(f"Errors: {len(errors)}")

        return blockbusters, high_potential

    def _store_result(self, result: Dict):
        """Store scan result in database"""
        conn = sqlite3.connect(self.results_db)
        conn.execute("""
            INSERT INTO scan_results
            (scan_date, company_name, nse_symbol, bse_code, blockbuster_score,
             revenue_yoy, pat_yoy, eps, is_blockbuster, criteria_met)
            VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result['company_name'],
            result.get('nse_symbol'),
            result.get('bse_code'),
            result['blockbuster_score'],
            result.get('revenue_yoy', 0),
            result.get('pat_yoy', 0),
            result.get('eps', 0),
            result['is_blockbuster'],
            result.get('criteria_met', '')
        ))
        conn.commit()
        conn.close()

    def print_summary(self, blockbusters: List[Dict], high_potential: List[Dict],
                     total_scanned: int, start_time: float):
        """Print comprehensive scan summary"""
        elapsed = time.time() - start_time

        print("\n" + "="*80)
        print("SCAN COMPLETE - SUMMARY REPORT")
        print("="*80)
        print(f"Total companies scanned: {total_scanned}")
        print(f"Time taken: {elapsed/60:.1f} minutes")
        print(f"Average per company: {elapsed/total_scanned:.1f} seconds")
        print("="*80)

        if blockbusters:
            print(f"\n🚀 BLOCKBUSTERS FOUND ({len(blockbusters)}):")
            print("-"*60)
            for b in sorted(blockbusters, key=lambda x: x['blockbuster_score'], reverse=True)[:10]:
                print(f"  • {b['company_name']:30} Score: {b['blockbuster_score']:3}/100")
                print(f"    Revenue: {b.get('revenue_yoy', 0):+.1f}% | PAT: {b.get('pat_yoy', 0):+.1f}%")
                print(f"    NSE: {b.get('nse_symbol', 'N/A'):15} BSE: {b.get('bse_code', 'N/A')}")
                print()

        if high_potential:
            print(f"\n⭐ HIGH POTENTIAL ({len(high_potential)}):")
            print("-"*60)
            for h in sorted(high_potential, key=lambda x: x['blockbuster_score'], reverse=True)[:10]:
                print(f"  • {h['company_name']:30} Score: {h['blockbuster_score']:3}/100")
                print(f"    Revenue: {h.get('revenue_yoy', 0):+.1f}% | PAT: {h.get('pat_yoy', 0):+.1f}%")
                print()

        # Statistics
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        print(f"Blockbuster rate: {len(blockbusters)/total_scanned*100:.1f}%")
        print(f"High potential rate: {len(high_potential)/total_scanned*100:.1f}%")
        print(f"Total opportunities: {len(blockbusters) + len(high_potential)}")

        # Save summary to file
        summary_file = f"data/scan_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        summary = {
            'scan_date': datetime.now().isoformat(),
            'total_scanned': total_scanned,
            'time_minutes': elapsed/60,
            'blockbusters': len(blockbusters),
            'high_potential': len(high_potential),
            'blockbuster_companies': [b['company_name'] for b in blockbusters],
            'top_scores': sorted([b['blockbuster_score'] for b in blockbusters], reverse=True)[:10]
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")
        print(f"Results database: {self.results_db}")
        print("="*80)

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced Blockbuster Scanner - Full Market')
    parser.add_argument('--source', choices=['file', 'db', 'top', 'demo'], default='top',
                       help='Data source: file (all symbols), db (earnings), top (liquid stocks), demo (10 companies)')
    parser.add_argument('--max', type=int, help='Maximum companies to scan')
    parser.add_argument('--batch', type=int, default=10, help='Batch size (default: 10)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between companies in seconds')

    args = parser.parse_args()

    scanner = FullMarketScanner()

    # Load companies based on source
    if args.source == 'file':
        print("Loading ALL companies from symbol file...")
        companies = scanner.load_companies_from_file()
    elif args.source == 'db':
        print("Loading companies from earnings database...")
        companies = scanner.load_companies_from_db()
    elif args.source == 'top':
        print("Loading top liquid companies...")
        companies = scanner.load_top_liquid_companies()
    else:  # demo
        print("Loading demo companies (10)...")
        companies = scanner.load_top_liquid_companies()[:10]

    if not companies:
        print("No companies found to scan!")
        return

    print(f"Loaded {len(companies)} companies")

    # Start scanning
    start_time = time.time()
    blockbusters, high_potential = scanner.scan_companies(
        companies,
        batch_size=args.batch,
        delay=args.delay,
        max_companies=args.max
    )

    # Print summary
    actual_scanned = min(len(companies), args.max) if args.max else len(companies)
    scanner.print_summary(blockbusters, high_potential, actual_scanned, start_time)

if __name__ == "__main__":
    main()
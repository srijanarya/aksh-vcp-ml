#!/usr/bin/env python3
"""
Quick Blockbuster Scanner
Scans top Indian companies for blockbuster earnings patterns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.ml.blockbuster_detector import BlockbusterDetector
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_top_companies():
    """Scan top Indian companies for blockbuster patterns"""

    detector = BlockbusterDetector()

    # Top companies to scan (mix of sectors)
    companies = [
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
    ]

    print("\n" + "="*70)
    print("BLOCKBUSTER EARNINGS SCANNER - INDIAN MARKETS")
    print("="*70)
    print(f"Scanning {len(companies)} top companies for blockbuster earnings...\n")

    blockbusters = []
    high_potential = []

    for company in companies:
        print(f"Analyzing {company['name']} ({company['nse']})...")

        try:
            is_blockbuster, result = detector.analyze_company(
                company_url=company['url'],
                company_name=company['name'],
                bse_code=company['bse'],
                nse_symbol=company['nse']
            )

            if 'error' in result:
                print(f"  ⚠️  {result['error']}")
                continue

            score = result['blockbuster_score']
            revenue_yoy = result.get('revenue_yoy', 0)
            pat_yoy = result.get('pat_yoy', 0)

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

            print()

        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            continue

    # Print summary
    print("="*70)
    print("SCAN SUMMARY")
    print("="*70)

    if blockbusters:
        print(f"\n🚀 BLOCKBUSTERS FOUND ({len(blockbusters)}):")
        for b in sorted(blockbusters, key=lambda x: x['blockbuster_score'], reverse=True):
            print(f"  • {b['company_name']}: Score {b['blockbuster_score']}/100")
            print(f"    Revenue: {b.get('revenue_yoy', 0):+.1f}% | PAT: {b.get('pat_yoy', 0):+.1f}%")

    if high_potential:
        print(f"\n⭐ HIGH POTENTIAL ({len(high_potential)}):")
        for h in sorted(high_potential, key=lambda x: x['blockbuster_score'], reverse=True):
            print(f"  • {h['company_name']}: Score {h['blockbuster_score']}/100")

    if not blockbusters and not high_potential:
        print("\nNo blockbusters or high-potential stocks found in this scan.")

    print("\n" + "="*70)
    print("Scan complete!")
    print("="*70)

if __name__ == "__main__":
    scan_top_companies()
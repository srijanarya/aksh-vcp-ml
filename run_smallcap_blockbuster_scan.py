#!/usr/bin/env python3
"""
Small & Mid-Cap Blockbuster Scanner
Focuses on high-growth smaller companies with explosive potential
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.ml.blockbuster_detector import BlockbusterDetector
import logging
import yfinance as yf
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scan_small_mid_caps():
    """Scan small and mid-cap companies for blockbuster patterns"""

    detector = BlockbusterDetector()

    # Small & Mid-Cap companies with high growth potential
    companies = [
        # Mid-Cap Tech & Finance
        {'url': 'MPHASIS', 'name': 'Mphasis', 'bse': '526299', 'nse': 'MPHASIS'},
        {'url': 'PERSISTENT', 'name': 'Persistent Systems', 'bse': '533179', 'nse': 'PERSISTENT'},
        {'url': 'COFORGE', 'name': 'Coforge', 'bse': '532541', 'nse': 'COFORGE'},
        {'url': 'LTIM', 'name': 'LTIMindtree', 'bse': '540005', 'nse': 'LTIM'},
        {'url': 'LICHSGFIN', 'name': 'LIC Housing Finance', 'bse': '500253', 'nse': 'LICHSGFIN'},

        # Mid-Cap Consumer
        {'url': 'TRENT', 'name': 'Trent', 'bse': '500251', 'nse': 'TRENT'},
        {'url': 'PAGEIND', 'name': 'Page Industries', 'bse': '532827', 'nse': 'PAGEIND'},
        {'url': 'RELAXO', 'name': 'Relaxo Footwears', 'bse': '530517', 'nse': 'RELAXO'},
        {'url': 'VMART', 'name': 'V-Mart Retail', 'bse': '534976', 'nse': 'VMART'},

        # Small-Cap High Growth
        {'url': 'DEEPAKNTR', 'name': 'Deepak Nitrite', 'bse': '506401', 'nse': 'DEEPAKNTR'},
        {'url': 'ALKYLAMINE', 'name': 'Alkyl Amines', 'bse': '506767', 'nse': 'ALKYLAMINE'},
        {'url': 'CLEAN', 'name': 'Clean Science', 'bse': '543318', 'nse': 'CLEAN'},
        {'url': 'HAPPSTMNDS', 'name': 'Happiest Minds', 'bse': '543227', 'nse': 'HAPPSTMNDS'},

        # Small-Cap Pharma & Chemicals
        {'url': 'CAPLIPOINT', 'name': 'Caplin Point', 'bse': '524742', 'nse': 'CAPLIPOINT'},
        {'url': 'NEULANDLAB', 'name': 'Neuland Laboratories', 'bse': '524558', 'nse': 'NEULANDLAB'},
        {'url': 'AAVAS', 'name': 'Aavas Financiers', 'bse': '541988', 'nse': 'AAVAS'},

        # Small-Cap Tech & Digital
        {'url': 'ROUTE', 'name': 'Route Mobile', 'bse': '543228', 'nse': 'ROUTE'},
        {'url': 'LATENTVIEW', 'name': 'Latent View Analytics', 'bse': '543398', 'nse': 'LATENTVIEW'},
        {'url': 'TANLA', 'name': 'Tanla Platforms', 'bse': '532790', 'nse': 'TANLA'},
        {'url': 'KPITTECH', 'name': 'KPIT Technologies', 'bse': '542651', 'nse': 'KPITTECH'},

        # Emerging Small-Caps
        {'url': 'NAZARA', 'name': 'Nazara Technologies', 'bse': '543280', 'nse': 'NAZARA'},
        {'url': 'CARTRADE', 'name': 'CarTrade Tech', 'bse': '543333', 'nse': 'CARTRADE'},
        {'url': 'ZOMATO', 'name': 'Zomato', 'bse': '543320', 'nse': 'ZOMATO'},
        {'url': 'NYKAA', 'name': 'FSN E-Commerce (Nykaa)', 'bse': '543384', 'nse': 'NYKAA'},
        {'url': 'PAYTM', 'name': 'One97 Communications', 'bse': '543396', 'nse': 'PAYTM'}
    ]

    print("\n" + "="*70)
    print("SMALL & MID-CAP BLOCKBUSTER SCANNER")
    print("="*70)
    print(f"Scanning {len(companies)} high-growth companies...")
    print("Focus: Companies with market cap < ₹50,000 Cr")
    print("-"*70)

    blockbusters = []
    high_potential = []
    momentum_plays = []

    for company in companies:
        print(f"\n📊 Analyzing {company['name']} ({company['nse']})...")

        try:
            # First check recent price momentum
            ticker = yf.Ticker(f"{company['nse']}.NS")
            hist = ticker.history(period="3mo")

            if not hist.empty:
                recent_return = (hist['Close'][-1] / hist['Close'][-20] - 1) * 100 if len(hist) >= 20 else 0
                volume_surge = hist['Volume'][-5:].mean() / hist['Volume'][-30:-5].mean() if len(hist) >= 30 else 1

                print(f"  📈 20-day return: {recent_return:.1f}%")
                print(f"  📊 Volume surge: {volume_surge:.1f}x")

                # Check for momentum
                if recent_return > 15 and volume_surge > 1.5:
                    momentum_plays.append({
                        'name': company['name'],
                        'nse': company['nse'],
                        'return_20d': recent_return,
                        'volume_surge': volume_surge
                    })
                    print(f"  🔥 MOMENTUM ALERT!")

            # Now check blockbuster potential
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
            eps = result.get('eps', 0)

            print(f"  ⭐ Blockbuster Score: {score}/100")
            print(f"  💰 Revenue YoY: {revenue_yoy:+.1f}%")
            print(f"  💵 PAT YoY: {pat_yoy:+.1f}%")
            print(f"  📊 EPS: ₹{eps:.2f}")

            # Categorize based on multiple criteria
            if is_blockbuster or score >= 60:
                blockbusters.append(result)
                print(f"  🚀 **BLOCKBUSTER DETECTED!**")
            elif score >= 40 or (revenue_yoy > 20 and pat_yoy > 15):
                high_potential.append(result)
                print(f"  ⭐ High growth potential")
            elif revenue_yoy > 25 or pat_yoy > 30:
                high_potential.append(result)
                print(f"  📈 Strong growth metrics")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue

    # Print comprehensive summary
    print("\n" + "="*70)
    print("SCAN SUMMARY - SMALL & MID-CAP OPPORTUNITIES")
    print("="*70)

    if blockbusters:
        print(f"\n🚀 BLOCKBUSTERS FOUND ({len(blockbusters)}):")
        for b in sorted(blockbusters, key=lambda x: x['blockbuster_score'], reverse=True)[:5]:
            print(f"  • {b['company_name']}: Score {b['blockbuster_score']}/100")
            print(f"    Revenue: {b.get('revenue_yoy', 0):+.1f}% | PAT: {b.get('pat_yoy', 0):+.1f}%")
            print(f"    EPS: ₹{b.get('eps', 0):.2f}")

    if high_potential:
        print(f"\n⭐ HIGH GROWTH POTENTIAL ({len(high_potential)}):")
        for h in sorted(high_potential, key=lambda x: x.get('revenue_yoy', 0), reverse=True)[:5]:
            print(f"  • {h['company_name']}: Score {h['blockbuster_score']}/100")
            print(f"    Revenue: {h.get('revenue_yoy', 0):+.1f}% | PAT: {h.get('pat_yoy', 0):+.1f}%")

    if momentum_plays:
        print(f"\n🔥 MOMENTUM PLAYS ({len(momentum_plays)}):")
        for m in sorted(momentum_plays, key=lambda x: x['return_20d'], reverse=True)[:5]:
            print(f"  • {m['name']}: +{m['return_20d']:.1f}% (Volume: {m['volume_surge']:.1f}x)")

    # Investment recommendations
    print("\n" + "-"*70)
    print("📌 INVESTMENT STRATEGY RECOMMENDATIONS:")

    if blockbusters:
        print("\n1. BLOCKBUSTERS (Aggressive Growth):")
        print("   • Allocate 30-40% to top blockbusters")
        print("   • Use trailing stop-loss at 8-10%")
        print("   • Target: 25-40% returns in 3-6 months")

    if momentum_plays:
        print("\n2. MOMENTUM PLAYS (Short-term):")
        print("   • Allocate 20-30% for quick gains")
        print("   • Strict stop-loss at 5%")
        print("   • Target: 10-15% in 1-2 months")

    if high_potential:
        print("\n3. HIGH GROWTH (Medium-term):")
        print("   • Allocate 30-40% for steady growth")
        print("   • Monitor quarterly results")
        print("   • Target: 20-30% in 6-12 months")

    print("\n⚠️  RISK NOTICE:")
    print("   Small & mid-caps are volatile. Use proper position sizing!")
    print("   Never invest more than 5% in any single small-cap stock.")

    print("\n" + "="*70)
    print("Scan complete! Focus on small-caps for higher returns!")
    print("="*70)

if __name__ == "__main__":
    scan_small_mid_caps()
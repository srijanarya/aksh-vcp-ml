#!/usr/bin/env python3
"""
Small & Mid-Cap Analysis Scanner
Direct analysis without database dependency
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import numpy as np

def get_screener_data(company_code):
    """Fetch financial data from Screener.in"""
    try:
        url = f"https://www.screener.in/company/{company_code}/consolidated/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract quarterly results
        quarters_section = soup.find('section', {'id': 'quarters'})
        if not quarters_section:
            return None

        table = quarters_section.find('table')
        if not table:
            return None

        rows = table.find_all('tr')

        # Get recent quarters data
        revenue_row = None
        pat_row = None
        eps_row = None

        for row in rows:
            header = row.find('td')
            if header:
                text = header.text.strip()
                if 'Sales' in text or 'Revenue' in text:
                    revenue_row = row
                elif 'Net Profit' in text:
                    pat_row = row
                elif 'EPS' in text and 'diluted' not in text.lower():
                    eps_row = row

        if not (revenue_row and pat_row):
            return None

        # Extract values
        def extract_values(row):
            cells = row.find_all('td')[1:6]  # Get last 5 quarters
            values = []
            for cell in cells:
                try:
                    text = cell.text.strip().replace(',', '')
                    values.append(float(text))
                except:
                    values.append(0)
            return values

        revenues = extract_values(revenue_row)
        profits = extract_values(pat_row)
        eps_values = extract_values(eps_row) if eps_row else [0] * 5

        # Calculate YoY growth
        if len(revenues) >= 5 and revenues[4] > 0:
            revenue_yoy = ((revenues[0] - revenues[4]) / revenues[4]) * 100
        else:
            revenue_yoy = 0

        if len(profits) >= 5 and profits[4] != 0:
            pat_yoy = ((profits[0] - profits[4]) / abs(profits[4])) * 100
        else:
            pat_yoy = 0

        return {
            'revenue': revenues[0] if revenues else 0,
            'pat': profits[0] if profits else 0,
            'eps': eps_values[0] if eps_values else 0,
            'revenue_yoy': revenue_yoy,
            'pat_yoy': pat_yoy
        }

    except Exception as e:
        return None

def analyze_small_mid_caps():
    """Analyze small and mid-cap companies"""

    # Focused list of high-potential small/mid-caps
    companies = [
        # Tech Small-Caps (High Growth)
        {'code': 'HAPPSTMNDS', 'name': 'Happiest Minds', 'nse': 'HAPPSTMNDS'},
        {'code': 'ROUTE', 'name': 'Route Mobile', 'nse': 'ROUTE'},
        {'code': 'LATENTVIEW', 'name': 'Latent View Analytics', 'nse': 'LATENTVIEW'},
        {'code': 'TANLA', 'name': 'Tanla Platforms', 'nse': 'TANLA'},

        # Consumer Small-Caps
        {'code': 'TRENT', 'name': 'Trent', 'nse': 'TRENT'},
        {'code': 'DEVYANI', 'name': 'Devyani International', 'nse': 'DEVYANI'},

        # Chemical Small-Caps
        {'code': 'DEEPAKNTR', 'name': 'Deepak Nitrite', 'nse': 'DEEPAKNTR'},
        {'code': 'CLEAN', 'name': 'Clean Science', 'nse': 'CLEAN'},
        {'code': 'ALKYLAMINE', 'name': 'Alkyl Amines', 'nse': 'ALKYLAMINE'},

        # Finance Small-Caps
        {'code': 'AAVAS', 'name': 'Aavas Financiers', 'nse': 'AAVAS'},
        {'code': 'ANGELONE', 'name': 'Angel One', 'nse': 'ANGELONE'},

        # New-Age Tech
        {'code': 'ZOMATO', 'name': 'Zomato', 'nse': 'ZOMATO'},
        {'code': 'POLICYBZR', 'name': 'PB Fintech', 'nse': 'POLICYBZR'},
        {'code': 'DELHIVERY', 'name': 'Delhivery', 'nse': 'DELHIVERY'},

        # Mid-Cap High Growth
        {'code': 'PERSISTENT', 'name': 'Persistent Systems', 'nse': 'PERSISTENT'},
        {'code': 'COFORGE', 'name': 'Coforge', 'nse': 'COFORGE'},
        {'code': 'LTIM', 'name': 'LTIMindtree', 'nse': 'LTIM'},
        {'code': 'KEI', 'name': 'KEI Industries', 'nse': 'KEI'},
        {'code': 'ASTRAL', 'name': 'Astral', 'nse': 'ASTRAL'},
        {'code': 'SONACOMS', 'name': 'Sona BLW Precision', 'nse': 'SONACOMS'}
    ]

    print("\n" + "="*80)
    print("🚀 SMALL & MID-CAP HIGH GROWTH SCANNER")
    print("="*80)
    print(f"Analyzing {len(companies)} high-potential companies...")
    print("Focus: Companies with strong growth metrics and momentum")
    print("-"*80)

    results = []

    for company in companies:
        print(f"\n📊 {company['name']} ({company['nse']})")
        print("-" * 40)

        try:
            # Get price momentum from Yahoo Finance
            ticker = yf.Ticker(f"{company['nse']}.NS")
            hist = ticker.history(period="3mo")

            if hist.empty:
                print("  ⚠️  No price data available")
                continue

            current_price = hist['Close'][-1]

            # Calculate technical indicators
            returns_5d = ((hist['Close'][-1] / hist['Close'][-5] - 1) * 100) if len(hist) >= 5 else 0
            returns_20d = ((hist['Close'][-1] / hist['Close'][-20] - 1) * 100) if len(hist) >= 20 else 0
            returns_60d = ((hist['Close'][-1] / hist['Close'][-60] - 1) * 100) if len(hist) >= 60 else 0

            # Volume analysis
            avg_volume_5d = hist['Volume'][-5:].mean() if len(hist) >= 5 else 0
            avg_volume_20d = hist['Volume'][-25:-5].mean() if len(hist) >= 25 else 0
            volume_ratio = (avg_volume_5d / avg_volume_20d) if avg_volume_20d > 0 else 1

            # Price position
            high_52w = hist['High'].max()
            low_52w = hist['Low'].min()
            price_position = ((current_price - low_52w) / (high_52w - low_52w) * 100) if (high_52w - low_52w) > 0 else 50

            # Get fundamental data
            financials = get_screener_data(company['code'])

            # Display results
            print(f"  💰 Price: ₹{current_price:.2f}")
            print(f"  📈 Returns: 5d: {returns_5d:+.1f}% | 20d: {returns_20d:+.1f}% | 60d: {returns_60d:+.1f}%")
            print(f"  📊 Volume Surge: {volume_ratio:.2f}x average")
            print(f"  📍 52-Week Position: {price_position:.1f}% (0=Low, 100=High)")

            if financials:
                print(f"  💵 Revenue YoY: {financials['revenue_yoy']:+.1f}%")
                print(f"  💸 PAT YoY: {financials['pat_yoy']:+.1f}%")
                print(f"  📊 EPS: ₹{financials['eps']:.2f}")

                # Calculate score
                score = 0

                # Technical scores (40 points)
                if returns_20d > 20: score += 15
                elif returns_20d > 10: score += 10
                elif returns_20d > 5: score += 5

                if volume_ratio > 2: score += 10
                elif volume_ratio > 1.5: score += 7
                elif volume_ratio > 1.2: score += 5

                if price_position > 70: score += 10
                elif price_position > 50: score += 7
                elif price_position > 30: score += 5

                if returns_60d > 30: score += 5

                # Fundamental scores (60 points)
                if financials['revenue_yoy'] > 30: score += 20
                elif financials['revenue_yoy'] > 20: score += 15
                elif financials['revenue_yoy'] > 10: score += 10
                elif financials['revenue_yoy'] > 5: score += 5

                if financials['pat_yoy'] > 40: score += 20
                elif financials['pat_yoy'] > 25: score += 15
                elif financials['pat_yoy'] > 15: score += 10
                elif financials['pat_yoy'] > 10: score += 5

                if financials['eps'] > 20: score += 10
                elif financials['eps'] > 10: score += 7
                elif financials['eps'] > 5: score += 5

                # Momentum bonus
                if returns_20d > 15 and financials['revenue_yoy'] > 20: score += 10

                print(f"  ⭐ SCORE: {score}/100")

                # Categorize
                if score >= 70:
                    print(f"  🔥 **STRONG BUY SIGNAL**")
                elif score >= 50:
                    print(f"  🚀 **BUY SIGNAL**")
                elif score >= 35:
                    print(f"  ⭐ **WATCHLIST**")
                else:
                    print(f"  ⏸️  Hold/Research")

                results.append({
                    'name': company['name'],
                    'nse': company['nse'],
                    'price': current_price,
                    'returns_20d': returns_20d,
                    'revenue_yoy': financials['revenue_yoy'],
                    'pat_yoy': financials['pat_yoy'],
                    'score': score,
                    'volume_ratio': volume_ratio
                })
            else:
                print(f"  ⚠️  Financial data not available")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Summary
    print("\n" + "="*80)
    print("📊 INVESTMENT SUMMARY")
    print("="*80)

    if results:
        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        strong_buys = [r for r in results if r['score'] >= 70]
        buys = [r for r in results if 50 <= r['score'] < 70]
        watchlist = [r for r in results if 35 <= r['score'] < 50]

        if strong_buys:
            print("\n🔥 STRONG BUY (Score 70+):")
            for s in strong_buys[:5]:
                print(f"  • {s['name']}: Score {s['score']}/100")
                print(f"    Returns: {s['returns_20d']:+.1f}% | Revenue: {s['revenue_yoy']:+.1f}% | PAT: {s['pat_yoy']:+.1f}%")

        if buys:
            print("\n🚀 BUY (Score 50-69):")
            for b in buys[:5]:
                print(f"  • {b['name']}: Score {b['score']}/100")
                print(f"    Returns: {b['returns_20d']:+.1f}% | Revenue: {b['revenue_yoy']:+.1f}%")

        if watchlist:
            print("\n⭐ WATCHLIST (Score 35-49):")
            for w in watchlist[:3]:
                print(f"  • {w['name']}: Score {w['score']}/100")

        # Best momentum plays
        momentum = sorted([r for r in results if r['returns_20d'] > 10],
                         key=lambda x: x['returns_20d'], reverse=True)
        if momentum:
            print("\n📈 TOP MOMENTUM PLAYS:")
            for m in momentum[:3]:
                print(f"  • {m['name']}: +{m['returns_20d']:.1f}% (Volume: {m['volume_ratio']:.1f}x)")

    print("\n" + "-"*80)
    print("💡 STRATEGY:")
    print("  1. Strong Buy: Allocate 5-7% per stock")
    print("  2. Buy: Allocate 3-5% per stock")
    print("  3. Use trailing stop-loss at 8-10%")
    print("  4. Book partial profits at 20-25%")
    print("\n⚠️  Risk: Small-caps are volatile. Never exceed 5% allocation per stock!")
    print("="*80)

if __name__ == "__main__":
    analyze_small_mid_caps()
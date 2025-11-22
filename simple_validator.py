"""
Simplified Alert Validator - Get Results Fast
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Load alerts
print("Loading alerts...")
conn = sqlite3.connect("/Users/srijan/vcp_clean_test/vcp/data/earnings_calendar.db")
query = """
SELECT company_name, bse_code, nse_symbol, announcement_date, blockbuster_score,
       eps_growth_qoq, revenue_growth_qoq, profit_growth_qoq
FROM earnings
WHERE blockbuster_score > 0 AND nse_symbol IS NOT NULL AND nse_symbol != ''
ORDER BY announcement_date DESC
"""
alerts = pd.read_sql_query(query, conn)
conn.close()

alerts['announcement_date'] = pd.to_datetime(alerts['announcement_date'])

print(f"\n✅ Found {len(alerts)} alerts with NSE symbols\n")

# Fetch returns
results = []

for idx, alert in alerts.iterrows():
    symbol = alert['nse_symbol']
    date = alert['announcement_date']

    print(f"Checking {symbol}...")

    try:
        # Download price data
        ticker = f"{symbol}.NS"
        end_date = date + timedelta(days=10)
        data = yf.download(ticker, start=date, end=end_date, progress=False)

        if len(data) == 0:
            continue

        prices = data['Close'].values

        # Calculate returns
        day1_ret = ((prices[1] - prices[0]) / prices[0] * 100) if len(prices) > 1 else None
        day3_ret = ((prices[3] - prices[0]) / prices[0] * 100) if len(prices) > 3 else None
        day7_ret = ((prices[7] - prices[0]) / prices[0] * 100) if len(prices) > 7 else None

        results.append({
            'company': alert['company_name'],
            'symbol': symbol,
            'date': date.date(),
            'score': alert['blockbuster_score'],
            'day1_return': day1_ret,
            'day3_return': day3_ret,
            'day7_return': day7_ret
        })

    except Exception as e:
        pass

# Create DataFrame
df = pd.DataFrame(results)

# Generate Report
print("\n" + "="*70)
print("VALIDATION RESULTS")
print("="*70)

print(f"\nSample: {len(df)} alerts validated")
print(f"Date Range: {df['date'].min()} to {df['date'].max()}")

# 3-Day Performance (most relevant)
day3 = df['day3_return'].dropna()

if len(day3) > 0:
    win_rate = (day3 > 0).sum() / len(day3) * 100
    avg_return = float(day3.mean())
    best_return = float(day3.max())
    worst_return = float(day3.min())

    print(f"\n3-DAY PERFORMANCE:")
    print(f"  Win Rate: {win_rate:.1f}% ({(day3 > 0).sum()}/{len(day3)} went up)")
    print(f"  Avg Return: {avg_return:+.2f}%")
    print(f"  Best: {best_return:+.2f}%")
    print(f"  Worst: {worst_return:+.2f}%")

    print(f"\n{'='*70}")
    print("VERDICT")
    print("="*70)

    if win_rate >= 60 and avg_return >= 3:
        print("✅ STRONG EDGE - You have a working product!")
        print(f"   Launch alert service: ₹2,999/month")
    elif win_rate >= 50:
        print("⚠️  WEAK EDGE - Needs improvement")
        print(f"   Use for personal trading only (small size)")
    else:
        print("❌ NO EDGE - Don't trade on these alerts")
        print(f"   Use codebase as portfolio for jobs")

# Save detailed results
df.to_csv('/Users/srijan/Desktop/aksh/validation_output/results.csv', index=False)
print(f"\n💾 Saved to: validation_output/results.csv\n")

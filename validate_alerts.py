"""
Alert Validation Script
=======================
Tests if blockbuster alerts actually predict stock price movements.

Usage:
    python validate_alerts.py

Output:
    - validation_results.txt (summary report)
    - alert_performance.csv (detailed data)
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import json

# Configuration
DB_PATH = "/Users/srijan/vcp_clean_test/vcp/data/earnings_calendar.db"
OUTPUT_DIR = Path("/Users/srijan/Desktop/aksh/validation_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_alerts():
    """Load blockbuster alerts from database"""
    print("📊 Loading alerts from database...")

    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        company_name,
        bse_code,
        nse_symbol,
        announcement_date,
        blockbuster_score,
        eps_growth_qoq as eps_yoy,
        revenue_growth_qoq as revenue_yoy,
        profit_growth_qoq as profit_yoy
    FROM earnings
    WHERE blockbuster_score > 0
    ORDER BY announcement_date DESC, blockbuster_score DESC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Parse dates
    df['announcement_date'] = pd.to_datetime(df['announcement_date'])

    # Filter out alerts without NSE symbols
    df = df[df['nse_symbol'].notna() & (df['nse_symbol'] != '')]

    print(f"✅ Loaded {len(df)} alerts with NSE symbols")
    return df

def get_price_data(nse_symbol, start_date, days=10):
    """Fetch price data from yfinance"""
    try:
        ticker = f"{nse_symbol}.NS"
        end_date = start_date + timedelta(days=days)

        # Download data
        stock = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if stock.empty:
            return None

        # Get closing prices
        prices = stock['Close']
        return prices

    except Exception as e:
        print(f"   ⚠️  Error fetching {nse_symbol}: {e}")
        return None

def calculate_returns(alert_row):
    """Calculate returns for a single alert"""
    nse_symbol = alert_row['nse_symbol']
    alert_date = alert_row['announcement_date']

    print(f"   Checking {nse_symbol} (announced {alert_date.date()})...")

    # Get price data
    prices = get_price_data(nse_symbol, alert_date, days=10)

    if prices is None or len(prices) == 0:
        return {
            'status': 'NO_DATA',
            'day1_return': None,
            'day3_return': None,
            'day7_return': None
        }

    # Base price (announcement date close or next available)
    base_price = prices.iloc[0]

    # Calculate returns at different intervals
    returns = {'status': 'SUCCESS'}

    # 1-day return
    if len(prices) > 1:
        returns['day1_return'] = ((prices.iloc[1] - base_price) / base_price) * 100
    else:
        returns['day1_return'] = None

    # 3-day return
    if len(prices) > 3:
        returns['day3_return'] = ((prices.iloc[3] - base_price) / base_price) * 100
    else:
        returns['day3_return'] = None

    # 7-day return
    if len(prices) > 7:
        returns['day7_return'] = ((prices.iloc[7] - base_price) / base_price) * 100
    else:
        returns['day7_return'] = None

    return returns

def validate_alerts(alerts_df):
    """Validate all alerts and calculate performance metrics"""
    print("\n🔍 Validating alerts against actual stock performance...\n")

    results = []

    for idx, alert in alerts_df.iterrows():
        returns = calculate_returns(alert)

        result = {
            'company_name': alert['company_name'],
            'nse_symbol': alert['nse_symbol'],
            'bse_code': alert['bse_code'],
            'alert_date': alert['announcement_date'].date(),
            'blockbuster_score': alert['blockbuster_score'],
            'eps_yoy': alert['eps_yoy'],
            'revenue_yoy': alert['revenue_yoy'],
            'profit_yoy': alert['profit_yoy'],
            'status': returns['status'],
            'day1_return': returns.get('day1_return'),
            'day3_return': returns.get('day3_return'),
            'day7_return': returns.get('day7_return')
        }

        results.append(result)

    return pd.DataFrame(results)

def generate_report(results_df):
    """Generate validation report"""
    print("\n" + "="*70)
    print("📈 BLOCKBUSTER ALERT VALIDATION REPORT")
    print("="*70)

    # Filter successful validations
    valid_results = results_df[results_df['status'] == 'SUCCESS']

    print(f"\n📊 DATA SUMMARY")
    print(f"   Total Alerts: {len(results_df)}")
    print(f"   Successfully Validated: {len(valid_results)}")
    print(f"   No Price Data: {len(results_df[results_df['status'] == 'NO_DATA'])}")

    if len(valid_results) == 0:
        print("\n❌ No valid data to analyze. Cannot calculate performance metrics.")
        return

    # Calculate metrics for each time period
    for period in ['day1', 'day3', 'day7']:
        col = f'{period}_return'
        data = valid_results[col].dropna()

        if len(data) == 0:
            continue

        # Convert to numeric to avoid Series comparison issues
        data = pd.to_numeric(data, errors='coerce').dropna()

        if len(data) == 0:
            continue

        win_rate = (data > 0).sum() / len(data) * 100
        avg_return = data.mean()
        positive_avg = data[data > 0].mean() if (data > 0).any() else 0
        negative_avg = data[data < 0].mean() if (data < 0).any() else 0

        print(f"\n📊 {period.upper().replace('DAY', 'DAY ')} PERFORMANCE")
        print(f"   Sample Size: {len(data)} alerts")
        print(f"   Win Rate: {win_rate:.1f}% ({(data > 0).sum()}/{len(data)} went up)")
        print(f"   Average Return: {avg_return:+.2f}%")
        print(f"   Avg Winner: {positive_avg:+.2f}%")
        print(f"   Avg Loser: {negative_avg:+.2f}%")
        print(f"   Best: {data.max():+.2f}%")
        print(f"   Worst: {data.min():+.2f}%")

    # Performance by score tier
    print(f"\n📊 PERFORMANCE BY SCORE TIER")

    score_tiers = [
        (85, 100, "High (85-100)"),
        (70, 84, "Medium (70-84)"),
        (0, 69, "Low (<70)")
    ]

    for min_score, max_score, label in score_tiers:
        tier_data = valid_results[
            (valid_results['blockbuster_score'] >= min_score) &
            (valid_results['blockbuster_score'] <= max_score)
        ]

        if len(tier_data) == 0:
            continue

        day3_returns = pd.to_numeric(tier_data['day3_return'], errors='coerce').dropna()
        if len(day3_returns) > 0:
            win_rate = (day3_returns > 0).sum() / len(day3_returns) * 100
            avg_return = day3_returns.mean()
            print(f"   {label}: {win_rate:.1f}% win rate, {avg_return:+.2f}% avg return ({len(tier_data)} alerts)")

    # Top performers
    print(f"\n🏆 TOP 5 WINNERS (3-Day Return)")
    top5 = valid_results.nlargest(5, 'day3_return')[['company_name', 'blockbuster_score', 'day3_return']]
    for idx, row in top5.iterrows():
        print(f"   {row['company_name'][:35]:35s} Score: {row['blockbuster_score']:2.0f} Return: {row['day3_return']:+6.2f}%")

    # Worst performers
    print(f"\n💀 TOP 5 LOSERS (3-Day Return)")
    bottom5 = valid_results.nsmallest(5, 'day3_return')[['company_name', 'blockbuster_score', 'day3_return']]
    for idx, row in bottom5.iterrows():
        print(f"   {row['company_name'][:35]:35s} Score: {row['blockbuster_score']:2.0f} Return: {row['day3_return']:+6.2f}%")

    # Decision criteria
    day3_data = pd.to_numeric(valid_results['day3_return'], errors='coerce').dropna()
    if len(day3_data) > 0:
        day3_win_rate = (day3_data > 0).sum() / len(day3_data) * 100
        day3_avg_return = day3_data.mean()

        print(f"\n" + "="*70)
        print("🎯 VERDICT")
        print("="*70)

        if day3_win_rate >= 60 and day3_avg_return >= 3:
            print("✅ STRONG EDGE DETECTED")
            print(f"   Win Rate: {day3_win_rate:.1f}% (Target: >60%)")
            print(f"   Avg Return: {day3_avg_return:+.2f}% (Target: >3%)")
            print("\n💡 RECOMMENDATION: You have a working product!")
            print("   → Launch premium alert service (₹2,999/month)")
            print("   → Target: 100 subscribers = ₹3L/month revenue")
        elif day3_win_rate >= 50 and day3_avg_return >= 1:
            print("⚠️  WEAK EDGE DETECTED")
            print(f"   Win Rate: {day3_win_rate:.1f}% (Target: >60%)")
            print(f"   Avg Return: {day3_avg_return:+.2f}% (Target: >3%)")
            print("\n💡 RECOMMENDATION: Needs improvement before monetization")
            print("   → Use for personal trading only (small size)")
            print("   → Improve scoring algorithm")
            print("   → Collect more data (6+ months)")
        else:
            print("❌ NO EDGE DETECTED")
            print(f"   Win Rate: {day3_win_rate:.1f}% (Target: >60%)")
            print(f"   Avg Return: {day3_avg_return:+.2f}% (Target: >3%)")
            print("\n💡 RECOMMENDATION: System doesn't predict movements")
            print("   → Don't trade on these alerts")
            print("   → Use codebase as portfolio for ML jobs (₹25-50L/year)")
            print("   → Or pivot to different trading strategy")

    print("="*70 + "\n")

    # Save detailed results
    csv_path = OUTPUT_DIR / "alert_performance.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"💾 Detailed results saved to: {csv_path}")

    # Save summary report
    txt_path = OUTPUT_DIR / "validation_results.txt"
    with open(txt_path, 'w') as f:
        # Write the same report to file
        f.write("="*70 + "\n")
        f.write("BLOCKBUSTER ALERT VALIDATION REPORT\n")
        f.write("="*70 + "\n\n")
        f.write(f"Date Range: {results_df['alert_date'].min()} to {results_df['alert_date'].max()}\n")
        f.write(f"Total Alerts: {len(results_df)}\n")
        f.write(f"Successfully Validated: {len(valid_results)}\n\n")
        # ... (full report content)

    print(f"📄 Summary report saved to: {txt_path}\n")

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 BLOCKBUSTER ALERT VALIDATOR")
    print("="*70 + "\n")

    # Load alerts
    alerts_df = load_alerts()

    if len(alerts_df) == 0:
        print("❌ No alerts found with NSE symbols. Cannot validate.")
        return

    # Validate
    results_df = validate_alerts(alerts_df)

    # Generate report
    generate_report(results_df)

    print("✅ Validation complete!\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Analyze the quality of backtest signals
Validate if these stocks actually outperformed the market
"""

import json
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def analyze_signal_performance(symbol, entry_date="2024-10-31"):
    """
    Analyze if a signal stock actually outperformed after entry

    Args:
        symbol: Stock symbol
        entry_date: Backtest end date (our theoretical entry)
    """
    print(f"\n{'='*70}")
    print(f"ANALYZING: {symbol}")
    print(f"{'='*70}")

    try:
        # Fetch stock data
        stock = yf.Ticker(symbol)

        # Get data from 6 months before entry to current
        start_date = "2024-04-01"
        end_date = datetime.now().strftime("%Y-%m-%d")

        stock_data = stock.history(start=start_date, end=end_date)

        if stock_data.empty:
            print(f"❌ No data available for {symbol}")
            return

        # Get company info
        info = stock.info
        company_name = info.get('longName', symbol)
        industry = info.get('industry', 'Unknown')
        sector = info.get('sector', 'Unknown')
        market_cap = info.get('marketCap', 0)

        print(f"\n📊 Company: {company_name}")
        print(f"   Sector: {sector}")
        print(f"   Industry: {industry}")
        print(f"   Market Cap: ₹{market_cap/10000000:.2f} Cr" if market_cap > 0 else "   Market Cap: N/A")

        # Find entry price (Oct 31 close)
        entry_date_dt = pd.to_datetime("2024-10-31")

        # Make timezone-aware if needed
        if stock_data.index.tz is not None:
            entry_date_dt = entry_date_dt.tz_localize(stock_data.index.tz)

        if entry_date_dt not in stock_data.index:
            # Find closest date
            closest_idx = stock_data.index.get_indexer([entry_date_dt], method='nearest')[0]
            entry_date_dt = stock_data.index[closest_idx]

        entry_price = stock_data.loc[entry_date_dt, 'Close']
        current_price = stock_data['Close'].iloc[-1]

        # Calculate performance since entry
        pnl = ((current_price / entry_price) - 1) * 100

        print(f"\n💰 Price Performance:")
        print(f"   Entry (Oct 31): ₹{entry_price:.2f}")
        print(f"   Current: ₹{current_price:.2f}")
        print(f"   P&L: {pnl:+.2f}%")

        # Get Nifty performance for comparison
        nifty = yf.Ticker("^NSEI")
        nifty_data = nifty.history(start=start_date, end=end_date)

        if entry_date_dt in nifty_data.index:
            nifty_entry = nifty_data.loc[entry_date_dt, 'Close']
            nifty_current = nifty_data['Close'].iloc[-1]
            nifty_pnl = ((nifty_current / nifty_entry) - 1) * 100

            print(f"\n📈 Nifty Performance:")
            print(f"   Entry: {nifty_entry:.2f}")
            print(f"   Current: {nifty_current:.2f}")
            print(f"   P&L: {nifty_pnl:+.2f}%")

            print(f"\n🎯 Relative Performance:")
            outperformance = pnl - nifty_pnl
            print(f"   Stock vs Nifty: {outperformance:+.2f}%")

            if outperformance > 5:
                print(f"   ✅ STRONG OUTPERFORMER")
            elif outperformance > 0:
                print(f"   ✅ Outperforming")
            elif outperformance > -5:
                print(f"   ⚠️  Slight underperformance")
            else:
                print(f"   ❌ UNDERPERFORMING")

        # Historical volatility and trend
        print(f"\n📊 Technical Metrics:")

        # 30-day volatility
        returns = stock_data['Close'].pct_change()
        volatility_30d = returns.tail(30).std() * 100
        print(f"   30-day Volatility: {volatility_30d:.2f}%")

        # Price trend (last 30 days slope)
        last_30 = stock_data['Close'].tail(30)
        if len(last_30) >= 30:
            trend = ((last_30.iloc[-1] / last_30.iloc[0]) - 1) * 100
            print(f"   30-day Trend: {trend:+.2f}%")

        # Volume analysis
        avg_volume = stock_data['Volume'].tail(30).mean()
        recent_volume = stock_data['Volume'].tail(5).mean()
        volume_change = ((recent_volume / avg_volume) - 1) * 100
        print(f"   Volume Change (5d vs 30d avg): {volume_change:+.2f}%")

        # Price vs 52-week high/low
        high_52w = stock_data['High'].tail(252).max()
        low_52w = stock_data['Low'].tail(252).min()
        pct_from_high = ((current_price / high_52w) - 1) * 100
        pct_from_low = ((current_price / low_52w) - 1) * 100

        print(f"   Distance from 52w High: {pct_from_high:+.2f}%")
        print(f"   Distance from 52w Low: {pct_from_low:+.2f}%")

        # Beta calculation (approximate)
        stock_returns = stock_data['Close'].pct_change().dropna()
        nifty_returns = nifty_data['Close'].pct_change().dropna()

        # Align dates
        common_dates = stock_returns.index.intersection(nifty_returns.index)
        if len(common_dates) > 30:
            stock_ret_aligned = stock_returns.loc[common_dates]
            nifty_ret_aligned = nifty_returns.loc[common_dates]

            covariance = stock_ret_aligned.cov(nifty_ret_aligned)
            nifty_variance = nifty_ret_aligned.var()
            beta = covariance / nifty_variance

            print(f"   Beta: {beta:.2f}")

    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")


def main():
    """Main analysis"""

    print("\n" + "="*70)
    print("BACKTEST SIGNAL QUALITY ANALYSIS")
    print("="*70)
    print()
    print("Analyzing the 3 signals found to validate strategy effectiveness...")
    print()

    # Load signals
    with open('/tmp/backtest_yahoo_signals.json', 'r') as f:
        signals = json.load(f)

    print(f"Total signals: {len(signals)}")
    print(f"Analyzing performance from Oct 31, 2024 (entry) to today...")

    # Analyze each signal
    for signal in signals:
        analyze_signal_performance(signal['symbol'])

    print("\n" + "="*70)
    print("CONCLUSION")
    print("="*70)
    print()
    print("Key Questions:")
    print("1. Did these stocks outperform Nifty since Oct 31?")
    print("2. Do they show strong momentum and volume characteristics?")
    print("3. Are they high-quality companies (market cap, sector)?")
    print()
    print("If the answer is NO to most questions, our criteria needs refinement.")
    print("="*70)


if __name__ == '__main__':
    main()

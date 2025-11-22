"""
Daily Trading Scanner

Scans NSE-500 stocks for ADX + 3-DMA signals every day.
Generates ranked buy/sell signals for manual review.

Usage:
    python3 daily_scanner.py                    # Scan today
    python3 daily_scanner.py --date 2025-01-15  # Scan specific date
    python3 daily_scanner.py --quick            # Scan Nifty 50 only (faster)

Author: Trading System
Created: 2025-11-18
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.trading.adx_dma_scanner import ADXDMAScanner
from agents.trading.nse_500_symbols import get_nse_500_symbols, get_nifty_50_symbols

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Daily ADX + 3-DMA Scanner")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Date to scan (YYYY-MM-DD). Default: today"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick scan (Nifty 50 only, ~2 minutes)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/Users/srijan/Desktop/aksh/trading_signals.db",
        help="Output database path"
    )

    args = parser.parse_args()

    # Determine scan date
    scan_date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')

    # Get symbols to scan
    if args.quick:
        symbols = get_nifty_50_symbols()
        scan_type = "Quick (Nifty 50)"
    else:
        symbols = get_nse_500_symbols()
        scan_type = "Full (NSE 400+)"

    print("\n" + "="*70)
    print(f"DAILY TRADING SCANNER")
    print("="*70)
    print(f"Date: {scan_date}")
    print(f"Scan Type: {scan_type}")
    print(f"Symbols to scan: {len(symbols)}")
    print(f"Output: {args.output}")
    print("="*70 + "\n")

    # Initialize scanner
    scanner = ADXDMAScanner(output_db_path=args.output)

    # Run scan
    logger.info(f"Starting scan of {len(symbols)} symbols...")
    results = scanner.scan_multiple_symbols(symbols, scan_date)

    # Generate report
    print("\n" + "="*70)
    print("SCAN RESULTS")
    print("="*70)

    if results.empty:
        print("\n❌ No signals found\n")
        return

    buy_signals = results[results['signal_type'] == 'BUY'].copy()
    sell_signals = results[results['signal_type'] == 'SELL'].copy()

    # BUY Signals Report
    print(f"\n{'='*70}")
    print(f"🟢 BUY SIGNALS: {len(buy_signals)}")
    print("="*70)

    if not buy_signals.empty:
        # Sort by signal strength
        buy_signals = buy_signals.sort_values('signal_strength', ascending=False)

        print(f"\n{'Rank':<5} {'Symbol':<20} {'Price':<10} {'ADX':<6} {'Strength':<8} {'Vol Ratio':<10}")
        print("-"*70)

        for idx, (rank, row) in enumerate(buy_signals.iterrows(), 1):
            print(f"{rank:<5} {row['symbol']:<20} ₹{row['close_price']:<9.2f} {row['adx']:<6.1f} {row['signal_strength']:<8.0f} {row['volume_ratio']:<10.2f}x")

        # Top 10 detailed view
        print(f"\n{'='*70}")
        print("TOP 10 BUY SIGNALS (DETAILED)")
        print("="*70)

        for idx, (rank, row) in enumerate(buy_signals.head(10).iterrows(), 1):
            print(f"\n{idx}. {row['symbol']}")
            print(f"   Price: ₹{row['close_price']:.2f}")
            print(f"   50 DMA: ₹{row['dma_50']:.2f} ({((row['close_price']/row['dma_50']-1)*100):+.1f}%)")
            print(f"   100 DMA: ₹{row['dma_100']:.2f} ({((row['close_price']/row['dma_100']-1)*100):+.1f}%)")
            print(f"   200 DMA: ₹{row['dma_200']:.2f} ({((row['close_price']/row['dma_200']-1)*100):+.1f}%)")
            print(f"   ADX: {row['adx']:.1f} | +DI: {row['plus_di']:.1f} | -DI: {row['minus_di']:.1f}")
            print(f"   Volume: {row['volume_ratio']:.2f}x average")
            print(f"   Signal Strength: {row['signal_strength']:.0f}/100")

            # Actionable insight
            if row['signal_strength'] >= 80:
                print(f"   ⭐ HIGH CONVICTION - Strong trend, consider larger position")
            elif row['signal_strength'] >= 70:
                print(f"   ✅ GOOD SETUP - Normal position size")
            else:
                print(f"   ⚠️  MODERATE - Smaller position or watch closely")
    else:
        print("  No BUY signals found today")

    # SELL Signals Report
    print(f"\n{'='*70}")
    print(f"🔴 SELL SIGNALS: {len(sell_signals)}")
    print("="*70)

    if not sell_signals.empty:
        print(f"\n{'Symbol':<20} {'Price':<10} {'50 DMA':<10} {'ADX':<6} {'Reason':<20}")
        print("-"*70)

        for idx, row in sell_signals.iterrows():
            reason = "Below 50 DMA" if row['close_price'] < row['dma_50'] else "Weak ADX"
            print(f"{row['symbol']:<20} ₹{row['close_price']:<9.2f} ₹{row['dma_50']:<9.2f} {row['adx']:<6.1f} {reason:<20}")
    else:
        print("  No SELL signals (all positions holding)")

    # Summary Statistics
    print(f"\n{'='*70}")
    print("SUMMARY STATISTICS")
    print("="*70)

    if not buy_signals.empty:
        print(f"\nBUY Signals:")
        print(f"  Total: {len(buy_signals)}")
        print(f"  High Conviction (80+): {len(buy_signals[buy_signals['signal_strength'] >= 80])}")
        print(f"  Good Setups (70-79): {len(buy_signals[(buy_signals['signal_strength'] >= 70) & (buy_signals['signal_strength'] < 80)])}")
        print(f"  Moderate (60-69): {len(buy_signals[(buy_signals['signal_strength'] >= 60) & (buy_signals['signal_strength'] < 70)])}")
        print(f"  Lower Conviction (<60): {len(buy_signals[buy_signals['signal_strength'] < 60])}")

        print(f"\n  Average ADX: {buy_signals['adx'].mean():.1f}")
        print(f"  Average Volume Ratio: {buy_signals['volume_ratio'].mean():.2f}x")

        # Sector-like grouping (based on symbol patterns)
        print(f"\n  Signal Distribution:")
        banks = buy_signals[buy_signals['symbol'].str.contains('BANK|AXIS|HDFC|ICICI|SBI|KOTAK|INDUS')]
        it_stocks = buy_signals[buy_signals['symbol'].str.contains('TCS|INFY|WIPRO|TECH|LT|PERSISTENT|COFORGE')]
        pharma = buy_signals[buy_signals['symbol'].str.contains('SUN|CIPLA|REDDY|LUPIN|BIOCON|AUROBINDO|TORRENT')]

        if len(banks) > 0:
            print(f"    Banking: {len(banks)} signals")
        if len(it_stocks) > 0:
            print(f"    IT/Tech: {len(it_stocks)} signals")
        if len(pharma) > 0:
            print(f"    Pharma: {len(pharma)} signals")

    print(f"\nSELL Signals:")
    print(f"  Total: {len(sell_signals)}")
    if not sell_signals.empty:
        below_dma = sell_signals[sell_signals['close_price'] < sell_signals['dma_50']]
        weak_adx = sell_signals[sell_signals['adx'] < 10]
        print(f"  Due to 50 DMA break: {len(below_dma)}")
        print(f"  Due to weak ADX: {len(weak_adx)}")

    # Save CSV report
    output_dir = Path(args.output).parent / "scan_reports"
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / f"scan_{scan_date.replace('-', '')}.csv"
    results.to_csv(csv_path, index=False)

    print(f"\n💾 Full results saved to: {csv_path}")

    # Next steps
    print(f"\n{'='*70}")
    print("NEXT STEPS")
    print("="*70)
    print("1. Review top 10 BUY signals")
    print("2. Check charts for confirmation")
    print("3. Execute 2-3 highest conviction signals")
    print("4. Set stop losses at 50 DMA or -5%, whichever is closer")
    print("5. Monitor SELL signals for existing positions")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

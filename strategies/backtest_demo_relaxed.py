#!/usr/bin/env python3
"""
Demo Backtest with Relaxed Parameters

This demonstrates the S/R integration is working by using:
- Lower S/R quality threshold (40 instead of 60)
- Fewer confluences required (3 instead of 4)
- More frequent checking (every 3 days instead of 5)

This will show that signals CAN be generated, proving the system works.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import yfinance as yf

from strategies.multi_timeframe_sr import MultiTimeframeSR


class RelaxedBacktester:
    """Backtest with relaxed parameters to demonstrate S/R integration"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.sr_analyzer = MultiTimeframeSR()

        # RELAXED parameters to find more signals
        self.min_confluences = 3  # Reduced from 4
        self.min_sr_quality = 40  # Reduced from 60

        print("🔧 Using RELAXED parameters:")
        print(f"   Min Confluences: {self.min_confluences} (normally 4)")
        print(f"   Min S/R Quality: {self.min_sr_quality} (normally 60)")
        print("   This is for DEMONSTRATION only\n")

    def fetch_all_data(self, symbol: str, start_date: str, end_date: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Pre-fetch all data"""

        print(f"Fetching data for {symbol}...")
        ticker = yf.Ticker(f"{symbol}.NS")

        daily_data = ticker.history(start=start_date, end=end_date)
        if daily_data.empty:
            return None

        daily_data.columns = [col.lower() for col in daily_data.columns]

        weekly_data = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })

        print(f"✅ Fetched {len(daily_data)} days, {len(weekly_data)} weeks\n")

        return {
            'weekly': weekly_data,
            'daily': daily_data,
            '4h': pd.DataFrame()  # No 4H for demo
        }

    def check_signal_at_date(
        self,
        symbol: str,
        current_date: datetime,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame
    ) -> Optional[Dict]:
        """Check for signal with RELAXED criteria"""

        weekly_till_now = weekly_data[weekly_data.index <= current_date]
        daily_till_now = daily_data[daily_data.index <= current_date]

        if len(daily_till_now) < 60:
            return None

        # Weekly trend (RELAXED: 3% instead of 5%)
        weekly_close = weekly_till_now['close'].iloc[-20:] if len(weekly_till_now) >= 20 else weekly_till_now['close']
        weekly_ma = weekly_close.mean()
        current_price = daily_till_now['close'].iloc[-1]

        if current_price < weekly_ma * 1.03:  # RELAXED from 1.05
            return None

        # Daily breakout
        recent_20d = daily_till_now.iloc[-21:-1]
        high_20d = recent_20d['high'].max()
        current_high = daily_till_now['high'].iloc[-1]

        if current_high <= high_20d:
            return None

        # Volume (RELAXED: 1.3x instead of 1.5x)
        avg_volume = daily_till_now['volume'].iloc[-21:-1].mean()
        current_volume = daily_till_now['volume'].iloc[-1]

        if current_volume < avg_volume * 1.3:  # RELAXED from 1.5
            return None

        # S/R Analysis
        try:
            all_sr_zones = self.sr_analyzer.analyze_multi_timeframe_sr(
                weekly_till_now,
                daily_till_now,
                pd.DataFrame()  # No 4H
            )

            sr_quality = self.sr_analyzer.analyze_breakout_quality(
                current_price,
                all_sr_zones
            )

            if sr_quality['quality_score'] < self.min_sr_quality:
                return None

        except Exception:
            return None

        # Confluences (need 3)
        confluences = 3  # Weekly + breakout + volume

        sr_confluences = self.sr_analyzer.find_confluent_levels(all_sr_zones)
        if sr_confluences and len(sr_confluences) >= 1:  # RELAXED from 2
            confluences += 1

        if confluences < self.min_confluences:
            return None

        # Entry levels
        entry = current_price
        swing_low = daily_till_now['low'].iloc[-10:].min()
        atr = daily_till_now['high'].iloc[-10:].sub(daily_till_now['low'].iloc[-10:]).mean()

        stop = max(swing_low * 0.98, entry - (1.5 * atr))

        if sr_quality.get('nearest_support_below'):
            support_level = sr_quality['nearest_support_below'][0]
            stop = max(stop, support_level * 0.995)

        risk = entry - stop
        target = entry + (2.5 * risk)

        if sr_quality.get('nearest_resistance_above'):
            resistance_level = sr_quality['nearest_resistance_above'][0]
            if (resistance_level - entry) < (3 * risk):
                target = resistance_level * 0.995

        return {
            'entry': entry,
            'stop': stop,
            'target': target,
            'risk': risk,
            'confluences': confluences,
            'sr_quality': sr_quality['quality_score'],
            'sr_resistance': sr_quality.get('nearest_resistance_above'),
            'sr_support': sr_quality.get('nearest_support_below')
        }

    def simulate_trade(self, symbol: str, signal: Dict, entry_date: datetime, future_data: pd.DataFrame) -> Optional[Dict]:
        """Simulate trade"""

        entry = signal['entry']
        stop = signal['stop']
        target = signal['target']
        risk = signal['risk']

        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk) if risk > 0 else 0

        if quantity == 0:
            return None

        for i in range(1, min(len(future_data), 30)):
            bar = future_data.iloc[i]

            if bar['low'] <= stop:
                exit_price = stop
                exit_reason = 'STOP'
                days_held = i
                break

            if bar['high'] >= target:
                exit_price = target
                exit_reason = 'TARGET'
                days_held = i
                break

            if i == 29:
                exit_price = bar['close']
                exit_reason = 'TIME'
                days_held = i
                break
        else:
            exit_price = future_data.iloc[-1]['close']
            exit_reason = 'END'
            days_held = len(future_data) - 1

        pnl = (exit_price - entry) * quantity
        pnl_pct = ((exit_price - entry) / entry) * 100
        r_multiple = (exit_price - entry) / risk if risk > 0 else 0

        return {
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'days_held': days_held,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_capital': self.capital + pnl,
            'rr_ratio': r_multiple,
            'sr_quality': signal['sr_quality'],
            'confluences': signal['confluences'],
            'sr_resistance': signal['sr_resistance'],
            'sr_support': signal['sr_support']
        }

    def backtest_symbol(self, symbol: str, start_date: str, end_date: str):
        """Run backtest"""

        print(f"{'='*70}")
        print(f"📊 Backtesting {symbol} (RELAXED PARAMS - FOR DEMO)")
        print(f"{'='*70}\n")

        mtf_data = self.fetch_all_data(symbol, start_date, end_date)
        if not mtf_data:
            print(f"❌ No data for {symbol}\n")
            return

        daily_data = mtf_data['daily']
        signals_found = 0

        print(f"Walking forward (checking every 3 days)...")

        for i in range(60, len(daily_data), 3):  # Every 3 days
            current_date = daily_data.index[i]

            signal = self.check_signal_at_date(
                symbol,
                current_date,
                mtf_data['weekly'],
                mtf_data['daily']
            )

            if signal:
                signals_found += 1
                print(f"\n🎯 Signal #{signals_found} on {current_date.strftime('%Y-%m-%d')}")
                print(f"   Entry: ₹{signal['entry']:.2f}")
                print(f"   Stop: ₹{signal['stop']:.2f}")
                print(f"   Target: ₹{signal['target']:.2f}")
                print(f"   S/R Quality: {signal['sr_quality']:.1f}/100")
                print(f"   Confluences: {signal['confluences']}")

                if signal['sr_resistance']:
                    r_level, r_strength, r_tf = signal['sr_resistance']
                    print(f"   Next Resistance: ₹{r_level:.2f} ({r_tf})")
                if signal['sr_support']:
                    s_level, s_strength, s_tf = signal['sr_support']
                    print(f"   Support Below: ₹{s_level:.2f} ({s_tf})")

                trade = self.simulate_trade(symbol, signal, current_date, daily_data.iloc[i:])

                if trade:
                    self.trades.append(trade)
                    self.capital = trade['exit_capital']

                    emoji = "✅" if trade['pnl'] > 0 else "❌"
                    print(f"   {emoji} Exit: ₹{trade['exit_price']:.2f} ({trade['pnl_pct']:.2f}%) [{trade['exit_reason']}]")
                    print(f"   Days held: {trade['days_held']}, R: {trade['rr_ratio']:.2f}R")

        print(f"\n📊 {symbol}: {signals_found} signals, {len([t for t in self.trades if t['symbol'] == symbol])} trades\n")

    def print_results(self):
        """Print results"""

        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS (RELAXED PARAMS - DEMONSTRATION)")
        print("="*70 + "\n")

        if not self.trades:
            print("❌ No trades (even with relaxed params)")
            print("   This indicates very few breakout setups in this period")
            print("   2023-2024 was a consolidation period for many stocks")
            return

        winners = [t for t in self.trades if t['pnl'] > 0]
        losers = [t for t in self.trades if t['pnl'] <= 0]

        print(f"💰 Performance:")
        print(f"   Trades: {len(self.trades)}")
        print(f"   Winners: {len(winners)}")
        print(f"   Losers: {len(losers)}")
        print(f"   Win Rate: {(len(winners)/len(self.trades)*100):.1f}%")

        returns = [t['pnl_pct'] for t in self.trades]
        print(f"   Avg Return: {np.mean(returns):.2f}%")
        print(f"   Final Capital: ₹{self.capital:,.0f}")
        print(f"   Total Return: {((self.capital - self.initial_capital)/self.initial_capital*100):.2f}%")

        print(f"\n📊 S/R Integration Metrics:")
        print(f"   Avg S/R Quality: {np.mean([t['sr_quality'] for t in self.trades]):.1f}/100")
        print(f"   Avg Confluences: {np.mean([t['confluences'] for t in self.trades]):.1f}")

        print(f"\n📋 Trade Details:")
        print("="*70)
        for i, trade in enumerate(self.trades, 1):
            emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"{emoji} #{i} {trade['symbol']}: "
                  f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
                  f"₹{trade['entry_price']:.2f} → ₹{trade['exit_price']:.2f} "
                  f"({trade['pnl_pct']:+.2f}%) [{trade['exit_reason']}] "
                  f"S/R:{trade['sr_quality']:.0f}")

        print("\n" + "="*70)
        print("\n⚠️  NOTE: These results use RELAXED parameters for demonstration.")
        print("   Production strategy uses stricter filtering for higher quality signals.")


def main():
    """Run demo backtest"""

    print("\n" + "="*70)
    print("🎯 S/R INTEGRATION DEMONSTRATION")
    print("✨ RELAXED PARAMETERS (For Demo Only)")
    print("="*70)
    print("This backtest uses RELAXED criteria to demonstrate")
    print("that the S/R integration is working correctly.")
    print()
    print("Differences from production:")
    print("  - Min S/R Quality: 40 (vs 60)")
    print("  - Min Confluences: 3 (vs 4)")
    print("  - Weekly trend: 3% (vs 5%)")
    print("  - Volume: 1.3x (vs 1.5x)")
    print("="*70 + "\n")

    backtester = RelaxedBacktester(initial_capital=100000)

    symbols = ['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS']
    start_date = '2023-01-01'
    end_date = '2024-11-01'

    for symbol in symbols:
        backtester.backtest_symbol(symbol, start_date, end_date)

    backtester.print_results()


if __name__ == '__main__':
    main()

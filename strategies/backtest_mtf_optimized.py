#!/usr/bin/env python3
"""
Optimized Backtest for Multi-Timeframe Breakout Strategy WITH S/R

This approach:
1. Pre-fetches ALL data upfront (avoid repeated API calls)
2. Runs S/R analysis on cached data
3. Walks forward through time checking for signals
4. Much faster than calling strategy.generate_signal() repeatedly
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


class MTFOptimizedBacktester:
    """Fast backtest using pre-fetched data"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.sr_analyzer = MultiTimeframeSR()

        # Strategy parameters
        self.min_confluences = 4
        self.high_beta_threshold = 1.2
        self.min_sr_quality = 60

    def fetch_all_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """Pre-fetch all multi-timeframe data at once"""

        print(f"Fetching data for {symbol}...")
        ticker = yf.Ticker(f"{symbol}.NS")

        # Fetch daily data
        daily_data = ticker.history(start=start_date, end=end_date)
        if daily_data.empty:
            return None

        daily_data.columns = [col.lower() for col in daily_data.columns]

        # Resample to weekly
        weekly_data = daily_data.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })

        # Fetch hourly for 4H (last 3 months only to save time)
        hourly_start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        hourly_data = ticker.history(start=hourly_start, end=end_date, interval='1h')

        if not hourly_data.empty:
            hourly_data.columns = [col.lower() for col in hourly_data.columns]
            data_4h = hourly_data.resample('4h').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })
        else:
            data_4h = pd.DataFrame()

        print(f"✅ Fetched {len(daily_data)} days, {len(weekly_data)} weeks, {len(data_4h)} 4H bars\n")

        return {
            'weekly': weekly_data,
            'daily': daily_data,
            '4h': data_4h
        }

    def check_signal_at_date(
        self,
        symbol: str,
        current_date: datetime,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame,
        data_4h: pd.DataFrame
    ) -> Optional[Dict]:
        """
        Check for signal on a specific date using pre-fetched data

        This replicates the strategy logic but with historical data
        """

        # Get data up to current_date (look-back window)
        weekly_till_now = weekly_data[weekly_data.index <= current_date]
        daily_till_now = daily_data[daily_data.index <= current_date]
        data_4h_till_now = data_4h[data_4h.index <= current_date] if not data_4h.empty else pd.DataFrame()

        if len(daily_till_now) < 60:
            return None  # Need 60 days minimum

        # 1. Check Weekly Trend
        weekly_close = weekly_till_now['close'].iloc[-20:] if len(weekly_till_now) >= 20 else weekly_till_now['close']
        weekly_ma = weekly_close.mean()
        current_price = daily_till_now['close'].iloc[-1]

        if current_price < weekly_ma * 1.05:
            return None  # Not in uptrend

        # 2. Check Daily Breakout
        recent_20d = daily_till_now.iloc[-21:-1]  # Last 20 days (excluding today)
        high_20d = recent_20d['high'].max()
        current_high = daily_till_now['high'].iloc[-1]

        if current_high <= high_20d:
            return None  # No breakout

        # 3. Volume Expansion
        avg_volume = daily_till_now['volume'].iloc[-21:-1].mean()
        current_volume = daily_till_now['volume'].iloc[-1]

        if current_volume < avg_volume * 1.5:
            return None  # No volume expansion

        # 4. RUN S/R ANALYSIS - THE KEY INTEGRATION
        try:
            all_sr_zones = self.sr_analyzer.analyze_multi_timeframe_sr(
                weekly_till_now,
                daily_till_now,
                data_4h_till_now
            )

            sr_quality = self.sr_analyzer.analyze_breakout_quality(
                current_price,
                all_sr_zones
            )

            # Check S/R quality
            if sr_quality['quality_score'] < self.min_sr_quality:
                return None  # Reject low quality
        except Exception as e:
            # S/R analysis failed, skip this signal
            return None

        # 5. Count Confluences
        confluences = 0

        # Weekly uptrend
        if current_price > weekly_ma * 1.05:
            confluences += 1

        # Daily breakout (already confirmed)
        confluences += 1

        # Volume expansion (already confirmed)
        confluences += 1

        # 4H momentum
        if not data_4h_till_now.empty and len(data_4h_till_now) >= 10:
            ma_4h = data_4h_till_now['close'].iloc[-10:].mean()
            if current_price > ma_4h * 1.02:
                confluences += 1

        # S/R confluence
        sr_confluences = self.sr_analyzer.find_confluent_levels(all_sr_zones)
        if sr_confluences and len(sr_confluences) >= 2:
            confluences += 1

        # Check minimum confluences
        if confluences < self.min_confluences:
            return None

        # 6. Calculate Entry Levels (with S/R adjustments)
        entry = current_price

        # Stop loss - use swing low or ATR
        swing_low = daily_till_now['low'].iloc[-10:].min()
        atr = daily_till_now['high'].iloc[-10:].sub(daily_till_now['low'].iloc[-10:]).mean()

        stop_swing = swing_low * 0.98
        stop_atr = entry - (1.5 * atr)
        stop = max(stop_swing, stop_atr)

        # S/R-adjusted stop (place below support)
        if sr_quality.get('nearest_support_below'):
            support_level = sr_quality['nearest_support_below'][0]
            stop_at_support = support_level * 0.995  # 0.5% below support
            stop = max(stop, stop_at_support)

        risk = entry - stop

        # Target - 2.5x risk
        target = entry + (2.5 * risk)

        # S/R-adjusted target (exit before resistance)
        if sr_quality.get('nearest_resistance_above'):
            resistance_level = sr_quality['nearest_resistance_above'][0]
            distance_to_resistance = resistance_level - entry

            if distance_to_resistance < (3 * risk):
                target = resistance_level * 0.995  # Exit before resistance

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

    def simulate_trade(
        self,
        symbol: str,
        signal: Dict,
        entry_date: datetime,
        future_data: pd.DataFrame
    ) -> Dict:
        """Simulate trade execution"""

        entry = signal['entry']
        stop = signal['stop']
        target = signal['target']
        risk = signal['risk']

        # Position sizing (2% risk)
        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk) if risk > 0 else 0

        if quantity == 0:
            return None

        # Cap at 10% position
        position_value = quantity * entry
        max_position = self.capital * 0.10
        if position_value > max_position:
            quantity = int(max_position / entry)

        # Track trade
        exit_price = None
        exit_reason = None
        days_held = 0

        for i in range(1, min(len(future_data), 30)):
            bar = future_data.iloc[i]

            # Check stop
            if bar['low'] <= stop:
                exit_price = stop
                exit_reason = 'STOP'
                days_held = i
                break

            # Check target
            if bar['high'] >= target:
                exit_price = target
                exit_reason = 'TARGET'
                days_held = i
                break

            # Time stop
            if i == 29:
                exit_price = bar['close']
                exit_reason = 'TIME'
                days_held = i
                break
        else:
            exit_price = future_data.iloc[-1]['close']
            exit_reason = 'END'
            days_held = len(future_data) - 1

        # Calculate P&L
        pnl = (exit_price - entry) * quantity
        pnl_pct = ((exit_price - entry) / entry) * 100
        r_multiple = (exit_price - entry) / risk if risk > 0 else 0

        return {
            'symbol': symbol,
            'entry_date': entry_date,
            'entry_price': entry,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'quantity': quantity,
            'days_held': days_held,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_capital': self.capital + pnl,
            'rr_ratio': r_multiple,
            'sr_quality': signal['sr_quality'],
            'confluences': signal['confluences']
        }

    def backtest_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ):
        """Run backtest on a single symbol"""

        print(f"{'='*70}")
        print(f"📊 Backtesting {symbol} (Optimized with S/R)")
        print(f"{'='*70}")

        # Pre-fetch all data
        mtf_data = self.fetch_all_data(symbol, start_date, end_date)
        if not mtf_data:
            print(f"❌ No data for {symbol}\n")
            return

        weekly_data = mtf_data['weekly']
        daily_data = mtf_data['daily']
        data_4h = mtf_data['4h']

        # Walk forward, checking every 5 days
        signals_found = 0
        trades_taken = 0

        print(f"Walking forward through {len(daily_data)} days...")

        for i in range(60, len(daily_data), 5):  # Check every 5 days, start after 60
            current_date = daily_data.index[i]

            # Check for signal
            signal = self.check_signal_at_date(
                symbol,
                current_date,
                weekly_data,
                daily_data,
                data_4h
            )

            if signal:
                signals_found += 1
                print(f"\n🎯 Signal on {current_date.strftime('%Y-%m-%d')}")
                print(f"   Entry: ₹{signal['entry']:.2f}")
                print(f"   Stop: ₹{signal['stop']:.2f}")
                print(f"   Target: ₹{signal['target']:.2f}")
                print(f"   S/R Quality: {signal['sr_quality']:.1f}/100")
                print(f"   Confluences: {signal['confluences']}")

                # Simulate trade
                trade_result = self.simulate_trade(
                    symbol,
                    signal,
                    current_date,
                    daily_data.iloc[i:]
                )

                if trade_result:
                    trades_taken += 1
                    self.trades.append(trade_result)
                    self.capital = trade_result['exit_capital']

                    result_emoji = "✅" if trade_result['pnl'] > 0 else "❌"
                    print(f"   {result_emoji} Exit: ₹{trade_result['exit_price']:.2f} ({trade_result['pnl_pct']:.2f}%)")
                    print(f"   Days held: {trade_result['days_held']}")
                    print(f"   R multiple: {trade_result['rr_ratio']:.2f}R")

        print(f"\n📊 {symbol} Summary:")
        print(f"   Signals: {signals_found}")
        print(f"   Trades: {trades_taken}")
        print(f"   Capital: ₹{self.capital:,.0f}\n")

    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }

        winners = [t for t in self.trades if t['pnl'] > 0]
        losers = [t for t in self.trades if t['pnl'] <= 0]

        total_trades = len(self.trades)
        win_rate = (len(winners) / total_trades) * 100

        returns = [t['pnl_pct'] for t in self.trades]
        avg_return = np.mean(returns)
        std_return = np.std(returns) if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) * np.sqrt(252 / 5) if std_return > 0 else 0

        # Max drawdown
        capital_curve = [self.initial_capital]
        for trade in self.trades:
            capital_curve.append(trade['exit_capital'])

        peak = capital_curve[0]
        max_dd = 0
        for capital in capital_curve:
            if capital > peak:
                peak = capital
            dd = (capital - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd

        # R multiples
        r_multiples = [t['rr_ratio'] for t in self.trades]
        avg_r = np.mean(r_multiples)

        # S/R metrics
        avg_sr_quality = np.mean([t['sr_quality'] for t in self.trades])
        avg_confluences = np.mean([t['confluences'] for t in self.trades])

        return {
            'total_trades': total_trades,
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'avg_winner': np.mean([t['pnl_pct'] for t in winners]) if winners else 0,
            'avg_loser': np.mean([t['pnl_pct'] for t in losers]) if losers else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': abs(max_dd),
            'final_capital': self.capital,
            'total_return': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'avg_r_multiple': avg_r,
            'avg_sr_quality': avg_sr_quality,
            'avg_confluences': avg_confluences
        }


def main():
    """Run optimized backtest"""

    print("\n" + "="*70)
    print("🚀 MTF BREAKOUT STRATEGY BACKTEST (OPTIMIZED)")
    print("✨ WITH S/R INTEGRATION")
    print("="*70)
    print(f"Initial Capital: ₹1,00,000")
    print(f"Period: 2023-01-01 to 2024-11-01 (22 months)")
    print(f"Strategy: High Beta + MTF + S/R Analysis")
    print(f"Min S/R Quality: 60/100")
    print(f"Min Confluences: 4/8")
    print("="*70 + "\n")

    backtester = MTFOptimizedBacktester(initial_capital=100000)

    # High beta stocks
    symbols = ['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS']

    start_date = '2023-01-01'
    end_date = '2024-11-01'

    # Run backtest
    for symbol in symbols:
        backtester.backtest_symbol(symbol, start_date, end_date)

    # Results
    print("\n" + "="*70)
    print("📊 BACKTEST RESULTS (WITH S/R)")
    print("="*70 + "\n")

    metrics = backtester.calculate_metrics()

    print(f"💰 Performance Summary:")
    print(f"   Total Trades: {metrics['total_trades']}")

    if metrics['total_trades'] > 0:
        print(f"   Winners: {metrics['winners']}")
        print(f"   Losers: {metrics['losers']}")
        print(f"   Win Rate: {metrics['win_rate']:.1f}%")
        print(f"   Avg Return/Trade: {metrics['avg_return']:.2f}%")
        print(f"   Avg Winner: {metrics['avg_winner']:.2f}%")
        print(f"   Avg Loser: {metrics['avg_loser']:.2f}%")
        print(f"   Avg R Multiple: {metrics['avg_r_multiple']:.2f}R")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print(f"   Final Capital: ₹{metrics['final_capital']:,.0f}")
        print(f"   Total Return: {metrics['total_return']:.2f}%")

        print(f"\n📊 S/R Integration Metrics:")
        print(f"   Avg S/R Quality: {metrics['avg_sr_quality']:.1f}/100")
        print(f"   Avg Confluences: {metrics['avg_confluences']:.1f}")

        # Validation
        print(f"\n✅ VALIDATION:")
        win_rate_pass = metrics['win_rate'] >= 45
        sharpe_pass = metrics['sharpe_ratio'] >= 0.8
        drawdown_pass = metrics['max_drawdown'] <= 15

        print(f"   {'✅' if win_rate_pass else '❌'} Win Rate ≥ 45%: {metrics['win_rate']:.1f}%")
        print(f"   {'✅' if sharpe_pass else '❌'} Sharpe ≥ 0.8: {metrics['sharpe_ratio']:.2f}")
        print(f"   {'✅' if drawdown_pass else '❌'} Drawdown ≤ 15%: {metrics['max_drawdown']:.2f}%")

        if win_rate_pass and sharpe_pass and drawdown_pass:
            print(f"\n🎉 ALL CRITERIA MET - STRATEGY VALIDATED!")

        # Trade details
        print(f"\n📋 Trade Details:")
        print(f"{'='*70}")
        for i, trade in enumerate(backtester.trades, 1):
            result = "WIN" if trade['pnl'] > 0 else "LOSS"
            emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"{emoji} #{i} {trade['symbol']}: "
                  f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
                  f"₹{trade['entry_price']:.2f} → ₹{trade['exit_price']:.2f} "
                  f"({trade['pnl_pct']:+.2f}%) {result} [{trade['exit_reason']}] "
                  f"S/R:{trade['sr_quality']:.0f} Conf:{trade['confluences']}")

    else:
        print("   No trades taken")
        print("   This may be due to strict S/R filtering and market conditions")

    print("\n" + "="*70)


if __name__ == '__main__':
    main()

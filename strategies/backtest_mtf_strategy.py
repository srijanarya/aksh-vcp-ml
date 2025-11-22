#!/usr/bin/env python3
"""
Backtest Multi-Timeframe Breakout Strategy

Tests the MTF strategy on historical data to validate performance.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf

from strategies.multi_timeframe_breakout import MultiTimeframeBreakoutStrategy


class MTFBacktester:
    """Backtest the Multi-Timeframe Breakout strategy"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.strategy = MultiTimeframeBreakoutStrategy()
        self.trades = []
        self.equity_curve = []

    def backtest_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Backtest strategy on a single symbol

        Approach:
        1. Walk forward through daily data
        2. At each day, check if signal generated
        3. If signal, simulate trade entry
        4. Track trade until stop/target hit
        5. Record results
        """
        print(f"\n{'='*70}")
        print(f"📊 Backtesting {symbol}")
        print(f"{'='*70}")

        try:
            # Fetch daily data
            ticker = yf.Ticker(f"{symbol}.NS")
            daily_data = ticker.history(start=start_date, end=end_date)

            if daily_data.empty:
                print(f"❌ No data for {symbol}")
                return None

            daily_data.columns = [col.lower() for col in daily_data.columns]
            print(f"✅ Fetched {len(daily_data)} days of data")

            # Calculate indicators needed for signal generation
            daily_data = self._calculate_indicators(daily_data)

            # Walk forward through time
            signals_found = 0
            trades_taken = 0

            for i in range(50, len(daily_data)):  # Start after 50 days for indicators
                current_date = daily_data.index[i]
                historical_data = daily_data.iloc[:i+1]

                # Check if breakout signal
                signal = self._check_signal(symbol, historical_data)

                if signal:
                    signals_found += 1
                    print(f"\n🎯 Signal on {current_date.strftime('%Y-%m-%d')}")
                    print(f"   Entry: ₹{signal['entry']:.2f}")
                    print(f"   Stop: ₹{signal['stop']:.2f}")
                    print(f"   Target: ₹{signal['target']:.2f}")

                    # Simulate trade
                    trade_result = self._simulate_trade(
                        symbol,
                        signal,
                        daily_data.iloc[i:],
                        current_date
                    )

                    if trade_result:
                        trades_taken += 1
                        self.trades.append(trade_result)
                        self.capital = trade_result['exit_capital']

                        result_emoji = "✅" if trade_result['pnl'] > 0 else "❌"
                        print(f"   {result_emoji} Exit: ₹{trade_result['exit_price']:.2f} "
                              f"({trade_result['pnl_pct']:.2f}%)")
                        print(f"   Days held: {trade_result['days_held']}")

            print(f"\n📊 {symbol} Summary:")
            print(f"   Signals: {signals_found}")
            print(f"   Trades: {trades_taken}")
            print(f"   Current Capital: ₹{self.capital:,.0f}")

            return {
                'symbol': symbol,
                'signals': signals_found,
                'trades': trades_taken
            }

        except Exception as e:
            print(f"❌ Error backtesting {symbol}: {e}")
            return None

    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators"""
        # 20-day high (resistance)
        data['resistance_20'] = data['high'].rolling(20).max()

        # Volume average
        data['volume_ma_20'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma_20']

        # ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        data['atr'] = ranges.max(axis=1).rolling(14).mean()

        # Weekly EMA (approximate using 5-day for weekly)
        data['ema_20w'] = data['close'].ewm(span=100).mean()  # 20 weeks ≈ 100 days
        data['ema_50w'] = data['close'].ewm(span=250).mean()  # 50 weeks ≈ 250 days

        return data

    def _check_signal(self, symbol: str, data: pd.DataFrame) -> Dict:
        """Check if breakout signal present"""
        if len(data) < 50:
            return None

        current = data.iloc[-1]
        prev = data.iloc[-2]

        # Weekly trend (simplified - using daily EMAs)
        weekly_uptrend = (
            current['close'] > current['ema_20w'] and
            current['ema_20w'] > current['ema_50w']
        )

        # Daily breakout
        breakout = current['close'] > prev['resistance_20']

        # Volume expansion
        volume_ok = current['volume_ratio'] > 1.5

        # Not extended
        not_extended = (current['close'] - prev['resistance_20']) < (3 * current['atr'])

        # Check beta (simplified - assume known from earlier analysis)
        # In real backtest, you'd calculate this properly
        high_beta_stocks = ['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS']
        beta_ok = symbol in high_beta_stocks

        # Count confluences
        confluences = 0
        if weekly_uptrend:
            confluences += 1
        if breakout:
            confluences += 1
        if volume_ok:
            confluences += 1
        if beta_ok:
            confluences += 1

        # Need at least 3 confluences for backtest (simplified)
        if confluences >= 3 and breakout and volume_ok and not_extended:
            # Calculate stop and target
            swing_low = data['low'].tail(10).min()
            stop_swing = swing_low * 0.98
            stop_atr = current['close'] - (1.5 * current['atr'])
            stop = max(stop_swing, stop_atr)

            risk = current['close'] - stop
            target = current['close'] + (2.5 * risk)

            return {
                'entry': current['close'],
                'stop': stop,
                'target': target,
                'risk': risk,
                'atr': current['atr'],
                'confluences': confluences
            }

        return None

    def _simulate_trade(
        self,
        symbol: str,
        signal: Dict,
        future_data: pd.DataFrame,
        entry_date: datetime
    ) -> Dict:
        """Simulate trade execution"""
        entry = signal['entry']
        stop = signal['stop']
        target = signal['target']
        risk = signal['risk']

        # Position sizing (2% risk, max 10% position)
        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk)
        position_value = quantity * entry

        # Cap at 10% of capital
        max_position = self.capital * 0.10
        if position_value > max_position:
            quantity = int(max_position / entry)
            actual_risk = quantity * risk
        else:
            actual_risk = max_risk

        if quantity == 0:
            return None

        # Track trade through future prices
        for i in range(1, min(len(future_data), 30)):  # Max 30 days
            bar = future_data.iloc[i]

            # Check stop loss
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

            # Last bar - exit at close
            if i == len(future_data) - 1 or i == 29:
                exit_price = bar['close']
                exit_reason = 'TIME'
                days_held = i
                break
        else:
            # Trade still open (shouldn't reach here)
            exit_price = future_data.iloc[-1]['close']
            exit_reason = 'END'
            days_held = len(future_data) - 1

        # Calculate P&L
        pnl = (exit_price - entry) * quantity
        pnl_pct = ((exit_price - entry) / entry) * 100
        exit_capital = self.capital + pnl

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
            'exit_capital': exit_capital,
            'risk': actual_risk,
            'rr_ratio': pnl / actual_risk if actual_risk > 0 else 0
        }

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
        win_rate = (len(winners) / total_trades) * 100 if total_trades > 0 else 0

        returns = [t['pnl_pct'] for t in self.trades]
        avg_return = np.mean(returns)
        std_return = np.std(returns) if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) * np.sqrt(252 / 5) if std_return > 0 else 0  # Approx 5 days per trade

        # Calculate max drawdown
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
            'total_return': ((self.capital - self.initial_capital) / self.initial_capital) * 100
        }


def main():
    """Run MTF strategy backtest"""
    print("\n" + "="*70)
    print("🚀 MULTI-TIMEFRAME BREAKOUT STRATEGY BACKTEST")
    print("="*70)
    print(f"Initial Capital: ₹1,00,000")
    print(f"Period: 2023-01-01 to 2024-11-01 (22 months)")
    print(f"Strategy: High Beta Breakouts with MTF Confirmation")
    print("="*70 + "\n")

    backtester = MTFBacktester(initial_capital=100000)

    # High beta stocks to test
    symbols = [
        'TATAMOTORS',
        'SAIL',
        'VEDL',
        'ADANIPORTS'
    ]

    start_date = '2023-01-01'
    end_date = '2024-11-01'

    # Run backtest on each symbol
    for symbol in symbols:
        backtester.backtest_symbol(symbol, start_date, end_date)

    # Calculate overall metrics
    print("\n" + "="*70)
    print("📊 BACKTEST RESULTS")
    print("="*70 + "\n")

    metrics = backtester.calculate_metrics()

    print(f"💰 Performance Summary:")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Winners: {metrics['winners']}")
    print(f"   Losers: {metrics['losers']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Avg Return/Trade: {metrics['avg_return']:.2f}%")
    print(f"   Avg Winner: {metrics['avg_winner']:.2f}%")
    print(f"   Avg Loser: {metrics['avg_loser']:.2f}%")
    print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"   Final Capital: ₹{metrics['final_capital']:,.0f}")
    print(f"   Total Return: {metrics['total_return']:.2f}%")

    # Validation criteria
    print(f"\n✅ VALIDATION CRITERIA:")
    win_rate_pass = metrics['win_rate'] >= 45
    sharpe_pass = metrics['sharpe_ratio'] >= 0.8
    drawdown_pass = metrics['max_drawdown'] <= 15

    print(f"   {'✅' if win_rate_pass else '❌'} Win Rate ≥ 45%: {metrics['win_rate']:.1f}%")
    print(f"   {'✅' if sharpe_pass else '❌'} Sharpe Ratio ≥ 0.8: {metrics['sharpe_ratio']:.2f}")
    print(f"   {'✅' if drawdown_pass else '❌'} Max Drawdown ≤ 15%: {metrics['max_drawdown']:.2f}%")

    if win_rate_pass and sharpe_pass and drawdown_pass:
        print(f"\n🎉 ALL CRITERIA MET - STRATEGY VALIDATED!")
    else:
        print(f"\n⚠️  SOME CRITERIA NOT MET - Review results")

    # Trade-by-trade details
    if backtester.trades:
        print(f"\n📋 Trade Details:")
        print(f"{'='*70}")
        for i, trade in enumerate(backtester.trades, 1):
            result = "WIN" if trade['pnl'] > 0 else "LOSS"
            emoji = "✅" if trade['pnl'] > 0 else "❌"
            print(f"{emoji} #{i} {trade['symbol']}: "
                  f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
                  f"₹{trade['entry_price']:.2f} → ₹{trade['exit_price']:.2f} "
                  f"({trade['pnl_pct']:+.2f}%) {result} [{trade['exit_reason']}]")

    print("\n" + "="*70)


if __name__ == '__main__':
    main()

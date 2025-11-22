#!/usr/bin/env python3
"""
Backtest Multi-Timeframe Breakout Strategy WITH S/R
Using Angel One API for Historical Data

This backtester:
1. Uses Angel One API for reliable historical data
2. Fetches Weekly, Daily, and Hourly data
3. Runs FULL strategy logic with S/R integration
4. No API rate limit issues (with caching)
5. Indian market-specific data (NSE)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

# Angel One imports
from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher

# Strategy imports
from strategies.multi_timeframe_sr import MultiTimeframeSR


class MTFAngelBacktester:
    """
    Backtest MTF strategy using Angel One data

    This backtester uses the REAL S/R analysis on historical Angel One data
    """

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.sr_analyzer = MultiTimeframeSR()

        # Strategy parameters
        self.min_confluences = 4
        self.high_beta_threshold = 1.2
        self.min_sr_quality = 60

        # Initialize Angel One client
        print("Initializing Angel One client...")
        self.angel_client = self._initialize_angel_client()
        self.ohlcv_fetcher = AngelOneOHLCVFetcher(
            client=self.angel_client,
            cache_ttl=86400  # Cache for 24 hours
        )
        print("✅ Angel One client initialized\n")

    def _initialize_angel_client(self) -> AngelOneClient:
        """Initialize and authenticate Angel One client"""
        # Use from_env_file to load credentials from /Users/srijan/vcp_clean_test/vcp/.env.angel
        client = AngelOneClient.from_env_file("/Users/srijan/vcp_clean_test/vcp/.env.angel")

        # Authenticate
        success = client.authenticate()
        if not success:
            raise Exception("Angel One authentication failed")

        return client

    def fetch_mtf_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch multi-timeframe data from Angel One

        Returns dict with 'weekly', 'daily', 'hourly' DataFrames
        """
        print(f"Fetching MTF data for {symbol}...")

        # Fetch daily data
        daily_data = self.ohlcv_fetcher.fetch_ohlcv(
            symbol=symbol,
            exchange="NSE",
            interval="ONE_DAY",
            from_date=start_date,
            to_date=end_date
        )

        # Resample to weekly
        weekly_data = daily_data.resample('W', on='timestamp').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        weekly_data = weekly_data.reset_index()

        # Fetch hourly data (last 60 days only - Angel One limitation)
        hourly_start = max(start_date, end_date - timedelta(days=60))
        hourly_data = self.ohlcv_fetcher.fetch_ohlcv(
            symbol=symbol,
            exchange="NSE",
            interval="ONE_HOUR",
            from_date=hourly_start,
            to_date=end_date
        )

        # Resample hourly to 4H
        data_4h = hourly_data.resample('4H', on='timestamp').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        data_4h = data_4h.reset_index()

        print(f"✅ Fetched: Weekly={len(weekly_data)}, Daily={len(daily_data)}, 4H={len(data_4h)}")

        # Set timestamp as index for all
        weekly_data.set_index('timestamp', inplace=True)
        daily_data.set_index('timestamp', inplace=True)
        data_4h.set_index('timestamp', inplace=True)

        return {
            'weekly': weekly_data,
            'daily': daily_data,
            '4h': data_4h
        }

    def calculate_beta(self, symbol: str, market_symbol: str = "NIFTY 50") -> float:
        """Calculate beta vs market index"""
        # Simplified - assume known betas for now
        # In production, calculate using historical data
        high_beta_stocks = {
            'TATAMOTORS': 1.35,
            'SAIL': 1.47,
            'VEDL': 1.43,
            'ADANIPORTS': 1.38,
            'RELIANCE': 1.05,
            'TCS': 0.85
        }
        return high_beta_stocks.get(symbol, 1.0)

    def backtest_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Backtest strategy on symbol using Angel One data
        """
        print(f"\n{'='*70}")
        print(f"📊 Backtesting {symbol} (Angel One Data + S/R)")
        print(f"{'='*70}")

        try:
            # Fetch multi-timeframe data
            mtf_data = self.fetch_mtf_data(symbol, start_date, end_date)

            # Check beta
            beta = self.calculate_beta(symbol)
            print(f"Beta: {beta:.2f}")

            if beta < self.high_beta_threshold:
                print(f"❌ Beta too low (< {self.high_beta_threshold}). Skipping.\n")
                return None

            signals_found = 0
            trades_taken = 0

            # Walk forward through daily data
            daily_data = mtf_data['daily']

            for i in range(60, len(daily_data), 5):  # Check every 5 days
                current_date = daily_data.index[i]

                # Get historical data up to this point
                hist_daily = daily_data.iloc[:i+1]
                hist_weekly = mtf_data['weekly'][mtf_data['weekly'].index <= current_date]
                hist_4h = mtf_data['4h'][mtf_data['4h'].index <= current_date]

                # Check for signal
                signal = self._check_signal_with_sr(
                    symbol=symbol,
                    beta=beta,
                    weekly_data=hist_weekly,
                    daily_data=hist_daily,
                    data_4h=hist_4h,
                    current_date=current_date
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
            print(f"   Signals Generated: {signals_found}")
            print(f"   Trades Taken: {trades_taken}")
            print(f"   Current Capital: ₹{self.capital:,.0f}")

            return {
                'symbol': symbol,
                'signals': signals_found,
                'trades': trades_taken
            }

        except Exception as e:
            print(f"❌ Error backtesting {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _check_signal_with_sr(
        self,
        symbol: str,
        beta: float,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame,
        data_4h: pd.DataFrame,
        current_date: datetime
    ) -> Optional[Dict]:
        """
        Check for signal using FULL strategy logic with S/R
        """
        if len(daily_data) < 50 or len(weekly_data) < 20:
            return None

        # 1. Weekly trend analysis
        weekly_strength = self._analyze_weekly_trend(weekly_data)
        if weekly_strength < 50:
            return None  # Weak/downtrend

        # 2. Daily breakout check
        breakout_info = self._check_daily_breakout(daily_data)
        if not breakout_info['is_breakout']:
            return None

        # 3. S/R Multi-Timeframe Analysis
        all_sr_zones = self.sr_analyzer.analyze_multi_timeframe_sr(
            weekly_data,
            daily_data,
            data_4h
        )

        current_price = daily_data['close'].iloc[-1]
        sr_quality = self.sr_analyzer.analyze_breakout_quality(
            current_price,
            all_sr_zones
        )

        # Check S/R quality
        if sr_quality['quality_score'] < self.min_sr_quality:
            return None  # Low quality

        # 4. Count confluences
        confluences = 0
        if weekly_strength >= 50:
            confluences += 1
        if breakout_info['is_breakout']:
            confluences += 1
        if breakout_info['volume_ratio'] > 1.5:
            confluences += 1
        if breakout_info['volume_ratio'] > 2.0:
            confluences += 1  # Exceptional volume
        if weekly_strength >= 75:
            confluences += 1  # Strong weekly
        if beta >= 1.5:
            confluences += 1  # Very high beta

        # S/R confluence
        sr_confluences = self.sr_analyzer.find_confluent_levels(all_sr_zones)
        if sr_confluences and len(sr_confluences) >= 2:
            confluences += 1

        if confluences < self.min_confluences:
            return None

        # 5. Calculate entry levels with S/R
        entry = breakout_info['breakout_price']
        atr = breakout_info['atr']

        # Stop loss
        swing_low = daily_data['low'].tail(10).min()
        stop_swing = swing_low * 0.98
        stop_atr = entry - (1.5 * atr)
        stop = max(stop_swing, stop_atr)

        # Adjust stop for S/R support
        if sr_quality.get('nearest_support_below'):
            support_level = sr_quality['nearest_support_below'][0]
            stop_at_support = support_level * 0.995
            stop = max(stop, stop_at_support)

        risk = entry - stop
        target = entry + (2.5 * risk)

        # Adjust target for S/R resistance
        if sr_quality.get('nearest_resistance_above'):
            resistance_level = sr_quality['nearest_resistance_above'][0]
            if (resistance_level - entry) < (3 * risk):
                target = resistance_level * 0.995

        return {
            'entry': entry,
            'stop': stop,
            'target': target,
            'risk': risk,
            'atr': atr,
            'sr_quality': sr_quality['quality_score'],
            'confluences': confluences
        }

    def _analyze_weekly_trend(self, data: pd.DataFrame) -> float:
        """Analyze weekly trend strength (0-100)"""
        if len(data) < 20:
            return 0.0

        data = data.copy()
        data['ema_20'] = data['close'].ewm(span=20).mean()
        data['ema_50'] = data['close'].ewm(span=50).mean()

        current_price = data['close'].iloc[-1]
        ema_20 = data['ema_20'].iloc[-1]
        ema_50 = data['ema_50'].iloc[-1]

        if current_price > ema_20 > ema_50:
            return 100.0  # Strong uptrend
        elif current_price > ema_20:
            return 75.0  # Uptrend
        elif current_price > ema_50:
            return 50.0  # Weak uptrend
        else:
            return 0.0  # Downtrend

    def _check_daily_breakout(self, data: pd.DataFrame) -> Dict:
        """Check for daily breakout"""
        if len(data) < 50:
            return {'is_breakout': False}

        data = data.copy()
        data['resistance_20'] = data['high'].rolling(20).max()
        data['volume_ma_20'] = data['volume'].rolling(20).mean()

        # ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        data['atr'] = ranges.max(axis=1).rolling(14).mean()

        current_close = data['close'].iloc[-1]
        prev_resistance = data['resistance_20'].iloc[-2]
        volume_ratio = data['volume'].iloc[-1] / data['volume_ma_20'].iloc[-1]
        atr = data['atr'].iloc[-1]

        # Breakout conditions
        price_breakout = current_close > prev_resistance
        volume_ok = volume_ratio > 1.5
        not_extended = (current_close - prev_resistance) < (3 * atr)

        if price_breakout and volume_ok and not_extended:
            return {
                'is_breakout': True,
                'breakout_price': current_close,
                'volume_ratio': volume_ratio,
                'atr': atr
            }

        return {'is_breakout': False}

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
        quantity = int(max_risk / risk) if risk > 0 else 0

        if quantity == 0:
            return None

        position_value = quantity * entry
        max_position = self.capital * 0.10
        if position_value > max_position:
            quantity = int(max_position / entry)
            actual_risk = quantity * risk
        else:
            actual_risk = max_risk

        # Track trade
        for i in range(1, min(len(future_data), 30)):  # Max 30 days
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

            # Time exit
            if i == len(future_data) - 1 or i == 29:
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
        exit_capital = self.capital + pnl
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
            'exit_capital': exit_capital,
            'risk': actual_risk,
            'rr_ratio': r_multiple,
            'sr_quality': signal['sr_quality'],
            'confluences': signal['confluences']
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

        # R multiple stats
        r_multiples = [t['rr_ratio'] for t in self.trades]
        avg_r = np.mean(r_multiples)

        # S/R quality stats
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
    """Run backtest with Angel One data"""
    print("\n" + "="*70)
    print("🚀 MTF BREAKOUT BACKTEST - ANGEL ONE DATA + S/R")
    print("="*70)
    print(f"Initial Capital: ₹1,00,000")
    print(f"Period: 2023-01-01 to 2024-11-01 (22 months)")
    print(f"Data Source: Angel One API (NSE)")
    print(f"Strategy: High Beta + MTF Confluences + S/R Analysis")
    print(f"S/R Min Quality: 60/100")
    print("="*70 + "\n")

    # Create backtester (credentials loaded from .env.angel file)
    try:
        backtester = MTFAngelBacktester(initial_capital=100000)
    except Exception as e:
        print(f"❌ Failed to initialize backtester: {e}")
        print("\nPlease check Angel One credentials in /Users/srijan/vcp_clean_test/vcp/.env.angel")
        return

    # High beta stocks
    symbols = ['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS']

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 11, 1)

    # Run backtest
    for symbol in symbols:
        backtester.backtest_symbol(symbol, start_date, end_date)

    # Calculate metrics
    print("\n" + "="*70)
    print("📊 BACKTEST RESULTS (Angel One + S/R)")
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
        print(f"   Avg S/R Quality Score: {metrics['avg_sr_quality']:.1f}/100")
        print(f"   Avg Confluences: {metrics['avg_confluences']:.1f}")

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

        # Trade-by-trade
        if backtester.trades:
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
        print("   No trades taken in this period.")
        print("   This may be due to:")
        print("   - Market in consolidation/downtrend")
        print("   - Strict S/R quality filter (>60)")
        print("   - High confluence requirement (4+)")

    print("\n" + "="*70)


if __name__ == '__main__':
    main()

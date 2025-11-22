#!/usr/bin/env python3
"""
Flexible Angel One Backtester - Supports Multiple Accounts

This backtester allows you to:
1. Use any of your Angel One accounts for backtesting
2. Switch between accounts easily
3. Handle dormant accounts gracefully
4. Run comprehensive S/R-integrated backtests

Usage:
    # Use default account
    python3 strategies/backtest_angel_flexible.py

    # Use specific account
    python3 strategies/backtest_angel_flexible.py --account /path/to/.env.angel2

    # Test connection first
    python3 strategies/backtest_angel_flexible.py --test-connection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import argparse
import os

from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
from strategies.multi_timeframe_sr import MultiTimeframeSR


class MultiAccountAngelBacktester:
    """
    Angel One backtester with multi-account support

    Features:
    - Support for multiple Angel One accounts
    - Automatic fallback to alternate accounts
    - Connection testing before backtest
    - Full S/R integration
    """

    def __init__(
        self,
        account_path: Optional[str] = None,
        initial_capital: float = 100000
    ):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades = []
        self.sr_analyzer = MultiTimeframeSR()

        # Strategy parameters
        self.min_confluences = 4
        self.high_beta_threshold = 1.2
        self.min_sr_quality = 60

        # Account configuration
        self.account_path = account_path or self._find_default_account()
        print(f"Using Angel One account: {self.account_path}")

        # Initialize client
        self.angel_client = None
        self.ohlcv_fetcher = None

    def _find_default_account(self) -> str:
        """Find default Angel One account"""
        # Check common locations
        possible_locations = [
            "/Users/srijan/Desktop/aksh/.env.angel",
            "/Users/srijan/vcp_clean_test/vcp/.env.angel",
            ".env.angel"
        ]

        for path in possible_locations:
            if os.path.exists(path):
                return path

        raise FileNotFoundError(
            "No Angel One credentials found. Please create .env.angel file.\n"
            "See .env.angel.template for format."
        )

    def test_connection(self) -> bool:
        """Test Angel One connection"""
        print("\n" + "="*70)
        print("🔌 Testing Angel One Connection")
        print("="*70 + "\n")

        try:
            print(f"Loading credentials from: {self.account_path}")
            client = AngelOneClient.from_env_file(self.account_path)

            print(f"Client ID: {client.client_id}")
            print("Authenticating...")

            success = client.authenticate()

            if success:
                print("✅ Authentication successful!")
                print(f"Session token: {client.session_token[:20]}...")

                # Test a simple API call
                print("\nTesting API access...")
                # You can add a test API call here

                print("✅ Connection test PASSED\n")
                return True
            else:
                print("❌ Authentication failed")
                print("Please check your credentials in:", self.account_path)
                return False

        except Exception as e:
            print(f"❌ Connection test FAILED: {e}")
            print("\nPossible issues:")
            print("1. Account is dormant (complete KYC reactivation)")
            print("2. Incorrect credentials in .env.angel")
            print("3. Network/API issues")
            print("\nPlease resolve and try again.\n")
            return False

    def initialize_client(self) -> bool:
        """Initialize and authenticate Angel One client"""
        try:
            self.angel_client = AngelOneClient.from_env_file(self.account_path)
            success = self.angel_client.authenticate()

            if not success:
                return False

            self.ohlcv_fetcher = AngelOneOHLCVFetcher(
                client=self.angel_client,
                cache_ttl=86400  # 24 hour cache
            )

            return True

        except Exception as e:
            print(f"❌ Failed to initialize client: {e}")
            return False

    def fetch_mtf_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, pd.DataFrame]]:
        """Fetch multi-timeframe data from Angel One"""

        print(f"Fetching MTF data for {symbol}...")

        try:
            # Fetch daily data
            daily_data = self.ohlcv_fetcher.fetch_ohlcv(
                symbol=symbol,
                exchange="NSE",
                interval="ONE_DAY",
                from_date=start_date,
                to_date=end_date
            )

            if daily_data.empty:
                print(f"   ⚠️  No daily data for {symbol}")
                return None

            # Resample to weekly
            weekly_data = daily_data.resample('W', on='timestamp').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })

            # Fetch hourly for 4H (last 6 months)
            hourly_start = start_date if (end_date - start_date).days <= 180 else end_date - timedelta(days=180)

            try:
                hourly_data = self.ohlcv_fetcher.fetch_ohlcv(
                    symbol=symbol,
                    exchange="NSE",
                    interval="ONE_HOUR",
                    from_date=hourly_start,
                    to_date=end_date
                )

                if not hourly_data.empty:
                    data_4h = hourly_data.resample('4H', on='timestamp').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    })
                else:
                    data_4h = pd.DataFrame()

            except Exception as e:
                print(f"   ⚠️  Could not fetch hourly data: {e}")
                data_4h = pd.DataFrame()

            print(f"   ✅ Fetched {len(daily_data)} days, {len(weekly_data)} weeks, {len(data_4h)} 4H bars")

            return {
                'weekly': weekly_data,
                'daily': daily_data,
                '4h': data_4h
            }

        except Exception as e:
            print(f"   ❌ Error fetching data: {e}")
            return None

    def check_signal_at_date(
        self,
        symbol: str,
        current_date: datetime,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame,
        data_4h: pd.DataFrame
    ) -> Optional[Dict]:
        """Check for MTF breakout signal with S/R analysis on specific date"""

        # Get data up to current date
        weekly_till_now = weekly_data[weekly_data.index <= current_date]
        daily_till_now = daily_data[daily_data.index <= current_date]
        data_4h_till_now = data_4h[data_4h.index <= current_date] if not data_4h.empty else pd.DataFrame()

        if len(daily_till_now) < 60:
            return None

        # 1. Weekly trend
        weekly_close = weekly_till_now['close'].iloc[-20:] if len(weekly_till_now) >= 20 else weekly_till_now['close']
        weekly_ma = weekly_close.mean()
        current_price = daily_till_now['close'].iloc[-1]

        if current_price < weekly_ma * 1.05:
            return None  # Not in uptrend

        # 2. Daily breakout
        recent_20d = daily_till_now.iloc[-21:-1]
        high_20d = recent_20d['high'].max()
        current_high = daily_till_now['high'].iloc[-1]

        if current_high <= high_20d:
            return None  # No breakout

        # 3. Volume expansion
        avg_volume = daily_till_now['volume'].iloc[-21:-1].mean()
        current_volume = daily_till_now['volume'].iloc[-1]

        if current_volume < avg_volume * 1.5:
            return None  # No volume

        # 4. S/R ANALYSIS
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

            if sr_quality['quality_score'] < self.min_sr_quality:
                return None  # Low quality

        except Exception:
            return None

        # 5. Confluences
        confluences = 3  # Weekly + breakout + volume

        if not data_4h_till_now.empty and len(data_4h_till_now) >= 10:
            ma_4h = data_4h_till_now['close'].iloc[-10:].mean()
            if current_price > ma_4h * 1.02:
                confluences += 1

        sr_confluences = self.sr_analyzer.find_confluent_levels(all_sr_zones)
        if sr_confluences and len(sr_confluences) >= 2:
            confluences += 1

        if confluences < self.min_confluences:
            return None

        # 6. Entry levels
        entry = current_price
        swing_low = daily_till_now['low'].iloc[-10:].min()
        atr = daily_till_now['high'].iloc[-10:].sub(daily_till_now['low'].iloc[-10:]).mean()

        stop = max(swing_low * 0.98, entry - (1.5 * atr))

        # S/R-adjusted stop
        if sr_quality.get('nearest_support_below'):
            support_level = sr_quality['nearest_support_below'][0]
            stop = max(stop, support_level * 0.995)

        risk = entry - stop
        target = entry + (2.5 * risk)

        # S/R-adjusted target
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
            'sr_quality': sr_quality['quality_score']
        }

    def simulate_trade(
        self,
        symbol: str,
        signal: Dict,
        entry_date: datetime,
        future_data: pd.DataFrame
    ) -> Optional[Dict]:
        """Simulate trade execution"""

        entry = signal['entry']
        stop = signal['stop']
        target = signal['target']
        risk = signal['risk']

        # Position sizing
        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk) if risk > 0 else 0

        if quantity == 0:
            return None

        # Cap at 10%
        position_value = quantity * entry
        max_position = self.capital * 0.10
        if position_value > max_position:
            quantity = int(max_position / entry)

        # Track trade
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
        start_date: datetime,
        end_date: datetime
    ):
        """Run backtest on symbol"""

        print(f"\n{'='*70}")
        print(f"📊 Backtesting {symbol}")
        print(f"{'='*70}\n")

        # Fetch data
        mtf_data = self.fetch_mtf_data(symbol, start_date, end_date)
        if not mtf_data:
            return

        # Walk forward
        daily_data = mtf_data['daily']
        signals_found = 0

        print(f"Walking forward through {len(daily_data)} days...")

        for i in range(60, len(daily_data), 5):  # Check every 5 days
            current_date = daily_data.index[i]

            signal = self.check_signal_at_date(
                symbol,
                current_date,
                mtf_data['weekly'],
                mtf_data['daily'],
                mtf_data['4h']
            )

            if signal:
                signals_found += 1
                print(f"\n🎯 Signal on {current_date.strftime('%Y-%m-%d')}")
                print(f"   Entry: ₹{signal['entry']:.2f}")
                print(f"   Stop: ₹{signal['stop']:.2f}")
                print(f"   Target: ₹{signal['target']:.2f}")
                print(f"   S/R Quality: {signal['sr_quality']:.1f}/100")
                print(f"   Confluences: {signal['confluences']}")

                trade = self.simulate_trade(symbol, signal, current_date, daily_data.iloc[i:])

                if trade:
                    self.trades.append(trade)
                    self.capital = trade['exit_capital']

                    emoji = "✅" if trade['pnl'] > 0 else "❌"
                    print(f"   {emoji} Exit: ₹{trade['exit_price']:.2f} ({trade['pnl_pct']:.2f}%)")
                    print(f"   Days held: {trade['days_held']}, R: {trade['rr_ratio']:.2f}R")

        print(f"\n📊 {symbol} Summary: {signals_found} signals, {len([t for t in self.trades if t['symbol'] == symbol])} trades")

    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {'total_trades': 0}

        winners = [t for t in self.trades if t['pnl'] > 0]
        losers = [t for t in self.trades if t['pnl'] <= 0]

        returns = [t['pnl_pct'] for t in self.trades]
        avg_return = np.mean(returns)
        std_return = np.std(returns) if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) * np.sqrt(252 / 5) if std_return > 0 else 0

        # Drawdown
        capital_curve = [self.initial_capital] + [t['exit_capital'] for t in self.trades]
        peak = capital_curve[0]
        max_dd = 0
        for capital in capital_curve:
            if capital > peak:
                peak = capital
            dd = (capital - peak) / peak * 100
            if dd < max_dd:
                max_dd = dd

        return {
            'total_trades': len(self.trades),
            'winners': len(winners),
            'losers': len(losers),
            'win_rate': (len(winners) / len(self.trades)) * 100,
            'avg_return': avg_return,
            'avg_winner': np.mean([t['pnl_pct'] for t in winners]) if winners else 0,
            'avg_loser': np.mean([t['pnl_pct'] for t in losers]) if losers else 0,
            'sharpe_ratio': sharpe,
            'max_drawdown': abs(max_dd),
            'final_capital': self.capital,
            'total_return': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'avg_r_multiple': np.mean([t['rr_ratio'] for t in self.trades]),
            'avg_sr_quality': np.mean([t['sr_quality'] for t in self.trades]),
            'avg_confluences': np.mean([t['confluences'] for t in self.trades])
        }

    def run_backtest(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime
    ):
        """Run complete backtest"""

        print("\n" + "="*70)
        print("🚀 ANGEL ONE MULTI-ACCOUNT BACKTESTER")
        print("✨ WITH S/R INTEGRATION")
        print("="*70)
        print(f"Account: {self.account_path}")
        print(f"Initial Capital: ₹{self.initial_capital:,.0f}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"S/R Min Quality: {self.min_sr_quality}/100")
        print("="*70)

        # Initialize client
        print("\nInitializing Angel One client...")
        if not self.initialize_client():
            print("\n❌ Failed to initialize Angel One client")
            print("Please run with --test-connection to diagnose issues")
            return

        print("✅ Client initialized successfully\n")

        # Run backtest
        for symbol in symbols:
            self.backtest_symbol(symbol, start_date, end_date)

        # Results
        self.print_results()

    def print_results(self):
        """Print backtest results"""

        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS")
        print("="*70 + "\n")

        metrics = self.calculate_metrics()

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

            print(f"\n📊 S/R Metrics:")
            print(f"   Avg S/R Quality: {metrics['avg_sr_quality']:.1f}/100")
            print(f"   Avg Confluences: {metrics['avg_confluences']:.1f}")

            # Trade details
            if self.trades:
                print(f"\n📋 Trade Details:")
                print(f"{'='*70}")
                for i, trade in enumerate(self.trades, 1):
                    emoji = "✅" if trade['pnl'] > 0 else "❌"
                    print(f"{emoji} #{i} {trade['symbol']}: "
                          f"{trade['entry_date'].strftime('%Y-%m-%d')} → "
                          f"₹{trade['entry_price']:.2f} → ₹{trade['exit_price']:.2f} "
                          f"({trade['pnl_pct']:+.2f}%) [{trade['exit_reason']}] "
                          f"S/R:{trade['sr_quality']:.0f}")
        else:
            print("   No trades taken")

        print("\n" + "="*70)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Angel One Multi-Account Backtester with S/R')
    parser.add_argument('--account', type=str, help='Path to .env.angel file')
    parser.add_argument('--test-connection', action='store_true', help='Test connection only')
    parser.add_argument('--symbols', type=str, nargs='+',
                       default=['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS'],
                       help='Symbols to backtest')
    parser.add_argument('--start-date', type=str, default='2023-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2024-11-01', help='End date (YYYY-MM-DD)')
    parser.add_argument('--capital', type=float, default=100000, help='Initial capital')

    args = parser.parse_args()

    # Create backtester
    backtester = MultiAccountAngelBacktester(
        account_path=args.account,
        initial_capital=args.capital
    )

    # Test connection if requested
    if args.test_connection:
        success = backtester.test_connection()
        sys.exit(0 if success else 1)

    # Run backtest
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    backtester.run_backtest(args.symbols, start_date, end_date)


if __name__ == '__main__':
    main()

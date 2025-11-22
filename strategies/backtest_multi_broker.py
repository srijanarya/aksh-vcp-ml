#!/usr/bin/env python3
"""
Multi-Broker Backtesting System with S/R Integration

Supports multiple brokers and accounts with intelligent fallback:
- Angel One (multiple accounts)
- Zerodha (multiple accounts)
- Upstox (multiple accounts)
- Yahoo Finance (free fallback)
- Cached data (fastest)

Features:
- Automatic broker account rotation
- Intelligent data source fallback
- Full S/R integration
- Multi-account health tracking
- Connection testing for all accounts

Usage:
    # Auto-select best available broker
    python3 strategies/backtest_multi_broker.py

    # Use specific broker account
    python3 strategies/backtest_multi_broker.py --broker angel1

    # Test all broker connections
    python3 strategies/backtest_multi_broker.py --test-all

    # List available brokers
    python3 strategies/backtest_multi_broker.py --list-brokers
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
from dataclasses import dataclass

from src.data.angel_one_client import AngelOneClient
from src.data.angel_one_ohlcv import AngelOneOHLCVFetcher
from src.data.yahoo_finance_fetcher import YahooFinanceFetcher
from src.data.data_source_fallback import DataSourceFallback
from src.data.sqlite_data_cache import SQLiteDataCache
from strategies.multi_timeframe_sr import MultiTimeframeSR


@dataclass
class BrokerAccount:
    """Broker account configuration"""
    name: str  # e.g., "angel1", "angel2", "zerodha1"
    broker: str  # e.g., "angel_one", "zerodha", "upstox"
    credentials_path: str
    is_active: bool = False
    last_test: Optional[datetime] = None
    test_result: Optional[str] = None


class MultiBrokerBacktester:
    """
    Backtest MTF strategy using multiple broker accounts with intelligent fallback

    This backtester:
    1. Discovers all available broker accounts
    2. Tests which accounts are active
    3. Uses best available data source (cache > primary broker > fallback broker > yahoo)
    4. Integrates full S/R analysis
    5. Handles account rotation automatically
    """

    def __init__(
        self,
        preferred_broker: Optional[str] = None,
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

        # Discover and initialize broker accounts
        self.broker_accounts = self._discover_broker_accounts()
        self.active_broker = None
        self.data_fetcher = None
        self.cache = None

        # Initialize preferred broker or auto-select
        self._initialize_broker(preferred_broker)

    def _discover_broker_accounts(self) -> List[BrokerAccount]:
        """Discover all available broker accounts"""

        accounts = []

        # Search common locations for broker credentials
        search_paths = [
            "/Users/srijan/Desktop/aksh",
            "/Users/srijan/vcp_clean_test/vcp",
            os.path.expanduser("~/.broker_credentials")
        ]

        patterns = {
            "angel_one": [".env.angel", ".env.angel1", ".env.angel2", ".env.angel3"],
            "zerodha": [".env.zerodha", ".env.zerodha1", ".env.zerodha2"],
            "upstox": [".env.upstox", ".env.upstox1", ".env.upstox2"],
        }

        for search_path in search_paths:
            if not os.path.exists(search_path):
                continue

            for broker, filenames in patterns.items():
                for filename in filenames:
                    credential_path = os.path.join(search_path, filename)
                    if os.path.exists(credential_path):
                        # Extract account name from filename
                        account_name = filename.replace('.env.', '')

                        accounts.append(BrokerAccount(
                            name=account_name,
                            broker=broker,
                            credentials_path=credential_path
                        ))

        return accounts

    def list_broker_accounts(self):
        """List all discovered broker accounts"""

        print("\n" + "="*70)
        print("📋 DISCOVERED BROKER ACCOUNTS")
        print("="*70 + "\n")

        if not self.broker_accounts:
            print("❌ No broker accounts found")
            print("\nSearched locations:")
            print("  - /Users/srijan/Desktop/aksh/.env.angel*")
            print("  - /Users/srijan/vcp_clean_test/vcp/.env.angel*")
            print("\nCreate credentials file using .env.angel.template")
            return

        print(f"Found {len(self.broker_accounts)} broker account(s):\n")

        for i, account in enumerate(self.broker_accounts, 1):
            status = "✅ ACTIVE" if account.is_active else "⏳ UNTESTED"
            print(f"{i}. {account.name} ({account.broker})")
            print(f"   Path: {account.credentials_path}")
            print(f"   Status: {status}")
            if account.test_result:
                print(f"   Last test: {account.test_result}")
            print()

    def test_broker_account(self, account: BrokerAccount) -> bool:
        """Test a single broker account connection"""

        print(f"\n🔌 Testing {account.name} ({account.broker})...")

        try:
            if account.broker == "angel_one":
                client = AngelOneClient.from_env_file(account.credentials_path)
                success = client.authenticate()

                if success:
                    account.is_active = True
                    account.last_test = datetime.now()
                    account.test_result = "✅ Authentication successful"
                    print(f"   ✅ {account.name}: Connected successfully")
                    return True
                else:
                    account.test_result = "❌ Authentication failed"
                    print(f"   ❌ {account.name}: Authentication failed")
                    return False

            # TODO: Add Zerodha, Upstox support
            elif account.broker in ["zerodha", "upstox"]:
                account.test_result = "⚠️  Broker not yet implemented"
                print(f"   ⚠️  {account.broker} integration pending")
                return False

        except Exception as e:
            account.test_result = f"❌ Error: {str(e)[:50]}"
            print(f"   ❌ {account.name}: {e}")
            return False

    def test_all_broker_accounts(self) -> List[BrokerAccount]:
        """Test all discovered broker accounts"""

        print("\n" + "="*70)
        print("🔌 TESTING ALL BROKER ACCOUNTS")
        print("="*70)

        if not self.broker_accounts:
            print("\n❌ No broker accounts found to test")
            return []

        active_accounts = []

        for account in self.broker_accounts:
            if self.test_broker_account(account):
                active_accounts.append(account)

        print("\n" + "="*70)
        print(f"✅ {len(active_accounts)}/{len(self.broker_accounts)} accounts active")
        print("="*70 + "\n")

        return active_accounts

    def _initialize_broker(self, preferred_broker: Optional[str] = None):
        """Initialize broker connection with fallback"""

        print("\n" + "="*70)
        print("🚀 INITIALIZING DATA SOURCES")
        print("="*70 + "\n")

        # Test all accounts if not tested
        if not any(acc.is_active for acc in self.broker_accounts):
            print("Testing broker accounts...")
            active_accounts = self.test_all_broker_accounts()
        else:
            active_accounts = [acc for acc in self.broker_accounts if acc.is_active]

        # Select broker
        selected_account = None

        if preferred_broker:
            # Try to use preferred broker
            for acc in active_accounts:
                if acc.name == preferred_broker:
                    selected_account = acc
                    break

            if not selected_account:
                print(f"⚠️  Preferred broker '{preferred_broker}' not available")
                print(f"   Falling back to best available...\n")

        # Auto-select first active account
        if not selected_account and active_accounts:
            selected_account = active_accounts[0]

        # Initialize data sources
        if selected_account:
            print(f"✅ Selected broker: {selected_account.name} ({selected_account.broker})")
            self.active_broker = selected_account

            # Initialize cache
            cache_path = "/Users/srijan/Desktop/aksh/data/ohlcv_cache.db"
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            self.cache = SQLiteDataCache(cache_path)

            # Initialize broker-specific fetcher
            if selected_account.broker == "angel_one":
                client = AngelOneClient.from_env_file(selected_account.credentials_path)
                client.authenticate()
                angel_fetcher = AngelOneOHLCVFetcher(client=client, cache_ttl=86400)

                # Initialize Yahoo as fallback
                yahoo_fetcher = YahooFinanceFetcher()

                # Create fallback mechanism
                self.data_fetcher = DataSourceFallback(
                    angel_fetcher=angel_fetcher,
                    yahoo_fetcher=yahoo_fetcher,
                    cache=self.cache
                )

                print(f"✅ Data sources ready: Cache → Angel One → Yahoo Finance")

        else:
            # Fall back to Yahoo Finance only
            print("⚠️  No broker accounts available")
            print("✅ Using Yahoo Finance (free data source)")

            cache_path = "/Users/srijan/Desktop/aksh/data/ohlcv_cache.db"
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            self.cache = SQLiteDataCache(cache_path)

            yahoo_fetcher = YahooFinanceFetcher()

            # Create minimal fallback (Yahoo only)
            self.data_fetcher = yahoo_fetcher

        print()

    def fetch_mtf_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, pd.DataFrame]]:
        """Fetch multi-timeframe data using best available source"""

        print(f"Fetching MTF data for {symbol}...")

        try:
            # Use fallback mechanism if available
            if isinstance(self.data_fetcher, DataSourceFallback):
                # Fetch daily
                result = self.data_fetcher.fetch_ohlcv(
                    symbol=symbol,
                    exchange="NSE",
                    interval="ONE_DAY",
                    from_date=start_date,
                    to_date=end_date
                )

                if result.data.empty:
                    print(f"   ❌ No data for {symbol}")
                    return None

                daily_data = result.data
                print(f"   Data source: {result.source}")

                # Resample to weekly
                weekly_data = daily_data.resample('W', on='timestamp').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                })

                # Try to fetch hourly
                hourly_start = max(start_date, end_date - timedelta(days=180))
                try:
                    hourly_result = self.data_fetcher.fetch_ohlcv(
                        symbol=symbol,
                        exchange="NSE",
                        interval="ONE_HOUR",
                        from_date=hourly_start,
                        to_date=end_date
                    )

                    if not hourly_result.data.empty:
                        data_4h = hourly_result.data.resample('4h', on='timestamp').agg({
                            'open': 'first',
                            'high': 'max',
                            'low': 'min',
                            'close': 'last',
                            'volume': 'sum'
                        })
                    else:
                        data_4h = pd.DataFrame()
                except Exception:
                    data_4h = pd.DataFrame()

            else:
                # Using Yahoo Finance only
                daily_data = self.data_fetcher.fetch_ohlcv(
                    symbol=f"{symbol}.NS",
                    from_date=start_date,
                    to_date=end_date,
                    interval="1d"
                )

                if daily_data.empty:
                    return None

                # Resample weekly
                weekly_data = daily_data.resample('W').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                })

                data_4h = pd.DataFrame()  # Yahoo hourly has limited history

            print(f"   ✅ Fetched {len(daily_data)} days, {len(weekly_data)} weeks, {len(data_4h)} 4H bars")

            return {
                'weekly': weekly_data,
                'daily': daily_data,
                '4h': data_4h
            }

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def check_signal_at_date(
        self,
        symbol: str,
        current_date: datetime,
        weekly_data: pd.DataFrame,
        daily_data: pd.DataFrame,
        data_4h: pd.DataFrame
    ) -> Optional[Dict]:
        """Check for MTF breakout signal with S/R on specific date"""

        # Get data up to current date
        weekly_till_now = weekly_data[weekly_data.index <= current_date]
        daily_till_now = daily_data[daily_data.index <= current_date]
        data_4h_till_now = data_4h[data_4h.index <= current_date] if not data_4h.empty else pd.DataFrame()

        if len(daily_till_now) < 60:
            return None

        # Weekly trend
        weekly_close = weekly_till_now['close'].iloc[-20:] if len(weekly_till_now) >= 20 else weekly_till_now['close']
        weekly_ma = weekly_close.mean()
        current_price = daily_till_now['close'].iloc[-1]

        if current_price < weekly_ma * 1.05:
            return None

        # Daily breakout
        recent_20d = daily_till_now.iloc[-21:-1]
        high_20d = recent_20d['high'].max()
        current_high = daily_till_now['high'].iloc[-1]

        if current_high <= high_20d:
            return None

        # Volume
        avg_volume = daily_till_now['volume'].iloc[-21:-1].mean()
        current_volume = daily_till_now['volume'].iloc[-1]

        if current_volume < avg_volume * 1.5:
            return None

        # S/R Analysis
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
                return None

        except Exception:
            return None

        # Confluences
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

        max_risk = self.capital * 0.02
        quantity = int(max_risk / risk) if risk > 0 else 0

        if quantity == 0:
            return None

        position_value = quantity * entry
        max_position = self.capital * 0.10
        if position_value > max_position:
            quantity = int(max_position / entry)

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

        mtf_data = self.fetch_mtf_data(symbol, start_date, end_date)
        if not mtf_data:
            return

        daily_data = mtf_data['daily']
        signals_found = 0

        print(f"Walking forward through {len(daily_data)} days...")

        for i in range(60, len(daily_data), 5):
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
                print(f"   Entry: ₹{signal['entry']:.2f}, S/R Quality: {signal['sr_quality']:.1f}/100")

                trade = self.simulate_trade(symbol, signal, current_date, daily_data.iloc[i:])

                if trade:
                    self.trades.append(trade)
                    self.capital = trade['exit_capital']

                    emoji = "✅" if trade['pnl'] > 0 else "❌"
                    print(f"   {emoji} Exit: ₹{trade['exit_price']:.2f} ({trade['pnl_pct']:.2f}%)")

        print(f"\n📊 {symbol}: {signals_found} signals")

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
            'avg_sr_quality': np.mean([t['sr_quality'] for t in self.trades]),
            'avg_confluences': np.mean([t['confluences'] for t in self.trades])
        }

    def print_results(self):
        """Print backtest results"""

        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS")
        print("="*70 + "\n")

        if self.active_broker:
            print(f"Data Source: {self.active_broker.name} ({self.active_broker.broker})")
        else:
            print("Data Source: Yahoo Finance (fallback)")
        print()

        metrics = self.calculate_metrics()

        print(f"💰 Performance:")
        print(f"   Trades: {metrics['total_trades']}")

        if metrics['total_trades'] > 0:
            print(f"   Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   Avg Return: {metrics['avg_return']:.2f}%")
            print(f"   Sharpe: {metrics['sharpe_ratio']:.2f}")
            print(f"   Max DD: {metrics['max_drawdown']:.2f}%")
            print(f"   Final Capital: ₹{metrics['final_capital']:,.0f}")
            print(f"   Total Return: {metrics['total_return']:.2f}%")
            print(f"\n📊 S/R Metrics:")
            print(f"   Avg S/R Quality: {metrics['avg_sr_quality']:.1f}/100")
            print(f"   Avg Confluences: {metrics['avg_confluences']:.1f}")

        print("\n" + "="*70)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Multi-Broker Backtester with S/R')
    parser.add_argument('--broker', type=str, help='Preferred broker account name (e.g., angel1)')
    parser.add_argument('--list-brokers', action='store_true', help='List available broker accounts')
    parser.add_argument('--test-all', action='store_true', help='Test all broker connections')
    parser.add_argument('--symbols', type=str, nargs='+',
                       default=['TATAMOTORS', 'SAIL', 'VEDL', 'ADANIPORTS'],
                       help='Symbols to backtest')
    parser.add_argument('--start-date', type=str, default='2023-01-01')
    parser.add_argument('--end-date', type=str, default='2024-11-01')
    parser.add_argument('--capital', type=float, default=100000)

    args = parser.parse_args()

    backtester = MultiBrokerBacktester(
        preferred_broker=args.broker,
        initial_capital=args.capital
    )

    if args.list_brokers:
        backtester.list_broker_accounts()
        return

    if args.test_all:
        backtester.test_all_broker_accounts()
        backtester.list_broker_accounts()
        return

    # Run backtest
    print("\n" + "="*70)
    print("🚀 MULTI-BROKER BACKTESTER WITH S/R")
    print("="*70)
    print(f"Period: {args.start_date} to {args.end_date}")
    print(f"Capital: ₹{args.capital:,.0f}")
    print("="*70)

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    for symbol in args.symbols:
        backtester.backtest_symbol(symbol, start_date, end_date)

    backtester.print_results()


if __name__ == '__main__':
    main()

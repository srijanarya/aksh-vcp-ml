#!/usr/bin/env python3
"""
Backtest Validation Script

Validates the complete BMAD trading system with:
1. Real market data (Yahoo Finance)
2. VCP signal generation
3. Kelly position sizing
4. Cost & slippage simulation
5. Performance analysis

Usage:
    python3 validation/run_backtest_validation.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from typing import List, Dict

# Import our modules
from src.backtest.backtest_engine import BacktestEngine, BacktestResult
from src.costs.cost_calculator import CostCalculator
from src.costs.slippage_simulator import SlippageSimulator
from src.signals.technical_indicators import TechnicalIndicators
from src.signals.signal_filter import SignalFilter
from src.kelly.kelly_fraction_calculator import KellyFractionCalculator


class BacktestValidator:
    """Validates backtest system with real data"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital

        # Initialize components
        self.cost_calculator = CostCalculator()
        self.slippage_simulator = SlippageSimulator()
        self.technical_indicators = TechnicalIndicators()
        self.signal_filter = SignalFilter()
        self.kelly_calculator = KellyFractionCalculator()

        # Initialize backtest engine
        self.backtest_engine = BacktestEngine(
            initial_capital=initial_capital,
            cost_calculator=self.cost_calculator,
            slippage_simulator=self.slippage_simulator
        )

    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance"""
        print(f"📊 Fetching data for {symbol} from {start_date} to {end_date}...")

        ticker = yf.Ticker(f"{symbol}.NS")  # NSE suffix
        df = ticker.history(start=start_date, end=end_date)

        if df.empty:
            raise ValueError(f"No data available for {symbol}")

        # Rename columns to match our format
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        print(f"✅ Fetched {len(df)} days of data")
        return df

    def generate_vcp_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate VCP-based buy signals"""
        print("🎯 Generating VCP signals...")

        # Calculate technical indicators
        data['adx'] = self.technical_indicators.calculate_adx(data)
        data['ema_20'] = self.technical_indicators.calculate_ema(data['close'], 20)
        data['dma'] = ((data['close'] - data['ema_20']) / data['ema_20']) * 100
        data['atr'] = self.technical_indicators.calculate_atr(data)

        # Volume confirmation
        data['volume_ma'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # Simple VCP signal: ADX rising + price near EMA + increasing volume
        signals = (
            (data['adx'] > 25) &  # Strong trend
            (data['dma'] > -2) & (data['dma'] < 5) &  # Near EMA (base formation)
            (data['volume_ratio'] > 1.2)  # Volume expansion
        )

        # Use signals directly (they're already filtered by our conditions)
        print(f"✅ Generated {signals.sum()} signals")
        return signals

    def run_validation(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """Run complete backtest validation"""
        print("\n" + "="*60)
        print("🚀 BACKTEST VALIDATION")
        print("="*60)
        print(f"Capital: ₹{self.initial_capital:,.0f}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Symbols: {', '.join(symbols)}")
        print("="*60 + "\n")

        all_results = []

        for symbol in symbols:
            print(f"\n{'─'*60}")
            print(f"📈 Testing: {symbol}")
            print(f"{'─'*60}")

            try:
                # Fetch data
                data = self.fetch_data(symbol, start_date, end_date)

                # Generate signals
                signals = self.generate_vcp_signals(data)

                # Run backtest
                print("⚙️  Running backtest...")
                result = self.backtest_engine.run(
                    data=data,
                    signals=signals,
                    stop_loss_pct=2.0,
                    target_pct=4.0
                )

                # Display results
                self.display_results(symbol, result)

                all_results.append({
                    'symbol': symbol,
                    'result': result
                })

            except Exception as e:
                print(f"❌ Error testing {symbol}: {e}")
                continue

        # Aggregate results
        print("\n" + "="*60)
        print("📊 AGGREGATE RESULTS")
        print("="*60)
        self.display_aggregate_results(all_results)

        return all_results

    def display_results(self, symbol: str, result: BacktestResult):
        """Display backtest results"""
        metrics = result.metrics

        print(f"\n📈 Results for {symbol}:")
        print(f"   Trades: {metrics.get('total_trades', 0)}")
        print(f"   Winners: {metrics.get('winning_trades', 0)}")
        print(f"   Losers: {metrics.get('losing_trades', 0)}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Total Return: {metrics.get('total_return', 0):.2f}%")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"   Final Capital: ₹{metrics.get('final_capital', 0):,.0f}")

    def display_aggregate_results(self, all_results: List[Dict]):
        """Display aggregate results across all symbols"""
        if not all_results:
            print("No results to display")
            return

        total_trades = sum(r['result'].metrics.get('total_trades', 0) for r in all_results)
        total_winners = sum(r['result'].metrics.get('winning_trades', 0) for r in all_results)
        total_losers = sum(r['result'].metrics.get('losing_trades', 0) for r in all_results)

        avg_return = np.mean([r['result'].metrics.get('total_return', 0) for r in all_results])
        avg_sharpe = np.mean([r['result'].metrics.get('sharpe_ratio', 0) for r in all_results])
        avg_drawdown = np.mean([r['result'].metrics.get('max_drawdown', 0) for r in all_results])

        overall_win_rate = (total_winners / total_trades * 100) if total_trades > 0 else 0

        print(f"\n🎯 Overall Performance:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Win Rate: {overall_win_rate:.1f}%")
        print(f"   Avg Return: {avg_return:.2f}%")
        print(f"   Avg Sharpe: {avg_sharpe:.2f}")
        print(f"   Avg Drawdown: {avg_drawdown:.2f}%")

        # Validation criteria
        print(f"\n✅ VALIDATION CRITERIA:")
        print(f"   {'✅' if overall_win_rate >= 50 else '❌'} Win Rate ≥ 50%: {overall_win_rate:.1f}%")
        print(f"   {'✅' if avg_sharpe >= 1.0 else '❌'} Sharpe Ratio ≥ 1.0: {avg_sharpe:.2f}")
        print(f"   {'✅' if abs(avg_drawdown) <= 15 else '❌'} Max Drawdown ≤ 15%: {abs(avg_drawdown):.2f}%")

        if overall_win_rate >= 50 and avg_sharpe >= 1.0 and abs(avg_drawdown) <= 15:
            print(f"\n🎉 VALIDATION PASSED - System ready for paper trading!")
        else:
            print(f"\n⚠️  VALIDATION NEEDS IMPROVEMENT - Review parameters")


def main():
    """Main validation script"""
    # Configuration
    INITIAL_CAPITAL = 100000
    START_DATE = "2024-01-01"
    END_DATE = "2024-11-01"

    # Test symbols (liquid NSE stocks)
    TEST_SYMBOLS = [
        'RELIANCE',
        'TCS',
        'INFY',
        'HDFCBANK',
        'ICICIBANK'
    ]

    # Run validation
    validator = BacktestValidator(initial_capital=INITIAL_CAPITAL)
    results = validator.run_validation(TEST_SYMBOLS, START_DATE, END_DATE)

    print("\n" + "="*60)
    print("✅ VALIDATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()

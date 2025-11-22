#!/usr/bin/env python3
"""
Optimized Backtest Validation

Uses optimized parameters from grid search optimization.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yfinance as yf
from typing import List, Dict
from datetime import datetime

from src.backtest.backtest_engine import BacktestEngine, BacktestResult
from src.signals.technical_indicators import TechnicalIndicators


# OPTIMIZED PARAMETERS (from optimization_results.csv)
OPTIMIZED_PARAMS = {
    'adx_threshold': 20,  # Lower threshold for more trades
    'dma_min': -2.0,  # Tighter base formation
    'dma_max': 3.0,  # Not too extended
    'volume_threshold': 1.1,  # Moderate volume expansion
    'stop_loss': 2.5,  # Wider stops for less whipsaws
    'target': 3.0  # More conservative target
}


class OptimizedBacktestValidator:
    """Run backtest with optimized parameters"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.backtest_engine = BacktestEngine(initial_capital=initial_capital)
        self.technical_indicators = TechnicalIndicators()

    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance"""
        print(f"📊 Fetching data for {symbol} from {start_date} to {end_date}...")

        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(start=start_date, end=end_date)

        if data.empty:
            raise ValueError(f"No data fetched for {symbol}")

        # Rename columns to lowercase
        data.columns = [col.lower() for col in data.columns]

        print(f"✅ Fetched {len(data)} days of data")

        return data

    def generate_vcp_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate VCP signals with OPTIMIZED parameters"""
        print("🎯 Generating VCP signals (OPTIMIZED)...")

        # Calculate technical indicators
        data['adx'] = self.technical_indicators.calculate_adx(data)
        data['ema_20'] = self.technical_indicators.calculate_ema(data['close'], 20)
        data['dma'] = ((data['close'] - data['ema_20']) / data['ema_20']) * 100
        data['atr'] = self.technical_indicators.calculate_atr(data)

        # Volume confirmation
        data['volume_ma'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # OPTIMIZED VCP signal generation
        signals = (
            (data['adx'] > OPTIMIZED_PARAMS['adx_threshold']) &
            (data['dma'] > OPTIMIZED_PARAMS['dma_min']) &
            (data['dma'] < OPTIMIZED_PARAMS['dma_max']) &
            (data['volume_ratio'] > OPTIMIZED_PARAMS['volume_threshold'])
        )

        print(f"✅ Generated {signals.sum()} signals")
        return signals

    def run_validation(self, symbols: List[str], start_date: str, end_date: str) -> Dict:
        """Run complete backtest validation with optimized parameters"""
        print("\n" + "="*60)
        print("🚀 OPTIMIZED BACKTEST VALIDATION")
        print("="*60)
        print(f"Capital: ₹{self.initial_capital:,.0f}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Symbols: {', '.join(symbols)}")
        print("\n📊 OPTIMIZED PARAMETERS:")
        print(f"   ADX Threshold: {OPTIMIZED_PARAMS['adx_threshold']}")
        print(f"   DMA Range: {OPTIMIZED_PARAMS['dma_min']}% to {OPTIMIZED_PARAMS['dma_max']}%")
        print(f"   Volume Threshold: {OPTIMIZED_PARAMS['volume_threshold']}x")
        print(f"   Stop Loss: {OPTIMIZED_PARAMS['stop_loss']}%")
        print(f"   Target: {OPTIMIZED_PARAMS['target']}%")
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

                # Run backtest with OPTIMIZED parameters
                print("⚙️  Running backtest...")
                result = self.backtest_engine.run(
                    data=data,
                    signals=signals,
                    stop_loss_pct=OPTIMIZED_PARAMS['stop_loss'],
                    target_pct=OPTIMIZED_PARAMS['target']
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

        # Calculate average metrics
        avg_win_rate = sum(r['result'].metrics.get('win_rate', 0) for r in all_results) / len(all_results)
        avg_return = sum(r['result'].metrics.get('total_return', 0) for r in all_results) / len(all_results)
        avg_sharpe = sum(r['result'].metrics.get('sharpe_ratio', 0) for r in all_results) / len(all_results)
        avg_drawdown = sum(r['result'].metrics.get('max_drawdown', 0) for r in all_results) / len(all_results)

        print(f"\n🎯 Overall Performance:")
        print(f"   Total Trades: {total_trades}")
        print(f"   Win Rate: {avg_win_rate:.1f}%")
        print(f"   Avg Return: {avg_return:.2f}%")
        print(f"   Avg Sharpe: {avg_sharpe:.2f}")
        print(f"   Avg Drawdown: {avg_drawdown:.2f}%")

        # Validation criteria
        print(f"\n✅ VALIDATION CRITERIA:")

        win_rate_pass = avg_win_rate >= 45
        sharpe_pass = avg_sharpe >= 0.8
        drawdown_pass = abs(avg_drawdown) <= 15

        print(f"   {'✅' if win_rate_pass else '❌'} Win Rate ≥ 45%: {avg_win_rate:.1f}%")
        print(f"   {'✅' if sharpe_pass else '❌'} Sharpe Ratio ≥ 0.8: {avg_sharpe:.2f}")
        print(f"   {'✅' if drawdown_pass else '❌'} Max Drawdown ≤ 15%: {abs(avg_drawdown):.2f}%")

        if win_rate_pass and sharpe_pass and drawdown_pass:
            print(f"\n🎉 ALL CRITERIA MET - READY FOR PAPER TRADING!")
        else:
            print(f"\n⚠️  VALIDATION NEEDS IMPROVEMENT - Review parameters")

        print("\n" + "="*60)
        print("✅ VALIDATION COMPLETE")
        print("="*60)


def main():
    """Run optimized backtest validation"""
    validator = OptimizedBacktestValidator(initial_capital=100000)

    symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
    start_date = '2024-01-01'
    end_date = '2024-11-01'

    validator.run_validation(symbols, start_date, end_date)


if __name__ == '__main__':
    main()

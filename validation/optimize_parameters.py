#!/usr/bin/env python3
"""
Strategy Parameter Optimization

Tests different parameter combinations to find optimal settings for VCP trading strategy.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from itertools import product
import yfinance as yf
from datetime import datetime

from src.backtest.backtest_engine import BacktestEngine
from src.signals.technical_indicators import TechnicalIndicators


class ParameterOptimizer:
    """Optimize strategy parameters using grid search"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.technical_indicators = TechnicalIndicators()

    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical data"""
        ticker = yf.Ticker(f"{symbol}.NS")
        data = ticker.history(start=start_date, end=end_date)

        if data.empty:
            raise ValueError(f"No data fetched for {symbol}")

        # Rename columns to lowercase
        data.columns = [col.lower() for col in data.columns]

        return data

    def generate_signals(
        self,
        data: pd.DataFrame,
        adx_threshold: float,
        dma_min: float,
        dma_max: float,
        volume_threshold: float
    ) -> pd.Series:
        """Generate VCP signals with given parameters"""
        # Calculate indicators
        data['adx'] = self.technical_indicators.calculate_adx(data)
        data['ema_20'] = self.technical_indicators.calculate_ema(data['close'], 20)
        data['dma'] = ((data['close'] - data['ema_20']) / data['ema_20']) * 100

        # Volume confirmation
        data['volume_ma'] = data['volume'].rolling(20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # Generate signals
        signals = (
            (data['adx'] > adx_threshold) &
            (data['dma'] > dma_min) & (data['dma'] < dma_max) &
            (data['volume_ratio'] > volume_threshold)
        )

        return signals

    def backtest_parameters(
        self,
        data: pd.DataFrame,
        params: Dict
    ) -> Dict:
        """Run backtest with specific parameters"""
        # Generate signals
        signals = self.generate_signals(
            data.copy(),
            params['adx_threshold'],
            params['dma_min'],
            params['dma_max'],
            params['volume_threshold']
        )

        # Run backtest
        engine = BacktestEngine(initial_capital=self.initial_capital)
        result = engine.run(
            data=data,
            signals=signals,
            stop_loss_pct=params['stop_loss'],
            target_pct=params['target']
        )

        return result.metrics

    def optimize(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        param_grid: Dict[str, List]
    ) -> pd.DataFrame:
        """Run grid search optimization"""
        print("\n" + "="*70)
        print("🔍 PARAMETER OPTIMIZATION")
        print("="*70)
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Period: {start_date} to {end_date}")
        print(f"Testing {self._count_combinations(param_grid)} parameter combinations...")
        print("="*70 + "\n")

        results = []

        # Generate parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))

        total_combinations = len(combinations)

        for idx, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))

            # Progress indicator
            if idx % 10 == 0 or idx == 1:
                print(f"Testing combination {idx}/{total_combinations}...")

            # Test on all symbols
            symbol_results = []

            for symbol in symbols:
                try:
                    # Fetch data
                    data = self.fetch_data(symbol, start_date, end_date)

                    # Backtest
                    metrics = self.backtest_parameters(data, params)

                    symbol_results.append({
                        'symbol': symbol,
                        'trades': metrics.get('total_trades', 0),
                        'win_rate': metrics.get('win_rate', 0),
                        'return': metrics.get('total_return_pct', 0),
                        'sharpe': metrics.get('sharpe_ratio', 0),
                        'max_dd': metrics.get('max_drawdown', 0)
                    })

                except Exception as e:
                    print(f"   ⚠️  Error testing {symbol}: {e}")
                    continue

            if not symbol_results:
                continue

            # Aggregate metrics
            avg_trades = np.mean([r['trades'] for r in symbol_results])
            avg_win_rate = np.mean([r['win_rate'] for r in symbol_results])
            avg_return = np.mean([r['return'] for r in symbol_results])
            avg_sharpe = np.mean([r['sharpe'] for r in symbol_results])
            avg_max_dd = np.mean([r['max_dd'] for r in symbol_results])

            # Score combination (higher is better)
            # Weight: 40% win rate, 30% sharpe, 20% return, 10% drawdown penalty
            score = (
                avg_win_rate * 0.4 +
                max(avg_sharpe, 0) * 10 * 0.3 +  # Scale sharpe to similar range
                avg_return * 0.2 -
                abs(avg_max_dd) * 0.1
            )

            results.append({
                **params,
                'avg_trades': avg_trades,
                'avg_win_rate': avg_win_rate,
                'avg_return': avg_return,
                'avg_sharpe': avg_sharpe,
                'avg_max_dd': avg_max_dd,
                'score': score
            })

        # Convert to DataFrame and sort by score
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('score', ascending=False)

        return results_df

    def _count_combinations(self, param_grid: Dict) -> int:
        """Count total parameter combinations"""
        count = 1
        for values in param_grid.values():
            count *= len(values)
        return count

    def display_top_results(self, results_df: pd.DataFrame, top_n: int = 10):
        """Display top parameter combinations"""
        print("\n" + "="*70)
        print(f"🏆 TOP {top_n} PARAMETER COMBINATIONS")
        print("="*70)

        for idx, row in results_df.head(top_n).iterrows():
            print(f"\n#{idx + 1} - Score: {row['score']:.2f}")
            print(f"   ADX Threshold: {row['adx_threshold']:.0f}")
            print(f"   DMA Range: {row['dma_min']:.1f}% to {row['dma_max']:.1f}%")
            print(f"   Volume Threshold: {row['volume_threshold']:.1f}x")
            print(f"   Stop Loss: {row['stop_loss']:.1f}%")
            print(f"   Target: {row['target']:.1f}%")
            print(f"   ─────────────────────────────")
            print(f"   Avg Trades: {row['avg_trades']:.1f}")
            print(f"   Avg Win Rate: {row['avg_win_rate']:.1f}%")
            print(f"   Avg Return: {row['avg_return']:.2f}%")
            print(f"   Avg Sharpe: {row['avg_sharpe']:.2f}")
            print(f"   Avg Max DD: {row['avg_max_dd']:.2f}%")

        print("\n" + "="*70)

        # Save results to CSV
        csv_path = Path(__file__).parent / 'optimization_results.csv'
        results_df.to_csv(csv_path, index=False)
        print(f"\n💾 Full results saved to: {csv_path}")

        return results_df.head(top_n)


def main():
    """Run parameter optimization"""
    optimizer = ParameterOptimizer(initial_capital=100000)

    # Symbols to test
    symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']

    # Date range
    start_date = '2024-01-01'
    end_date = '2024-11-01'

    # Parameter grid for optimization
    # Start with coarse grid, then refine based on results
    param_grid = {
        'adx_threshold': [20, 25, 30],  # ADX strength threshold
        'dma_min': [-5, -3, -2],  # DMA minimum (base formation)
        'dma_max': [3, 5, 8],  # DMA maximum (not too extended)
        'volume_threshold': [1.1, 1.2, 1.3],  # Volume expansion
        'stop_loss': [1.5, 2.0, 2.5],  # Stop loss %
        'target': [3.0, 4.0, 5.0]  # Target profit %
    }

    print(f"\n🎯 Testing {optimizer._count_combinations(param_grid)} combinations")
    print(f"   This may take 5-10 minutes...\n")

    # Run optimization
    results = optimizer.optimize(symbols, start_date, end_date, param_grid)

    # Display top results
    top_params = optimizer.display_top_results(results, top_n=10)

    # Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)

    best = top_params.iloc[0]

    print(f"\n🥇 BEST PARAMETER SET:")
    print(f"   ADX Threshold: {best['adx_threshold']:.0f}")
    print(f"   DMA Range: {best['dma_min']:.1f}% to {best['dma_max']:.1f}%")
    print(f"   Volume Threshold: {best['volume_threshold']:.1f}x")
    print(f"   Stop Loss: {best['stop_loss']:.1f}%")
    print(f"   Target: {best['target']:.1f}%")

    print(f"\n📊 EXPECTED PERFORMANCE:")
    print(f"   Win Rate: {best['avg_win_rate']:.1f}%")
    print(f"   Return: {best['avg_return']:.2f}%")
    print(f"   Sharpe Ratio: {best['avg_sharpe']:.2f}")
    print(f"   Max Drawdown: {best['avg_max_dd']:.2f}%")

    # Validation check
    print(f"\n✅ VALIDATION CRITERIA:")
    meets_win_rate = best['avg_win_rate'] >= 45
    meets_sharpe = best['avg_sharpe'] >= 0.8
    meets_drawdown = abs(best['avg_max_dd']) <= 15

    print(f"   {'✅' if meets_win_rate else '❌'} Win Rate ≥ 45%: {best['avg_win_rate']:.1f}%")
    print(f"   {'✅' if meets_sharpe else '❌'} Sharpe Ratio ≥ 0.8: {best['avg_sharpe']:.2f}")
    print(f"   {'✅' if meets_drawdown else '❌'} Max Drawdown ≤ 15%: {best['avg_max_dd']:.2f}%")

    if meets_win_rate and meets_sharpe and meets_drawdown:
        print("\n🎉 READY FOR PAPER TRADING!")
    else:
        print("\n⚠️  Consider refining parameters further or extending test period")

    print("\n" + "="*70)


if __name__ == '__main__':
    main()

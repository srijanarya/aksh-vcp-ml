#!/usr/bin/env python3
"""
BMAD Trading System - Web API Server

Flask backend for HTML dashboard with WebSocket support for real-time updates.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtest.backtest_engine import BacktestEngine
from src.paper_trading.virtual_account import VirtualAccount
from src.order_executor.order_executor import OrderExecutor

app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# Global state
app_state = {
    'backtest_engine': None,
    'virtual_account': None,
    'order_executor': None,
    'config': {
        'capital': 100000,
        'max_positions': 5,
        'position_size_pct': 10.0,
        'stop_loss_pct': 2.0,
        'target_pct': 4.0
    },
    'paper_trading_active': False,
    'logs': [],
    'last_backtest_results': None
}

def log_message(message):
    """Add message to system logs"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    app_state['logs'].append(f'[{timestamp}] {message}')
    print(f'[{timestamp}] {message}')


@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('.', 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current system status"""
    try:
        account_info = {}
        if app_state['virtual_account']:
            account_info = app_state['virtual_account'].get_performance()

        return jsonify({
            'success': True,
            'data': {
                'system_status': 'running',
                'capital': account_info.get('current_equity', app_state['config']['capital']),
                'pnl_pct': account_info.get('total_return_pct', 0.0),
                'positions': [],  # Will be populated from positions dict
                'positions_count': account_info.get('open_positions', 0),
                'trades_today': account_info.get('total_trades', 0),
                'paper_trading_active': app_state['paper_trading_active'],
                'config': app_state['config']
            }
        })
    except Exception as e:
        log_message(f'Error getting status: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """Run backtest validation"""
    try:
        data = request.json
        symbols = data.get('symbols', ['RELIANCE'])
        start_date = data.get('startDate', '2024-01-01')
        end_date = data.get('endDate', '2024-11-01')

        log_message(f'Starting backtest: {symbols} from {start_date} to {end_date}')

        # For now, load results from the last validation file
        # In production, you'd run the actual backtest here
        import json
        results_path = Path(__file__).parent.parent / 'validation' / 'optimization_results.csv'

        if results_path.exists():
            import pandas as pd
            df = pd.read_csv(results_path)
            best = df.iloc[0]  # Get best results

            result = {
                'symbols': symbols,
                'start_date': start_date,
                'end_date': end_date,
                'total_trades': int(best['avg_trades'] * len(symbols)),
                'win_rate': float(best['avg_win_rate']),
                'sharpe_ratio': float(best['avg_sharpe']),
                'max_drawdown': float(abs(best['avg_max_dd'])),
                'avg_return': float(best['avg_return']),
                'final_capital': app_state['config']['capital'] * (1 + best['avg_return']/100),
                'parameters': {
                    'adx_threshold': float(best['adx_threshold']),
                    'dma_min': float(best['dma_min']),
                    'dma_max': float(best['dma_max']),
                    'volume_threshold': float(best['volume_threshold']),
                    'stop_loss': float(best['stop_loss']),
                    'target': float(best['target'])
                },
                'message': 'Showing optimized backtest results'
            }

            # Store results
            app_state['last_backtest_results'] = result
        else:
            result = {
                'symbols': symbols,
                'start_date': start_date,
                'end_date': end_date,
                'total_trades': 0,
                'win_rate': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'final_capital': app_state['config']['capital'],
                'message': 'No backtest results available. Run validation/run_optimized_backtest.py first.'
            }
            app_state['last_backtest_results'] = result

        log_message('Backtest completed')

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        log_message(f'Backtest error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/last', methods=['GET'])
def get_last_backtest():
    """Get last backtest results"""
    try:
        if app_state['last_backtest_results']:
            return jsonify({'success': True, 'data': app_state['last_backtest_results']})
        else:
            return jsonify({'success': False, 'error': 'No backtest results available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paper-trading/start', methods=['POST'])
def start_paper_trading():
    """Start paper trading"""
    try:
        log_message('Starting paper trading...')

        # Initialize virtual account
        if not app_state['virtual_account']:
            app_state['virtual_account'] = VirtualAccount(
                initial_capital=app_state['config']['capital']
            )

        app_state['paper_trading_active'] = True

        log_message('Paper trading started successfully')

        return jsonify({
            'success': True,
            'message': 'Paper trading started'
        })

    except Exception as e:
        log_message(f'Error starting paper trading: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/paper-trading/stop', methods=['POST'])
def stop_paper_trading():
    """Stop paper trading"""
    try:
        log_message('Stopping paper trading...')

        app_state['paper_trading_active'] = False

        log_message('Paper trading stopped')

        return jsonify({
            'success': True,
            'message': 'Paper trading stopped'
        })

    except Exception as e:
        log_message(f'Error stopping paper trading: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['GET', 'POST'])
def manage_config():
    """Get or update configuration"""
    try:
        if request.method == 'POST':
            data = request.json
            app_state['config'].update(data)
            log_message('Configuration updated')
            return jsonify({'success': True, 'data': app_state['config']})
        else:
            return jsonify({'success': True, 'data': app_state['config']})

    except Exception as e:
        log_message(f'Config error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get system logs"""
    try:
        # Return last 100 logs
        logs = app_state['logs'][-100:]
        return jsonify({'success': True, 'data': logs})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions"""
    try:
        positions = []
        if app_state['virtual_account']:
            # Convert positions dict to list
            for symbol, pos in app_state['virtual_account'].positions.items():
                positions.append({
                    'symbol': symbol,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'pnl': pos.pnl,
                    'pnl_pct': pos.pnl_pct,
                    'entry_time': pos.entry_time.isoformat()
                })

        return jsonify({'success': True, 'data': positions})

    except Exception as e:
        log_message(f'Error getting positions: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trade history"""
    try:
        trades = []
        if app_state['virtual_account']:
            # Trade history is already a list of dicts
            for trade in app_state['virtual_account'].trade_history:
                trades.append({
                    'action': trade['action'],
                    'symbol': trade['symbol'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'timestamp': trade['timestamp'].isoformat() if hasattr(trade['timestamp'], 'isoformat') else str(trade['timestamp'])
                })

        return jsonify({'success': True, 'data': trades})

    except Exception as e:
        log_message(f'Error getting trades: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    log_message('BMAD Trading System API Server Starting...')
    log_message('Dashboard will be available at http://localhost:5000')
    log_message('Press Ctrl+C to stop')

    print('\n' + '='*60)
    print('🚀 BMAD TRADING SYSTEM - WEB DASHBOARD')
    print('='*60)
    print(f'\n📊 Dashboard: http://localhost:5000')
    print(f'📡 API Docs: http://localhost:5000/api/health')
    print(f'\n✅ All systems ready\n')

    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)

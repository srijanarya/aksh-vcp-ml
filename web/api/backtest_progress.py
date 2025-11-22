#!/usr/bin/env python3
"""
Backtest Progress API
Serves real-time backtest log data for frontend monitoring dashboard
"""
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Get paths
API_DIR = Path(__file__).parent
WEB_DIR = API_DIR.parent
HTML_FILE = WEB_DIR / "backtest_monitor.html"

@app.route('/api/backtest/progress')
def get_progress():
    """Get current backtest progress from log file"""
    log_path = '/tmp/smallcap_backtest.log'

    try:
        # Check if log file exists
        if not os.path.exists(log_path):
            return jsonify({
                'status': 'not_started',
                'log': '',
                'timestamp': None
            })

        # Read log file
        with open(log_path, 'r') as f:
            log_content = f.read()

        # Get file modification time
        mtime = os.path.getmtime(log_path)
        last_modified = datetime.fromtimestamp(mtime).isoformat()

        # Parse some basic stats
        lines = log_content.split('\n')
        analyzing_lines = [l for l in lines if '🔍 Analyzing' in l]
        completed_lines = [l for l in lines if 'Backtest complete' in l]

        current_symbol = None
        if analyzing_lines:
            # Extract current symbol from last analyzing line
            last_line = analyzing_lines[-1]
            if '.NS' in last_line:
                symbol = last_line.split('.NS')[0].split()[-1]
                current_symbol = symbol

        return jsonify({
            'status': 'running',
            'log': log_content,
            'timestamp': last_modified,
            'current_symbol': current_symbol,
            'completed_count': len(completed_lines) // 5,  # 5 walk-forward windows per symbol
            'total_symbols': 80
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'log': '',
            'timestamp': None
        }), 500

@app.route('/api/backtest/results')
def get_results():
    """Get final backtest results (when complete)"""
    results_path = '/tmp/smallcap_backtest_results.json'

    try:
        if not os.path.exists(results_path):
            return jsonify({
                'status': 'not_available',
                'message': 'Results not yet generated'
            })

        with open(results_path, 'r') as f:
            results = f.read()

        return jsonify({
            'status': 'complete',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'backtest-progress-api'})

@app.route('/')
@app.route('/backtest_monitor.html')
def serve_dashboard():
    """Serve the monitoring dashboard HTML"""
    if HTML_FILE.exists():
        return send_file(str(HTML_FILE))
    else:
        return jsonify({'error': 'Dashboard HTML not found'}), 404

if __name__ == '__main__':
    print("🚀 Backtest Progress API starting on http://localhost:5001")
    print("📊 Dashboard: http://localhost:5001/backtest_monitor.html")
    app.run(host='0.0.0.0', port=5001, debug=True)

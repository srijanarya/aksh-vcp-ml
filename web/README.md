# Backtest Monitoring Dashboard

Real-time web dashboard for monitoring backtesting progress.

## Features

- Live progress tracking (auto-refreshes every 5 seconds)
- Symbol-by-symbol status visualization (80 symbols)
- ETA calculation based on current progress
- Trade count display
- Elapsed time counter
- Recent activity log viewer
- Responsive purple gradient design

## Quick Start

### Option 1: Using the startup script

```bash
cd /Users/srijan/Desktop/aksh
./web/start_monitor.sh
```

This will:
1. Start the Flask API server on port 5001
2. Open the dashboard in your default browser

### Option 2: Manual start

1. Start the API server:
```bash
cd /Users/srijan/Desktop/aksh/web/api
python3 backtest_progress.py
```

2. Open the dashboard in your browser:
```
http://localhost:5001
```

Then navigate to [backtest_monitor.html](http://localhost:5001/backtest_monitor.html) or open [web/backtest_monitor.html](./backtest_monitor.html) directly.

## Architecture

```
web/
├── backtest_monitor.html       # Frontend dashboard (HTML + JS)
├── api/
│   └── backtest_progress.py   # Flask backend API
└── start_monitor.sh            # Convenience startup script
```

### API Endpoints

**GET /api/backtest/progress**
- Returns current backtest progress
- Response:
  ```json
  {
    "status": "running",
    "log": "full log text...",
    "timestamp": "2024-11-19T16:20:00",
    "current_symbol": "DIXON",
    "completed_count": 2,
    "total_symbols": 80
  }
  ```

**GET /api/backtest/results**
- Returns final backtest results (when complete)

**GET /health**
- Health check endpoint

## Log File Location

The dashboard reads from: `/tmp/smallcap_backtest.log`

This file is created by the backtesting CLI when you run:
```bash
python3 agents/backtesting/cli.py analyze \
  --strategy strategies/multi_timeframe_breakout.py \
  --start-date 2022-01-01 \
  --end-date 2024-11-01 \
  --symbols "SUZLON.NS,DIXON.NS,..." \
  2>&1 | tee /tmp/smallcap_backtest.log
```

## Customization

### Change Update Frequency

Edit [backtest_monitor.html](./backtest_monitor.html) line 446:
```javascript
setInterval(fetchProgress, 5000);  // 5 seconds (5000ms)
```

### Change Symbol List

The dashboard is currently configured for 80 small/mid cap symbols. To update the list, edit line 267-278 in [backtest_monitor.html](./backtest_monitor.html).

### Change API Port

Edit [api/backtest_progress.py](./api/backtest_progress.py) line 76:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

And update the API URL in [backtest_monitor.html](./backtest_monitor.html) line 312:
```javascript
const response = await fetch('http://localhost:5001/api/backtest/progress');
```

## Troubleshooting

### API not responding
```bash
# Check if API is running
ps aux | grep backtest_progress

# Check if port 5001 is in use
lsof -i :5001

# Restart API
pkill -f backtest_progress
cd /Users/srijan/Desktop/aksh/web/api
python3 backtest_progress.py
```

### Dashboard not updating
1. Open browser console (F12)
2. Check for CORS errors or fetch failures
3. Verify API is running: `curl http://localhost:5001/health`
4. Check log file exists: `ls -l /tmp/smallcap_backtest.log`

### Log file not found
Make sure the backtest is running and outputting to `/tmp/smallcap_backtest.log`. Check the bash command includes `| tee /tmp/smallcap_backtest.log`.

## Production Deployment

For production, replace Flask development server with a production WSGI server:

```bash
pip install gunicorn
cd /Users/srijan/Desktop/aksh/web/api
gunicorn -w 4 -b 0.0.0.0:5001 backtest_progress:app
```

## Integration with Backtesting System

The dashboard automatically integrates with the backtesting system:

1. **Run a backtest** with log output:
   ```bash
   python3 agents/backtesting/cli.py analyze \
     --strategy strategies/multi_timeframe_breakout.py \
     --start-date 2022-01-01 \
     --end-date 2024-11-01 \
     --symbols "$(cat agents/backtesting/symbol_lists/smallcap_midcap_strategy.txt)" \
     2>&1 | tee /tmp/smallcap_backtest.log
   ```

2. **Start the monitoring dashboard** (in another terminal):
   ```bash
   ./web/start_monitor.sh
   ```

3. **Watch progress in real-time** at http://localhost:5001/backtest_monitor.html

## Development

### Add new API endpoints

Edit [api/backtest_progress.py](./api/backtest_progress.py):
```python
@app.route('/api/new_endpoint')
def new_endpoint():
    return jsonify({'data': 'value'})
```

### Modify dashboard UI

Edit [backtest_monitor.html](./backtest_monitor.html). The dashboard uses vanilla JavaScript (no frameworks) for simplicity.

## License

Part of the VCP Financial Research System.

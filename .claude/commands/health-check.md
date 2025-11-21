# System Health Check

Run comprehensive system health check:

```bash
cd /Users/srijan/Desktop/aksh

# Run all tests
python3 -m pytest tests/unit/ -v --tb=short

# Check backtest
python3 validation/run_backtest_validation.py

# Verify modules
python3 -c "
from src.backtest.backtest_engine import BacktestEngine
from src.paper_trading.virtual_account import VirtualAccount
from src.order_executor.order_executor import OrderExecutor
print('✅ All core modules loaded successfully')
"

# Check API health
curl http://localhost:5000/api/health 2>/dev/null || echo "Web server not running"
```

Report results to user.

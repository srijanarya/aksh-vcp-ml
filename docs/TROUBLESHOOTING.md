# VCP ML System - Troubleshooting Guide

**Common issues, solutions, and debugging techniques**

---

## Quick Diagnosis

```bash
# Check system health
curl http://localhost:8000/api/v1/health

# Check logs
tail -f logs/api.log

# Check database
sqlite3 vcp_trading_local.db "SELECT COUNT(*) FROM price_movements;"

# Check model files
ls -lh data/models/

# Run tests
pytest tests/ -v
```

---

## Common Issues

### 1. API Won't Start

**Symptom:**
```
ERROR: Could not bind to 0.0.0.0:8000
```

**Causes & Solutions:**

**A) Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn api.main:app --port 8001
```

**B) Missing dependencies**
```bash
# Reinstall requirements
pip install -r requirements.txt

# Check specific packages
python -c "import fastapi, pandas, xgboost"
```

**C) Database not found**
```bash
# Check database exists
ls -l vcp_trading_local.db

# If missing, recreate
python -m agents.ml.ml_data_collector --setup-db
```

---

### 2. Prediction Returns Error

**Symptom:**
```json
{
  "error": "Insufficient historical data for bse_code: 500325"
}
```

**Causes & Solutions:**

**A) Missing price data**
```bash
# Check if price data exists
sqlite3 vcp_trading_local.db "
  SELECT COUNT(*) FROM price_movements WHERE bse_code = '500325';
"

# If less than 365 rows, collect more data
python -m agents.ml.price_collector --bse-code 500325 --days 365
```

**B) Invalid BSE code**
```bash
# Verify code is in master list
python -c "
import json
with open('data/master_stock_list.json') as f:
    stocks = json.load(f)
    codes = [s['bse_code'] for s in stocks]
    print('500325' in codes)
"
```

**C) Missing financial data**
```python
# Collect financial data
from agents.ml.financial_data_collector import FinancialDataCollector
collector = FinancialDataCollector()
collector.collect_stock_data("500325")
```

---

### 3. Slow API Response

**Symptom:**
```
Request taking > 5 seconds
```

**Causes & Solutions:**

**A) Feature extraction bottleneck**
```python
# Use optimized feature extractor (Epic 7.1)
from agents.ml.optimization import FeatureOptimizer

optimizer = FeatureOptimizer(db_path="vcp_trading_local.db")
features = optimizer.batch_extract_features(bse_codes, date)
# 3x faster than baseline
```

**B) Database not indexed**
```bash
sqlite3 vcp_trading_local.db <<EOF
CREATE INDEX IF NOT EXISTS idx_bse_code ON price_movements(bse_code);
CREATE INDEX IF NOT EXISTS idx_date ON price_movements(date);
CREATE INDEX IF NOT EXISTS idx_bse_date ON price_movements(bse_code, date);
EOF
```

**C) Too many concurrent requests**
```bash
# Increase workers
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

### 4. Model Accuracy Degrading

**Symptom:**
```
Model accuracy dropped from 0.73 to 0.60
```

**Causes & Solutions:**

**A) Data drift**
```python
# Check feature distributions
from agents.ml.feature_quality_validator import FeatureQualityValidator

validator = FeatureQualityValidator()
results = validator.validate_all_features(new_data)

if results['drift_detected']:
    print("Retraining recommended")
```

**B) Market regime change**
```python
# Retrain model with recent data
from agents.ml.baseline_trainer import BaselineTrainer

trainer = BaselineTrainer()
model, metrics = trainer.train_xgboost(X_train, y_train)
print(f"New F1: {metrics['f1']:.3f}")
```

**C) Stale model**
```bash
# Check model age
ls -lh data/models/*.pkl

# Retrain if > 3 months old
python -m agents.ml.baseline_trainer --retrain
```

---

### 5. High Memory Usage

**Symptom:**
```
Process using > 8GB RAM
```

**Causes & Solutions:**

**A) Loading too much data at once**
```python
# Use chunking for large datasets
def process_in_chunks(data, chunk_size=1000):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        yield process_chunk(chunk)
```

**B) Memory leak in feature extraction**
```python
# Clear cache periodically
import gc

def predict_with_cleanup(bse_code, date):
    result = make_prediction(bse_code, date)
    gc.collect()
    return result
```

**C) Too many workers**
```bash
# Reduce worker count
gunicorn api.main:app -w 2  # Instead of 4
```

---

### 6. Database Lock Errors

**Symptom:**
```
sqlite3.OperationalError: database is locked
```

**Causes & Solutions:**

**A) Concurrent writes**
```python
# Use connection pooling
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('vcp_trading_local.db', timeout=30)
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**B) Long-running transactions**
```python
# Break into smaller transactions
def bulk_insert_chunked(data, chunk_size=1000):
    for chunk in chunks(data, chunk_size):
        with get_db_connection() as conn:
            conn.executemany("INSERT INTO ...", chunk)
```

**C) Consider PostgreSQL for production**
```bash
# Migration guide in docs/DEPLOYMENT.md
```

---

### 7. Docker Container Fails

**Symptom:**
```
Container exits with code 1
```

**Causes & Solutions:**

**A) Database path issues**
```dockerfile
# Ensure volume is mounted
volumes:
  - ./data:/app/data
  - ./vcp_trading_local.db:/app/vcp_trading_local.db
```

**B) Missing environment variables**
```bash
# Check .env file
docker run -it --env-file .env vcp-ml-api:latest
```

**C) Port conflicts**
```bash
# Use different host port
docker run -p 8001:8000 vcp-ml-api:latest
```

---

### 8. Tests Failing

**Symptom:**
```
FAILED tests/unit/test_baseline_trainer.py
```

**Causes & Solutions:**

**A) Missing test data**
```bash
# Generate test fixtures
python tests/generate_fixtures.py
```

**B) Environment differences**
```bash
# Use consistent Python version
python --version  # Should be 3.9+

# Clean install
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**C) Test database conflicts**
```bash
# Use separate test database
export TEST_DB_PATH=test_vcp_trading.db
pytest tests/
```

---

## Performance Debugging

### Profiling API Endpoints

```python
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()

    # Run endpoint
    response = make_prediction("500325", "2025-11-15")

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 slowest functions
```

### Database Query Analysis

```sql
-- Enable query logging
PRAGMA query_log = ON;

-- Analyze query plan
EXPLAIN QUERY PLAN
SELECT * FROM price_movements WHERE bse_code = '500325' AND date >= '2024-01-01';

-- Check for missing indexes
SELECT name FROM sqlite_master WHERE type='index';
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass

# Run with: python -m memory_profiler your_script.py
```

---

## Monitoring & Alerts

### Check Prometheus Metrics

```bash
# API request rate
curl http://localhost:9090/api/v1/query?query=rate(api_requests_total[5m])

# Error rate
curl http://localhost:9090/api/v1/query?query=rate(api_errors_total[5m])

# Latency (p95)
curl http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(api_request_duration_seconds_bucket[5m]))
```

### Check Grafana Dashboards

```bash
# Open in browser
open http://localhost:3000

# Dashboards:
# - System Health
# - Model Performance
# - Business Metrics
```

---

## Logging

### Enable Debug Logging

```python
# In .env
LOG_LEVEL=DEBUG

# Or runtime
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Useful Log Queries

```bash
# Find errors in last hour
grep "ERROR" logs/api.log | tail -100

# Find slow requests (>1s)
grep "duration_ms\":.*[0-9]{4}" logs/api.log

# Find specific BSE code
grep "500325" logs/api.log | tail -20
```

---

## Data Issues

### Verify Data Quality

```python
from agents.ml.feature_quality_validator import FeatureQualityValidator

validator = FeatureQualityValidator()

# Check missing values
missing_report = validator.check_missing_values(data)
print(f"Missing values: {missing_report['total_missing']}")

# Check outliers
outlier_report = validator.detect_outliers(data)
print(f"Outliers: {outlier_report['total_outliers']}")

# Check data drift
drift_report = validator.detect_drift(reference_data, current_data)
if drift_report['drift_detected']:
    print("WARNING: Data drift detected!")
```

### Fix Corrupted Data

```bash
# Backup database
cp vcp_trading_local.db vcp_trading_local.db.backup

# Run integrity check
sqlite3 vcp_trading_local.db "PRAGMA integrity_check;"

# If corrupted, restore from backup or re-collect
python -m agents.ml.price_collector --force-refresh
```

---

## Model Issues

### Debug Model Predictions

```python
import shap

# Load model
model = load_model("data/models/xgboost_best.pkl")

# Get SHAP explanations
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Visualize
shap.summary_plot(shap_values, X_test)
```

### Validate Model Files

```bash
# Check model file integrity
python -c "
import pickle
with open('data/models/xgboost_best.pkl', 'rb') as f:
    model = pickle.load(f)
    print('Model loaded successfully')
    print(f'Features: {model.n_features_in_}')
"
```

---

## Network Issues

### API Connectivity

```bash
# Test local connectivity
curl http://localhost:8000/api/v1/health

# Test external connectivity
curl http://vcp-api.example.com/api/v1/health

# Check firewall
sudo ufw status

# Check DNS
nslookup vcp-api.example.com
```

### Timeout Issues

```python
# Increase request timeout
import requests

response = requests.post(
    url,
    json=data,
    timeout=30  # 30 seconds
)
```

---

## Getting Help

### Self-Diagnosis Checklist

Before seeking help, check:

- [ ] System health endpoint responding
- [ ] Database contains data (`SELECT COUNT(*)`)
- [ ] Model files exist in `data/models/`
- [ ] Logs show any errors (`grep ERROR logs/api.log`)
- [ ] Tests passing (`pytest tests/`)
- [ ] Disk space available (`df -h`)
- [ ] Memory usage reasonable (`free -h`)

### Gather Diagnostic Info

```bash
# Run diagnostic script
python tools/diagnose.py

# Or manually:
echo "=== System Info ===" > diagnostic.txt
python --version >> diagnostic.txt
pip list >> diagnostic.txt
echo "\n=== Database Info ===" >> diagnostic.txt
sqlite3 vcp_trading_local.db "
  SELECT 'Price records:', COUNT(*) FROM price_movements;
  SELECT 'Financial records:', COUNT(*) FROM historical_financials;
" >> diagnostic.txt
echo "\n=== Recent Errors ===" >> diagnostic.txt
grep "ERROR" logs/api.log | tail -20 >> diagnostic.txt
```

### Submit Issue

Include:
1. Diagnostic info (above)
2. Steps to reproduce
3. Expected vs actual behavior
4. Error messages (full traceback)
5. Environment (OS, Python version)

**Submit to:** https://github.com/<org>/aksh/issues

---

## Emergency Procedures

### Complete System Reset

```bash
# CAUTION: This deletes all data!

# 1. Stop services
docker-compose down

# 2. Backup database
cp vcp_trading_local.db backup_$(date +%Y%m%d).db

# 3. Clean data
rm -rf data/models/*
rm -rf data/cache/*

# 4. Rebuild database
python -m agents.ml.ml_data_collector --setup-db

# 5. Recollect data
python -m agents.ml.price_collector --days 365
python -m agents.ml.financial_data_collector

# 6. Retrain models
python -m agents.ml.baseline_trainer

# 7. Restart services
docker-compose up -d
```

### Rollback Deployment

```bash
# Docker
docker-compose down
docker tag vcp-ml-api:latest vcp-ml-api:broken
docker tag vcp-ml-api:v1.0.0 vcp-ml-api:latest
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/vcp-ml-api
kubectl rollout status deployment/vcp-ml-api
```

---

## Prevention

### Regular Maintenance

```bash
# Weekly
- Check logs for errors
- Verify data quality
- Monitor API latency
- Review model performance

# Monthly
- Retrain models
- Update dependencies
- Backup database
- Review and optimize queries

# Quarterly
- Full system audit
- Performance testing
- Security review
- Documentation update
```

### Monitoring Alerts

Set up alerts for:
- API error rate > 5%
- API latency p95 > 200ms
- Model accuracy drop > 10%
- Database size > 80% capacity
- Memory usage > 80%
- Disk usage > 80%

---

**Remember:** Most issues can be resolved by checking logs, verifying data, and ensuring all dependencies are installed correctly.

**Last Updated:** November 14, 2025

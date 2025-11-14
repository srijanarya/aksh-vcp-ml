# Epic 5: Monitoring & Alerts

**Epic ID**: EPIC-5
**Priority**: P0 (Critical Path)
**Status**: Ready to Start
**Estimated Effort**: 10 days (12 days with buffer)
**Dependencies**: EPIC-4 (Production Deployment) - COMPLETE ✅

---

## Epic Goal

Implement comprehensive monitoring and alerting system to detect model degradation, data drift, performance issues, and system health in production. Target: Detect model F1 degradation >5% within 24 hours, data drift detection with <1% false positive rate, 99.9% uptime monitoring.

---

## Success Criteria

1. **Performance Monitoring**: Track latency, throughput, error rates in real-time
2. **Data Drift Detection**: Detect feature distribution changes with statistical tests
3. **Model Degradation**: Alert when F1 drops >5% from baseline
4. **Logging Infrastructure**: Centralized logs with 30-day retention
5. **Dashboard**: Real-time metrics visualization with Grafana/custom HTML
6. **Alerting**: Email/Slack alerts within 5 minutes of issue detection

---

## Stories (5 total)

### Story 5.1: Performance Monitoring
- Prometheus metrics collection
- API latency, throughput, error rate tracking
- System resource monitoring (CPU, memory, disk)
- **Effort**: 2 days

### Story 5.2: Data Drift Detection
- Statistical tests (KS test, PSI)
- Feature distribution monitoring
- Drift alerts with severity levels
- **Effort**: 3 days

### Story 5.3: Model Degradation Alerts
- F1 score tracking on production predictions
- Comparison with baseline performance
- Automatic model rollback triggers
- **Effort**: 2 days

### Story 5.4: Logging Infrastructure
- Structured JSON logging
- Log aggregation with rotation
- Error tracking and stack traces
- **Effort**: 2 days

### Story 5.5: Dashboard for Metrics
- Grafana dashboard (or custom HTML)
- Real-time metric visualization
- Historical trend analysis
- **Effort**: 1 day

---

## File Structure

```
agents/ml/monitoring/
├── performance_monitor.py           # Story 5.1
├── drift_detector.py                # Story 5.2
├── model_monitor.py                 # Story 5.3
├── logging_config.py                # Story 5.4
└── alert_manager.py                 # All stories

dashboards/
├── grafana/
│   └── vcp_ml_dashboard.json        # Story 5.5
└── custom/
    └── metrics_dashboard.html       # Story 5.5 (fallback)

tests/unit/
├── test_performance_monitor.py
├── test_drift_detector.py
├── test_model_monitor.py
└── test_alert_manager.py

data/monitoring/
├── metrics.db                       # Time-series metrics
├── drift_reports/                   # Daily drift reports
└── alerts.db                        # Alert history
```

---

## Story 5.1: Performance Monitoring

**Story ID:** EPIC5-S1
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S1 (API Server)

### User Story

**As a** Production Engineer,
**I want** real-time performance metrics for the ML API,
**so that** I can detect and resolve performance issues before they impact users.

### Acceptance Criteria

**AC5.1.1:** Prometheus metrics integration
- File: `/Users/srijan/Desktop/aksh/agents/ml/monitoring/performance_monitor.py`
- Metrics library: `prometheus-client`
- Expose metrics at `/metrics` endpoint (Prometheus format)
- Integration with FastAPI middleware

**AC5.1.2:** API latency metrics
- Metric: `api_request_duration_seconds` (histogram)
- Labels: `endpoint, method, status_code`
- Buckets: `[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]` seconds
- Track p50, p95, p99 latencies
- Alert if p95 > 150ms for 5 minutes

**AC5.1.3:** Throughput metrics
- Metric: `api_requests_total` (counter)
- Labels: `endpoint, method, status_code`
- Calculate requests per second (rate)
- Alert if throughput drops >50% from baseline

**AC5.1.4:** Error rate metrics
- Metric: `api_errors_total` (counter)
- Labels: `endpoint, error_type, status_code`
- Track 4xx and 5xx separately
- Calculate error rate: `errors / total_requests`
- Alert if error rate >5% for 10 minutes

**AC5.1.5:** System resource metrics
- CPU usage: `process_cpu_seconds_total`
- Memory: `process_resident_memory_bytes`
- Disk I/O: `disk_read_bytes_total`, `disk_write_bytes_total`
- Alert if CPU >80% for 15 minutes
- Alert if memory >90% for 5 minutes

**AC5.1.6:** Model prediction metrics
- Metric: `model_predictions_total` (counter)
- Labels: `predicted_label, confidence, model_version`
- Track prediction distribution:
  - Positive predictions (label=1)
  - Negative predictions (label=0)
  - High/Medium/Low confidence breakdown
- Alert if positive rate >20% (unusual spike)

**AC5.1.7:** Custom business metrics
- Metric: `daily_upper_circuit_candidates` (gauge)
- Metric: `feature_extraction_failures_total` (counter)
- Metric: `model_cache_hit_rate` (gauge)
- Update daily/hourly

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/monitoring/performance_monitor.py`

**Key Components:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
import time

# Metrics
REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method', 'status_code'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

REQUESTS_TOTAL = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status_code']
)

ERRORS_TOTAL = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type', 'status_code']
)

class PerformanceMonitor:
    def __init__(self):
        """Initialize performance monitoring"""
        
    async def track_request(
        self,
        request: Request,
        call_next
    ):
        """Middleware to track request metrics"""
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        REQUEST_DURATION.labels(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code
        ).observe(duration)
        
        REQUESTS_TOTAL.labels(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code
        ).inc()
        
        return response
        
    def check_thresholds(self) -> List[Alert]:
        """Check if any metrics exceed thresholds"""

# FastAPI integration
from fastapi.responses import PlainTextResponse

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest())

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Apply performance monitoring middleware"""
    monitor = PerformanceMonitor()
    return await monitor.track_request(request, call_next)
```

**Dependencies:**
- `prometheus-client` - Metrics library
- `psutil` - System resource monitoring

**Test File:** `tests/unit/test_performance_monitor.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Metrics endpoint returns valid Prometheus format
- [ ] Load test: Verify metrics under 1000 req/min load
- [ ] Manual test: View metrics in Prometheus
- [ ] Documentation: Metrics catalog with descriptions

---

## Story 5.2: Data Drift Detection

**Story ID:** EPIC5-S2
**Priority:** P0
**Estimated Effort:** 3 days
**Dependencies:** EPIC4-S2 (Batch Predictor)

### User Story

**As a** ML Engineer,
**I want** automated data drift detection for production features,
**so that** I know when model retraining is needed due to data distribution changes.

### Acceptance Criteria

**AC5.2.1:** DriftDetector class with statistical tests
- File: `/Users/srijan/Desktop/aksh/agents/ml/monitoring/drift_detector.py`
- Class: `DriftDetector` with methods for KS test and PSI
- Input: Production feature distributions vs training distributions
- Output: Drift scores per feature + overall drift status

**AC5.2.2:** Kolmogorov-Smirnov (KS) test for continuous features
- Test: Compare production feature distribution vs training baseline
- Metric: KS statistic (0 to 1, higher = more drift)
- Threshold: `ks_stat > 0.3` indicates significant drift
- Apply to: Technical features (RSI, MACD, volume ratios)
- Test all 15-20 technical features daily

**AC5.2.3:** Population Stability Index (PSI) for all features
- Formula: `PSI = Σ (actual% - expected%) * ln(actual% / expected%)`
- Interpretation:
  - PSI < 0.1: No significant drift
  - 0.1 ≤ PSI < 0.25: Moderate drift (monitor)
  - PSI ≥ 0.25: Significant drift (retrain needed)
- Apply to: All 25 features
- Calculate daily and weekly PSI

**AC5.2.4:** Baseline distribution storage
- Store training data distributions in `drift_baselines.db`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS drift_baselines (
    baseline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    feature_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    distribution_type TEXT CHECK(distribution_type IN ('histogram', 'summary')),
    bins TEXT,  -- JSON array of bin edges
    counts TEXT,  -- JSON array of counts per bin
    mean REAL,
    std REAL,
    min REAL,
    max REAL,
    percentiles TEXT,  -- JSON: {p5, p25, p50, p75, p95}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(feature_name, model_version)
);
```

**AC5.2.5:** Daily drift detection job
- Run daily after batch predictions (Story 4.2)
- Compare today's feature distributions vs baseline
- Test all 25 features
- Generate drift report
- Store results in `drift_reports.db`

**AC5.2.6:** Drift report generation
- Report format:
```
========================================
DATA DRIFT DETECTION REPORT
========================================
Date: 2025-11-14
Model Version: 1.2.0
Baseline: 2025-09-01 to 2025-10-31 (60 days)

SUMMARY:
- Features Tested: 25
- Features with Drift: 3 (12%)
- Severity: MODERATE

DETAILED RESULTS:
Feature Name           | KS Stat | PSI   | Status      | Action
-----------------------|---------|-------|-------------|------------------
revenue_growth_yoy     | 0.15    | 0.08  | OK          | -
npm_trend              | 0.22    | 0.12  | OK          | Monitor
rsi_14                 | 0.35    | 0.28  | DRIFT       | Retrain recommended
volume_ratio_30d       | 0.41    | 0.32  | DRIFT       | Retrain recommended
macd_signal            | 0.18    | 0.15  | MODERATE    | Monitor
...

DRIFT SEVERITY: MODERATE
- 3 features show significant drift (PSI ≥ 0.25)
- Affected features: rsi_14, volume_ratio_30d, price_momentum_30d
- Likely cause: Market regime change (bull → bear transition)

RECOMMENDATIONS:
1. Retrain model on last 90 days of data
2. Monitor model performance closely next 7 days
3. Consider adaptive feature normalization

ALERT: Email sent to ml-team@company.com
========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/monitoring/drift_reports/drift_{YYYY-MM-DD}.txt`

**AC5.2.7:** Alert thresholds and escalation
- **Low drift**: PSI < 0.1 → No alert, log only
- **Moderate drift**: 0.1 ≤ PSI < 0.25 → Slack notification
- **High drift**: PSI ≥ 0.25 → Email + Slack, recommend retrain
- **Critical drift**: PSI ≥ 0.4 or >30% features drifting → Page on-call engineer
- Alert deduplication: Max 1 alert per severity level per day

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/monitoring/drift_detector.py`

**Key Components:**
```python
from scipy.stats import ks_2samp
import numpy as np
import pandas as pd

class DriftDetector:
    def __init__(
        self,
        baseline_db: str,
        drift_reports_db: str,
        model_version: str
    ):
        """Initialize drift detector"""
        
    def calculate_ks_statistic(
        self,
        baseline_dist: np.ndarray,
        production_dist: np.ndarray
    ) -> float:
        """
        Kolmogorov-Smirnov test for continuous distributions.
        
        Returns:
            KS statistic (0 to 1)
        """
        statistic, p_value = ks_2samp(baseline_dist, production_dist)
        return statistic
        
    def calculate_psi(
        self,
        baseline_dist: np.ndarray,
        production_dist: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Population Stability Index.
        
        Args:
            baseline_dist: Training data distribution
            production_dist: Production data distribution
            bins: Number of bins for discretization
            
        Returns:
            PSI score (0 to infinity, typically 0 to 1)
        """
        # Discretize into bins
        baseline_binned, bin_edges = np.histogram(baseline_dist, bins=bins)
        production_binned, _ = np.histogram(production_dist, bins=bin_edges)
        
        # Calculate percentages
        baseline_pct = baseline_binned / len(baseline_dist)
        production_pct = production_binned / len(production_dist)
        
        # PSI formula
        psi = np.sum((production_pct - baseline_pct) * np.log(production_pct / (baseline_pct + 1e-10)))
        return psi
        
    def detect_drift_daily(self, date: str) -> DriftReport:
        """
        Run drift detection for all features.
        
        Args:
            date: Production date to check
            
        Returns:
            DriftReport with drift scores per feature
        """
        
    def load_baseline_distributions(self) -> Dict[str, np.ndarray]:
        """Load baseline feature distributions from DB"""
        
    def load_production_distributions(self, date: str) -> Dict[str, np.ndarray]:
        """Load production feature distributions for given date"""
        
    def generate_drift_report(
        self,
        drift_scores: Dict[str, Tuple[float, float]],
        date: str
    ) -> DriftReport:
        """Generate human-readable drift report"""
        
    def send_alerts(self, report: DriftReport):
        """Send alerts based on drift severity"""
```

**Dependencies:**
- `scipy` - Statistical tests
- `numpy` - Numerical operations
- `pandas` - Data manipulation

**Test File:** `tests/unit/test_drift_detector.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Detect drift on synthetic data
- [ ] Statistical validation: KS test and PSI calculations correct
- [ ] Manual test: Run drift detection on 30 days of production data
- [ ] Alert test: Verify email/Slack alerts sent correctly
- [ ] Documentation: Drift detection methodology documented

---

## Story 5.3: Model Degradation Alerts

**Story ID:** EPIC5-S3
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S2 (Batch Predictor)

### User Story

**As a** ML Team Lead,
**I want** automated detection of model performance degradation,
**so that** I can retrain or rollback models before accuracy impacts business.

### Acceptance Criteria

**AC5.3.1:** ModelMonitor class to track production F1
- File: `/Users/srijan/Desktop/aksh/agents/ml/monitoring/model_monitor.py`
- Class: `ModelMonitor` with method: `evaluate_production_performance(date: str) -> PerformanceReport`
- Compare production predictions vs actual outcomes (after earnings)
- Calculate F1, precision, recall, ROC-AUC on production data

**AC5.3.2:** Ground truth collection
- After earnings announcement, collect actual outcome:
  - Did stock hit upper circuit? (from BhavCopy or price data)
  - Store in `production_labels.db`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS production_labels (
    label_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    prediction_date DATE NOT NULL,
    earnings_date DATE NOT NULL,
    actual_label INTEGER NOT NULL CHECK(actual_label IN (0, 1)),
    predicted_label INTEGER NOT NULL CHECK(predicted_label IN (0, 1)),
    predicted_probability REAL,
    model_version TEXT,
    labeled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, prediction_date)
);
```

**AC5.3.3:** Rolling performance calculation
- Calculate F1 score on last 7 days, 30 days, 90 days
- Store in `model_performance_history.db`
- Track: F1, precision, recall, ROC-AUC, prediction count
- Compare to baseline (test set performance from training)

**AC5.3.4:** Degradation detection thresholds
- **Minor degradation**: F1 drops 3-5% from baseline → Log warning
- **Moderate degradation**: F1 drops 5-10% from baseline → Slack alert
- **Severe degradation**: F1 drops >10% from baseline → Email + Slack, recommend rollback
- Check: Minimum 100 predictions in window before alerting (avoid noise)

**AC5.3.5:** Performance report generation
- Report format:
```
========================================
MODEL PERFORMANCE REPORT
========================================
Date: 2025-11-14
Model Version: 1.2.0

BASELINE PERFORMANCE (Test Set):
- F1 Score: 0.72
- Precision: 0.68
- Recall: 0.76
- ROC-AUC: 0.79

PRODUCTION PERFORMANCE (Last 30 Days):
- F1 Score: 0.67 (↓ 7%)
- Precision: 0.63 (↓ 7%)
- Recall: 0.72 (↓ 5%)
- ROC-AUC: 0.75 (↓ 5%)
- Predictions: 1,234
- True Positives: 89
- False Positives: 52
- False Negatives: 35
- True Negatives: 1,058

STATUS: MODERATE DEGRADATION
- F1 dropped 7% from baseline
- Likely cause: Data drift in rsi_14, volume_ratio_30d (see Drift Report)

RECOMMENDATIONS:
1. Retrain model on last 90 days of data
2. Review drift report for feature changes
3. Consider model rollback to v1.1.0 (F1: 0.70)

ALERT: Sent to ml-team@company.com
========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/monitoring/performance_reports/performance_{YYYY-MM-DD}.txt`

**AC5.3.6:** Automatic model rollback trigger
- If severe degradation detected (F1 drop >10%):
  - Send alert to on-call engineer
  - Recommend rollback to previous stable version
  - Provide rollback command: `POST /api/v1/models/rollback?version=1.1.0`
- Rollback is manual (requires engineer approval)
- Log rollback decisions in `model_rollback_history.db`

**AC5.3.7:** Performance dashboard metrics
- Expose metrics for Grafana:
  - `model_f1_score` (gauge)
  - `model_precision` (gauge)
  - `model_recall` (gauge)
  - `model_roc_auc` (gauge)
  - `model_degradation_severity` (enum: NONE, MINOR, MODERATE, SEVERE)
- Update daily after performance calculation

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/monitoring/model_monitor.py`

**Key Components:**
```python
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
import pandas as pd

class ModelMonitor:
    def __init__(
        self,
        predictions_db: str,
        labels_db: str,
        baseline_metrics: Dict[str, float]
    ):
        """Initialize model performance monitor"""
        
    def collect_ground_truth(self, date: str) -> int:
        """
        Collect actual outcomes for predictions made on date.
        
        Args:
            date: Prediction date
            
        Returns:
            Number of labels collected
        """
        
    def evaluate_production_performance(
        self,
        start_date: str,
        end_date: str
    ) -> PerformanceReport:
        """
        Calculate F1, precision, recall on production data.
        
        Args:
            start_date: Start of evaluation window
            end_date: End of evaluation window
            
        Returns:
            PerformanceReport with metrics
        """
        
    def detect_degradation(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float]
    ) -> DegradationStatus:
        """
        Compare current vs baseline performance.
        
        Returns:
            DegradationStatus: NONE, MINOR, MODERATE, SEVERE
        """
        
    def generate_performance_report(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float],
        date: str
    ) -> PerformanceReport:
        """Generate human-readable performance report"""
        
    def recommend_rollback(
        self,
        current_version: str,
        degradation_status: DegradationStatus
    ) -> Optional[str]:
        """
        Recommend model rollback if needed.
        
        Returns:
            Previous stable version or None
        """
```

**Dependencies:**
- `scikit-learn` - Metrics calculation
- `pandas` - Data manipulation

**Test File:** `tests/unit/test_model_monitor.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Integration test: Simulate performance degradation
- [ ] Manual test: Run performance evaluation on 90 days of data
- [ ] Alert test: Verify degradation alerts sent
- [ ] Rollback test: Verify rollback recommendation logic
- [ ] Documentation: Performance monitoring guide

---

## Story 5.4: Logging Infrastructure

**Story ID:** EPIC5-S4
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S1 (API Server)

### User Story

**As a** DevOps Engineer,
**I want** centralized structured logging with rotation and retention,
**so that** I can debug production issues and audit ML predictions.

### Acceptance Criteria

**AC5.4.1:** Structured JSON logging configuration
- File: `/Users/srijan/Desktop/aksh/agents/ml/monitoring/logging_config.py`
- Format: JSON with fields: `timestamp, level, logger, message, context, trace_id`
- Example:
```json
{
  "timestamp": "2025-11-14T10:30:00.123Z",
  "level": "INFO",
  "logger": "api_server",
  "message": "Prediction request received",
  "context": {
    "bse_code": "500325",
    "prediction_date": "2025-11-14",
    "endpoint": "/api/v1/predict"
  },
  "trace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**AC5.4.2:** Log levels and severity
- **DEBUG**: Detailed diagnostic info (feature extraction details)
- **INFO**: General info (prediction requests, batch jobs started)
- **WARNING**: Warning messages (data drift detected, high latency)
- **ERROR**: Error events (feature extraction failed, model load error)
- **CRITICAL**: Critical errors (database unavailable, model crash)
- Default level: INFO (configurable via env var `LOG_LEVEL`)

**AC5.4.3:** Log rotation and retention
- Rotate logs daily at midnight IST
- Keep 30 days of logs (delete older)
- Max log file size: 100MB (rotate if exceeded before daily)
- Compressed archives: `.log.gz` for old logs
- Directory: `/var/log/vcp-ml/` or `/app/logs/` in Docker

**AC5.4.4:** Contextual logging with trace IDs
- Generate UUID trace_id for each API request
- Propagate trace_id through entire request lifecycle
- Log trace_id in all log entries for that request
- Include in error responses for debugging

**AC5.4.5:** Error tracking with stack traces
- Log full stack trace for all ERROR and CRITICAL levels
- Include: Exception type, message, stack trace, context
- Store in separate `errors.log` file for easy filtering
- Alert on-call if CRITICAL error occurs

**AC5.4.6:** Audit logging for ML predictions
- Log every prediction made (for compliance)
- Audit log: `/app/logs/audit.log`
- Fields: `timestamp, bse_code, prediction_date, predicted_label, probability, model_version, user_id (if applicable), trace_id`
- Retention: 90 days (longer for audit trail)

**AC5.4.7:** Integration with logging aggregators
- Support for: Elasticsearch, Splunk, Datadog (via log shippers)
- Log to stdout/stderr in JSON format (Docker best practice)
- Optional: Direct shipping to Elasticsearch via `python-elasticsearch`

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/monitoring/logging_config.py`

**Key Components:**
```python
import logging
import logging.handlers
import json
import uuid
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "context": getattr(record, "context", {}),
            "trace_id": getattr(record, "trace_id", None)
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "/app/logs"
):
    """
    Configure logging for the application.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    """
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=f"{log_dir}/app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=f"{log_dir}/errors.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    return logger

def get_logger_with_trace_id(name: str, trace_id: str = None):
    """Get logger with trace_id context"""
    logger = logging.getLogger(name)
    if trace_id:
        logger = logging.LoggerAdapter(logger, {"trace_id": trace_id})
    return logger
```

**Dependencies:**
- `logging` (built-in)
- `uuid` (built-in)

**Test File:** `tests/unit/test_logging_config.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥85% coverage
- [ ] Integration test: Verify log rotation works
- [ ] Manual test: Generate logs, check JSON format
- [ ] Verify logs appear in stdout (Docker)
- [ ] Documentation: Logging configuration guide

---

## Story 5.5: Dashboard for Metrics

**Story ID:** EPIC5-S5
**Priority:** P1
**Estimated Effort:** 1 day
**Dependencies:** EPIC5-S1 (Performance Monitor), EPIC5-S2 (Drift Detector), EPIC5-S3 (Model Monitor)

### User Story

**As a** ML Team,
**I want** a visual dashboard to monitor ML system health,
**so that** I can quickly identify issues without querying databases.

### Acceptance Criteria

**AC5.5.1:** Grafana dashboard (preferred)
- File: `/Users/srijan/Desktop/aksh/dashboards/grafana/vcp_ml_dashboard.json`
- Prometheus data source
- 4 panels:
  1. **API Performance**: Latency (p50, p95, p99), throughput, error rate
  2. **Model Performance**: F1, precision, recall (7-day, 30-day rolling)
  3. **Data Drift**: PSI scores for top 10 features
  4. **System Health**: CPU, memory, disk usage

**AC5.5.2:** Custom HTML dashboard (fallback)
- File: `/Users/srijan/Desktop/aksh/dashboards/custom/metrics_dashboard.html`
- JavaScript: Chart.js or Plotly.js for visualizations
- Auto-refresh: Every 30 seconds
- Fetch data from `/metrics` endpoint (Prometheus format)
- Mobile-friendly responsive design

**AC5.5.3:** Real-time metrics display
- API latency: Line chart (last 24 hours)
- Throughput: Bar chart (requests per hour)
- Error rate: Line chart with threshold line (5%)
- Model F1: Line chart with baseline (last 90 days)
- Drift PSI: Heatmap (features × dates)

**AC5.5.4:** Historical trend analysis
- Time range selector: Last 24h, 7d, 30d, 90d
- Compare current metrics vs previous period
- Highlight anomalies (spikes, drops)
- Export chart as PNG

**AC5.5.5:** Alert status panel
- Show active alerts: Drift, degradation, performance
- Alert history: Last 10 alerts
- Acknowledge button for alerts
- Link to detailed reports

**AC5.5.6:** Model metadata display
- Current model version
- Model type (XGBoost, LightGBM)
- Training date
- Test set metrics (F1, ROC-AUC)
- Feature importance top 10

**AC5.5.7:** Dashboard deployment
- Serve dashboard via FastAPI endpoint: `GET /dashboard`
- Embed in API server or separate service
- Authentication: Basic auth (username/password)
- HTTPS recommended for production

### Technical Specifications

**Grafana Dashboard JSON:**
```json
{
  "dashboard": {
    "title": "VCP ML System Monitoring",
    "panels": [
      {
        "title": "API Latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Model F1 Score (30-day rolling)",
        "type": "graph",
        "targets": [
          {
            "expr": "model_f1_score"
          }
        ]
      }
    ]
  }
}
```

**Custom HTML Dashboard (snippet):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>VCP ML Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <h1>VCP ML System Monitoring</h1>
    
    <div id="api-latency">
        <canvas id="latencyChart"></canvas>
    </div>
    
    <script>
        // Fetch metrics from /metrics endpoint
        fetch('/metrics')
            .then(response => response.text())
            .then(data => {
                // Parse Prometheus format
                // Render Chart.js chart
            });
            
        // Auto-refresh every 30s
        setInterval(() => { location.reload(); }, 30000);
    </script>
</body>
</html>
```

**Dependencies:**
- Grafana (if using Grafana dashboard)
- Chart.js or Plotly.js (if custom dashboard)

**Test File:** `tests/integration/test_dashboard.py`

**Test Coverage Requirements:** ≥80%

### Definition of Done

- [ ] Grafana dashboard JSON created
- [ ] Custom HTML dashboard created (fallback)
- [ ] Integration test: Verify dashboard loads
- [ ] Manual test: View dashboard in browser
- [ ] Verify auto-refresh works
- [ ] Documentation: Dashboard setup guide

---

## Epic Completion Criteria

All 5 stories (EPIC5-S1 through EPIC5-S5) must meet Definition of Done:

- [ ] All acceptance criteria passing for all stories
- [ ] ≥90% unit test coverage across monitoring code
- [ ] Integration tests passing: Metrics collection, drift detection, alerts
- [ ] Performance validated: Monitoring overhead <5% CPU
- [ ] Dashboard accessible via /dashboard
- [ ] Alerts tested: Email and Slack notifications work
- [ ] Deliverables exist:
  - `agents/ml/monitoring/performance_monitor.py`
  - `agents/ml/monitoring/drift_detector.py`
  - `agents/ml/monitoring/model_monitor.py`
  - `agents/ml/monitoring/logging_config.py`
  - `dashboards/grafana/vcp_ml_dashboard.json`
  - `dashboards/custom/metrics_dashboard.html`

**Ready for Epic 6:** Backtesting & Validation

---

**Total Duration**: 10 days + 2 day buffer = 12 days
**Next Epic**: Epic 6 - Backtesting & Validation

**Author**: VCP Financial Research Team
**Created**: 2025-11-14

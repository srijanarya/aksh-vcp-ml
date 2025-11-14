# Epic 4: Production Deployment & Real-time Inference

**Epic ID**: EPIC-4
**Priority**: P0 (Critical Path)
**Status**: Ready to Start
**Estimated Effort**: 12 days (14 days with buffer)
**Dependencies**: EPIC-3 (Model Training) - COMPLETE ✅

---

## Epic Goal

Deploy trained ML models to production with FastAPI endpoints for real-time predictions, batch inference pipelines for daily scoring of all NSE/BSE stocks, and Docker containerization for scalable deployment. Target: <100ms prediction latency, 99.9% uptime, process 11,000 companies in <10 minutes daily.

---

## Success Criteria

1. **API Performance**: <100ms p95 latency for single stock prediction
2. **Batch Throughput**: Process 11,000 stocks in <10 minutes (18 stocks/sec)
3. **Uptime**: 99.9% availability (8.76 hours downtime/year max)
4. **Model Loading**: <5 seconds cold start time
5. **Documentation**: OpenAPI/Swagger docs auto-generated
6. **Containerization**: Docker image <500MB, starts in <30 seconds

---

## Stories (5 total)

### Story 4.1: FastAPI Prediction Endpoint
- REST API with /predict, /batch_predict, /health endpoints
- Request validation with Pydantic models
- Target: <100ms p95 latency
- **Effort**: 3 days

### Story 4.2: Batch Prediction Pipeline
- Daily scoring of all NSE/BSE stocks
- Parallel processing with multiprocessing
- Output to predictions.db and CSV
- **Effort**: 3 days

### Story 4.3: Model Loading & Caching
- LRU cache for model instances
- Lazy loading on first request
- Graceful fallback to previous version
- **Effort**: 2 days

### Story 4.4: API Documentation & Testing
- OpenAPI/Swagger auto-docs
- Integration tests for all endpoints
- Load testing with Locust
- **Effort**: 2 days

### Story 4.5: Docker Containerization
- Multi-stage Dockerfile
- Docker Compose for local dev
- Health checks and graceful shutdown
- **Effort**: 2 days

---

## File Structure

```
agents/ml/production/
├── api_server.py                    # Story 4.1
├── batch_predictor.py               # Story 4.2
├── model_loader.py                  # Story 4.3
├── schemas.py                       # Pydantic models (Story 4.1)
└── config.py                        # Configuration

docker/
├── Dockerfile                       # Story 4.5
├── docker-compose.yml               # Story 4.5
└── .dockerignore

tests/integration/
├── test_api_endpoints.py            # Story 4.4
├── test_batch_pipeline.py           # Story 4.2
└── test_docker_deployment.py        # Story 4.5

docs/
└── api/
    └── openapi.yaml                 # Auto-generated (Story 4.4)
```

---

## Story 4.1: FastAPI Prediction Endpoint

**Story ID:** EPIC4-S1
**Priority:** P0
**Estimated Effort:** 3 days
**Dependencies:** EPIC-3 (Model Registry, Model Evaluator)

### User Story

**As a** Trading System,
**I want** REST API endpoints to get real-time upper circuit predictions,
**so that** I can integrate ML predictions into automated trading workflows.

### Acceptance Criteria

**AC4.1.1:** FastAPI application with structured endpoints
- File: `/Users/srijan/Desktop/aksh/agents/ml/production/api_server.py`
- Endpoints:
  - `POST /api/v1/predict` - Single stock prediction
  - `POST /api/v1/batch_predict` - Multiple stocks (max 100)
  - `GET /api/v1/health` - Health check
  - `GET /api/v1/models` - List available models
  - `POST /api/v1/models/reload` - Reload models (admin)
- CORS enabled for web dashboard integration
- Structured logging with correlation IDs

**AC4.1.2:** Pydantic request/response schemas
- File: `/Users/srijan/Desktop/aksh/agents/ml/production/schemas.py`
- Request schema:
```python
class PredictionRequest(BaseModel):
    bse_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]+$")
    nse_symbol: Optional[str] = None
    prediction_date: str = Field(..., description="ISO format: YYYY-MM-DD")
    include_features: bool = False  # Return feature values
    include_shap: bool = False      # Return SHAP explanations

class BatchPredictionRequest(BaseModel):
    predictions: List[PredictionRequest] = Field(..., max_items=100)
```
- Response schema:
```python
class PredictionResponse(BaseModel):
    bse_code: str
    nse_symbol: str
    prediction_date: str
    predicted_label: int              # 0 or 1
    probability: float                # 0.0 to 1.0
    confidence: str                   # "LOW", "MEDIUM", "HIGH"
    model_version: str
    prediction_timestamp: str         # ISO timestamp
    features: Optional[Dict[str, float]] = None
    shap_values: Optional[Dict[str, float]] = None
```
- Validation: BSE code format, date format, probability bounds

**AC4.1.3:** Feature extraction integration
- Import from Epic 2 feature extractors:
```python
from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor
from agents.ml.financial_feature_extractor import FinancialFeatureExtractor
from agents.ml.sentiment_feature_extractor import SentimentFeatureExtractor
from agents.ml.seasonality_feature_extractor import SeasonalityFeatureExtractor
```
- Extract 25 features for given stock and date
- Handle missing data gracefully (impute with median/mean)
- Cache feature extraction results (5-minute TTL)
- If feature extraction fails: Return HTTP 422 with error details

**AC4.1.4:** Model prediction with error handling
- Load best model from registry (Epic 3)
- Predict probability: `model.predict_proba(features)[:, 1]`
- Convert to label: `label = 1 if probability >= 0.5 else 0`
- Confidence levels:
  - HIGH: `0.7 <= probability <= 1.0` or `0.0 <= probability <= 0.3`
  - MEDIUM: `0.5 <= probability < 0.7` or `0.3 < probability < 0.5`
  - LOW: Near decision boundary (0.45-0.55)
- If prediction fails: Return HTTP 500 with error, log stack trace

**AC4.1.5:** Performance targets
- **Latency**: p95 < 100ms for `/predict` endpoint
  - Feature extraction: <50ms
  - Model prediction: <30ms
  - Response serialization: <20ms
- **Throughput**: ≥100 requests/second on single core
- Use async/await for I/O operations (DB queries)
- Connection pooling for database access

**AC4.1.6:** Health check endpoint
- `GET /api/v1/health` returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:30:00Z",
  "model_loaded": true,
  "model_version": "1.2.0",
  "model_type": "XGBoost",
  "uptime_seconds": 3600,
  "requests_processed": 15432,
  "avg_latency_ms": 45.3,
  "error_rate": 0.002
}
```
- Status codes: 200 (healthy), 503 (model not loaded or DB unavailable)

**AC4.1.7:** Error handling and validation
- HTTP 400: Invalid request format (wrong BSE code, bad date)
- HTTP 404: Stock not found in database
- HTTP 422: Feature extraction failed (missing data)
- HTTP 429: Rate limit exceeded (100 req/sec per IP)
- HTTP 500: Internal server error
- All errors return structured JSON:
```json
{
  "error": "FEATURE_EXTRACTION_FAILED",
  "message": "Missing financial data for Q3 2024",
  "bse_code": "500325",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/production/api_server.py`

**Key Components:**
```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="VCP Upper Circuit Prediction API",
    description="ML API for predicting upper circuit movements",
    version="1.0.0"
)

class PredictionService:
    def __init__(self, model_registry_path: str, feature_dbs: Dict[str, str]):
        """Initialize with model registry and feature databases"""
        
    async def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        """Predict for single stock"""
        
    async def predict_batch(self, request: BatchPredictionRequest) -> List[PredictionResponse]:
        """Predict for multiple stocks in parallel"""
        
    async def extract_features(self, bse_code: str, date: str) -> Dict[str, float]:
        """Extract 25 features for given stock and date"""
        
    async def get_health_status(self) -> HealthResponse:
        """Return API health metrics"""

@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, service: PredictionService = Depends()):
    """Single stock prediction endpoint"""

@app.post("/api/v1/batch_predict", response_model=List[PredictionResponse])
async def batch_predict(request: BatchPredictionRequest, service: PredictionService = Depends()):
    """Batch prediction endpoint"""

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
```

**Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Request/response validation
- `prometheus-client` - Metrics (optional)

**Test File:** `tests/integration/test_api_endpoints.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Integration tests achieving ≥90% coverage
- [ ] Load test: 100 req/sec sustained for 5 minutes
- [ ] Latency benchmark: p95 < 100ms verified
- [ ] Manual test: Predict RELIANCE.NS for 2024-11-14
- [ ] Code review: Passes ruff linter, mypy type checking
- [ ] Documentation: API endpoints documented with examples

---

## Story 4.2: Batch Prediction Pipeline

**Story ID:** EPIC4-S2
**Priority:** P0
**Estimated Effort:** 3 days
**Dependencies:** EPIC4-S1 (API Server for feature extraction logic)

### User Story

**As a** Research Analyst,
**I want** daily batch predictions for all NSE/BSE stocks,
**so that** I can identify high-probability upper circuit candidates for next earnings.

### Acceptance Criteria

**AC4.2.1:** BatchPredictor class with parallel processing
- File: `/Users/srijan/Desktop/aksh/agents/ml/production/batch_predictor.py`
- Class: `BatchPredictor` with method: `predict_all_stocks(date: str, output_path: str) -> BatchReport`
- Use `multiprocessing.Pool` for parallel feature extraction
- Workers: `cpu_count() - 1` (leave 1 core for system)
- Batch size: 100 stocks per worker
- Progress bar: tqdm for visual feedback

**AC4.2.2:** Fetch all active stocks from master list
- Query: `SELECT bse_code, nse_symbol, company_name FROM master_stock_list WHERE status='ACTIVE'`
- Expected: ~11,000 active stocks
- Filter: Only stocks with earnings in next 30 days (optional high-priority mode)
- Sort: By market cap descending (prioritize large caps)

**AC4.2.3:** Extract features for all stocks
- Reuse feature extractors from Epic 2
- Handle missing data per stock:
  - If financial data missing: Use industry median
  - If price data missing: Skip stock, log to `skipped_stocks.csv`
  - If >50% features missing: Skip stock
- Cache feature matrices in memory (LRU cache, max 1000 stocks)

**AC4.2.4:** Batch predict with loaded model
- Load best model once at start (not per stock)
- Predict in batches of 1,000 stocks
- Output: `(bse_code, probability, label, confidence, model_version)`
- Sort by probability descending

**AC4.2.5:** Save predictions to database and CSV
- Database: `predictions.db`
- Schema:
```sql
CREATE TABLE IF NOT EXISTS daily_predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bse_code TEXT NOT NULL,
    nse_symbol TEXT,
    company_name TEXT,
    prediction_date DATE NOT NULL,
    predicted_label INTEGER NOT NULL CHECK(predicted_label IN (0, 1)),
    probability REAL NOT NULL CHECK(probability BETWEEN 0 AND 1),
    confidence TEXT CHECK(confidence IN ('LOW', 'MEDIUM', 'HIGH')),
    model_version TEXT,
    model_type TEXT,
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(bse_code, prediction_date, model_version)
);
CREATE INDEX idx_date_prob ON daily_predictions(prediction_date, probability DESC);
CREATE INDEX idx_bse_date ON daily_predictions(bse_code, prediction_date);
```
- CSV: `/Users/srijan/Desktop/aksh/data/predictions/predictions_{YYYY-MM-DD}.csv`
- CSV columns: `bse_code, nse_symbol, company_name, probability, label, confidence, market_cap_cr`

**AC4.2.6:** Generate batch prediction report
- Report format:
```
========================================
BATCH PREDICTION REPORT
========================================
Date: 2025-11-14
Model: XGBoost v1.2.0 (F1: 0.72)
Duration: 8m 23s

SUMMARY:
- Total Stocks Processed: 10,856
- Stocks Skipped: 144 (1.3%)
- Predicted Upper Circuit: 423 (3.9%)
- High Confidence: 127 (1.2%)
- Medium Confidence: 189 (1.7%)
- Low Confidence: 107 (1.0%)

TOP 20 PREDICTIONS:
Rank | BSE Code | NSE Symbol | Company Name        | Probability | Confidence
-----|----------|------------|---------------------|-------------|------------
1    | 532978   | TATAMOTORS | TATA MOTORS LTD     | 0.89        | HIGH
2    | 500325   | RELIANCE   | RELIANCE IND LTD    | 0.87        | HIGH
...

PERFORMANCE:
- Feature Extraction: 6m 12s (avg 34ms/stock)
- Model Prediction: 1m 48s (avg 10ms/stock)
- Database Write: 23s
- Throughput: 21.6 stocks/second

OUTPUT FILES:
- Database: predictions.db (10,856 rows inserted)
- CSV: predictions_2025-11-14.csv (10,856 rows)
- Skipped: skipped_stocks_2025-11-14.csv (144 rows)

========================================
```
- Save to: `/Users/srijan/Desktop/aksh/data/predictions/report_{YYYY-MM-DD}.txt`

**AC4.2.7:** Performance targets
- **Total time**: Process 11,000 stocks in <10 minutes
- **Throughput**: ≥18 stocks/second
- **Memory**: <4GB RAM usage
- **CPU**: Utilize all available cores efficiently
- Error rate: <2% (failures due to missing data)

**AC4.2.8:** Scheduling and automation
- CLI command: `python -m agents.ml.production.batch_predictor --date 2025-11-14`
- Cron job support: Daily at 7:00 AM IST (before market open)
- Email notification on completion (optional)
- Slack webhook for high-confidence predictions (optional)

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/production/batch_predictor.py`

**Key Components:**
```python
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import pandas as pd

class BatchPredictor:
    def __init__(
        self,
        model_registry_path: str,
        feature_dbs: Dict[str, str],
        output_dir: str
    ):
        """Initialize batch predictor"""
        
    def predict_all_stocks(self, date: str, output_path: str) -> BatchReport:
        """Main batch prediction pipeline"""
        
    def fetch_active_stocks(self) -> pd.DataFrame:
        """Get all active stocks from master list"""
        
    def extract_features_parallel(
        self,
        stocks: List[str],
        date: str,
        n_workers: int = cpu_count() - 1
    ) -> pd.DataFrame:
        """Extract features in parallel"""
        
    def predict_batch(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Predict for batch of stocks"""
        
    def save_predictions(
        self,
        predictions_df: pd.DataFrame,
        date: str
    ) -> Tuple[int, int]:
        """Save to DB and CSV, return (db_rows, csv_rows)"""
        
    def generate_report(
        self,
        predictions_df: pd.DataFrame,
        duration_seconds: float,
        date: str
    ) -> BatchReport:
        """Generate batch prediction report"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    
    predictor = BatchPredictor(...)
    report = predictor.predict_all_stocks(args.date, ...)
    print(report)
```

**Dependencies:**
- `multiprocessing` - Parallel processing
- `tqdm` - Progress bar
- `pandas` - Data manipulation
- `sqlite3` - Database operations

**Test File:** `tests/integration/test_batch_pipeline.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 8 acceptance criteria passing
- [ ] Integration test: Batch predict 100 stocks
- [ ] Performance test: 11,000 stocks in <10 minutes
- [ ] Memory test: <4GB RAM usage verified
- [ ] Manual test: Run batch prediction for 2024-11-14
- [ ] Cron job setup documented
- [ ] Code review: Passes linter, type checking

---

## Story 4.3: Model Loading & Caching

**Story ID:** EPIC4-S3
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S1 (API Server)

### User Story

**As a** Production System,
**I want** efficient model loading with caching and version management,
**so that** API latency stays <100ms and model updates don't cause downtime.

### Acceptance Criteria

**AC4.3.1:** ModelLoader class with LRU caching
- File: `/Users/srijan/Desktop/aksh/agents/ml/production/model_loader.py`
- Class: `ModelLoader` with caching decorator
- LRU cache: Keep 3 most recent models in memory
- Cache key: `(model_type, version)`
- Memory limit: <1GB per model

**AC4.3.2:** Lazy loading on first request
- Model not loaded on server startup (cold start <2s)
- Load on first `/predict` request
- Loading time: <5 seconds
- While loading: Return HTTP 503 "Model loading, retry in 5s"
- Once loaded: Cache in memory, subsequent requests use cached model

**AC4.3.3:** Hot reload without downtime
- Endpoint: `POST /api/v1/models/reload`
- Load new model version in background thread
- Atomic swap: Old model → New model
- During swap: Continue serving with old model
- After swap: Old model evicted from cache after 60s grace period

**AC4.3.4:** Version pinning and fallback
- Config: `PREFERRED_MODEL_VERSION=1.2.0`
- If preferred version fails to load: Fallback to latest stable
- If all versions fail: Return HTTP 503
- Log fallback events to `model_load_errors.log`

**AC4.3.5:** Model metadata caching
- Cache model metadata (version, F1, ROC-AUC, features) separately
- Metadata endpoint: `GET /api/v1/models` returns metadata without loading full model
- TTL: 5 minutes for metadata cache

**AC4.3.6:** Performance monitoring
- Track: Load time, cache hit rate, memory usage
- Metrics:
  - `model_load_time_seconds` (histogram)
  - `model_cache_hit_rate` (counter)
  - `model_memory_bytes` (gauge)
- Expose via `/metrics` endpoint (Prometheus format)

**AC4.3.7:** Graceful degradation
- If model loading fails: Log error, retry 3x with exponential backoff
- If retries exhausted: Fall back to previous version
- If no version available: Return HTTP 503 with clear error message

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/production/model_loader.py`

**Key Components:**
```python
from functools import lru_cache
from threading import Lock
import joblib

class ModelLoader:
    def __init__(self, registry_path: str, cache_size: int = 3):
        """Initialize model loader with LRU cache"""
        self._cache = {}
        self._lock = Lock()
        self._registry = ModelRegistry(registry_path)
        
    @lru_cache(maxsize=3)
    def load_model(self, model_type: str, version: Optional[str] = None):
        """
        Load model from registry with caching.
        
        Args:
            model_type: "XGBoost", "LightGBM", etc.
            version: Specific version or None for latest
            
        Returns:
            Loaded model object
            
        Raises:
            ModelLoadError: If model loading fails
        """
        
    def load_model_async(self, model_type: str, version: str):
        """Load model in background thread"""
        
    def reload_models(self) -> Dict[str, str]:
        """Hot reload all cached models"""
        
    def get_model_metadata(self, model_type: str) -> Dict[str, Any]:
        """Get metadata without loading full model"""
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache hit rate, memory usage, etc."""
```

**Dependencies:**
- `functools.lru_cache` - Caching
- `joblib` - Model deserialization
- `threading` - Background loading

**Test File:** `tests/unit/test_model_loader.py`

**Test Coverage Requirements:** ≥90%

### Definition of Done

- [ ] Code implemented following TDD
- [ ] All 7 acceptance criteria passing
- [ ] Unit tests achieving ≥90% coverage
- [ ] Load test: 1000 predictions with cache hit rate >95%
- [ ] Hot reload test: Zero downtime during model swap
- [ ] Memory test: 3 cached models use <3GB RAM
- [ ] Code review: Passes linter, type checking

---

## Story 4.4: API Documentation & Testing

**Story ID:** EPIC4-S4
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S1 (API Server), EPIC4-S2 (Batch Predictor)

### User Story

**As a** API Consumer,
**I want** comprehensive API documentation and automated tests,
**so that** I can integrate the prediction API confidently.

### Acceptance Criteria

**AC4.4.1:** OpenAPI/Swagger auto-documentation
- FastAPI auto-generates OpenAPI spec at `/docs`
- Swagger UI at `/docs`, ReDoc at `/redoc`
- All endpoints documented with:
  - Description
  - Request schema with examples
  - Response schema with examples
  - Error codes and messages

**AC4.4.2:** Example requests and responses
- Example request for `/predict`:
```json
{
  "bse_code": "500325",
  "nse_symbol": "RELIANCE",
  "prediction_date": "2025-11-14",
  "include_features": true,
  "include_shap": false
}
```
- Example response:
```json
{
  "bse_code": "500325",
  "nse_symbol": "RELIANCE",
  "prediction_date": "2025-11-14",
  "predicted_label": 1,
  "probability": 0.87,
  "confidence": "HIGH",
  "model_version": "1.2.0",
  "prediction_timestamp": "2025-11-14T10:30:00Z",
  "features": {
    "revenue_growth_yoy": 0.23,
    "npm_trend": 0.15,
    ...
  }
}
```

**AC4.4.3:** Integration tests for all endpoints
- File: `tests/integration/test_api_endpoints.py`
- Test cases:
  - `test_predict_single_stock_success` - Valid request → 200 OK
  - `test_predict_invalid_bse_code` - Invalid BSE code → 400 Bad Request
  - `test_predict_stock_not_found` - Stock not in DB → 404 Not Found
  - `test_predict_missing_features` - Missing data → 422 Unprocessable Entity
  - `test_batch_predict_100_stocks` - Batch request → 200 OK with 100 results
  - `test_health_endpoint` - Health check → 200 OK
  - `test_models_endpoint` - List models → 200 OK
  - `test_rate_limiting` - 101 requests/sec → 429 Too Many Requests
- Coverage: ≥95% for api_server.py

**AC4.4.4:** Load testing with Locust
- File: `tests/load/locustfile.py`
- Simulate: 100 concurrent users, 1000 requests total
- Target: p95 latency <100ms, error rate <1%
- Test scenarios:
  - Steady load: 50 req/sec for 5 minutes
  - Spike: 0→200 req/sec in 10 seconds
  - Sustained: 100 req/sec for 10 minutes

**AC4.4.5:** Contract testing
- Use `pytest` with `requests` library
- Mock external dependencies (databases, yfinance)
- Test schema validation strictly
- Test backward compatibility (old API versions)

**AC4.4.6:** Performance benchmarks
- Benchmark script: `tests/benchmarks/benchmark_api.py`
- Measure:
  - Single prediction latency (p50, p95, p99)
  - Batch prediction throughput
  - Cache hit rate impact on latency
- Generate report: `benchmarks_{YYYY-MM-DD}.txt`

**AC4.4.7:** CI/CD integration tests
- Run tests on every commit
- Test matrix: Python 3.9, 3.10, 3.11
- Fail build if test coverage <90%
- Fail build if p95 latency >150ms (with buffer)

### Technical Specifications

**Test Files:**
- `tests/integration/test_api_endpoints.py`
- `tests/load/locustfile.py`
- `tests/benchmarks/benchmark_api.py`

**Key Test Components:**
```python
from fastapi.testclient import TestClient
from locust import HttpUser, task, between

# Integration Tests
class TestPredictionAPI:
    def test_predict_single_stock_success(self, client: TestClient):
        """Test successful single stock prediction"""
        response = client.post("/api/v1/predict", json={
            "bse_code": "500325",
            "prediction_date": "2025-11-14"
        })
        assert response.status_code == 200
        assert "probability" in response.json()

# Load Tests
class PredictionUser(HttpUser):
    wait_time = between(1, 2)
    
    @task
    def predict_random_stock(self):
        """Simulate user predicting random stock"""
        self.client.post("/api/v1/predict", json={...})
```

**Dependencies:**
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `locust` - Load testing
- `requests` - HTTP client

**Test Coverage Requirements:** ≥95% for API code

### Definition of Done

- [ ] OpenAPI docs accessible at /docs
- [ ] All integration tests passing
- [ ] Load test: 100 req/sec sustained with p95 <100ms
- [ ] Contract tests: Schema validation strict
- [ ] Benchmark report generated
- [ ] CI/CD pipeline configured
- [ ] Code review: All tests reviewed

---

## Story 4.5: Docker Containerization

**Story ID:** EPIC4-S5
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC4-S1 (API Server), EPIC4-S3 (Model Loader)

### User Story

**As a** DevOps Engineer,
**I want** Docker containers for the ML API,
**so that** I can deploy to any environment consistently.

### Acceptance Criteria

**AC4.5.1:** Multi-stage Dockerfile for optimization
- File: `/Users/srijan/Desktop/aksh/docker/Dockerfile`
- Stage 1 (builder): Install dependencies, compile libraries
- Stage 2 (runtime): Copy artifacts, minimal runtime image
- Base image: `python:3.10-slim` (smaller than full Python)
- Final image size: <500MB

**AC4.5.2:** Dockerfile best practices
- Use `.dockerignore` to exclude unnecessary files
- Layer caching: Copy requirements.txt first, then code
- Non-root user: Run as `mluser` (UID 1000)
- Health check: `HEALTHCHECK CMD curl -f http://localhost:8000/api/v1/health`
- Graceful shutdown: Handle SIGTERM

**AC4.5.3:** Docker Compose for local development
- File: `/Users/srijan/Desktop/aksh/docker/docker-compose.yml`
- Services:
  - `api`: FastAPI server (port 8000)
  - `db`: SQLite mounted as volume (or PostgreSQL for production)
  - `redis`: Cache (optional)
- Volumes: Mount `/data` for models and databases
- Networks: Internal network for service communication

**AC4.5.4:** Environment configuration
- Use `.env` file for configuration
- Environment variables:
  - `MODEL_REGISTRY_PATH=/data/models/registry`
  - `FEATURE_DBS_PATH=/data/features`
  - `LOG_LEVEL=INFO`
  - `API_PORT=8000`
  - `WORKERS=4` (for Gunicorn/Uvicorn)
- Config validation on startup

**AC4.5.5:** Container startup and health checks
- Startup time: <30 seconds (cold start)
- Health check interval: 30s
- Retry: 3 attempts before marking unhealthy
- Readiness probe: Wait for model to load
- Liveness probe: Check /health endpoint every 30s

**AC4.5.6:** Logging and monitoring
- Structured JSON logs to stdout/stderr
- Log rotation: Not needed (Docker handles this)
- Metrics: Expose Prometheus metrics at `/metrics`
- Trace IDs: Include in all log entries

**AC4.5.7:** Production deployment configuration
- Use Gunicorn with Uvicorn workers
- Workers: `2 * cpu_count() + 1`
- Worker timeout: 120 seconds
- Max requests per worker: 1000 (restart after)
- Graceful shutdown: 30 second timeout

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/docker/Dockerfile`

```dockerfile
# Stage 1: Builder
FROM python:3.10-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim

# Create non-root user
RUN useradd -m -u 1000 mluser

# Copy dependencies from builder
COPY --from=builder /root/.local /home/mluser/.local
ENV PATH=/home/mluser/.local/bin:$PATH

# Copy application code
WORKDIR /app
COPY agents/ ./agents/
COPY data/ ./data/

# Set ownership
RUN chown -R mluser:mluser /app

# Switch to non-root user
USER mluser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "agents.ml.production.api_server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**File:** `/Users/srijan/Desktop/aksh/docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ../data:/app/data
    environment:
      - MODEL_REGISTRY_PATH=/app/data/models/registry
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 3s
      retries: 3
    restart: unless-stopped
```

**Dependencies:**
- Docker 20.10+
- Docker Compose 2.0+

**Test File:** `tests/integration/test_docker_deployment.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] Dockerfile created with multi-stage build
- [ ] Docker Compose file created
- [ ] .dockerignore configured
- [ ] Image builds successfully: `docker build -t vcp-ml-api .`
- [ ] Image size <500MB verified
- [ ] Container starts in <30 seconds
- [ ] Health check passes after startup
- [ ] Integration test: API accessible via Docker
- [ ] Documentation: Docker deployment guide

---

## Epic Completion Criteria

All 5 stories (EPIC4-S1 through EPIC4-S5) must meet Definition of Done:

- [ ] All acceptance criteria passing for all stories
- [ ] ≥90% unit test coverage across production code
- [ ] Integration tests passing: Full API + Batch + Docker
- [ ] Performance validated: <100ms p95 latency, 11K stocks in <10 min
- [ ] Load test: 100 req/sec sustained for 10 minutes
- [ ] Docker image builds and runs successfully
- [ ] Deliverables exist:
  - `agents/ml/production/api_server.py` (FastAPI app)
  - `agents/ml/production/batch_predictor.py` (Batch pipeline)
  - `agents/ml/production/model_loader.py` (Model caching)
  - `docker/Dockerfile` (Container image)
  - `docker/docker-compose.yml` (Local deployment)
  - OpenAPI docs at `/docs`

**Ready for Epic 5:** Monitoring & Alerts

---

**Total Duration**: 12 days + 2 day buffer = 14 days
**Next Epic**: Epic 5 - Monitoring & Alerts

**Author**: VCP Financial Research Team
**Created**: 2025-11-14

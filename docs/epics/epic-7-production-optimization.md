# Epic 7: Production Optimization

**Epic ID**: EPIC-7
**Priority**: P1 (Performance)
**Status**: Ready to Start
**Estimated Effort**: 10 days (12 days with buffer)
**Dependencies**: EPIC-4 (Production Deployment), EPIC-5 (Monitoring) - COMPLETE ✅

---

## Epic Goal

Optimize production ML system for speed, scalability, and cost-efficiency. Target: Reduce API latency from 100ms to <50ms p95, process 11,000 stocks in <5 minutes (down from 10 min), reduce database query time by 60%, implement intelligent caching to cut redundant computations by 80%.

---

## Success Criteria

1. **API Latency**: p95 < 50ms (down from 100ms baseline)
2. **Batch Throughput**: 11,000 stocks in <5 minutes (36+ stocks/sec, up from 18/sec)
3. **Database Performance**: Query time reduced by 60%
4. **Cache Hit Rate**: ≥80% for feature extraction
5. **Cost Reduction**: 40% reduction in compute time (faster = cheaper)
6. **Load Testing**: Handle 500 req/sec sustained (up from 100 req/sec)

---

## Stories (5 total)

### Story 7.1: Feature Computation Optimization
- Vectorize calculations with NumPy
- Batch database queries
- Precompute static features
- **Effort**: 2 days

### Story 7.2: Model Inference Optimization
- ONNX Runtime for faster inference
- Batch prediction optimization
- Quantization for smaller models
- **Effort**: 2 days

### Story 7.3: Database Query Optimization
- Add indexes to all foreign keys
- Query result caching (Redis)
- Connection pooling
- **Effort**: 2 days

### Story 7.4: Caching Strategy
- Redis for feature cache (5-min TTL)
- LRU cache for model predictions
- CDN for static assets
- **Effort**: 2 days

### Story 7.5: Load Testing & Scaling
- Locust load tests (500 req/sec)
- Horizontal scaling with load balancer
- Auto-scaling configuration
- **Effort**: 2 days

---

## File Structure

```
agents/ml/optimization/
├── feature_optimizer.py             # Story 7.1
├── inference_optimizer.py           # Story 7.2
├── db_optimizer.py                  # Story 7.3
├── cache_manager.py                 # Story 7.4
└── load_tester.py                   # Story 7.5

config/
├── redis.conf                       # Story 7.4
└── nginx_load_balancer.conf         # Story 7.5

tests/performance/
├── test_feature_optimization.py
├── test_inference_speed.py
├── test_db_performance.py
├── test_cache_hit_rate.py
└── test_load_scaling.py
```

---

## Story 7.1: Feature Computation Optimization

**Story ID:** EPIC7-S1
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC-2 (Feature Engineering)

### User Story

**As a** Performance Engineer,
**I want** faster feature computation through vectorization and batching,
**so that** batch predictions complete in <5 minutes instead of 10 minutes.

### Acceptance Criteria

**AC7.1.1:** FeatureOptimizer class to replace slow feature extractors
- File: `/Users/srijan/Desktop/aksh/agents/ml/optimization/feature_optimizer.py`
- Class: `FeatureOptimizer` with vectorized implementations
- Replace loops with NumPy array operations
- Target: 3x speedup (from 34ms/stock to <12ms/stock)

**AC7.1.2:** Vectorize technical indicator calculations
- Current: `for stock in stocks: calculate_rsi(stock)`
- Optimized: `rsi_values = calculate_rsi_vectorized(price_array)`
- Use pandas rolling windows: `df['rsi'] = df['close'].rolling(14).apply(rsi_formula)`
- Use TA-Lib (C library) instead of pure Python: `import talib; talib.RSI(close, 14)`
- Expected: 5x speedup for RSI, MACD, Bollinger Bands

**AC7.1.3:** Batch database queries
- Current: 11,000 individual queries for price data
- Optimized: 1 query with `WHERE bse_code IN (...)` for all stocks
- Load all price data into memory, then vectorize calculations
- Expected: 10x speedup for database fetches

**AC7.1.4:** Precompute static features
- Identify: Features that don't change daily (e.g., company sector, market cap tier)
- Precompute: Once per month, store in `static_features.db`
- Runtime: Load from cache instead of recalculating
- Expected: 20% reduction in feature computation time

**AC7.1.5:** Parallel feature extraction for independent features
- Identify: Independent feature groups (technical, financial, sentiment)
- Use `multiprocessing.Pool` to compute groups in parallel
- Workers: `cpu_count() - 1`
- Expected: 2x speedup on multi-core systems

**AC7.1.6:** Benchmark before and after optimization
- Benchmark script: `tests/performance/test_feature_optimization.py`
- Metrics:
  - Time to compute 25 features for 1 stock
  - Time to compute features for 11,000 stocks (batch)
  - Memory usage
- Results table:
```
Feature Type      | Before  | After   | Speedup
------------------|---------|---------|----------
RSI (1 stock)     | 5ms     | 1ms     | 5x
MACD (1 stock)    | 8ms     | 1.5ms   | 5.3x
Financial (1)     | 12ms    | 4ms     | 3x
All 25 (1 stock)  | 34ms    | 12ms    | 2.8x
Batch 11K stocks  | 6m 12s  | 2m 10s  | 2.9x
```

**AC7.1.7:** Maintain accuracy (no precision loss)
- Test: Compare optimized vs original feature values
- Tolerance: <0.01% difference (floating point rounding acceptable)
- Validation: Run on 1,000 random stocks, verify all features match

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/optimization/feature_optimizer.py`

**Key Components:**
```python
import numpy as np
import pandas as pd
import talib

class FeatureOptimizer:
    def __init__(self, cache_enabled: bool = True):
        """Initialize feature optimizer with caching"""
        self.static_features_cache = {}
        
    def calculate_rsi_vectorized(
        self,
        close_prices: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """
        Vectorized RSI calculation using TA-Lib.
        
        Args:
            close_prices: Array of closing prices
            period: RSI period (default: 14)
            
        Returns:
            Array of RSI values
        """
        return talib.RSI(close_prices, timeperiod=period)
        
    def batch_extract_features(
        self,
        bse_codes: List[str],
        date: str
    ) -> pd.DataFrame:
        """
        Extract features for multiple stocks in batch.
        
        Args:
            bse_codes: List of BSE codes
            date: Prediction date
            
        Returns:
            DataFrame with (bse_code, feature1, feature2, ...)
        """
        # Load all price data in one query
        price_data = self._batch_load_price_data(bse_codes, date)
        
        # Vectorize technical indicators
        price_data['rsi_14'] = self.calculate_rsi_vectorized(price_data['close'])
        price_data['macd'], price_data['macd_signal'], _ = talib.MACD(
            price_data['close']
        )
        
        # Load static features from cache
        static_features = self._load_static_features(bse_codes)
        
        # Merge
        return price_data.merge(static_features, on='bse_code')
        
    def _batch_load_price_data(
        self,
        bse_codes: List[str],
        date: str
    ) -> pd.DataFrame:
        """Load price data for all stocks in single query"""
        query = f"""
        SELECT bse_code, date, open, high, low, close, volume
        FROM price_movements
        WHERE bse_code IN ({','.join(['?']*len(bse_codes))})
          AND date <= ?
        ORDER BY bse_code, date
        """
        return pd.read_sql(query, self.conn, params=bse_codes + [date])
        
    def _load_static_features(
        self,
        bse_codes: List[str]
    ) -> pd.DataFrame:
        """Load precomputed static features"""
        # Check cache first
        if self.static_features_cache:
            return self.static_features_cache[self.static_features_cache['bse_code'].isin(bse_codes)]
        
        # Load from DB and cache
        query = "SELECT * FROM static_features WHERE bse_code IN (...)"
        self.static_features_cache = pd.read_sql(query, self.conn)
        return self.static_features_cache
```

**Dependencies:**
- `talib` - Technical analysis library (C-based, fast)
- `numpy` - Vectorized operations
- `pandas` - Batch data manipulation

**Test File:** `tests/performance/test_feature_optimization.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] Code implemented with benchmarks
- [ ] All 7 acceptance criteria passing
- [ ] Performance tests verify 2.8x speedup
- [ ] Accuracy tests: <0.01% difference from original
- [ ] Integration test: Batch extract 11,000 stocks in <2m 10s
- [ ] Memory test: <4GB RAM usage
- [ ] Documentation: Optimization techniques explained

---

## Story 7.2: Model Inference Optimization

**Story ID:** EPIC7-S2
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC-3 (Model Training)

### User Story

**As a** API Developer,
**I want** faster model inference through ONNX and batching,
**so that** API latency drops from 100ms to <50ms p95.

### Acceptance Criteria

**AC7.2.1:** Convert models to ONNX format
- File: `/Users/srijan/Desktop/aksh/agents/ml/optimization/inference_optimizer.py`
- Convert XGBoost/LightGBM to ONNX: `onnxmltools.convert_xgboost(...)`
- Save ONNX models to `data/models/onnx/`
- Load with ONNX Runtime: `ort.InferenceSession(model_path)`
- Expected: 2-3x speedup for inference

**AC7.2.2:** Batch prediction optimization
- Current: Predict 1 stock at a time
- Optimized: Predict batches of 100 stocks
- ONNX Runtime supports batching natively
- Expected: 5x speedup for batch predictions

**AC7.2.3:** Model quantization for smaller size
- Quantize: Float32 → Int8 (8-bit integers)
- Use: `onnxruntime.quantization.quantize_dynamic(...)`
- Expected: 4x smaller model size, 1.5x faster inference
- Validate: Ensure <1% F1 degradation after quantization

**AC7.2.4:** GPU acceleration (optional, if available)
- ONNX Runtime supports CUDA for GPU inference
- Check GPU availability: `ort.get_available_providers()`
- If GPU available: Use `providers=['CUDAExecutionProvider']`
- Expected: 10x speedup on GPU vs CPU

**AC7.2.5:** Inference profiling and bottleneck analysis
- Profile: Time spent in feature extraction vs model inference
- Tool: `cProfile` or `line_profiler`
- Identify: Slowest operations in inference pipeline
- Optimize: Top 3 bottlenecks

**AC7.2.6:** Benchmark before and after optimization
- Metrics:
  - Single prediction latency (p50, p95, p99)
  - Batch prediction throughput (predictions/sec)
  - Model file size (MB)
- Results table:
```
Model Format    | Size   | Latency (p95) | Throughput  | Speedup
----------------|--------|---------------|-------------|----------
XGBoost PKL     | 45 MB  | 30ms          | 33 pred/s   | 1x
ONNX FP32       | 38 MB  | 12ms          | 83 pred/s   | 2.5x
ONNX INT8       | 10 MB  | 8ms           | 125 pred/s  | 3.75x
ONNX GPU        | 10 MB  | 2ms           | 500 pred/s  | 15x
```

**AC7.2.7:** Maintain accuracy (minimal degradation)
- Test: ONNX model predictions vs original model
- Tolerance: F1 difference ≤1%
- Quantized model: F1 difference ≤2%
- Validation: Run on 10,000 test samples

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/optimization/inference_optimizer.py`

**Key Components:**
```python
import onnxruntime as ort
import onnxmltools
from onnxruntime.quantization import quantize_dynamic, QuantType

class InferenceOptimizer:
    def __init__(self, model_registry_path: str):
        """Initialize inference optimizer"""
        
    def convert_to_onnx(
        self,
        model,
        model_type: str,
        output_path: str
    ):
        """
        Convert XGBoost/LightGBM to ONNX.
        
        Args:
            model: Trained model object
            model_type: "XGBoost", "LightGBM", etc.
            output_path: Where to save ONNX model
        """
        if model_type == "XGBoost":
            onnx_model = onnxmltools.convert_xgboost(model)
        elif model_type == "LightGBM":
            onnx_model = onnxmltools.convert_lightgbm(model)
        
        onnxmltools.utils.save_model(onnx_model, output_path)
        
    def quantize_onnx_model(
        self,
        onnx_model_path: str,
        output_path: str
    ):
        """Quantize ONNX model from FP32 to INT8"""
        quantize_dynamic(
            onnx_model_path,
            output_path,
            weight_type=QuantType.QInt8
        )
        
    def load_onnx_model(
        self,
        model_path: str,
        use_gpu: bool = False
    ) -> ort.InferenceSession:
        """Load ONNX model with ONNX Runtime"""
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if use_gpu else ['CPUExecutionProvider']
        return ort.InferenceSession(model_path, providers=providers)
        
    def predict_batch_onnx(
        self,
        session: ort.InferenceSession,
        features: np.ndarray
    ) -> np.ndarray:
        """Batch prediction with ONNX Runtime"""
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        return session.run([output_name], {input_name: features})[0]
        
    def benchmark_inference(
        self,
        model_paths: Dict[str, str],
        test_features: np.ndarray
    ) -> pd.DataFrame:
        """Benchmark different model formats"""
        results = []
        for name, path in model_paths.items():
            # Time inference
            start = time.time()
            predictions = self.predict_batch_onnx(...)
            duration = time.time() - start
            
            results.append({
                'model': name,
                'latency_ms': duration * 1000,
                'throughput': len(test_features) / duration
            })
        return pd.DataFrame(results)
```

**Dependencies:**
- `onnxruntime` - ONNX Runtime
- `onnxmltools` - Model conversion
- `skl2onnx` - Scikit-learn to ONNX

**Test File:** `tests/performance/test_inference_speed.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] ONNX conversion implemented
- [ ] All 7 acceptance criteria passing
- [ ] Performance tests verify 2.5x speedup (FP32)
- [ ] Quantization: 3.75x speedup, <2% F1 degradation
- [ ] Accuracy tests: ONNX predictions match original
- [ ] Benchmark report generated
- [ ] Documentation: ONNX conversion guide

---

## Story 7.3: Database Query Optimization

**Story ID:** EPIC7-S3
**Priority:** P0
**Estimated Effort:** 2 days
**Dependencies:** EPIC-1 (Data Collection)

### User Story

**As a** Database Administrator,
**I want** optimized database queries and indexes,
**so that** query time is reduced by 60% and API latency decreases.

### Acceptance Criteria

**AC7.3.1:** DBOptimizer class to analyze and optimize queries
- File: `/Users/srijan/Desktop/aksh/agents/ml/optimization/db_optimizer.py`
- Class: `DBOptimizer` with methods to analyze slow queries
- Tool: SQLite `EXPLAIN QUERY PLAN` to identify missing indexes

**AC7.3.2:** Add indexes to all foreign keys and WHERE clauses
- Analyze: Identify columns used in WHERE, JOIN, ORDER BY
- Add indexes:
```sql
CREATE INDEX IF NOT EXISTS idx_bse_code ON price_movements(bse_code);
CREATE INDEX IF NOT EXISTS idx_date ON price_movements(date);
CREATE INDEX IF NOT EXISTS idx_bse_date ON price_movements(bse_code, date);
CREATE INDEX IF NOT EXISTS idx_earnings_bse ON historical_financials(bse_code);
CREATE INDEX IF NOT EXISTS idx_earnings_quarter_year ON historical_financials(quarter, year);
```
- Expected: 10x speedup for filtered queries

**AC7.3.3:** Query result caching with Redis
- Cache: Query results for 5 minutes (TTL=300s)
- Key format: `query:hash(sql_query + params)`
- Hit: Return from cache (O(1) lookup)
- Miss: Execute query, cache result, return
- Expected: 80% cache hit rate, 100x speedup on cache hit

**AC7.3.4:** Connection pooling for SQLite/PostgreSQL
- Current: Open/close connection per query
- Optimized: Connection pool with 10 connections
- Library: `sqlite3` with `threading`, or `psycopg2.pool` for PostgreSQL
- Expected: 3x speedup by avoiding connection overhead

**AC7.3.5:** Optimize expensive JOIN queries
- Current: Multi-table JOINs in feature extraction
- Optimized: Denormalize tables for read-heavy workloads
- Create: Materialized view or precomputed join table
- Expected: 5x speedup for complex queries

**AC7.3.6:** Benchmark before and after optimization
- Metrics:
  - Query execution time (ms)
  - Database CPU usage (%)
  - Disk I/O (MB/s)
- Test queries:
  1. Fetch price data for 1 stock, 365 days
  2. Fetch financial data for 11,000 stocks
  3. JOIN price + financial + labels for 100,000 samples
- Results table:
```
Query                        | Before  | After  | Speedup
-----------------------------|---------|--------|----------
Price 1 stock (365 days)     | 45ms    | 5ms    | 9x
Financial 11K stocks         | 2,300ms | 180ms  | 12.8x
JOIN 100K samples            | 8,500ms | 1,200ms| 7.1x
Batch features (cache hit)   | 6,000ms | 50ms   | 120x
```

**AC7.3.7:** Database maintenance tasks
- VACUUM: Reclaim space from deleted records
- ANALYZE: Update query planner statistics
- Rebuild indexes: `REINDEX` for fragmented indexes
- Schedule: Run weekly via cron job

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/optimization/db_optimizer.py`

**Key Components:**
```python
import sqlite3
import redis
import hashlib

class DBOptimizer:
    def __init__(
        self,
        db_path: str,
        redis_host: str = "localhost",
        redis_port: int = 6379
    ):
        """Initialize DB optimizer with Redis cache"""
        self.conn_pool = self._create_connection_pool(db_path, pool_size=10)
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        
    def analyze_slow_queries(self) -> List[str]:
        """Identify queries without indexes"""
        # Run EXPLAIN QUERY PLAN on common queries
        # Return list of recommended indexes
        
    def create_indexes(self, indexes: List[str]):
        """Create indexes on database"""
        for idx_sql in indexes:
            self.conn_pool.execute(idx_sql)
            
    def query_with_cache(
        self,
        query: str,
        params: tuple = (),
        ttl: int = 300
    ) -> List:
        """
        Execute query with Redis caching.
        
        Args:
            query: SQL query string
            params: Query parameters
            ttl: Cache TTL in seconds
            
        Returns:
            Query results (from cache or DB)
        """
        # Generate cache key
        cache_key = f"query:{hashlib.md5((query + str(params)).encode()).hexdigest()}"
        
        # Check cache
        cached = self.redis_client.get(cache_key)
        if cached:
            return pickle.loads(cached)
        
        # Execute query
        cursor = self.conn_pool.execute(query, params)
        results = cursor.fetchall()
        
        # Cache results
        self.redis_client.setex(cache_key, ttl, pickle.dumps(results))
        
        return results
        
    def create_connection_pool(
        self,
        db_path: str,
        pool_size: int = 10
    ):
        """Create connection pool"""
        # For SQLite (single-threaded), use queue of connections
        # For PostgreSQL, use psycopg2.pool.ThreadedConnectionPool
        
    def vacuum_database(self):
        """Reclaim space and defragment"""
        self.conn_pool.execute("VACUUM")
        
    def analyze_database(self):
        """Update query planner statistics"""
        self.conn_pool.execute("ANALYZE")
```

**Dependencies:**
- `redis` - Caching
- `sqlite3` or `psycopg2` - Database

**Test File:** `tests/performance/test_db_performance.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] Indexes created on all databases
- [ ] All 7 acceptance criteria passing
- [ ] Performance tests verify 60%+ speedup
- [ ] Redis cache working with 80% hit rate
- [ ] Connection pooling implemented
- [ ] Benchmark report generated
- [ ] Documentation: Database optimization guide

---

## Story 7.4: Caching Strategy

**Story ID:** EPIC7-S4
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC7-S1 (Feature Optimization)

### User Story

**As a** System Architect,
**I want** multi-layer caching to reduce redundant computations,
**so that** cache hit rate reaches 80% and latency drops significantly.

### Acceptance Criteria

**AC7.4.1:** CacheManager class for multi-layer caching
- File: `/Users/srijan/Desktop/aksh/agents/ml/optimization/cache_manager.py`
- Class: `CacheManager` with Redis (L1) and in-memory LRU (L2)
- L1 (Redis): Distributed cache, 5-minute TTL
- L2 (LRU): Process-local cache, 1-minute TTL, max 1000 entries

**AC7.4.2:** Cache feature extraction results
- Key format: `features:{bse_code}:{date}:{hash(feature_names)}`
- Value: JSON serialized feature dict
- TTL: 5 minutes (features don't change within 5 min)
- Expected: 80% hit rate (same stocks requested repeatedly)

**AC7.4.3:** Cache model predictions
- Key format: `prediction:{bse_code}:{date}:{model_version}`
- Value: `{label, probability, confidence}`
- TTL: 1 hour (predictions stable within 1 hour)
- Expected: 60% hit rate (users re-check same stocks)

**AC7.4.4:** Cache invalidation strategy
- Invalidate: When new model deployed, clear prediction cache
- Invalidate: When new price data arrives, clear feature cache for affected stocks
- Endpoint: `POST /api/v1/cache/clear?type=predictions`
- Manual: `redis-cli FLUSHDB` to clear all

**AC7.4.5:** Cache hit rate monitoring
- Metric: `cache_hit_rate = hits / (hits + misses)`
- Expose: Prometheus metric `cache_hit_rate_percent`
- Dashboard: Show in Grafana (Story 5.5)
- Target: ≥80% for features, ≥60% for predictions

**AC7.4.6:** Fallback when Redis unavailable
- If Redis connection fails: Fall back to L2 (LRU) only
- Log warning: "Redis unavailable, using in-memory cache only"
- Graceful degradation: API still functional, just slower
- Auto-reconnect: Retry Redis connection every 30 seconds

**AC7.4.7:** Benchmark caching impact
- Metrics:
  - API latency with cache (hit)
  - API latency without cache (miss)
  - Cache overhead (time to check cache)
- Results table:
```
Scenario                    | Latency | Speedup
----------------------------|---------|----------
Feature extraction (miss)   | 34ms    | 1x
Feature extraction (hit)    | 2ms     | 17x
Prediction (miss)           | 45ms    | 1x
Prediction (hit)            | 5ms     | 9x
```

### Technical Specifications

**File:** `/Users/srijan/Desktop/aksh/agents/ml/optimization/cache_manager.py`

**Key Components:**
```python
import redis
from functools import lru_cache
import hashlib
import json

class CacheManager:
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        lru_maxsize: int = 1000
    ):
        """Initialize multi-layer cache"""
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.lru_cache = {}  # Will use @lru_cache decorator
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L2 → L1).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Check L2 (in-memory LRU) first
        if key in self.lru_cache:
            self.hits += 1
            return self.lru_cache[key]
        
        # Check L1 (Redis)
        try:
            value = self.redis_client.get(key)
            if value:
                self.hits += 1
                # Populate L2
                self.lru_cache[key] = json.loads(value)
                return json.loads(value)
        except redis.ConnectionError:
            logger.warning("Redis unavailable, using L2 cache only")
        
        self.misses += 1
        return None
        
    def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300
    ):
        """Set value in both cache layers"""
        # L2 (in-memory)
        self.lru_cache[key] = value
        
        # L1 (Redis)
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except redis.ConnectionError:
            logger.warning("Redis unavailable, cached in-memory only")
            
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except redis.ConnectionError:
            pass
        
        # Clear L2
        self.lru_cache.clear()
        
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

# Decorator for automatic caching
def cached(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Check cache
            cached_value = cache_manager.get(cache_key)
            if cached_value:
                return cached_value
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

**Dependencies:**
- `redis` - Redis client
- `functools` - LRU cache

**Test File:** `tests/performance/test_cache_hit_rate.py`

**Test Coverage Requirements:** ≥85%

### Definition of Done

- [ ] CacheManager implemented
- [ ] All 7 acceptance criteria passing
- [ ] Performance tests verify 80% hit rate
- [ ] Redis fallback tested
- [ ] Invalidation strategy working
- [ ] Prometheus metrics exposed
- [ ] Documentation: Caching strategy guide

---

## Story 7.5: Load Testing & Scaling

**Story ID:** EPIC7-S5
**Priority:** P1
**Estimated Effort:** 2 days
**Dependencies:** EPIC7-S1, EPIC7-S2, EPIC7-S3, EPIC7-S4

### User Story

**As a** Infrastructure Engineer,
**I want** load testing and auto-scaling configuration,
**so that** the system handles 500 req/sec with horizontal scaling.

### Acceptance Criteria

**AC7.5.1:** Locust load test scenarios
- File: `/Users/srijan/Desktop/aksh/tests/performance/locustfile.py`
- Scenarios:
  1. Steady load: 100 req/sec for 10 minutes
  2. Spike: 0 → 500 req/sec in 30 seconds
  3. Sustained: 500 req/sec for 5 minutes
- User behavior: Mix of `/predict` (70%) and `/batch_predict` (30%)

**AC7.5.2:** Performance targets under load
- At 100 req/sec: p95 latency <50ms, error rate <1%
- At 500 req/sec: p95 latency <100ms, error rate <5%
- No memory leaks: Memory usage stable over 10 minutes
- CPU usage: <80% on single instance

**AC7.5.3:** Horizontal scaling configuration
- Load balancer: Nginx or cloud load balancer (AWS ALB, GCP LB)
- Health check: `/api/v1/health` endpoint
- Scaling policy: Add instance if CPU >70% for 2 minutes
- Min instances: 2, Max instances: 10

**AC7.5.4:** Nginx load balancer configuration
- File: `/Users/srijan/Desktop/aksh/config/nginx_load_balancer.conf`
- Algorithm: Least connections (route to least busy instance)
- Session persistence: Sticky sessions by IP hash (optional)
- Health check interval: 10 seconds

**AC7.5.5:** Auto-scaling policies (cloud deployment)
- AWS: Auto Scaling Group with target tracking (CPU 70%)
- GCP: Instance Group with autoscaler (CPU 70%)
- Kubernetes: Horizontal Pod Autoscaler (CPU 70%, custom metrics)
- Cool down: 5 minutes between scale-out events

**AC7.5.6:** Load test report generation
- Report format:
```
========================================
LOAD TESTING REPORT
========================================
Date: 2025-11-14
Tool: Locust
Duration: 10 minutes

SCENARIO 1: Steady Load (100 req/sec)
- Total Requests: 60,000
- Failed Requests: 234 (0.39%)
- p50 Latency: 25ms
- p95 Latency: 48ms ✓
- p99 Latency: 72ms
- Throughput: 101.3 req/sec
- PASS

SCENARIO 2: Spike (0→500 req/sec)
- Peak Throughput: 487 req/sec
- Failed Requests: 1,245 (4.2%)
- p95 Latency: 95ms ✓
- Recovery Time: 45 seconds
- PASS

SCENARIO 3: Sustained (500 req/sec, 5 min)
- Total Requests: 150,000
- Failed Requests: 6,234 (4.16%)
- p95 Latency: 98ms ✓
- Throughput: 498.7 req/sec
- PASS

SYSTEM METRICS:
- CPU Usage: 68% (avg), 82% (peak)
- Memory Usage: 2.3 GB (stable)
- Network I/O: 45 MB/s
- No memory leaks detected

SCALING EVENTS:
- 10:15:30 - CPU exceeded 70%, added instance 2
- 10:17:45 - CPU exceeded 70%, added instance 3
- 10:22:10 - CPU below 50%, removed instance 3

ASSESSMENT: PASS
System handles 500 req/sec with acceptable latency and error rate.
Recommend deploying with 2-4 instances for production.

========================================
```
- Save to: `/Users/srijan/Desktop/aksh/tests/performance/load_test_report.txt`

**AC7.5.7:** Identify and resolve bottlenecks
- Profile: CPU, memory, I/O during load test
- Identify: Top 3 bottlenecks (e.g., database queries, feature extraction)
- Resolve: Apply optimizations from Stories 7.1-7.4
- Re-test: Verify improvements

### Technical Specifications

**Locust Load Test:**
```python
from locust import HttpUser, task, between
import random

class PredictionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(7)
    def predict_single_stock(self):
        """70% of requests: single stock prediction"""
        bse_code = random.choice(["500325", "532977", "500180"])
        self.client.post("/api/v1/predict", json={
            "bse_code": bse_code,
            "prediction_date": "2025-11-14"
        })
        
    @task(3)
    def batch_predict(self):
        """30% of requests: batch prediction"""
        bse_codes = random.sample(["500325", "532977", "500180", ...], 10)
        self.client.post("/api/v1/batch_predict", json={
            "predictions": [{"bse_code": c, "prediction_date": "2025-11-14"} for c in bse_codes]
        })
```

**Nginx Config:**
```nginx
upstream ml_api {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://ml_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # Health check
        health_check interval=10s fails=3 passes=2 uri=/api/v1/health;
    }
}
```

**Dependencies:**
- `locust` - Load testing
- `nginx` - Load balancer

**Test File:** `tests/performance/test_load_scaling.py`

**Test Coverage Requirements:** N/A (performance testing)

### Definition of Done

- [ ] Locust load tests written
- [ ] All 7 acceptance criteria passing
- [ ] Load test: 500 req/sec sustained with p95 <100ms
- [ ] Scaling: Auto-scaling triggers correctly
- [ ] Nginx config tested
- [ ] Load test report generated
- [ ] Documentation: Scaling guide

---

## Epic Completion Criteria

All 5 stories (EPIC7-S1 through EPIC7-S5) must meet Definition of Done:

- [ ] All acceptance criteria passing for all stories
- [ ] Performance benchmarks documented
- [ ] API latency: p95 <50ms (normal load)
- [ ] Batch throughput: 11,000 stocks in <5 minutes
- [ ] Cache hit rate: ≥80%
- [ ] Load test: 500 req/sec sustained
- [ ] Deliverables exist:
  - `agents/ml/optimization/feature_optimizer.py`
  - `agents/ml/optimization/inference_optimizer.py`
  - `agents/ml/optimization/db_optimizer.py`
  - `agents/ml/optimization/cache_manager.py`
  - `tests/performance/locustfile.py`
  - `config/nginx_load_balancer.conf`
  - Performance benchmark reports

**Ready for Epic 8:** Documentation & Handoff

---

**Total Duration**: 10 days + 2 day buffer = 12 days
**Next Epic**: Epic 8 - Documentation & Handoff

**Author**: VCP Financial Research Team
**Created**: 2025-11-14

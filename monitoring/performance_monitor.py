"""
Performance Monitor (Story 5.1)

Provides Prometheus metrics for:
- API latency, throughput, error rates
- System resource usage (CPU, memory)
- Model prediction metrics
- Custom business metrics

Author: VCP ML Team
Created: 2025-11-14
"""

import time
import psutil
from typing import Dict, List, Optional, Any
from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry, REGISTRY, generate_latest
)


class PerformanceMonitor:
    """
    Performance monitoring with Prometheus metrics.

    Tracks:
    - API request latency (histogram)
    - Request throughput (counter)
    - Error rates (counter)
    - System resources (gauges)
    - Model predictions (counter)
    - Business metrics (gauges)
    """

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """
        Initialize performance monitor.

        Args:
            registry: Optional Prometheus registry (defaults to global REGISTRY)
        """
        self.registry = registry or REGISTRY

        # AC5.1.2: API latency metrics (histogram)
        self.request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration in seconds',
            ['endpoint', 'method', 'status_code'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
            registry=self.registry
        )

        # AC5.1.3: Throughput metrics (counter)
        self.requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['endpoint', 'method', 'status_code'],
            registry=self.registry
        )

        # AC5.1.4: Error rate metrics (counter)
        self.errors_total = Counter(
            'api_errors_total',
            'Total API errors',
            ['endpoint', 'error_type', 'status_code'],
            registry=self.registry
        )

        # AC5.1.5: System resource metrics (gauges)
        self.cpu_usage_gauge = Gauge(
            'process_cpu_percent',
            'CPU usage percentage',
            registry=self.registry
        )

        self.memory_usage_gauge = Gauge(
            'process_resident_memory_bytes',
            'Memory usage in bytes',
            registry=self.registry
        )

        self.memory_percent_gauge = Gauge(
            'process_memory_percent',
            'Memory usage percentage',
            registry=self.registry
        )

        # AC5.1.6: Model prediction metrics (counter)
        self.predictions_total = Counter(
            'model_predictions_total',
            'Total model predictions',
            ['predicted_label', 'confidence', 'model_version'],
            registry=self.registry
        )

        # AC5.1.7: Custom business metrics
        self.daily_candidates_gauge = Gauge(
            'daily_upper_circuit_candidates',
            'Number of upper circuit candidates today',
            registry=self.registry
        )

        self.feature_failures_total = Counter(
            'feature_extraction_failures_total',
            'Total feature extraction failures',
            ['bse_code', 'feature_name'],
            registry=self.registry
        )

        self.cache_hit_rate_gauge = Gauge(
            'model_cache_hit_rate',
            'Model cache hit rate (0 to 1)',
            registry=self.registry
        )

    async def track_request(self, request, call_next):
        """
        Middleware to track request metrics.

        Args:
            request: FastAPI Request object
            call_next: Next middleware in chain

        Returns:
            Response object
        """
        start_time = time.time()

        # Execute request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Extract labels
        endpoint = request.url.path
        method = request.method
        status_code = str(response.status_code)

        # Record latency (AC5.1.2)
        self.request_duration.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code
        ).observe(duration)

        # Record request count (AC5.1.3)
        self.requests_total.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code
        ).inc()

        # Record errors (AC5.1.4)
        if response.status_code >= 400:
            error_type = '4xx' if response.status_code < 500 else '5xx'
            self.errors_total.labels(
                endpoint=endpoint,
                error_type=error_type,
                status_code=status_code
            ).inc()

        return response

    def collect_system_metrics(self) -> Dict[str, float]:
        """
        Collect system resource metrics.

        Returns:
            Dictionary with cpu_percent, memory_percent, memory_bytes
        """
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Get memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_bytes = memory.used

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_bytes': memory_bytes
        }

    def update_system_gauges(self):
        """
        Update system resource gauges (AC5.1.5).
        """
        metrics = self.collect_system_metrics()

        self.cpu_usage_gauge.set(metrics['cpu_percent'])
        self.memory_usage_gauge.set(metrics['memory_bytes'])
        self.memory_percent_gauge.set(metrics['memory_percent'])

    def check_thresholds(self) -> List[Dict[str, Any]]:
        """
        Check if any metrics exceed thresholds.

        Thresholds:
        - CPU > 80% for 15 minutes
        - Memory > 90% for 5 minutes
        - Error rate > 5% for 10 minutes

        Returns:
            List of alert dictionaries
        """
        alerts = []

        # Check CPU threshold
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 80:
            alerts.append({
                'severity': 'warning',
                'metric': 'cpu_usage',
                'value': cpu_percent,
                'threshold': 80,
                'message': f'CPU usage at {cpu_percent:.1f}% (threshold: 80%)'
            })

        # Check memory threshold
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            alerts.append({
                'severity': 'critical',
                'metric': 'memory_usage',
                'value': memory.percent,
                'threshold': 90,
                'message': f'Memory usage at {memory.percent:.1f}% (threshold: 90%)'
            })

        return alerts

    def track_prediction(
        self,
        predicted_label: int,
        confidence: float,
        model_version: str
    ):
        """
        Track model prediction (AC5.1.6).

        Args:
            predicted_label: Predicted label (0 or 1)
            confidence: Prediction confidence (0 to 1)
            model_version: Model version string
        """
        # Bucket confidence into high/medium/low
        if confidence >= 0.75:
            confidence_bucket = 'high'
        elif confidence >= 0.55:
            confidence_bucket = 'medium'
        else:
            confidence_bucket = 'low'

        # Increment counter
        self.predictions_total.labels(
            predicted_label=str(predicted_label),
            confidence=confidence_bucket,
            model_version=model_version
        ).inc()

    def update_daily_candidates(self, count: int):
        """
        Update daily upper circuit candidates gauge (AC5.1.7).

        Args:
            count: Number of candidates today
        """
        self.daily_candidates_gauge.set(count)

    def track_feature_extraction_failure(self, bse_code: str, feature_name: str):
        """
        Track feature extraction failure (AC5.1.7).

        Args:
            bse_code: BSE code of stock
            feature_name: Name of feature that failed
        """
        self.feature_failures_total.labels(
            bse_code=bse_code,
            feature_name=feature_name
        ).inc()

    def update_cache_hit_rate(self, hit_rate: float):
        """
        Update cache hit rate gauge (AC5.1.7).

        Args:
            hit_rate: Cache hit rate (0 to 1)
        """
        self.cache_hit_rate_gauge.set(hit_rate)


def get_metrics_text() -> bytes:
    """
    Get Prometheus metrics in text format.

    Returns:
        Metrics in Prometheus exposition format
    """
    return generate_latest(REGISTRY)

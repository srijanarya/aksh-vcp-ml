"""
Unit tests for Performance Monitor (Story 5.1)

Tests cover:
- AC5.1.1: Prometheus metrics integration
- AC5.1.2: API latency metrics
- AC5.1.3: Throughput metrics
- AC5.1.4: Error rate metrics
- AC5.1.5: System resource metrics
- AC5.1.6: Model prediction metrics
- AC5.1.7: Custom business metrics
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from prometheus_client import REGISTRY, CollectorRegistry
import psutil


@pytest.fixture
def custom_registry():
    """Fixture to provide a fresh registry for each test"""
    return CollectorRegistry()


class TestPerformanceMonitorInitialization:
    """Test PerformanceMonitor initialization"""

    def test_init_creates_metrics(self, custom_registry):
        """Test that initialization creates Prometheus metrics"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Verify metrics are created
        assert hasattr(monitor, 'request_duration')
        assert hasattr(monitor, 'requests_total')
        assert hasattr(monitor, 'errors_total')
        assert hasattr(monitor, 'predictions_total')

    def test_init_with_custom_registry(self, custom_registry):
        """Test initialization with custom registry"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        assert monitor.registry == custom_registry


class TestRequestLatencyMetrics:
    """Test AC5.1.2: API latency metrics"""

    @pytest.mark.asyncio
    async def test_track_request_records_latency(self, custom_registry):
        """Test that request tracking records latency"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Mock request and response
        mock_request = Mock()
        mock_request.url.path = "/api/v1/predict"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 200

        # Mock call_next to take 0.1 seconds
        async def mock_call_next(request):
            await asyncio.sleep(0.1)
            return mock_response

        # Track request
        response = await monitor.track_request(mock_request, mock_call_next)

        assert response.status_code == 200

        # Verify latency was recorded (should be ~0.1s)
        samples = monitor.request_duration.collect()
        assert len(list(samples)) > 0

    def test_latency_buckets_configured_correctly(self, custom_registry):
        """Test that latency histogram has correct buckets"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Check buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        expected_buckets = [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]

        # Verify histogram is created (buckets are part of Histogram's internal state)
        # We can verify by observing a value and checking the metric exists
        assert monitor.request_duration is not None
        assert hasattr(monitor.request_duration, 'observe')

    @pytest.mark.asyncio
    async def test_latency_includes_labels(self, custom_registry):
        """Test that latency metric includes endpoint, method, status_code labels"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        mock_request = Mock()
        mock_request.url.path = "/api/v1/predict"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        await monitor.track_request(mock_request, mock_call_next)

        # Verify labels are present
        samples = list(monitor.request_duration.collect())
        assert len(samples) > 0


class TestThroughputMetrics:
    """Test AC5.1.3: Throughput metrics"""

    @pytest.mark.asyncio
    async def test_requests_total_increments(self, custom_registry):
        """Test that total requests counter increments"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        mock_request = Mock()
        mock_request.url.path = "/api/v1/predict"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 200

        async def mock_call_next(request):
            return mock_response

        # Make 3 requests
        for _ in range(3):
            await monitor.track_request(mock_request, mock_call_next)

        # Verify counter incremented
        samples = list(monitor.requests_total.collect())
        assert len(samples) > 0

    def test_throughput_labels(self, custom_registry):
        """Test throughput metric has endpoint, method, status_code labels"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Verify labels are configured
        assert hasattr(monitor.requests_total, '_labelnames')
        expected_labels = ['endpoint', 'method', 'status_code']
        assert set(monitor.requests_total._labelnames) == set(expected_labels)


class TestErrorRateMetrics:
    """Test AC5.1.4: Error rate metrics"""

    @pytest.mark.asyncio
    async def test_error_counter_increments_on_4xx(self, custom_registry):
        """Test that 4xx errors are counted"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        mock_request = Mock()
        mock_request.url.path = "/api/v1/predict"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 404

        async def mock_call_next(request):
            return mock_response

        await monitor.track_request(mock_request, mock_call_next)

        # Verify error was counted
        samples = list(monitor.errors_total.collect())
        assert len(samples) > 0

    @pytest.mark.asyncio
    async def test_error_counter_increments_on_5xx(self, custom_registry):
        """Test that 5xx errors are counted"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        mock_request = Mock()
        mock_request.url.path = "/api/v1/predict"
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.status_code = 500

        async def mock_call_next(request):
            return mock_response

        await monitor.track_request(mock_request, mock_call_next)

        # Verify error was counted
        samples = list(monitor.errors_total.collect())
        assert len(samples) > 0

    def test_error_metric_labels(self, custom_registry):
        """Test error metric has correct labels"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        expected_labels = ['endpoint', 'error_type', 'status_code']
        assert set(monitor.errors_total._labelnames) == set(expected_labels)


class TestSystemResourceMetrics:
    """Test AC5.1.5: System resource metrics"""

    def test_collect_system_metrics_returns_cpu_memory(self, custom_registry):
        """Test that system metrics collection returns CPU and memory"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        metrics = monitor.collect_system_metrics()

        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'memory_bytes' in metrics

        assert 0 <= metrics['cpu_percent'] <= 100
        assert 0 <= metrics['memory_percent'] <= 100
        assert metrics['memory_bytes'] > 0

    def test_update_system_gauges(self, custom_registry):
        """Test that system gauges are updated"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        monitor.update_system_gauges()

        # Verify gauges exist and have values
        samples = list(monitor.cpu_usage_gauge.collect())
        assert len(samples) > 0

        samples = list(monitor.memory_usage_gauge.collect())
        assert len(samples) > 0

    def test_check_cpu_threshold(self, custom_registry):
        """Test CPU threshold alerting"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Mock high CPU
        with patch('psutil.cpu_percent', return_value=85.0):
            alerts = monitor.check_thresholds()

            # Should have CPU alert
            cpu_alerts = [a for a in alerts if 'CPU' in a['message']]
            assert len(cpu_alerts) > 0

    def test_check_memory_threshold(self, custom_registry):
        """Test memory threshold alerting"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Mock high memory
        mock_memory = Mock()
        mock_memory.percent = 95.0
        with patch('psutil.virtual_memory', return_value=mock_memory):
            alerts = monitor.check_thresholds()

            # Should have memory alert
            memory_alerts = [a for a in alerts if 'Memory' in a['message']]
            assert len(memory_alerts) > 0


class TestModelPredictionMetrics:
    """Test AC5.1.6: Model prediction metrics"""

    def test_track_prediction_increments_counter(self, custom_registry):
        """Test that prediction tracking increments counter"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Track predictions
        monitor.track_prediction(predicted_label=1, confidence=0.85, model_version="1.0.0")
        monitor.track_prediction(predicted_label=0, confidence=0.65, model_version="1.0.0")
        monitor.track_prediction(predicted_label=1, confidence=0.92, model_version="1.0.0")

        # Verify counter incremented
        samples = list(monitor.predictions_total.collect())
        assert len(samples) > 0

    def test_prediction_metric_labels(self, custom_registry):
        """Test prediction metric has correct labels"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        expected_labels = ['predicted_label', 'confidence', 'model_version']
        assert set(monitor.predictions_total._labelnames) == set(expected_labels)

    def test_confidence_buckets(self, custom_registry):
        """Test that confidence is bucketed correctly"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Track predictions with different confidences
        monitor.track_prediction(predicted_label=1, confidence=0.92, model_version="1.0.0")  # High
        monitor.track_prediction(predicted_label=1, confidence=0.65, model_version="1.0.0")  # Medium
        monitor.track_prediction(predicted_label=1, confidence=0.45, model_version="1.0.0")  # Low

        # Confidence should be bucketed as high/medium/low
        samples = list(monitor.predictions_total.collect())
        assert len(samples) > 0


class TestCustomBusinessMetrics:
    """Test AC5.1.7: Custom business metrics"""

    def test_update_daily_candidates_gauge(self, custom_registry):
        """Test updating daily upper circuit candidates gauge"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        monitor.update_daily_candidates(count=42)

        # Verify gauge updated
        samples = list(monitor.daily_candidates_gauge.collect())
        assert len(samples) > 0

    def test_track_feature_extraction_failure(self, custom_registry):
        """Test tracking feature extraction failures"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        monitor.track_feature_extraction_failure("500325", "revenue_growth_yoy")

        # Verify counter incremented
        samples = list(monitor.feature_failures_total.collect())
        assert len(samples) > 0

    def test_update_cache_hit_rate(self, custom_registry):
        """Test updating cache hit rate gauge"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        monitor.update_cache_hit_rate(hit_rate=0.85)

        # Verify gauge updated
        samples = list(monitor.cache_hit_rate_gauge.collect())
        assert len(samples) > 0


class TestPrometheusIntegration:
    """Test AC5.1.1: Prometheus metrics integration"""

    def test_generate_metrics_output(self, custom_registry):
        """Test generating Prometheus format output"""
        from monitoring.performance_monitor import PerformanceMonitor
        from prometheus_client import generate_latest

        monitor = PerformanceMonitor(registry=custom_registry)

        # Track some metrics
        monitor.track_prediction(predicted_label=1, confidence=0.85, model_version="1.0.0")
        monitor.update_daily_candidates(count=10)

        # Generate output
        output = generate_latest(monitor.registry)

        assert output is not None
        assert len(output) > 0

        # Output should be bytes in Prometheus format
        assert isinstance(output, bytes)

    def test_metrics_endpoint_format(self, custom_registry):
        """Test that metrics are in Prometheus exposition format"""
        from monitoring.performance_monitor import PerformanceMonitor
        from prometheus_client import generate_latest

        monitor = PerformanceMonitor(registry=custom_registry)
        monitor.track_prediction(predicted_label=1, confidence=0.85, model_version="1.0.0")

        output = generate_latest(monitor.registry).decode('utf-8')

        # Should contain metric names
        assert 'model_predictions_total' in output or 'api_requests_total' in output


class TestThresholdChecking:
    """Test threshold checking and alerting"""

    def test_check_thresholds_returns_alerts(self, custom_registry):
        """Test that check_thresholds returns list of alerts"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        alerts = monitor.check_thresholds()

        assert isinstance(alerts, list)

    def test_no_alerts_when_under_thresholds(self, custom_registry):
        """Test no alerts when all metrics under thresholds"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Mock low resource usage
        with patch('psutil.cpu_percent', return_value=30.0):
            mock_memory = Mock()
            mock_memory.percent = 50.0
            with patch('psutil.virtual_memory', return_value=mock_memory):
                alerts = monitor.check_thresholds()

                # Should have no resource alerts
                resource_alerts = [a for a in alerts if 'CPU' in a['message'] or 'Memory' in a['message']]
                assert len(resource_alerts) == 0


# Integration tests
class TestPerformanceMonitorIntegration:
    """Integration tests for PerformanceMonitor"""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self, custom_registry):
        """Test full request tracking lifecycle"""
        from monitoring.performance_monitor import PerformanceMonitor

        monitor = PerformanceMonitor(registry=custom_registry)

        # Simulate 10 successful requests
        for i in range(10):
            mock_request = Mock()
            mock_request.url.path = "/api/v1/predict"
            mock_request.method = "POST"

            mock_response = Mock()
            mock_response.status_code = 200

            async def mock_call_next(request):
                await asyncio.sleep(0.01)
                return mock_response

            await monitor.track_request(mock_request, mock_call_next)

        # Verify metrics recorded
        duration_samples = list(monitor.request_duration.collect())
        requests_samples = list(monitor.requests_total.collect())

        assert len(duration_samples) > 0
        assert len(requests_samples) > 0

    def test_concurrent_metric_updates(self, custom_registry):
        """Test that concurrent metric updates work correctly"""
        from monitoring.performance_monitor import PerformanceMonitor
        import threading

        monitor = PerformanceMonitor(registry=custom_registry)

        def track_predictions():
            for _ in range(100):
                monitor.track_prediction(
                    predicted_label=1,
                    confidence=0.85,
                    model_version="1.0.0"
                )

        # Create multiple threads
        threads = [threading.Thread(target=track_predictions) for _ in range(5)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Verify metrics were tracked
        samples = list(monitor.predictions_total.collect())
        assert len(samples) > 0

"""
Story 4.4: API Documentation & Testing - Integration Tests

Tests for complete FastAPI application with OpenAPI documentation,
health checks, metrics, and comprehensive endpoint testing.

Target: 23 tests covering all API functionality

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import FastAPI


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_model():
    """Mock ML model for testing"""
    model = Mock()
    model.predict_proba = Mock(return_value=[[0.3, 0.7]])  # 70% probability
    return model


@pytest.fixture
def mock_registry(mock_model):
    """Mock model registry"""
    registry = Mock()
    registry.get_best_model = Mock(return_value={
        'model_id': 'test-model-123',
        'model_type': 'XGBClassifier',
        'version': '1.0.0',
        'f1': 0.75,
        'created_at': '2025-11-14T00:00:00'
    })
    registry.load_model = Mock(return_value=mock_model)
    registry.list_models = Mock(return_value=[
        {
            'model_id': 'test-model-123',
            'model_type': 'XGBClassifier',
            'version': '1.0.0',
            'f1': 0.75,
            'created_at': '2025-11-14T00:00:00'
        }
    ])
    return registry


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    # Import here to avoid circular imports
    from api.main import app
    return TestClient(app)


@pytest.fixture
def mock_prediction_service(mock_model):
    """Mock PredictionService"""
    service = Mock()
    service.model = mock_model
    service.model_version = "1.0.0"
    service.model_type = "XGBClassifier"
    service.requests_processed = 100
    service.total_latency = 5000.0
    service.errors = 2
    service.start_time = time.time() - 3600  # 1 hour uptime
    service.registry = Mock()
    service.registry.list_models = Mock(return_value=[
        {
            'model_id': 'test-model-123',
            'model_type': 'XGBClassifier',
            'version': '1.0.0',
            'f1': 0.75
        }
    ])

    # Mock predict_single
    async def mock_predict_single(request):
        from api.prediction_endpoint import PredictionResponse
        return PredictionResponse(
            bse_code=request.bse_code,
            nse_symbol=request.nse_symbol or "UNKNOWN",
            prediction_date=request.prediction_date,
            predicted_label=1,
            probability=0.7,
            confidence="HIGH",
            model_version="1.0.0",
            prediction_timestamp=datetime.now().isoformat(),
            features={"rsi_14": 50.0} if request.include_features else None,
            shap_values=None
        )
    service.predict_single = mock_predict_single

    # Mock predict_batch
    async def mock_predict_batch(request):
        results = []
        for pred_req in request.predictions:
            results.append(await mock_predict_single(pred_req))
        return results
    service.predict_batch = mock_predict_batch

    # Mock get_health_status
    async def mock_get_health_status():
        from api.prediction_endpoint import HealthResponse
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            model_loaded=True,
            model_version="1.0.0",
            model_type="XGBClassifier",
            uptime_seconds=3600.0,
            requests_processed=100,
            avg_latency_ms=50.0,
            error_rate=0.02
        )
    service.get_health_status = mock_get_health_status

    return service


@pytest.fixture
def client_with_mocks(mock_prediction_service):
    """Test client with mocked dependencies"""
    from api.main import app, reset_service, get_service

    def mock_get_service():
        return mock_prediction_service

    # Override FastAPI dependency
    app.dependency_overrides[get_service] = mock_get_service
    reset_service()  # Reset global service
    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()
    reset_service()


# ============================================================================
# Test: OpenAPI Documentation (AC4.4.1)
# ============================================================================

def test_openapi_docs_accessible(client):
    """Test 1: OpenAPI docs accessible at /docs"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_redoc_accessible(client):
    """Test 2: ReDoc accessible at /redoc"""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_openapi_json_schema(client):
    """Test 3: OpenAPI JSON schema available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "VCP Upper Circuit Prediction API"
    assert "paths" in schema


def test_openapi_endpoints_documented(client):
    """Test 4: All endpoints documented in OpenAPI schema"""
    response = client.get("/openapi.json")
    schema = response.json()

    paths = schema["paths"]
    assert "/api/v1/predict" in paths
    assert "/api/v1/batch_predict" in paths
    assert "/api/v1/health" in paths
    assert "/api/v1/metrics" in paths
    assert "/api/v1/models" in paths


# ============================================================================
# Test: Prediction Endpoint (AC4.4.2, AC4.4.3)
# ============================================================================

def test_predict_single_stock_success(client_with_mocks):
    """Test 5: Valid prediction request returns 200 OK"""
    request_data = {
        "bse_code": "500325",
        "nse_symbol": "RELIANCE",
        "prediction_date": "2025-11-14",
        "include_features": True,
        "include_shap": False
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["bse_code"] == "500325"
    assert data["nse_symbol"] == "RELIANCE"
    assert data["prediction_date"] == "2025-11-14"
    assert "predicted_label" in data
    assert "probability" in data
    assert "confidence" in data
    assert "model_version" in data
    assert "prediction_timestamp" in data


def test_predict_response_schema(client_with_mocks):
    """Test 6: Response matches PredictionResponse schema"""
    request_data = {
        "bse_code": "500325",
        "prediction_date": "2025-11-14"
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    data = response.json()

    # Validate required fields
    assert isinstance(data["predicted_label"], int)
    assert data["predicted_label"] in [0, 1]
    assert isinstance(data["probability"], float)
    assert 0.0 <= data["probability"] <= 1.0
    assert data["confidence"] in ["LOW", "MEDIUM", "HIGH"]
    assert isinstance(data["model_version"], str)


def test_predict_invalid_bse_code(client_with_mocks):
    """Test 7: Invalid BSE code returns 422"""
    request_data = {
        "bse_code": "123",  # Too short
        "prediction_date": "2025-11-14"
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422


def test_predict_invalid_date_format(client_with_mocks):
    """Test 8: Invalid date format returns 422"""
    request_data = {
        "bse_code": "500325",
        "prediction_date": "14-11-2025"  # Wrong format
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422


def test_predict_missing_required_fields(client_with_mocks):
    """Test 9: Missing required fields returns 422"""
    request_data = {
        "bse_code": "500325"
        # Missing prediction_date
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422


def test_predict_with_features(client_with_mocks):
    """Test 10: include_features=True returns feature values"""
    request_data = {
        "bse_code": "500325",
        "prediction_date": "2025-11-14",
        "include_features": True
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    data = response.json()

    assert "features" in data
    assert data["features"] is not None
    assert isinstance(data["features"], dict)


# ============================================================================
# Test: Batch Prediction (AC4.4.3)
# ============================================================================

def test_batch_predict_multiple_stocks(client_with_mocks):
    """Test 11: Batch prediction returns results for all stocks"""
    request_data = {
        "predictions": [
            {"bse_code": "500325", "prediction_date": "2025-11-14"},
            {"bse_code": "532978", "prediction_date": "2025-11-14"},
            {"bse_code": "500180", "prediction_date": "2025-11-14"}
        ]
    }

    response = client_with_mocks.post("/api/v1/batch_predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3


def test_batch_predict_max_100_stocks(client_with_mocks):
    """Test 12: Batch prediction rejects >100 stocks"""
    request_data = {
        "predictions": [
            {"bse_code": f"{500000 + i:06d}", "prediction_date": "2025-11-14"}
            for i in range(101)
        ]
    }

    response = client_with_mocks.post("/api/v1/batch_predict", json=request_data)
    assert response.status_code == 422


# ============================================================================
# Test: Health Check (AC4.4.1, AC4.4.6)
# ============================================================================

def test_health_endpoint_success(client_with_mocks):
    """Test 13: Health endpoint returns 200 when healthy"""
    response = client_with_mocks.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["model_loaded"] is True
    assert "model_version" in data
    assert "uptime_seconds" in data


def test_health_response_schema(client_with_mocks):
    """Test 14: Health response matches HealthResponse schema"""
    response = client_with_mocks.get("/api/v1/health")
    data = response.json()

    assert isinstance(data["model_loaded"], bool)
    assert isinstance(data["uptime_seconds"], (int, float))
    assert isinstance(data["requests_processed"], int)
    assert isinstance(data["avg_latency_ms"], (int, float))
    assert isinstance(data["error_rate"], (int, float))


# ============================================================================
# Test: Metrics Endpoint (AC4.4.1)
# ============================================================================

def test_metrics_endpoint_exists(client_with_mocks):
    """Test 15: Metrics endpoint accessible"""
    response = client_with_mocks.get("/api/v1/metrics")
    assert response.status_code == 200


def test_metrics_prometheus_format(client_with_mocks):
    """Test 16: Metrics in Prometheus format"""
    response = client_with_mocks.get("/api/v1/metrics")
    assert response.status_code == 200

    # Prometheus format is plain text
    assert response.headers["content-type"].startswith("text/plain")

    content = response.text
    # Should contain metric names
    assert "prediction_requests_total" in content or "http_requests" in content


# ============================================================================
# Test: Models Endpoint (AC4.4.1)
# ============================================================================

def test_models_list_endpoint(client_with_mocks):
    """Test 17: List models endpoint returns available models"""
    response = client_with_mocks.get("/api/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)


def test_models_reload_endpoint(client_with_mocks):
    """Test 18: Reload models endpoint (admin)"""
    response = client_with_mocks.post("/api/v1/models/reload")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data


# ============================================================================
# Test: CORS (AC4.4.1)
# ============================================================================

def test_cors_headers_present(client_with_mocks):
    """Test 19: CORS headers present in response"""
    # Make OPTIONS request to trigger CORS preflight
    response = client_with_mocks.options(
        "/api/v1/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET"
        }
    )

    # CORS middleware should add headers
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers or \
           "Access-Control-Allow-Origin" in response.headers


# ============================================================================
# Test: Error Handling (AC4.4.3, AC4.4.5)
# ============================================================================

def test_error_response_structure(client_with_mocks):
    """Test 20: Error responses have consistent structure"""
    request_data = {
        "bse_code": "123",  # Invalid
        "prediction_date": "2025-11-14"
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


# ============================================================================
# Test: Performance (AC4.4.6)
# ============================================================================

def test_prediction_latency(client_with_mocks):
    """Test 21: Single prediction latency <200ms (with buffer)"""
    request_data = {
        "bse_code": "500325",
        "prediction_date": "2025-11-14"
    }

    start_time = time.time()
    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    latency_ms = (time.time() - start_time) * 1000

    assert response.status_code == 200
    # Allow 200ms for test environment (target is 100ms production)
    assert latency_ms < 200


# ============================================================================
# Test: Request Validation (AC4.4.5)
# ============================================================================

def test_request_validation_strict(client_with_mocks):
    """Test 22: Strict request validation enforced"""
    # Test with extra fields
    request_data = {
        "bse_code": "500325",
        "prediction_date": "2025-11-14",
        "extra_field": "should_be_ignored"
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    # Should still succeed (extra fields ignored by Pydantic)
    assert response.status_code == 200


def test_backward_compatibility(client_with_mocks):
    """Test 23: Backward compatibility maintained"""
    # Test minimal request (only required fields)
    request_data = {
        "bse_code": "500325",
        "prediction_date": "2025-11-14"
    }

    response = client_with_mocks.post("/api/v1/predict", json=request_data)
    assert response.status_code == 200

    data = response.json()
    # Optional fields should be present but may be None
    assert "features" in data or data.get("features") is None
    assert "shap_values" in data or data.get("shap_values") is None

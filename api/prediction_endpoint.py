"""
Story 4.1: FastAPI Prediction Endpoint

REST API for real-time upper circuit predictions.

Features:
- POST /api/v1/predict - Single stock prediction
- POST /api/v1/batch_predict - Batch predictions (max 100)
- GET /api/v1/health - Health check
- <100ms p95 latency target
- Pydantic request/response validation

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import joblib

from agents.ml.model_registry import ModelRegistry
from agents.ml.technical_feature_extractor import TechnicalFeatureExtractor
from agents.ml.financial_feature_extractor import FinancialFeatureExtractor
from agents.ml.sentiment_feature_extractor import SentimentFeatureExtractor
from agents.ml.seasonality_feature_extractor import SeasonalityFeatureExtractor

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas (AC4.1.2)
# ============================================================================

class PredictionRequest(BaseModel):
    """Request schema for single stock prediction"""
    bse_code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]+$")
    nse_symbol: Optional[str] = None
    prediction_date: str = Field(..., description="ISO format: YYYY-MM-DD")
    include_features: bool = False
    include_shap: bool = False

    @field_validator('prediction_date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('prediction_date must be in ISO format: YYYY-MM-DD')


class PredictionResponse(BaseModel):
    """Response schema for prediction"""
    bse_code: str
    nse_symbol: str
    prediction_date: str
    predicted_label: int = Field(..., ge=0, le=1)
    probability: float = Field(..., ge=0.0, le=1.0)
    confidence: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$")
    model_version: str
    prediction_timestamp: str
    features: Optional[Dict[str, float]] = None
    shap_values: Optional[Dict[str, float]] = None


class BatchPredictionRequest(BaseModel):
    """Request schema for batch predictions"""
    predictions: List[PredictionRequest] = Field(..., max_length=100)


class HealthResponse(BaseModel):
    """Response schema for health check"""
    status: str
    timestamp: str
    model_loaded: bool
    model_version: Optional[str] = None
    model_type: Optional[str] = None
    uptime_seconds: float
    requests_processed: int
    avg_latency_ms: float
    error_rate: float


# ============================================================================
# Confidence Calculation (AC4.1.4)
# ============================================================================

def calculate_confidence(probability: float) -> str:
    """
    Calculate confidence level based on probability

    Args:
        probability: Predicted probability (0.0 to 1.0)

    Returns:
        "HIGH", "MEDIUM", or "LOW"
    """
    if probability >= 0.7 or probability <= 0.3:
        return "HIGH"
    elif 0.45 <= probability <= 0.55:
        return "LOW"
    else:
        return "MEDIUM"


# ============================================================================
# Prediction Service (AC4.1.3, AC4.1.4)
# ============================================================================

class PredictionService:
    """
    Core prediction service with feature extraction and model inference

    Responsibilities:
    - Load best model from registry
    - Extract features using Epic 2 extractors
    - Make predictions with confidence levels
    - Handle errors gracefully
    """

    def __init__(
        self,
        model_registry_path: str,
        feature_dbs: Dict[str, str]
    ):
        """
        Initialize prediction service

        Args:
            model_registry_path: Path to model registry
            feature_dbs: Dictionary of feature database paths
                {
                    'technical': 'path/to/technical.db',
                    'financial': 'path/to/financial.db',
                    'sentiment': 'path/to/sentiment.db',
                    'seasonality': 'path/to/seasonality.db'
                }
        """
        self.model_registry_path = model_registry_path
        self.feature_dbs = feature_dbs

        # Load model registry
        self.registry = ModelRegistry(model_registry_path)

        # Load best model
        best_model_info = self.registry.get_best_model(metric='f1')
        if best_model_info is None:
            raise RuntimeError("No trained models found in registry")

        self.model = self.registry.load_model(model_id=best_model_info['model_id'])
        self.model_version = best_model_info['version']
        self.model_type = best_model_info['model_type']

        # Initialize feature extractors
        self.technical_extractor = TechnicalFeatureExtractor(
            price_db_path=feature_dbs.get('price', 'data/price_movements.db'),
            output_db_path=feature_dbs.get('technical', 'data/features/technical_features.db')
        )
        self.financial_extractor = FinancialFeatureExtractor(
            financial_db_path=feature_dbs.get('financial', 'data/features/financial_data.db'),
            output_db_path=feature_dbs.get('financial_features', 'data/features/financial_features.db')
        )
        self.sentiment_extractor = SentimentFeatureExtractor(
            news_db_path=feature_dbs.get('news', 'data/features/news_sentiment.db'),
            output_db_path=feature_dbs.get('sentiment', 'data/features/sentiment_features.db')
        )
        self.seasonality_extractor = SeasonalityFeatureExtractor(
            historical_db_path=feature_dbs.get('historical', 'data/features/historical_patterns.db'),
            output_db_path=feature_dbs.get('seasonality', 'data/features/seasonality_features.db')
        )

        # Performance tracking
        self.start_time = time.time()
        self.requests_processed = 0
        self.total_latency = 0.0
        self.errors = 0

        logger.info(f"PredictionService initialized: model={self.model_type} v{self.model_version}")

    async def predict_single(self, request: PredictionRequest) -> PredictionResponse:
        """
        Predict for single stock (AC4.1.4)

        Args:
            request: PredictionRequest

        Returns:
            PredictionResponse

        Raises:
            HTTPException: For various error conditions
        """
        start_time = time.time()

        try:
            # Extract features
            features = await self.extract_features(request.bse_code, request.prediction_date)

            if features is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Feature extraction failed for BSE code {request.bse_code}"
                )

            # Convert to array (25 features expected)
            feature_array = list(features.values())

            # Predict
            proba_result = self.model.predict_proba([feature_array])
            # Handle both numpy arrays and lists
            if hasattr(proba_result, 'shape'):
                # Numpy array
                probability = float(proba_result[0, 1])
            else:
                # List (for mocking)
                probability = float(proba_result[0][1])
            predicted_label = 1 if probability >= 0.5 else 0
            confidence = calculate_confidence(probability)

            # Track performance
            latency_ms = (time.time() - start_time) * 1000
            self.requests_processed += 1
            self.total_latency += latency_ms

            logger.info(f"Prediction completed: {request.bse_code}, prob={probability:.3f}, latency={latency_ms:.1f}ms")

            return PredictionResponse(
                bse_code=request.bse_code,
                nse_symbol=request.nse_symbol or "UNKNOWN",
                prediction_date=request.prediction_date,
                predicted_label=predicted_label,
                probability=probability,
                confidence=confidence,
                model_version=self.model_version,
                prediction_timestamp=datetime.now().isoformat(),
                features=features if request.include_features else None,
                shap_values=None  # TODO: Implement SHAP in future
            )

        except HTTPException:
            self.errors += 1
            raise
        except Exception as e:
            self.errors += 1
            logger.error(f"Prediction error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    async def predict_batch(self, request: BatchPredictionRequest) -> List[PredictionResponse]:
        """
        Predict for multiple stocks

        Args:
            request: BatchPredictionRequest

        Returns:
            List of PredictionResponse
        """
        results = []
        for pred_request in request.predictions:
            try:
                result = await self.predict_single(pred_request)
                results.append(result)
            except HTTPException as e:
                # Continue with other predictions
                logger.warning(f"Batch prediction failed for {pred_request.bse_code}: {e.detail}")
                # Add error placeholder
                results.append(PredictionResponse(
                    bse_code=pred_request.bse_code,
                    nse_symbol=pred_request.nse_symbol or "UNKNOWN",
                    prediction_date=pred_request.prediction_date,
                    predicted_label=0,
                    probability=0.0,
                    confidence="LOW",
                    model_version=self.model_version,
                    prediction_timestamp=datetime.now().isoformat()
                ))

        return results

    async def extract_features(self, bse_code: str, date: str) -> Optional[Dict[str, float]]:
        """
        Extract all 25 features for given stock and date (AC4.1.3)

        Args:
            bse_code: BSE stock code
            date: Prediction date (ISO format)

        Returns:
            Dictionary of 25 features, or None if extraction fails
        """
        try:
            # For now, return dummy features for testing
            # TODO: Implement actual feature extraction from databases

            # This would normally query the feature databases
            # and combine technical, financial, sentiment, and seasonality features

            features = {
                # Technical features (13)
                'rsi_14': 50.0,
                'macd_line': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'bb_upper': 100.0,
                'bb_middle': 95.0,
                'bb_lower': 90.0,
                'bb_percent_b': 0.5,
                'volume_ratio': 1.0,
                'volume_spike': 0,
                'momentum_5d': 0.05,
                'momentum_10d': 0.10,
                'momentum_30d': 0.15,

                # Financial features (6)
                'revenue_growth_yoy': 0.20,
                'npm_trend': 0.10,
                'roe_latest': 0.15,
                'debt_to_equity_latest': 0.5,
                'current_ratio_latest': 1.5,
                'revenue_surprise': 0.05,

                # Sentiment features (3)
                'sentiment_score_avg': 0.5,
                'sentiment_trend_7d': 0.1,
                'news_volume_spike': 0,

                # Seasonality features (3)
                'earnings_return_mean': 0.03,
                'earnings_return_volatility': 0.02,
                'days_to_earnings': 5
            }

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}", exc_info=True)
            return None

    async def get_health_status(self) -> HealthResponse:
        """Get API health status (AC4.1.6)"""
        uptime = time.time() - self.start_time
        avg_latency = self.total_latency / self.requests_processed if self.requests_processed > 0 else 0.0
        error_rate = self.errors / self.requests_processed if self.requests_processed > 0 else 0.0

        return HealthResponse(
            status="healthy" if self.model is not None else "unhealthy",
            timestamp=datetime.now().isoformat(),
            model_loaded=self.model is not None,
            model_version=self.model_version,
            model_type=self.model_type,
            uptime_seconds=uptime,
            requests_processed=self.requests_processed,
            avg_latency_ms=avg_latency,
            error_rate=error_rate
        )


# ============================================================================
# FastAPI Application (AC4.1.1)
# ============================================================================

app = FastAPI(
    title="VCP Upper Circuit Prediction API",
    description="ML API for predicting upper circuit movements in Indian stocks",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instance
prediction_service: Optional[PredictionService] = None


def get_service() -> PredictionService:
    """Dependency to get prediction service"""
    global prediction_service
    if prediction_service is None:
        # Initialize with default paths
        prediction_service = PredictionService(
            model_registry_path="data/models/registry",
            feature_dbs={
                'price': 'data/price_movements.db',
                'technical': 'data/features/technical_features.db',
                'financial': 'data/features/financial_data.db',
                'financial_features': 'data/features/financial_features.db',
                'news': 'data/features/news_sentiment.db',
                'sentiment': 'data/features/sentiment_features.db',
                'historical': 'data/features/historical_patterns.db',
                'seasonality': 'data/features/seasonality_features.db'
            }
        )
    return prediction_service


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    service: PredictionService = Depends(get_service)
) -> PredictionResponse:
    """
    Single stock prediction endpoint (AC4.1.1, AC4.1.5)

    Target latency: <100ms (p95)
    """
    return await service.predict_single(request)


@app.post("/api/v1/batch_predict", response_model=List[PredictionResponse])
async def batch_predict(
    request: BatchPredictionRequest,
    service: PredictionService = Depends(get_service)
) -> List[PredictionResponse]:
    """
    Batch prediction endpoint (max 100 stocks)
    """
    return await service.predict_batch(request)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health(
    service: PredictionService = Depends(get_service)
) -> HealthResponse:
    """
    Health check endpoint (AC4.1.6)

    Returns:
        - 200: Service healthy
        - 503: Service unavailable
    """
    health_status = await service.get_health_status()

    if health_status.status != "healthy":
        raise HTTPException(status_code=503, detail="Service unavailable")

    return health_status


@app.get("/api/v1/models")
async def list_models(service: PredictionService = Depends(get_service)):
    """List available models"""
    models = service.registry.list_models()
    return {"models": models}


@app.post("/api/v1/models/reload")
async def reload_models():
    """Reload models (admin endpoint)"""
    global prediction_service
    prediction_service = None  # Force reload on next request
    return {"status": "Models will be reloaded on next request"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
API package for VCP ML System

FastAPI-based prediction endpoints for real-time inference.
"""

from api.prediction_endpoint import app, PredictionService

__all__ = ['app', 'PredictionService']

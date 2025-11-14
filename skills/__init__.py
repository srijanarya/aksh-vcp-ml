"""
Skills Library - Domain-specific business logic for ML agents

Skills combine Tools into higher-level workflows with domain knowledge:
- PDF text extraction from financial statements
- Sentiment analysis on earnings announcements
- VCP (Volatility Contraction Pattern) detection
- Technical indicator calculation (RSI, MACD, Bollinger Bands)
- Circuit breaker detection (upper/lower circuit hits)

Skills encode the "how" - they know the business rules and best practices
for Indian stock market analysis.

Author: VCP Financial Research Team
Version: 1.0.0
"""

from .pdf_text_extractor import extract_text_from_pdf, extract_financial_tables
from .sentiment_analyzer import analyze_earnings_sentiment, classify_sentiment
from .vcp_detector import detect_vcp_pattern, calculate_contraction_stages
from .technical_indicators import calculate_rsi, calculate_macd, calculate_bollinger_bands
from .circuit_detector import detect_upper_circuit, detect_lower_circuit, is_circuit_hit

__all__ = [
    # PDF extraction
    "extract_text_from_pdf",
    "extract_financial_tables",

    # Sentiment analysis
    "analyze_earnings_sentiment",
    "classify_sentiment",

    # VCP detection
    "detect_vcp_pattern",
    "calculate_contraction_stages",

    # Technical indicators
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",

    # Circuit detection
    "detect_upper_circuit",
    "detect_lower_circuit",
    "is_circuit_hit",
]

__version__ = "1.0.0"

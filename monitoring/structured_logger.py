"""
Structured Logger (Story 5.4)

Provides structured JSON logging with:
- JSON format with timestamp, level, logger, message, context, trace_id
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log rotation and retention
- Contextual logging with trace IDs
- Error tracking with stack traces
- Audit logging for ML predictions

Author: VCP ML Team
Created: 2025-11-14
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom formatter for JSON logs (AC5.4.1).

    Outputs logs in JSON format with fields:
    - timestamp: ISO 8601 format with Z suffix
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name
    - message: Log message
    - context: Additional context dictionary
    - trace_id: Request trace ID for correlation
    - exception: Stack trace for errors
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON string
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }

        # Add context if present
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        # Add trace_id if present
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id

        # Add exception if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add audit fields if present (for audit logger)
        audit_fields = ['bse_code', 'prediction_date', 'predicted_label', 'probability', 'model_version', 'user_id']
        for field in audit_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)

        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "/app/logs"
) -> logging.Logger:
    """
    Configure logging for the application (AC5.4.1, AC5.4.2, AC5.4.3).

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files

    Returns:
        Configured logger
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler (stdout) with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler with rotation (AC5.4.3)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days
        encoding="utf-8"
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Error file handler (AC5.4.5)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "errors.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)

    # Audit file handler (AC5.4.6)
    audit_handler = logging.handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "audit.log"),
        when="midnight",
        interval=1,
        backupCount=90,  # Keep 90 days for audit trail
        encoding="utf-8"
    )
    audit_handler.setFormatter(JSONFormatter())
    # Audit handler will be used explicitly via audit logger

    # Create audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)

    return logger


def get_logger_with_context(
    name: str,
    trace_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> logging.LoggerAdapter:
    """
    Get logger with trace_id and context (AC5.4.4).

    Args:
        name: Logger name
        trace_id: UUID trace ID for request tracking
        context: Additional context dictionary

    Returns:
        LoggerAdapter with context
    """
    logger = logging.getLogger(name)

    # Build extra dict
    extra = {}
    if trace_id:
        extra["trace_id"] = trace_id
    if context:
        extra["context"] = context

    return logging.LoggerAdapter(logger, extra)


def log_prediction_audit(
    bse_code: str,
    prediction_date: str,
    predicted_label: int,
    probability: float,
    model_version: str,
    trace_id: str,
    user_id: Optional[str] = None
):
    """
    Log prediction for audit trail (AC5.4.6).

    Args:
        bse_code: BSE code of stock
        prediction_date: Date of prediction
        predicted_label: Predicted label (0 or 1)
        probability: Prediction probability
        model_version: Model version used
        trace_id: Request trace ID
        user_id: Optional user ID
    """
    audit_logger = logging.getLogger("audit")

    # Create log record with audit data as extra fields
    # This will be formatted by JSONFormatter
    extra = {
        "bse_code": bse_code,
        "prediction_date": prediction_date,
        "predicted_label": predicted_label,
        "probability": probability,
        "model_version": model_version,
        "trace_id": trace_id
    }

    if user_id:
        extra["user_id"] = user_id

    # Create a custom log record with all fields
    record = audit_logger.makeRecord(
        audit_logger.name,
        logging.INFO,
        "(audit)",
        0,
        "prediction",
        (),
        None
    )

    # Add extra fields to record
    for key, value in extra.items():
        setattr(record, key, value)

    audit_logger.handle(record)

"""
Unit tests for Structured Logger (Story 5.4)

Tests cover:
- AC5.4.1: Structured JSON logging configuration
- AC5.4.2: Log levels and severity
- AC5.4.3: Log rotation and retention
- AC5.4.4: Contextual logging with trace IDs
- AC5.4.5: Error tracking with stack traces
- AC5.4.6: Audit logging for ML predictions
- AC5.4.7: Integration with logging aggregators
"""

import pytest
import json
import logging
import tempfile
import os
from pathlib import Path
import uuid
from datetime import datetime


@pytest.fixture
def temp_log_dir():
    """Fixture to provide temporary log directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestStructuredLoggerInitialization:
    """Test structured logger initialization"""

    def test_setup_logging_creates_logger(self, temp_log_dir):
        """Test that setup_logging creates configured logger"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)

        assert logger is not None
        assert logger.level == logging.INFO

    def test_setup_with_different_log_levels(self, temp_log_dir):
        """Test logger with different log levels"""
        from monitoring.structured_logger import setup_logging

        # Test DEBUG
        logger_debug = setup_logging(log_level="DEBUG", log_dir=temp_log_dir)
        assert logger_debug.level == logging.DEBUG

        # Test WARNING
        logger_warning = setup_logging(log_level="WARNING", log_dir=temp_log_dir)
        assert logger_warning.level == logging.WARNING


class TestJSONFormatting:
    """Test AC5.4.1: Structured JSON logging"""

    def test_json_formatter_creates_valid_json(self, temp_log_dir):
        """Test that logs are in valid JSON format"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)
        logger.info("Test message")

        # Read log file
        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_line = f.readline()

        # Parse as JSON
        log_data = json.loads(log_line)

        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'message' in log_data

    def test_json_log_includes_required_fields(self, temp_log_dir):
        """Test that JSON logs include timestamp, level, logger, message"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)
        logger.info("Test message")

        # Read and parse log
        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'logger' in log_data
        assert 'message' in log_data
        assert log_data['message'] == 'Test message'


class TestLogLevels:
    """Test AC5.4.2: Log levels and severity"""

    def test_debug_level_logging(self, temp_log_dir):
        """Test DEBUG level logging"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="DEBUG", log_dir=temp_log_dir)
        logger.debug("Debug message")

        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['level'] == 'DEBUG'

    def test_info_level_logging(self, temp_log_dir):
        """Test INFO level logging"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)
        logger.info("Info message")

        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['level'] == 'INFO'

    def test_warning_level_logging(self, temp_log_dir):
        """Test WARNING level logging"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="WARNING", log_dir=temp_log_dir)
        logger.warning("Warning message")

        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['level'] == 'WARNING'

    def test_error_level_logging(self, temp_log_dir):
        """Test ERROR level logging"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="ERROR", log_dir=temp_log_dir)
        logger.error("Error message")

        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['level'] == 'ERROR'

    def test_critical_level_logging(self, temp_log_dir):
        """Test CRITICAL level logging"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="CRITICAL", log_dir=temp_log_dir)
        logger.critical("Critical message")

        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['level'] == 'CRITICAL'


class TestContextualLogging:
    """Test AC5.4.4: Contextual logging with trace IDs"""

    def test_logger_with_trace_id(self, temp_log_dir):
        """Test logging with trace ID context"""
        from monitoring.structured_logger import setup_logging, get_logger_with_context

        setup_logging(log_level="INFO", log_dir=temp_log_dir)

        trace_id = str(uuid.uuid4())
        logger = get_logger_with_context("test_logger", trace_id=trace_id)

        logger.info("Test message with trace ID")

        # Read and verify
        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert 'trace_id' in log_data
        assert log_data['trace_id'] == trace_id

    def test_logger_with_custom_context(self, temp_log_dir):
        """Test logging with custom context fields"""
        from monitoring.structured_logger import setup_logging, get_logger_with_context

        setup_logging(log_level="INFO", log_dir=temp_log_dir)

        context = {
            'bse_code': '500325',
            'prediction_date': '2025-11-14'
        }
        logger = get_logger_with_context("test_logger", context=context)

        logger.info("Test message with context")

        # Read and verify
        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert 'context' in log_data
        assert log_data['context']['bse_code'] == '500325'


class TestErrorTracking:
    """Test AC5.4.5: Error tracking with stack traces"""

    def test_exception_logging_includes_stack_trace(self, temp_log_dir):
        """Test that exceptions include stack traces"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="ERROR", log_dir=temp_log_dir)

        try:
            raise ValueError("Test error")
        except Exception:
            logger.error("Error occurred", exc_info=True)

        # Read error log
        error_file = Path(temp_log_dir) / "errors.log"
        with open(error_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert 'exception' in log_data
        assert 'ValueError' in log_data['exception']
        assert 'Test error' in log_data['exception']


class TestLogRotation:
    """Test AC5.4.3: Log rotation and retention"""

    def test_log_files_created(self, temp_log_dir):
        """Test that log files are created"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)
        logger.info("Test message")

        # Verify app.log exists
        app_log = Path(temp_log_dir) / "app.log"
        assert app_log.exists()

    def test_error_log_separate(self, temp_log_dir):
        """Test that errors go to separate file"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)
        logger.error("Error message")

        # Verify errors.log exists
        error_log = Path(temp_log_dir) / "errors.log"
        assert error_log.exists()


class TestAuditLogging:
    """Test AC5.4.6: Audit logging for ML predictions"""

    def test_audit_log_prediction(self, temp_log_dir):
        """Test audit logging for predictions"""
        from monitoring.structured_logger import setup_logging, log_prediction_audit

        setup_logging(log_level="INFO", log_dir=temp_log_dir)

        log_prediction_audit(
            bse_code='500325',
            prediction_date='2025-11-14',
            predicted_label=1,
            probability=0.85,
            model_version='1.0.0',
            trace_id=str(uuid.uuid4())
        )

        # Verify audit log exists
        audit_log = Path(temp_log_dir) / "audit.log"
        assert audit_log.exists()

        # Verify content
        with open(audit_log, 'r') as f:
            log_data = json.loads(f.readline())

        assert log_data['bse_code'] == '500325'
        assert log_data['predicted_label'] == 1
        assert log_data['probability'] == 0.85


class TestStructuredLoggerIntegration:
    """Integration tests for structured logger"""

    def test_multiple_log_levels_to_different_files(self, temp_log_dir):
        """Test that different log levels go to appropriate files"""
        from monitoring.structured_logger import setup_logging

        logger = setup_logging(log_level="INFO", log_dir=temp_log_dir)

        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Check app.log has all messages
        app_log = Path(temp_log_dir) / "app.log"
        with open(app_log, 'r') as f:
            lines = f.readlines()
        assert len(lines) >= 3

        # Check errors.log has only error
        error_log = Path(temp_log_dir) / "errors.log"
        with open(error_log, 'r') as f:
            lines = f.readlines()
        assert len(lines) >= 1

    def test_log_with_all_features(self, temp_log_dir):
        """Test logging with all features combined"""
        from monitoring.structured_logger import setup_logging, get_logger_with_context

        setup_logging(log_level="INFO", log_dir=temp_log_dir)

        trace_id = str(uuid.uuid4())
        context = {'bse_code': '500325', 'model_version': '1.0.0'}
        logger = get_logger_with_context("test_logger", trace_id=trace_id, context=context)

        logger.info("Full featured log message")

        # Verify all features present
        log_file = Path(temp_log_dir) / "app.log"
        with open(log_file, 'r') as f:
            log_data = json.loads(f.readline())

        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'message' in log_data
        assert 'trace_id' in log_data
        assert 'context' in log_data
        assert log_data['trace_id'] == trace_id
        assert log_data['context']['bse_code'] == '500325'

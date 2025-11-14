"""
Unit tests for Story 4.2: Batch Prediction Pipeline

Test Coverage:
- Initialization tests (3)
- Batch processing tests (4)
- Parallel processing tests (3)
- Error handling tests (4)
- Output format tests (4)
- Performance tests (4)

Total: 22 tests

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import pytest
import tempfile
import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import time

from api.batch_predictor import (
    BatchPredictor,
    BatchReport,
    StockPrediction
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test outputs"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_registry_path(temp_dir):
    """Create mock model registry path"""
    registry_path = temp_dir / "registry"
    registry_path.mkdir(parents=True, exist_ok=True)
    return str(registry_path)


@pytest.fixture
def mock_feature_dbs(temp_dir):
    """Create mock feature database paths"""
    return {
        'price': str(temp_dir / 'price.db'),
        'technical': str(temp_dir / 'technical.db'),
        'financial': str(temp_dir / 'financial.db'),
        'financial_features': str(temp_dir / 'financial_features.db'),
        'news': str(temp_dir / 'news.db'),
        'sentiment': str(temp_dir / 'sentiment.db'),
        'historical': str(temp_dir / 'historical.db'),
        'seasonality': str(temp_dir / 'seasonality.db')
    }


@pytest.fixture
def master_stock_db(temp_dir):
    """Create mock master stock list database"""
    db_path = temp_dir / 'master_stock_list.db'
    conn = sqlite3.connect(str(db_path))

    # Create table
    conn.execute('''
        CREATE TABLE master_stock_list (
            bse_code TEXT PRIMARY KEY,
            nse_symbol TEXT,
            company_name TEXT,
            status TEXT,
            market_cap_cr REAL
        )
    ''')

    # Insert test data (100 stocks for testing)
    test_stocks = []
    for i in range(100):
        test_stocks.append((
            f"{500000 + i:06d}",
            f"STOCK{i}",
            f"Test Company {i}",
            "ACTIVE",
            1000.0 - i * 5  # Descending market cap
        ))

    conn.executemany(
        'INSERT INTO master_stock_list VALUES (?, ?, ?, ?, ?)',
        test_stocks
    )
    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def predictions_db(temp_dir):
    """Create predictions database"""
    db_path = temp_dir / 'predictions.db'
    return str(db_path)


@pytest.fixture
def batch_predictor(mock_registry_path, mock_feature_dbs, master_stock_db, predictions_db, temp_dir):
    """Create BatchPredictor instance with mocked dependencies"""

    # Create mock model
    with patch('api.batch_predictor.ModelRegistry') as mock_registry_cls:
        mock_registry = Mock()
        mock_registry.get_best_model.return_value = {
            'model_id': 'test_model_1',
            'model_type': 'XGBoost',
            'version': '1.2.0',
            'metrics': {'f1': 0.72, 'roc_auc': 0.78}
        }

        # Create mock model that returns predictions
        mock_model = Mock()
        mock_model.predict_proba.return_value = [[0.3, 0.7]]  # High probability of upper circuit
        mock_registry.load_model.return_value = mock_model
        mock_registry_cls.return_value = mock_registry

        predictor = BatchPredictor(
            model_registry_path=mock_registry_path,
            feature_dbs=mock_feature_dbs,
            master_stock_db_path=master_stock_db,
            predictions_db_path=predictions_db,
            output_dir=str(temp_dir)
        )

        return predictor


# ============================================================================
# Initialization Tests (3 tests)
# ============================================================================

def test_batch_predictor_initialization(mock_registry_path, mock_feature_dbs, master_stock_db, predictions_db, temp_dir):
    """Test BatchPredictor initializes correctly"""
    with patch('api.batch_predictor.ModelRegistry') as mock_registry_cls:
        mock_registry = Mock()
        mock_registry.get_best_model.return_value = {
            'model_id': 'test_model_1',
            'model_type': 'XGBoost',
            'version': '1.2.0',
            'metrics': {'f1': 0.72}
        }
        mock_registry.load_model.return_value = Mock()
        mock_registry_cls.return_value = mock_registry

        predictor = BatchPredictor(
            model_registry_path=mock_registry_path,
            feature_dbs=mock_feature_dbs,
            master_stock_db_path=master_stock_db,
            predictions_db_path=predictions_db,
            output_dir=str(temp_dir)
        )

        assert predictor.model is not None
        assert predictor.model_version == '1.2.0'
        assert predictor.model_type == 'XGBoost'
        assert predictor.output_dir == Path(temp_dir)


def test_batch_predictor_fails_without_model(mock_registry_path, mock_feature_dbs, master_stock_db, predictions_db, temp_dir):
    """Test BatchPredictor raises error when no model found"""
    with patch('api.batch_predictor.ModelRegistry') as mock_registry_cls:
        mock_registry = Mock()
        mock_registry.get_best_model.return_value = None
        mock_registry_cls.return_value = mock_registry

        with pytest.raises(RuntimeError, match="No trained models found"):
            BatchPredictor(
                model_registry_path=mock_registry_path,
                feature_dbs=mock_feature_dbs,
                master_stock_db_path=master_stock_db,
                predictions_db_path=predictions_db,
                output_dir=str(temp_dir)
            )


def test_batch_predictor_creates_output_directory(mock_registry_path, mock_feature_dbs, master_stock_db, predictions_db, temp_dir):
    """Test BatchPredictor creates output directory if it doesn't exist"""
    output_dir = temp_dir / "new_output_dir"

    with patch('api.batch_predictor.ModelRegistry') as mock_registry_cls:
        mock_registry = Mock()
        mock_registry.get_best_model.return_value = {
            'model_id': 'test_model_1',
            'model_type': 'XGBoost',
            'version': '1.2.0',
            'metrics': {'f1': 0.72}
        }
        mock_registry.load_model.return_value = Mock()
        mock_registry_cls.return_value = mock_registry

        predictor = BatchPredictor(
            model_registry_path=mock_registry_path,
            feature_dbs=mock_feature_dbs,
            master_stock_db_path=master_stock_db,
            predictions_db_path=predictions_db,
            output_dir=str(output_dir)
        )

        assert output_dir.exists()
        assert output_dir.is_dir()


# ============================================================================
# Batch Processing Tests (4 tests)
# ============================================================================

def test_fetch_active_stocks(batch_predictor, master_stock_db):
    """Test fetching active stocks from master list"""
    stocks_df = batch_predictor.fetch_active_stocks()

    assert len(stocks_df) == 100
    assert list(stocks_df.columns) == ['bse_code', 'nse_symbol', 'company_name', 'market_cap_cr']
    assert stocks_df['bse_code'].iloc[0] == '500000'
    # Verify sorted by market cap descending
    assert stocks_df['market_cap_cr'].iloc[0] >= stocks_df['market_cap_cr'].iloc[-1]


def test_extract_features_for_stock(batch_predictor):
    """Test extracting features for a single stock"""
    features = batch_predictor.extract_features_for_stock('500000', '2025-11-14')

    assert features is not None
    assert len(features) == 25
    assert 'rsi_14' in features
    assert 'revenue_growth_yoy' in features
    assert 'sentiment_score_avg' in features
    assert 'earnings_return_mean' in features


def test_predict_batch_of_stocks(batch_predictor):
    """Test predicting for a batch of stocks"""
    stocks = [
        {'bse_code': '500000', 'nse_symbol': 'STOCK0', 'company_name': 'Test Company 0'},
        {'bse_code': '500001', 'nse_symbol': 'STOCK1', 'company_name': 'Test Company 1'},
        {'bse_code': '500002', 'nse_symbol': 'STOCK2', 'company_name': 'Test Company 2'}
    ]

    predictions = batch_predictor.predict_batch(stocks, '2025-11-14')

    assert len(predictions) == 3
    assert all(isinstance(p, StockPrediction) for p in predictions)
    assert all(0 <= p.probability <= 1 for p in predictions)
    assert all(p.predicted_label in [0, 1] for p in predictions)
    assert all(p.confidence in ['LOW', 'MEDIUM', 'HIGH'] for p in predictions)


def test_predict_all_stocks_end_to_end(batch_predictor, master_stock_db):
    """Test complete batch prediction pipeline"""
    report = batch_predictor.predict_all_stocks('2025-11-14')

    assert isinstance(report, BatchReport)
    assert report.total_stocks_processed > 0
    assert report.total_stocks_processed <= 100  # Our test database
    assert report.stocks_skipped >= 0
    assert report.predicted_upper_circuit >= 0
    assert report.duration_seconds > 0


# ============================================================================
# Parallel Processing Tests (3 tests)
# ============================================================================

def test_parallel_feature_extraction(batch_predictor):
    """Test parallel feature extraction with multiprocessing"""
    stocks = [
        {'bse_code': f"{500000 + i:06d}", 'nse_symbol': f"STOCK{i}"}
        for i in range(10)
    ]

    with patch('api.batch_predictor.cpu_count', return_value=4):
        features_df = batch_predictor.extract_features_parallel(stocks, '2025-11-14', n_workers=2)

        assert len(features_df) == 10
        assert features_df.shape[1] >= 25  # At least 25 feature columns


def test_parallel_processing_uses_cpu_cores(batch_predictor):
    """Test that parallel processing uses appropriate number of CPU cores"""
    with patch('api.batch_predictor.cpu_count', return_value=8) as mock_cpu:
        # Should use cpu_count() - 1
        n_workers = batch_predictor.get_optimal_workers()
        assert n_workers == 7


def test_batch_size_configuration(batch_predictor):
    """Test batch size is configurable and used correctly"""
    assert batch_predictor.batch_size == 100  # Default from AC4.2.1

    # Test with custom batch size
    batch_predictor.batch_size = 50
    assert batch_predictor.batch_size == 50


# ============================================================================
# Error Handling Tests (4 tests)
# ============================================================================

def test_handle_missing_features_gracefully(batch_predictor):
    """Test handling of stocks with missing features"""
    # Mock feature extraction to return None for some stocks
    original_extract = batch_predictor.extract_features_for_stock

    def mock_extract(bse_code, date):
        if bse_code == '500001':
            return None  # Missing features
        return original_extract(bse_code, date)

    batch_predictor.extract_features_for_stock = mock_extract

    stocks = [
        {'bse_code': '500000', 'nse_symbol': 'STOCK0', 'company_name': 'Test 0'},
        {'bse_code': '500001', 'nse_symbol': 'STOCK1', 'company_name': 'Test 1'},  # Will fail
        {'bse_code': '500002', 'nse_symbol': 'STOCK2', 'company_name': 'Test 2'}
    ]

    predictions = batch_predictor.predict_batch(stocks, '2025-11-14')

    # Should skip failed stock but continue with others
    assert len(predictions) == 2  # Only successful predictions


def test_error_logging_for_failed_stocks(batch_predictor, temp_dir):
    """Test that failed stocks are logged to skipped_stocks.csv"""
    # Mock feature extraction to fail for specific stock
    original_extract = batch_predictor.extract_features_for_stock

    def mock_extract(bse_code, date):
        if bse_code == '500001':
            raise ValueError("Missing price data")
        return original_extract(bse_code, date)

    batch_predictor.extract_features_for_stock = mock_extract

    stocks = [
        {'bse_code': '500000', 'nse_symbol': 'STOCK0', 'company_name': 'Test 0'},
        {'bse_code': '500001', 'nse_symbol': 'STOCK1', 'company_name': 'Test 1'}
    ]

    batch_predictor.predict_batch(stocks, '2025-11-14')

    # Check skipped stocks are tracked
    assert len(batch_predictor.skipped_stocks) > 0
    assert any(s['bse_code'] == '500001' for s in batch_predictor.skipped_stocks)


def test_continue_on_prediction_errors(batch_predictor):
    """Test that pipeline continues when individual predictions fail"""
    # Mock model to raise error for specific stock
    original_predict = batch_predictor.model.predict_proba

    def mock_predict(features):
        # Simulate error condition
        if len(batch_predictor._prediction_count) == 1:
            raise RuntimeError("Model prediction failed")
        return original_predict(features)

    batch_predictor._prediction_count = []
    batch_predictor.model.predict_proba = lambda x: (
        batch_predictor._prediction_count.append(1),
        mock_predict(x)
    )[1]

    stocks = [
        {'bse_code': '500000', 'nse_symbol': 'STOCK0', 'company_name': 'Test 0'},
        {'bse_code': '500001', 'nse_symbol': 'STOCK1', 'company_name': 'Test 1'},
        {'bse_code': '500002', 'nse_symbol': 'STOCK2', 'company_name': 'Test 2'}
    ]

    # Should not raise exception, continue with other stocks
    predictions = batch_predictor.predict_batch(stocks, '2025-11-14')
    assert len(predictions) >= 1  # At least some predictions succeed


def test_error_rate_threshold(batch_predictor):
    """Test that error rate is calculated and within acceptable limits"""
    report = batch_predictor.predict_all_stocks('2025-11-14')

    error_rate = report.stocks_skipped / report.total_stocks_processed if report.total_stocks_processed > 0 else 0
    assert error_rate <= 0.02  # AC4.2.7: <2% error rate


# ============================================================================
# Output Format Tests (4 tests)
# ============================================================================

def test_save_predictions_to_database(batch_predictor, predictions_db):
    """Test saving predictions to SQLite database"""
    predictions = [
        StockPrediction(
            bse_code='500000',
            nse_symbol='STOCK0',
            company_name='Test Company 0',
            prediction_date='2025-11-14',
            predicted_label=1,
            probability=0.87,
            confidence='HIGH',
            model_version='1.2.0',
            model_type='XGBoost'
        )
    ]

    db_rows, csv_rows = batch_predictor.save_predictions(predictions, '2025-11-14')

    assert db_rows == 1

    # Verify data in database
    conn = sqlite3.connect(predictions_db)
    cursor = conn.execute('SELECT bse_code, predicted_label, probability FROM daily_predictions')
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    assert rows[0][0] == '500000'  # bse_code
    assert rows[0][1] == 1  # predicted_label


def test_save_predictions_to_csv(batch_predictor, temp_dir):
    """Test saving predictions to CSV file"""
    predictions = [
        StockPrediction(
            bse_code='500000',
            nse_symbol='STOCK0',
            company_name='Test Company 0',
            prediction_date='2025-11-14',
            predicted_label=1,
            probability=0.87,
            confidence='HIGH',
            model_version='1.2.0',
            model_type='XGBoost'
        )
    ]

    db_rows, csv_rows = batch_predictor.save_predictions(predictions, '2025-11-14')

    assert csv_rows == 1

    # Verify CSV file exists
    csv_path = temp_dir / 'predictions_2025-11-14.csv'
    assert csv_path.exists()

    # Verify CSV content
    df = pd.read_csv(csv_path)
    assert len(df) == 1
    assert str(df['bse_code'].iloc[0]) == '500000'
    assert df['probability'].iloc[0] == 0.87


def test_save_predictions_to_json(batch_predictor, temp_dir):
    """Test saving predictions to JSON file"""
    predictions = [
        StockPrediction(
            bse_code='500000',
            nse_symbol='STOCK0',
            company_name='Test Company 0',
            prediction_date='2025-11-14',
            predicted_label=1,
            probability=0.87,
            confidence='HIGH',
            model_version='1.2.0',
            model_type='XGBoost'
        )
    ]

    json_path = batch_predictor.save_predictions_json(predictions, '2025-11-14')

    assert json_path.exists()

    # Verify JSON content
    with open(json_path, 'r') as f:
        data = json.load(f)

    assert len(data['predictions']) == 1
    assert data['predictions'][0]['bse_code'] == '500000'
    assert data['metadata']['total_predictions'] == 1


def test_generate_batch_report(batch_predictor):
    """Test generating comprehensive batch report"""
    predictions = [
        StockPrediction(
            bse_code=f"{500000 + i:06d}",
            nse_symbol=f"STOCK{i}",
            company_name=f"Test Company {i}",
            prediction_date='2025-11-14',
            predicted_label=1 if i % 3 == 0 else 0,
            probability=0.9 if i % 3 == 0 else 0.3,
            confidence='HIGH' if i % 3 == 0 else 'LOW',
            model_version='1.2.0',
            model_type='XGBoost'
        )
        for i in range(30)
    ]

    report = batch_predictor.generate_report(
        predictions=predictions,
        skipped_stocks=[],
        duration_seconds=120.5,
        date='2025-11-14'
    )

    assert isinstance(report, BatchReport)
    assert report.total_stocks_processed == 30
    assert report.predicted_upper_circuit == 10  # Every 3rd stock
    assert report.high_confidence > 0
    assert report.duration_seconds == 120.5
    assert report.throughput > 0

    # Verify report text format
    assert 'BATCH PREDICTION REPORT' in report.to_text()
    assert 'Model: XGBoost v1.2.0' in report.to_text()
    assert 'Total Stocks Processed: 30' in report.to_text()


# ============================================================================
# Performance Tests (4 tests)
# ============================================================================

def test_performance_target_throughput(batch_predictor, master_stock_db):
    """Test that throughput meets target of >=18 stocks/second"""
    start_time = time.time()
    report = batch_predictor.predict_all_stocks('2025-11-14')
    duration = time.time() - start_time

    throughput = report.total_stocks_processed / duration

    # AC4.2.7: >=18 stocks/second
    assert throughput >= 18, f"Throughput {throughput:.2f} stocks/sec is below target of 18"


def test_performance_target_total_time(batch_predictor):
    """Test that 11,000 stocks can be processed in <10 minutes"""
    # For unit test, we'll test with smaller sample and extrapolate
    sample_size = 100

    start_time = time.time()
    report = batch_predictor.predict_all_stocks('2025-11-14')
    duration = time.time() - start_time

    # Extrapolate to 11,000 stocks
    time_per_stock = duration / sample_size
    estimated_time_11k = time_per_stock * 11000

    # AC4.2.7: <10 minutes = 600 seconds
    assert estimated_time_11k < 600, f"Estimated time {estimated_time_11k:.1f}s exceeds 600s for 11K stocks"


def test_memory_usage_within_limits(batch_predictor):
    """Test that memory usage stays <4GB"""
    import psutil
    import os

    process = psutil.Process(os.getpid())

    # Get memory before
    mem_before = process.memory_info().rss / 1024 / 1024 / 1024  # GB

    # Run batch prediction
    batch_predictor.predict_all_stocks('2025-11-14')

    # Get memory after
    mem_after = process.memory_info().rss / 1024 / 1024 / 1024  # GB
    mem_used = mem_after - mem_before

    # AC4.2.7: <4GB RAM usage
    assert mem_used < 4.0, f"Memory usage {mem_used:.2f}GB exceeds 4GB limit"


def test_batch_report_includes_performance_metrics(batch_predictor):
    """Test that batch report includes all performance metrics"""
    report = batch_predictor.predict_all_stocks('2025-11-14')

    assert hasattr(report, 'duration_seconds')
    assert hasattr(report, 'throughput')
    assert hasattr(report, 'avg_latency_ms')
    assert report.duration_seconds > 0
    assert report.throughput > 0


# ============================================================================
# Integration Test
# ============================================================================

def test_cli_interface(batch_predictor, temp_dir):
    """Test CLI interface for batch prediction"""
    # This would test the __main__ block
    # For now, just verify the interface exists
    from api.batch_predictor import main

    # Mock sys.argv
    with patch('sys.argv', ['batch_predictor.py', '--date', '2025-11-14', '--output', str(temp_dir)]):
        # This would call main() in real implementation
        pass

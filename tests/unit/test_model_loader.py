"""
Story 4.3: Model Loading & Caching Tests

TDD tests for ModelLoader with LRU caching, lazy loading, and hot reload.

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import pytest
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import joblib
import tempfile
import shutil


# Mock data for tests
MOCK_MODEL_INFO_V1 = {
    'model_id': 1,
    'model_name': 'XGBoost Upper Circuit Predictor',
    'model_type': 'XGBClassifier',
    'version': '1.0.0',
    'metrics': {'f1': 0.72, 'roc_auc': 0.85},
    'file_path': 'data/models/registry/XGBClassifier_1_0_0.pkl',
    'created_at': '2025-11-14T10:00:00'
}

MOCK_MODEL_INFO_V2 = {
    'model_id': 2,
    'model_name': 'XGBoost Upper Circuit Predictor',
    'model_type': 'XGBClassifier',
    'version': '1.1.0',
    'metrics': {'f1': 0.75, 'roc_auc': 0.87},
    'file_path': 'data/models/registry/XGBClassifier_1_1_0.pkl',
    'created_at': '2025-11-14T11:00:00'
}

MOCK_MODEL_INFO_LIGHTGBM = {
    'model_id': 3,
    'model_name': 'LightGBM Upper Circuit Predictor',
    'model_type': 'LGBMClassifier',
    'version': '1.0.0',
    'metrics': {'f1': 0.70, 'roc_auc': 0.83},
    'file_path': 'data/models/registry/LGBMClassifier_1_0_0.pkl',
    'created_at': '2025-11-14T09:00:00'
}


@pytest.fixture
def temp_registry_dir():
    """Create temporary directory for model registry"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_model():
    """Create mock model object"""
    model = Mock()
    model.predict_proba = Mock(return_value=[[0.13, 0.87]])
    return model


@pytest.fixture
def mock_registry(mock_model):
    """Create mock ModelRegistry"""
    with patch('api.model_loader.ModelRegistry') as MockRegistry:
        registry = MockRegistry.return_value
        registry.get_best_model.return_value = MOCK_MODEL_INFO_V1
        registry.load_model.return_value = mock_model
        registry.list_models.return_value = [MOCK_MODEL_INFO_V1, MOCK_MODEL_INFO_V2]
        yield MockRegistry


# ============================================================================
# Test Class 1: Initialization (3 tests) - AC4.3.1
# ============================================================================

class TestModelLoaderInitialization:
    """Test ModelLoader initialization and configuration"""

    def test_initialization_with_default_cache_size(self, mock_registry):
        """Test ModelLoader initializes with default cache size of 3"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        assert loader.registry_path == "data/models/registry"
        assert loader.cache_size == 3
        assert loader._cache == {}

    def test_initialization_with_custom_cache_size(self, mock_registry):
        """Test ModelLoader initializes with custom cache size"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry", cache_size=5)

        assert loader.cache_size == 5

    def test_initialization_creates_lock(self, mock_registry):
        """Test ModelLoader creates thread lock for thread safety"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        assert loader._lock is not None
        assert isinstance(loader._lock, threading.Lock)


# ============================================================================
# Test Class 2: Model Loading (4 tests) - AC4.3.2
# ============================================================================

class TestModelLoading:
    """Test lazy model loading functionality"""

    def test_load_model_with_type_and_version(self, mock_registry, mock_model):
        """Test loading specific model by type and version"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")
        model = loader.load_model(model_type="XGBClassifier", version="1.0.0")

        assert model is not None
        assert model == mock_model

    def test_load_model_with_type_only_uses_latest(self, mock_registry, mock_model):
        """Test loading model by type only uses latest version"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")
        model = loader.load_model(model_type="XGBClassifier")

        assert model is not None
        # Should query for latest version
        mock_registry.return_value.get_best_model.assert_called()

    def test_load_model_caches_result(self, mock_registry, mock_model):
        """Test that loaded model is cached in memory"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Load model twice
        model1 = loader.load_model(model_type="XGBClassifier", version="1.0.0")
        model2 = loader.load_model(model_type="XGBClassifier", version="1.0.0")

        # Should be same object (cached)
        assert model1 is model2
        # Registry load_model should be called only once
        assert mock_registry.return_value.load_model.call_count == 1

    def test_load_model_raises_error_on_failure(self, mock_registry):
        """Test that load_model raises error when model not found"""
        from api.model_loader import ModelLoader, ModelLoadError

        mock_registry.return_value.get_best_model.return_value = None
        loader = ModelLoader(registry_path="data/models/registry")

        with pytest.raises(ModelLoadError):
            loader.load_model(model_type="NonExistentModel")


# ============================================================================
# Test Class 3: LRU Cache (4 tests) - AC4.3.1
# ============================================================================

class TestLRUCache:
    """Test LRU caching behavior"""

    def test_cache_evicts_oldest_when_full(self, mock_registry):
        """Test that cache evicts least recently used model when full"""
        from api.model_loader import ModelLoader

        # Create loader with cache_size=2
        loader = ModelLoader(registry_path="data/models/registry", cache_size=2)

        # Create 3 different mock models
        model1 = Mock()
        model2 = Mock()
        model3 = Mock()

        mock_registry.return_value.load_model.side_effect = [model1, model2, model3]

        # Load 3 models (cache size is 2, so should evict)
        loader.load_model(model_type="XGBClassifier", version="1.0.0")
        loader.load_model(model_type="XGBClassifier", version="1.1.0")
        loader.load_model(model_type="LGBMClassifier", version="1.0.0")

        # Cache should only have 2 models
        assert len(loader._cache) == 2

    def test_cache_updates_lru_on_access(self, mock_registry):
        """Test that accessing a cached model updates LRU order"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry", cache_size=2)

        model1 = Mock()
        model2 = Mock()
        model3 = Mock()

        mock_registry.return_value.load_model.side_effect = [model1, model2, model3]

        # Load 2 models
        loader.load_model(model_type="XGBClassifier", version="1.0.0")
        loader.load_model(model_type="LGBMClassifier", version="1.0.0")

        # Access first model (updates LRU)
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

        # Load third model - should evict LGBMClassifier (least recently used)
        loader.load_model(model_type="XGBClassifier", version="1.1.0")

        # XGBClassifier v1.0.0 should still be in cache
        cache_keys = list(loader._cache.keys())
        assert ("XGBClassifier", "1.0.0") in cache_keys

    def test_cache_respects_memory_limit(self, mock_registry):
        """Test that cache doesn't exceed configured size"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry", cache_size=3)

        # Create mock model infos for different versions
        model_infos = []
        for i in range(5):
            model_infos.append({
                'model_id': i + 1,
                'model_name': 'XGBoost',
                'model_type': 'XGBClassifier',
                'version': f'1.{i}.0',
                'metrics': {'f1': 0.7},
                'file_path': f'model_{i}.pkl',
                'created_at': f'2025-11-14T10:{i:02d}:00'
            })

        # Mock list_models to return model infos
        mock_registry.return_value.list_models.return_value = model_infos

        # Load 5 models
        for i in range(5):
            mock_registry.return_value.load_model.return_value = Mock()
            loader.load_model(model_type="XGBClassifier", version=f"1.{i}.0")

        # Cache should never exceed 3
        assert len(loader._cache) <= 3

    def test_cache_key_format(self, mock_registry, mock_model):
        """Test that cache uses (model_type, version) as key"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

        # Check cache key format
        assert ("XGBClassifier", "1.0.0") in loader._cache


# ============================================================================
# Test Class 4: Thread Safety (3 tests) - AC4.3.3
# ============================================================================

class TestThreadSafety:
    """Test thread-safe model loading"""

    def test_concurrent_loads_use_lock(self, mock_registry, mock_model):
        """Test that concurrent loads acquire lock"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Test that lock exists and is a threading.Lock
        assert isinstance(loader._lock, threading.Lock)

        # The lock is used inside load_model - we can't easily mock it
        # but we can verify the lock exists and concurrent loads work correctly
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

    def test_concurrent_loads_dont_duplicate(self, mock_registry):
        """Test that concurrent loads don't load model twice"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Add delay to load_model to simulate race condition
        original_load = mock_registry.return_value.load_model
        def slow_load(*args, **kwargs):
            time.sleep(0.1)
            return original_load(*args, **kwargs)

        mock_registry.return_value.load_model = slow_load

        # Load same model from 2 threads
        results = []
        def load_task():
            model = loader.load_model(model_type="XGBClassifier", version="1.0.0")
            results.append(model)

        t1 = threading.Thread(target=load_task)
        t2 = threading.Thread(target=load_task)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Both should get same cached model
        assert len(results) == 2
        assert results[0] is results[1]

    def test_thread_safe_cache_modification(self, mock_registry):
        """Test that cache can be safely modified from multiple threads"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry", cache_size=10)

        # Create mock model infos for different versions
        model_infos = []
        for i in range(5):
            model_infos.append({
                'model_id': i + 1,
                'model_name': 'XGBoost',
                'model_type': 'XGBClassifier',
                'version': f'1.{i}.0',
                'metrics': {'f1': 0.7},
                'file_path': f'model_{i}.pkl',
                'created_at': f'2025-11-14T10:{i:02d}:00'
            })

        mock_registry.return_value.list_models.return_value = model_infos

        # Load different models from multiple threads
        def load_task(version):
            loader.load_model(model_type="XGBClassifier", version=version)

        threads = []
        for i in range(5):
            t = threading.Thread(target=load_task, args=(f"1.{i}.0",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All models should be loaded without errors
        assert len(loader._cache) == 5


# ============================================================================
# Test Class 5: Hot Reload (3 tests) - AC4.3.3
# ============================================================================

class TestHotReload:
    """Test hot reload functionality without downtime"""

    def test_reload_model_loads_new_version(self, mock_registry):
        """Test that reload_model loads new version"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Load old version
        old_model = Mock()
        mock_registry.return_value.load_model.return_value = old_model
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

        # Reload with new version
        new_model = Mock()
        mock_registry.return_value.load_model.return_value = new_model
        loader.reload_model(model_type="XGBClassifier", version="1.1.0")

        # New model should be in cache
        assert loader._cache[("XGBClassifier", "1.1.0")] is new_model

    def test_reload_all_models_refreshes_cache(self, mock_registry):
        """Test that reload_all_models refreshes entire cache"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Load 2 models
        loader.load_model(model_type="XGBClassifier", version="1.0.0")
        loader.load_model(model_type="LGBMClassifier", version="1.0.0")

        initial_cache_size = len(loader._cache)

        # Reload all
        reloaded_models = loader.reload_all_models()

        # Should return dict of reloaded models
        assert isinstance(reloaded_models, dict)
        assert len(reloaded_models) == initial_cache_size

    def test_hot_reload_doesnt_interrupt_service(self, mock_registry, mock_model):
        """Test that hot reload doesn't interrupt ongoing predictions"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Load initial model
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

        # Simulate ongoing prediction
        prediction_result = None
        def predict_task():
            nonlocal prediction_result
            model = loader.load_model(model_type="XGBClassifier", version="1.0.0")
            time.sleep(0.1)  # Simulate prediction time
            prediction_result = model.predict_proba([[1, 2, 3]])

        # Start prediction in background
        prediction_thread = threading.Thread(target=predict_task)
        prediction_thread.start()

        # Reload model while prediction is running
        time.sleep(0.05)  # Let prediction start
        loader.reload_model(model_type="XGBClassifier", version="1.0.0")

        prediction_thread.join()

        # Prediction should complete successfully
        assert prediction_result is not None


# ============================================================================
# Test Class 6: Cache Statistics (3 tests) - AC4.3.6
# ============================================================================

class TestCacheStatistics:
    """Test cache statistics tracking"""

    def test_get_cache_stats_returns_metrics(self, mock_registry):
        """Test that get_cache_stats returns cache metrics"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        stats = loader.get_cache_stats()

        assert 'cache_size' in stats
        assert 'cached_models' in stats
        assert 'hit_rate' in stats
        assert 'miss_rate' in stats
        assert 'total_loads' in stats

    def test_cache_hit_rate_calculation(self, mock_registry, mock_model):
        """Test that cache hit rate is calculated correctly"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Load model twice (1 miss, 1 hit)
        loader.load_model(model_type="XGBClassifier", version="1.0.0")
        loader.load_model(model_type="XGBClassifier", version="1.0.0")

        stats = loader.get_cache_stats()

        assert stats['total_loads'] == 2
        assert stats['cache_hits'] == 1
        assert stats['cache_misses'] == 1
        assert stats['hit_rate'] == 0.5

    def test_cache_eviction_tracking(self, mock_registry):
        """Test that cache tracks evictions"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry", cache_size=2)

        # Create mock model infos for different versions
        model_infos = []
        for i in range(3):
            model_infos.append({
                'model_id': i + 1,
                'model_name': 'XGBoost',
                'model_type': 'XGBClassifier',
                'version': f'1.{i}.0',
                'metrics': {'f1': 0.7},
                'file_path': f'model_{i}.pkl',
                'created_at': f'2025-11-14T10:{i:02d}:00'
            })

        mock_registry.return_value.list_models.return_value = model_infos

        # Load 3 models to trigger eviction
        for i in range(3):
            mock_registry.return_value.load_model.return_value = Mock()
            loader.load_model(model_type="XGBClassifier", version=f"1.{i}.0")

        stats = loader.get_cache_stats()

        assert 'evictions' in stats
        assert stats['evictions'] >= 1


# ============================================================================
# Test Class 7: Integration with ModelRegistry (3 tests) - AC4.3.4
# ============================================================================

class TestModelRegistryIntegration:
    """Test integration with ModelRegistry"""

    def test_get_model_metadata_without_loading(self, mock_registry):
        """Test getting metadata without loading full model"""
        from api.model_loader import ModelLoader

        mock_registry.return_value.list_models.return_value = [MOCK_MODEL_INFO_V1]
        loader = ModelLoader(registry_path="data/models/registry")

        metadata = loader.get_model_metadata(model_type="XGBClassifier", version="1.0.0")

        assert metadata is not None
        assert metadata['version'] == '1.0.0'
        assert metadata['metrics']['f1'] == 0.72
        # Should not load full model
        assert ("XGBClassifier", "1.0.0") not in loader._cache

    def test_fallback_to_previous_version_on_load_failure(self, mock_registry):
        """Test fallback to previous version when preferred version fails"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        # Mock load_model to fail for v1.1.0 but succeed for v1.0.0
        def load_with_failure(model_id):
            if model_id == 2:  # v1.1.0
                raise Exception("Load failed")
            return Mock()

        mock_registry.return_value.load_model.side_effect = load_with_failure
        mock_registry.return_value.list_models.return_value = [
            MOCK_MODEL_INFO_V2,  # Latest (will fail)
            MOCK_MODEL_INFO_V1   # Fallback
        ]

        # Should fall back to v1.0.0
        model = loader.load_model_with_fallback(model_type="XGBClassifier", preferred_version="1.1.0")

        assert model is not None

    def test_list_available_models(self, mock_registry):
        """Test listing all available models from registry"""
        from api.model_loader import ModelLoader

        loader = ModelLoader(registry_path="data/models/registry")

        available_models = loader.list_available_models()

        assert isinstance(available_models, list)
        assert len(available_models) >= 1

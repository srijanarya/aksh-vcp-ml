"""
Unit tests for Story 3.5: Model Persistence

TDD Phase: RED (write tests first)
Target: >=90% test coverage

Test Coverage:
- AC3.5.1: ModelRegistry class initialization
- AC3.5.2: Save model with metadata
- AC3.5.3: Load model by ID and version
- AC3.5.4: List models with filtering
- AC3.5.5: Get best model by metric
- AC3.5.6: Version management
- AC3.5.7: Model deletion
- AC3.5.8: Edge case handling

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import pytest
import sqlite3
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestModelRegistryInitialization:
    """Test ModelRegistry class initialization (AC3.5.1)"""

    def test_registry_class_exists(self):
        """AC3.5.1: Verify ModelRegistry can be imported"""
        from agents.ml.model_registry import ModelRegistry
        assert ModelRegistry is not None

    def test_registry_instantiation(self, tmp_path):
        """AC3.5.1: Registry can be instantiated with storage path"""
        from agents.ml.model_registry import ModelRegistry

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        assert registry.storage_path == str(registry_path)
        assert Path(registry_path).exists()

    def test_registry_creates_database(self, tmp_path):
        """AC3.5.1: Registry creates SQLite database on initialization"""
        from agents.ml.model_registry import ModelRegistry

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        db_path = Path(registry_path) / "registry.db"
        assert db_path.exists()

        # Verify table exists
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='models'")
        table_exists = cursor.fetchone()
        conn.close()

        assert table_exists is not None

    def test_registry_default_storage_path(self):
        """AC3.5.1: Registry uses default storage path if none provided"""
        from agents.ml.model_registry import ModelRegistry

        registry = ModelRegistry()

        # Should create default directory
        assert registry.storage_path is not None
        assert "data/models/registry" in registry.storage_path


class TestSaveModel:
    """Test save model functionality (AC3.5.2)"""

    def test_save_model_basic(self, tmp_path):
        """AC3.5.2: save_model saves model with metadata"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        # Create simple model
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model = LogisticRegression(random_state=42)
        model.fit(X, y)

        metrics = {
            'f1': 0.75,
            'precision': 0.72,
            'recall': 0.78,
            'roc_auc': 0.85,
            'pr_auc': 0.80
        }

        hyperparameters = {'C': 1.0, 'max_iter': 100}

        model_id = registry.save_model(
            model=model,
            model_name="logistic_regression_v1.0.0",
            model_type="LogisticRegression",
            metrics=metrics,
            hyperparameters=hyperparameters,
            description="Test model"
        )

        assert model_id is not None
        assert isinstance(model_id, int)

    def test_save_model_creates_pickle_file(self, tmp_path):
        """AC3.5.2: save_model creates joblib pickle file"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75}
        )

        # Check pickle file exists
        db_path = Path(registry_path) / "registry.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM models WHERE model_id=?", (model_id,))
        file_path = cursor.fetchone()[0]
        conn.close()

        assert Path(file_path).exists()
        assert file_path.endswith('.pkl')

    def test_save_model_stores_metadata_in_db(self, tmp_path):
        """AC3.5.2: save_model stores all metadata in database"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        metrics = {'f1': 0.75, 'roc_auc': 0.85}
        hyperparameters = {'C': 1.0}
        description = "Test model description"

        model_id = registry.save_model(
            model=model,
            model_name="test_model_v1.0.0",
            model_type="LogisticRegression",
            metrics=metrics,
            hyperparameters=hyperparameters,
            description=description
        )

        # Query database
        db_path = Path(registry_path) / "registry.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT model_name, model_type, version, metrics, hyperparameters, description
            FROM models WHERE model_id=?
        """, (model_id,))
        row = cursor.fetchone()
        conn.close()

        assert row[0] == "test_model_v1.0.0"
        assert row[1] == "LogisticRegression"
        assert row[2] == "1.0.0"
        assert json.loads(row[3]) == metrics
        assert json.loads(row[4]) == hyperparameters
        assert row[5] == description

    def test_save_model_auto_version_increment(self, tmp_path):
        """AC3.5.2: save_model auto-increments patch version"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # Save first model
        id1 = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75},
            version="1.0.0"
        )

        # Save second model with same type (should auto-increment to 1.0.1)
        id2 = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.76}
        )

        # Check versions
        db_path = Path(registry_path) / "registry.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM models WHERE model_id=?", (id1,))
        version1 = cursor.fetchone()[0]
        cursor.execute("SELECT version FROM models WHERE model_id=?", (id2,))
        version2 = cursor.fetchone()[0]
        conn.close()

        assert version1 == "1.0.0"
        assert version2 == "1.0.1"


class TestLoadModel:
    """Test load model functionality (AC3.5.3)"""

    def test_load_model_by_id(self, tmp_path):
        """AC3.5.3: load_model loads model by ID"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75}
        )

        # Load model
        loaded_model = registry.load_model(model_id=model_id)

        assert loaded_model is not None
        assert type(loaded_model).__name__ == 'LogisticRegression'

    def test_load_model_by_version(self, tmp_path):
        """AC3.5.3: load_model loads model by version"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75},
            version="2.0.0"
        )

        # Load by version
        loaded_model = registry.load_model(version="2.0.0")

        assert loaded_model is not None
        assert type(loaded_model).__name__ == 'LogisticRegression'

    def test_load_model_predictions_work(self, tmp_path):
        """AC3.5.3: Loaded model can make predictions"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        X_train = np.random.rand(100, 5)
        y_train = np.random.randint(0, 2, 100)
        model = LogisticRegression(random_state=42)
        model.fit(X_train, y_train)

        model_id = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75}
        )

        # Load and predict
        loaded_model = registry.load_model(model_id=model_id)
        X_test = np.random.rand(10, 5)
        predictions = loaded_model.predict(X_test)

        assert predictions is not None
        assert len(predictions) == 10

    def test_load_model_returns_none_if_not_found(self, tmp_path):
        """AC3.5.3: load_model returns None if model not found"""
        from agents.ml.model_registry import ModelRegistry

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        loaded_model = registry.load_model(model_id=99999)

        assert loaded_model is None


class TestListModels:
    """Test list models functionality (AC3.5.4)"""

    def test_list_models_returns_all_models(self, tmp_path):
        """AC3.5.4: list_models returns all models"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # Save multiple models
        registry.save_model(model, "model1", "LogisticRegression", {'f1': 0.75})
        registry.save_model(model, "model2", "LogisticRegression", {'f1': 0.80})

        models = registry.list_models()

        assert len(models) == 2
        assert isinstance(models, list)

    def test_list_models_filters_by_model_type(self, tmp_path):
        """AC3.5.4: list_models filters by model type"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression
        import xgboost as xgb

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)

        lr_model = LogisticRegression(random_state=42)
        lr_model.fit(X, y)

        xgb_model = xgb.XGBClassifier(random_state=42, n_estimators=10)
        xgb_model.fit(X, y)

        registry.save_model(lr_model, "lr_model", "LogisticRegression", {'f1': 0.75})
        registry.save_model(xgb_model, "xgb_model", "XGBClassifier", {'f1': 0.80})

        # Filter by type
        lr_models = registry.list_models(model_type="LogisticRegression")

        assert len(lr_models) == 1
        assert lr_models[0]['model_type'] == "LogisticRegression"

    def test_list_models_filters_by_min_f1(self, tmp_path):
        """AC3.5.4: list_models filters by minimum F1 score"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(model, "model1", "LogisticRegression", {'f1': 0.65})
        registry.save_model(model, "model2", "LogisticRegression", {'f1': 0.75})
        registry.save_model(model, "model3", "LogisticRegression", {'f1': 0.85})

        # Filter by min F1
        good_models = registry.list_models(min_f1=0.70)

        assert len(good_models) == 2
        for model_info in good_models:
            assert model_info['metrics']['f1'] >= 0.70

    def test_list_models_includes_metadata(self, tmp_path):
        """AC3.5.4: list_models returns complete metadata"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75},
            hyperparameters={'C': 1.0},
            description="Test description"
        )

        models = registry.list_models()

        assert len(models) == 1
        model_info = models[0]

        assert 'model_id' in model_info
        assert 'model_name' in model_info
        assert 'model_type' in model_info
        assert 'version' in model_info
        assert 'metrics' in model_info
        assert 'hyperparameters' in model_info
        assert 'created_at' in model_info
        assert 'description' in model_info


class TestGetBestModel:
    """Test get best model functionality (AC3.5.5)"""

    def test_get_best_model_by_f1(self, tmp_path):
        """AC3.5.5: get_best_model returns model with highest F1"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(model, "model1", "LogisticRegression", {'f1': 0.65, 'roc_auc': 0.70})
        registry.save_model(model, "model2", "LogisticRegression", {'f1': 0.85, 'roc_auc': 0.80})
        registry.save_model(model, "model3", "LogisticRegression", {'f1': 0.75, 'roc_auc': 0.90})

        best_model_info = registry.get_best_model(metric='f1')

        assert best_model_info is not None
        assert best_model_info['metrics']['f1'] == 0.85

    def test_get_best_model_by_roc_auc(self, tmp_path):
        """AC3.5.5: get_best_model supports different metrics"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(model, "model1", "LogisticRegression", {'f1': 0.65, 'roc_auc': 0.70})
        registry.save_model(model, "model2", "LogisticRegression", {'f1': 0.85, 'roc_auc': 0.80})
        registry.save_model(model, "model3", "LogisticRegression", {'f1': 0.75, 'roc_auc': 0.90})

        best_model_info = registry.get_best_model(metric='roc_auc')

        assert best_model_info is not None
        assert best_model_info['metrics']['roc_auc'] == 0.90

    def test_get_best_model_filters_by_type(self, tmp_path):
        """AC3.5.5: get_best_model can filter by model type"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression
        import xgboost as xgb

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)

        lr_model = LogisticRegression(random_state=42)
        lr_model.fit(X, y)

        xgb_model = xgb.XGBClassifier(random_state=42, n_estimators=10)
        xgb_model.fit(X, y)

        registry.save_model(lr_model, "lr_model", "LogisticRegression", {'f1': 0.75})
        registry.save_model(xgb_model, "xgb_model", "XGBClassifier", {'f1': 0.85})

        best_lr = registry.get_best_model(metric='f1', model_type="LogisticRegression")

        assert best_lr is not None
        assert best_lr['model_type'] == "LogisticRegression"


class TestVersionManagement:
    """Test version management functionality (AC3.5.6)"""

    def test_semantic_versioning_format(self, tmp_path):
        """AC3.5.6: Versions follow semantic versioning (major.minor.patch)"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75},
            version="1.2.3"
        )

        models = registry.list_models()
        version = models[0]['version']

        # Verify semantic versioning format
        parts = version.split('.')
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_auto_increment_patch_version(self, tmp_path):
        """AC3.5.6: Patch version auto-increments for same model type"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # Save three models without specifying version
        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75})
        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.76})
        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.77})

        models = registry.list_models()
        versions = [m['version'] for m in models]

        # Versions should auto-increment
        assert "1.0.0" in versions
        assert "1.0.1" in versions
        assert "1.0.2" in versions

    def test_manual_major_version_bump(self, tmp_path):
        """AC3.5.6: Can manually specify major version bump"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75}, version="1.0.0")
        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.80}, version="2.0.0")

        models = registry.list_models()
        versions = [m['version'] for m in models]

        assert "1.0.0" in versions
        assert "2.0.0" in versions

    def test_get_model_by_specific_version(self, tmp_path):
        """AC3.5.6: Can retrieve specific version of model"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75}, version="1.0.0")
        registry.save_model(model, "model", "LogisticRegression", {'f1': 0.80}, version="1.1.0")

        # Load specific version
        model_v1 = registry.load_model(version="1.0.0")
        model_v11 = registry.load_model(version="1.1.0")

        assert model_v1 is not None
        assert model_v11 is not None


class TestModelDeletion:
    """Test model deletion functionality (AC3.5.7)"""

    def test_delete_model_by_id(self, tmp_path):
        """AC3.5.7: delete_model removes model from registry"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75})

        # Delete model
        result = registry.delete_model(model_id=model_id)

        assert result is True

        # Model should not be in list
        models = registry.list_models()
        assert len(models) == 0

    def test_delete_model_removes_pickle_file(self, tmp_path):
        """AC3.5.7: delete_model removes pickle file from disk"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75})

        # Get file path before deletion
        models = registry.list_models()
        file_path = models[0]['file_path']

        # Delete model
        registry.delete_model(model_id=model_id)

        # File should not exist
        assert not Path(file_path).exists()


class TestEdgeCases:
    """Test edge case handling (AC3.5.8)"""

    def test_save_model_without_optional_params(self, tmp_path):
        """AC3.5.8: save_model works without optional parameters"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        # Save with only required params
        model_id = registry.save_model(
            model=model,
            model_name="test_model",
            model_type="LogisticRegression",
            metrics={'f1': 0.75}
        )

        assert model_id is not None

    def test_list_models_empty_registry(self, tmp_path):
        """AC3.5.8: list_models returns empty list if no models"""
        from agents.ml.model_registry import ModelRegistry

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        models = registry.list_models()

        assert models == []

    def test_get_best_model_empty_registry(self, tmp_path):
        """AC3.5.8: get_best_model returns None if no models"""
        from agents.ml.model_registry import ModelRegistry

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        best_model = registry.get_best_model(metric='f1')

        assert best_model is None

    def test_handles_corrupted_pickle_file(self, tmp_path):
        """AC3.5.8: Handles corrupted pickle file gracefully"""
        from agents.ml.model_registry import ModelRegistry
        from sklearn.linear_model import LogisticRegression

        registry_path = tmp_path / "registry"
        registry = ModelRegistry(storage_path=str(registry_path))

        model = LogisticRegression(random_state=42)
        X = np.random.rand(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)

        model_id = registry.save_model(model, "model", "LogisticRegression", {'f1': 0.75})

        # Corrupt the pickle file
        models = registry.list_models()
        file_path = models[0]['file_path']
        with open(file_path, 'w') as f:
            f.write("corrupted data")

        # Should handle gracefully
        loaded_model = registry.load_model(model_id=model_id)
        # Should return None or raise specific error
        assert loaded_model is None or isinstance(loaded_model, Exception)

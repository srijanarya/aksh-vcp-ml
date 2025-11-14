"""
Story 3.5: Model Persistence

Model registry with versioning for ML models.

Features:
- SQLite database for model metadata
- Joblib for model serialization
- Semantic versioning (major.minor.patch)
- Filter by type and metrics
- Get best model by metric
- Full CRUD operations

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import sqlite3
import json
import joblib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Model registry with versioning and metadata tracking.

    Capabilities:
    - Save models with joblib (more efficient than pickle)
    - SQLite database for metadata storage
    - Semantic versioning with auto-increment
    - Filter models by type, minimum F1, etc.
    - Get best model by any metric
    - Load models by ID or version
    - Delete models (with cleanup)

    Database Schema:
    - model_id: INTEGER PRIMARY KEY
    - model_name: TEXT
    - model_type: TEXT (XGBoost, LightGBM, etc.)
    - version: TEXT (semantic versioning)
    - metrics: TEXT (JSON: f1, roc_auc, etc.)
    - hyperparameters: TEXT (JSON)
    - file_path: TEXT (path to .pkl file)
    - created_at: TEXT (ISO timestamp)
    - description: TEXT (optional)
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize model registry (AC3.5.1)

        Args:
            storage_path: Directory for model files and database
                         (default: data/models/registry)
        """
        if storage_path is None:
            storage_path = "data/models/registry"

        self.storage_path = str(storage_path)
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        self.db_path = str(Path(self.storage_path) / "registry.db")
        self._create_database()

        logger.info(f"ModelRegistry initialized: storage_path={storage_path}")

    def _create_database(self):
        """
        Create SQLite database with models table

        Table schema:
        - model_id: INTEGER PRIMARY KEY AUTOINCREMENT
        - model_name: TEXT NOT NULL
        - model_type: TEXT NOT NULL
        - version: TEXT NOT NULL
        - metrics: TEXT NOT NULL (JSON)
        - hyperparameters: TEXT (JSON)
        - file_path: TEXT NOT NULL
        - created_at: TEXT NOT NULL
        - description: TEXT
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                version TEXT NOT NULL,
                metrics TEXT NOT NULL,
                hyperparameters TEXT,
                file_path TEXT NOT NULL,
                created_at TEXT NOT NULL,
                description TEXT
            )
        """)

        conn.commit()
        conn.close()

        logger.debug(f"Database created/verified: {self.db_path}")

    def _get_next_version(self, model_type: str, version: Optional[str] = None) -> str:
        """
        Get next version number for a model type

        Args:
            model_type: Type of model (e.g., "XGBClassifier")
            version: Manual version override (optional)

        Returns:
            Version string in format "major.minor.patch"
        """
        if version is not None:
            return version

        # Get latest version for this model type
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT version FROM models
            WHERE model_type = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (model_type,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            # First model of this type
            return "1.0.0"

        # Parse current version and increment patch
        current_version = row[0]
        parts = current_version.split('.')
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        # Auto-increment patch version
        patch += 1

        return f"{major}.{minor}.{patch}"

    def save_model(
        self,
        model: Any,
        model_name: str,
        model_type: str,
        metrics: Dict[str, float],
        hyperparameters: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        description: Optional[str] = None
    ) -> int:
        """
        Save model with metadata (AC3.5.2)

        Args:
            model: Trained model object
            model_name: Name of the model
            model_type: Type (e.g., "XGBClassifier", "LogisticRegression")
            metrics: Dictionary of metrics (f1, roc_auc, etc.)
            hyperparameters: Model hyperparameters (optional)
            version: Manual version override (optional)
            description: Model description (optional)

        Returns:
            model_id: Database ID of saved model
        """
        # Get version
        model_version = self._get_next_version(model_type, version)

        # Save model to disk using joblib
        model_filename = f"{model_type}_{model_version.replace('.', '_')}.pkl"
        model_filepath = str(Path(self.storage_path) / model_filename)

        joblib.dump(model, model_filepath)
        logger.info(f"Model saved to disk: {model_filepath}")

        # Save metadata to database
        created_at = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO models (
                model_name, model_type, version, metrics, hyperparameters,
                file_path, created_at, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            model_name,
            model_type,
            model_version,
            json.dumps(metrics),
            json.dumps(hyperparameters) if hyperparameters else None,
            model_filepath,
            created_at,
            description
        ))

        model_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Model metadata saved: id={model_id}, version={model_version}")

        return model_id

    def load_model(
        self,
        model_id: Optional[int] = None,
        version: Optional[str] = None
    ) -> Optional[Any]:
        """
        Load model by ID or version (AC3.5.3)

        Args:
            model_id: Database ID of model (optional)
            version: Version string (optional)

        Returns:
            Loaded model object, or None if not found

        Note:
            Must specify either model_id or version
        """
        if model_id is None and version is None:
            raise ValueError("Must specify either model_id or version")

        # Query database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if model_id is not None:
            cursor.execute("SELECT file_path FROM models WHERE model_id=?", (model_id,))
        else:
            cursor.execute("SELECT file_path FROM models WHERE version=?", (version,))

        row = cursor.fetchone()
        conn.close()

        if row is None:
            logger.warning(f"Model not found: id={model_id}, version={version}")
            return None

        file_path = row[0]

        # Load model from disk
        try:
            model = joblib.load(file_path)
            logger.info(f"Model loaded: {file_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model from {file_path}: {e}")
            return None

    def list_models(
        self,
        model_type: Optional[str] = None,
        min_f1: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        List models with optional filtering (AC3.5.4)

        Args:
            model_type: Filter by model type (optional)
            min_f1: Minimum F1 score (optional)

        Returns:
            List of model metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Build query
        query = "SELECT * FROM models"
        params = []

        if model_type is not None:
            query += " WHERE model_type=?"
            params.append(model_type)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Parse results
        models = []
        for row in rows:
            metrics = json.loads(row[4])

            # Filter by min F1
            if min_f1 is not None:
                if metrics.get('f1', 0) < min_f1:
                    continue

            model_info = {
                'model_id': row[0],
                'model_name': row[1],
                'model_type': row[2],
                'version': row[3],
                'metrics': metrics,
                'hyperparameters': json.loads(row[5]) if row[5] else None,
                'file_path': row[6],
                'created_at': row[7],
                'description': row[8]
            }
            models.append(model_info)

        return models

    def get_best_model(
        self,
        metric: str = 'f1',
        model_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get best model by metric (AC3.5.5)

        Args:
            metric: Metric to optimize (default: 'f1')
            model_type: Filter by model type (optional)

        Returns:
            Model metadata dictionary, or None if no models
        """
        models = self.list_models(model_type=model_type)

        if not models:
            return None

        # Find best by metric
        best_model = max(
            models,
            key=lambda m: m['metrics'].get(metric, 0)
        )

        return best_model

    def delete_model(self, model_id: int) -> bool:
        """
        Delete model from registry and disk (AC3.5.7)

        Args:
            model_id: Database ID of model to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Get file path
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT file_path FROM models WHERE model_id=?", (model_id,))
        row = cursor.fetchone()

        if row is None:
            conn.close()
            logger.warning(f"Model not found: id={model_id}")
            return False

        file_path = row[0]

        # Delete from database
        cursor.execute("DELETE FROM models WHERE model_id=?", (model_id,))
        conn.commit()
        conn.close()

        # Delete file
        try:
            Path(file_path).unlink()
            logger.info(f"Model deleted: id={model_id}, file={file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

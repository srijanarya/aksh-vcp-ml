"""
Story 4.3: Model Loading & Caching

Efficient model loading with LRU caching, lazy loading, and hot reload.

Features:
- LRU cache for loaded models (max 3 models in memory)
- Lazy loading: load model on first request
- Thread-safe caching with locks
- Hot reload: reload model without downtime
- Model versioning support
- Cache statistics: hit rate, miss rate, evictions

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import threading
from collections import OrderedDict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from agents.ml.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelLoadError(Exception):
    """Exception raised when model loading fails"""
    pass


class ModelLoader:
    """
    Model loader with LRU caching and hot reload support.

    Capabilities:
    - LRU cache with configurable size (default: 3 models)
    - Lazy loading on first request (AC4.3.2)
    - Thread-safe with locking (AC4.3.3)
    - Hot reload without downtime (AC4.3.3)
    - Cache statistics tracking (AC4.3.6)
    - Version pinning and fallback (AC4.3.4)

    Cache Key Format:
    - (model_type, version) tuple

    Performance Targets:
    - Model loading: <5 seconds
    - Cache hit latency: <1ms
    - Memory: <1GB per model
    """

    def __init__(self, registry_path: str, cache_size: int = 3):
        """
        Initialize model loader (AC4.3.1)

        Args:
            registry_path: Path to model registry
            cache_size: Maximum number of models to cache (default: 3)
        """
        self.registry_path = registry_path
        self.cache_size = cache_size

        # LRU cache: OrderedDict maintains insertion order
        # Key: (model_type, version), Value: model object
        self._cache: OrderedDict[Tuple[str, str], Any] = OrderedDict()

        # Thread lock for thread-safe operations
        self._lock = threading.Lock()

        # Cache statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'evictions': 0,
            'total_loads': 0
        }

        # Initialize registry
        self.registry = ModelRegistry(registry_path)

        logger.info(f"ModelLoader initialized: cache_size={cache_size}, registry={registry_path}")

    def load_model(
        self,
        model_type: str,
        version: Optional[str] = None
    ) -> Any:
        """
        Load model with LRU caching (AC4.3.1, AC4.3.2)

        Args:
            model_type: Type of model (e.g., "XGBClassifier", "LGBMClassifier")
            version: Specific version or None for latest

        Returns:
            Loaded model object

        Raises:
            ModelLoadError: If model loading fails
        """
        with self._lock:
            # Track total loads
            self._stats['total_loads'] += 1

            # Get version if not specified (use latest)
            if version is None:
                best_model = self.registry.get_best_model(model_type=model_type)
                if best_model is None:
                    raise ModelLoadError(f"No models found for type: {model_type}")
                version = best_model['version']

            cache_key = (model_type, version)

            # Check cache (LRU: move to end if exists)
            if cache_key in self._cache:
                logger.debug(f"Cache HIT: {cache_key}")
                self._stats['cache_hits'] += 1

                # Move to end (most recently used)
                self._cache.move_to_end(cache_key)
                return self._cache[cache_key]

            # Cache miss - load from registry
            logger.debug(f"Cache MISS: {cache_key}")
            self._stats['cache_misses'] += 1

            # Find model info
            model_info = self._find_model_info(model_type, version)
            if model_info is None:
                raise ModelLoadError(f"Model not found: {model_type} v{version}")

            # Load model from disk
            model = self.registry.load_model(model_id=model_info['model_id'])
            if model is None:
                raise ModelLoadError(f"Failed to load model: {model_type} v{version}")

            # Add to cache
            self._add_to_cache(cache_key, model)

            logger.info(f"Model loaded: {model_type} v{version}")
            return model

    def _find_model_info(self, model_type: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Find model info in registry

        Args:
            model_type: Model type
            version: Model version

        Returns:
            Model info dict or None
        """
        models = self.registry.list_models(model_type=model_type)
        for model_info in models:
            if model_info['version'] == version:
                return model_info
        return None

    def _add_to_cache(self, cache_key: Tuple[str, str], model: Any):
        """
        Add model to cache with LRU eviction

        Args:
            cache_key: (model_type, version) tuple
            model: Model object to cache
        """
        # Evict oldest if cache is full
        if len(self._cache) >= self.cache_size:
            # Remove first item (oldest)
            evicted_key = next(iter(self._cache))
            del self._cache[evicted_key]
            self._stats['evictions'] += 1
            logger.debug(f"Evicted from cache: {evicted_key}")

        # Add to cache (at end)
        self._cache[cache_key] = model

    def reload_model(self, model_type: str, version: str) -> Any:
        """
        Hot reload specific model (AC4.3.3)

        Args:
            model_type: Model type
            version: Model version

        Returns:
            Reloaded model object
        """
        with self._lock:
            cache_key = (model_type, version)

            # Remove from cache if exists
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.info(f"Removed from cache for reload: {cache_key}")

            # Load fresh model (bypasses cache check)
            model_info = self._find_model_info(model_type, version)
            if model_info is None:
                raise ModelLoadError(f"Model not found: {model_type} v{version}")

            model = self.registry.load_model(model_id=model_info['model_id'])
            if model is None:
                raise ModelLoadError(f"Failed to reload model: {model_type} v{version}")

            # Add to cache
            self._add_to_cache(cache_key, model)

            logger.info(f"Model reloaded: {model_type} v{version}")
            return model

    def reload_all_models(self) -> Dict[str, Any]:
        """
        Reload all cached models (AC4.3.3)

        Returns:
            Dictionary of reloaded models by cache key
        """
        with self._lock:
            # Get current cache keys
            cache_keys = list(self._cache.keys())

            # Clear cache
            self._cache.clear()

            # Reload all models (without additional locking)
            reloaded = {}
            for model_type, version in cache_keys:
                try:
                    # Find model info
                    model_info = self._find_model_info(model_type, version)
                    if model_info is None:
                        logger.warning(f"Model not found: {model_type} v{version}")
                        continue

                    # Load model
                    model = self.registry.load_model(model_id=model_info['model_id'])
                    if model is None:
                        logger.warning(f"Failed to reload model: {model_type} v{version}")
                        continue

                    # Add to cache
                    cache_key = (model_type, version)
                    self._add_to_cache(cache_key, model)
                    reloaded[f"{model_type}:{version}"] = model

                except Exception as e:
                    logger.error(f"Failed to reload {model_type} v{version}: {e}")

            logger.info(f"Reloaded {len(reloaded)} models")
            return reloaded

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics (AC4.3.6)

        Returns:
            Dictionary with cache metrics:
            - cache_size: Max cache size
            - cached_models: Number of models currently cached
            - cache_hits: Total cache hits
            - cache_misses: Total cache misses
            - hit_rate: Cache hit rate (0.0 to 1.0)
            - miss_rate: Cache miss rate (0.0 to 1.0)
            - evictions: Number of evictions
            - total_loads: Total load requests
        """
        with self._lock:
            total = self._stats['total_loads']
            hit_rate = self._stats['cache_hits'] / total if total > 0 else 0.0
            miss_rate = self._stats['cache_misses'] / total if total > 0 else 0.0

            return {
                'cache_size': self.cache_size,
                'cached_models': len(self._cache),
                'cache_hits': self._stats['cache_hits'],
                'cache_misses': self._stats['cache_misses'],
                'hit_rate': hit_rate,
                'miss_rate': miss_rate,
                'evictions': self._stats['evictions'],
                'total_loads': total
            }

    def get_model_metadata(
        self,
        model_type: str,
        version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get model metadata without loading full model (AC4.3.5)

        Args:
            model_type: Model type
            version: Model version

        Returns:
            Model metadata dict or None
        """
        model_info = self._find_model_info(model_type, version)
        return model_info

    def load_model_with_fallback(
        self,
        model_type: str,
        preferred_version: str,
        max_retries: int = 3
    ) -> Any:
        """
        Load model with fallback to previous versions (AC4.3.4, AC4.3.7)

        Args:
            model_type: Model type
            preferred_version: Preferred version
            max_retries: Maximum retry attempts

        Returns:
            Loaded model object

        Raises:
            ModelLoadError: If all versions fail to load
        """
        # Get all models of this type sorted by version descending
        models = self.registry.list_models(model_type=model_type)
        if not models:
            raise ModelLoadError(f"No models found for type: {model_type}")

        # Sort by created_at descending (latest first)
        models.sort(key=lambda m: m['created_at'], reverse=True)

        # Try preferred version first
        for model_info in models:
            if model_info['version'] == preferred_version:
                # Try to load with retries
                for attempt in range(max_retries):
                    try:
                        model = self.load_model(model_type, preferred_version)
                        logger.info(f"Loaded preferred version: {model_type} v{preferred_version}")
                        return model
                    except Exception as e:
                        logger.warning(f"Load attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            continue
                        else:
                            logger.warning(f"Preferred version failed, falling back")
                            break

        # Fallback to latest stable version
        for model_info in models:
            if model_info['version'] != preferred_version:
                try:
                    model = self.load_model(model_type, model_info['version'])
                    logger.info(f"Fallback successful: {model_type} v{model_info['version']}")
                    return model
                except Exception as e:
                    logger.warning(f"Fallback to {model_info['version']} failed: {e}")
                    continue

        raise ModelLoadError(f"All versions failed to load for {model_type}")

    def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models from registry

        Returns:
            List of model metadata dictionaries
        """
        return self.registry.list_models()

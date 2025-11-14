"""
Story 7.2: Model Inference Optimization

Provides ONNX conversion, quantization, and benchmarking for faster model inference.

Target: 2.5x inference speedup through ONNX Runtime
"""

import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logging.warning("ONNX Runtime not available. Install with: pip install onnxruntime")

try:
    import onnxmltools
    from onnxmltools.convert import convert_xgboost, convert_lightgbm
    from onnxmltools.convert.common.data_types import FloatTensorType as OnnxmlFloatTensorType
    ONNXMLTOOLS_AVAILABLE = True
except ImportError:
    ONNXMLTOOLS_AVAILABLE = False
    OnnxmlFloatTensorType = None
    logging.warning("onnxmltools not available. Install with: pip install onnxmltools")

try:
    from skl2onnx import to_onnx
    from skl2onnx.common.data_types import FloatTensorType as Skl2onnxFloatTensorType
    SKL2ONNX_AVAILABLE = True
except ImportError:
    SKL2ONNX_AVAILABLE = False
    Skl2onnxFloatTensorType = None
    logging.warning("skl2onnx not available. Install with: pip install skl2onnx")

try:
    from onnxruntime.quantization import quantize_dynamic, QuantType
    QUANTIZATION_AVAILABLE = True
except ImportError:
    QUANTIZATION_AVAILABLE = False
    logging.warning("ONNX quantization not available")

logger = logging.getLogger(__name__)


class InferenceOptimizer:
    """
    Optimize model inference through ONNX conversion and quantization.

    Features:
    - Convert XGBoost/LightGBM/Sklearn to ONNX format
    - Quantize models (FP32 -> INT8)
    - Benchmark inference performance
    - 2.5x+ speedup target

    Usage:
        optimizer = InferenceOptimizer(model_dir="data/models/onnx")

        # Convert model
        onnx_path = optimizer.convert_to_onnx(
            xgb_model,
            model_type="xgboost",
            output_path="model.onnx",
            input_shape=(None, 25)
        )

        # Quantize
        quantized_path = optimizer.quantize_model(onnx_path, "model_int8.onnx")

        # Benchmark
        results = optimizer.benchmark_inference(
            original_model=xgb_model,
            onnx_model_path=quantized_path,
            test_features=X_test
        )
    """

    def __init__(self, model_dir: str = "data/models/onnx"):
        """
        Initialize inference optimizer.

        Args:
            model_dir: Directory to store ONNX models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        if not ONNX_AVAILABLE:
            raise ImportError("ONNX Runtime required. Install: pip install onnxruntime")

    def convert_to_onnx(
        self,
        model: Any,
        model_type: str,
        output_path: str,
        input_shape: Tuple[Optional[int], int] = (None, 25)
    ) -> str:
        """
        Convert trained model to ONNX format.

        Args:
            model: Trained model (XGBoost, LightGBM, Sklearn)
            model_type: Model type ("xgboost", "lightgbm", "sklearn")
            output_path: Path to save ONNX model
            input_shape: Input tensor shape (batch_size, n_features)

        Returns:
            Path to saved ONNX model

        Raises:
            ValueError: If model_type is not supported
            ImportError: If required conversion library not available
        """
        model_type = model_type.lower()

        if model_type == "xgboost":
            if not ONNXMLTOOLS_AVAILABLE:
                raise ImportError("onnxmltools required for XGBoost conversion")
            return self._convert_xgboost(model, output_path, input_shape)

        elif model_type == "lightgbm":
            if not ONNXMLTOOLS_AVAILABLE:
                raise ImportError("onnxmltools required for LightGBM conversion")
            return self._convert_lightgbm(model, output_path, input_shape)

        elif model_type == "sklearn":
            if not SKL2ONNX_AVAILABLE:
                raise ImportError("skl2onnx required for Sklearn conversion")
            return self._convert_sklearn(model, output_path, input_shape)

        else:
            raise ValueError(
                f"Unsupported model_type: {model_type}. "
                f"Supported: xgboost, lightgbm, sklearn"
            )

    def _convert_xgboost(
        self,
        model: Any,
        output_path: str,
        input_shape: Tuple[Optional[int], int]
    ) -> str:
        """Convert XGBoost model to ONNX"""
        try:
            # Define initial types for ONNX conversion - use onnxmltools type
            initial_type = [('float_input', OnnxmlFloatTensorType([None, input_shape[1]]))]

            # Convert using onnxmltools
            onnx_model = convert_xgboost(
                model,
                initial_types=initial_type,
                target_opset=12
            )

            # Save ONNX model
            with open(output_path, "wb") as f:
                f.write(onnx_model.SerializeToString())

            logger.info(f"XGBoost model converted to ONNX: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"XGBoost conversion failed: {e}")
            raise

    def _convert_lightgbm(
        self,
        model: Any,
        output_path: str,
        input_shape: Tuple[Optional[int], int]
    ) -> str:
        """Convert LightGBM model to ONNX"""
        try:
            # Define initial types - use onnxmltools type
            initial_type = [('float_input', OnnxmlFloatTensorType([None, input_shape[1]]))]

            # Convert using onnxmltools
            onnx_model = convert_lightgbm(
                model,
                initial_types=initial_type,
                target_opset=12
            )

            # Save ONNX model
            with open(output_path, "wb") as f:
                f.write(onnx_model.SerializeToString())

            logger.info(f"LightGBM model converted to ONNX: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"LightGBM conversion failed: {e}")
            raise

    def _convert_sklearn(
        self,
        model: Any,
        output_path: str,
        input_shape: Tuple[Optional[int], int]
    ) -> str:
        """Convert Sklearn model to ONNX"""
        try:
            # Convert using skl2onnx
            onnx_model = to_onnx(
                model,
                X=np.zeros((1, input_shape[1]), dtype=np.float32),
                target_opset=12
            )

            # Save ONNX model
            with open(output_path, "wb") as f:
                f.write(onnx_model.SerializeToString())

            logger.info(f"Sklearn model converted to ONNX: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Sklearn conversion failed: {e}")
            raise

    def quantize_model(
        self,
        onnx_model_path: str,
        output_path: str
    ) -> str:
        """
        Quantize ONNX model from FP32 to INT8.

        Args:
            onnx_model_path: Path to FP32 ONNX model
            output_path: Path to save quantized INT8 model

        Returns:
            Path to quantized model

        Raises:
            ImportError: If quantization not available
        """
        if not QUANTIZATION_AVAILABLE:
            raise ImportError("ONNX quantization not available")

        try:
            # Fix opset import issue for XGBoost/LightGBM models
            import onnx
            model = onnx.load(onnx_model_path)

            # Ensure proper opset is set
            if len(model.opset_import) == 0 or not any(
                opset.domain in ['', 'ai.onnx'] for opset in model.opset_import
            ):
                # Add ai.onnx opset if missing
                model.opset_import.append(onnx.helper.make_opsetid('ai.onnx', 12))

                # Save fixed model temporarily
                temp_path = onnx_model_path + '.fixed.onnx'
                onnx.save(model, temp_path)
                onnx_model_path = temp_path

            # Dynamic quantization (weights only, faster inference)
            quantize_dynamic(
                model_input=onnx_model_path,
                model_output=output_path,
                weight_type=QuantType.QInt8
            )

            # Clean up temp file if created
            if onnx_model_path.endswith('.fixed.onnx'):
                os.remove(onnx_model_path)

            # Log size reduction
            fp32_size = os.path.getsize(onnx_model_path.replace('.fixed.onnx', ''))
            int8_size = os.path.getsize(output_path)
            reduction = (1 - int8_size / fp32_size) * 100 if fp32_size > 0 else 0

            logger.info(
                f"Model quantized: {onnx_model_path} -> {output_path}\n"
                f"Size: {fp32_size:,} bytes -> {int8_size:,} bytes "
                f"({reduction:.1f}% reduction)"
            )

            return output_path

        except Exception as e:
            logger.error(f"Quantization failed: {e}")
            raise

    def load_onnx_model(
        self,
        model_path: str,
        use_gpu: bool = False
    ) -> ort.InferenceSession:
        """
        Load ONNX model for inference.

        Args:
            model_path: Path to ONNX model
            use_gpu: Whether to use GPU (if available)

        Returns:
            ONNX Runtime inference session
        """
        providers = []

        if use_gpu:
            # Try CUDA first, fallback to CPU
            available_providers = ort.get_available_providers()
            if 'CUDAExecutionProvider' in available_providers:
                providers.append('CUDAExecutionProvider')
                logger.info("Using GPU (CUDA) for inference")
            else:
                logger.warning("GPU requested but CUDA not available, using CPU")

        providers.append('CPUExecutionProvider')

        session = ort.InferenceSession(model_path, providers=providers)
        logger.info(f"ONNX model loaded: {model_path} (providers: {session.get_providers()})")

        return session

    def predict_with_onnx(
        self,
        session: ort.InferenceSession,
        features: np.ndarray
    ) -> np.ndarray:
        """
        Run inference with ONNX model.

        Args:
            session: ONNX Runtime session
            features: Input features (N, n_features)

        Returns:
            Predictions (N,) - probabilities for positive class
        """
        # Ensure float32 dtype
        if features.dtype != np.float32:
            features = features.astype(np.float32)

        # Get input name
        input_name = session.get_inputs()[0].name

        # Run inference - get all outputs
        outputs = session.run(None, {input_name: features})

        # XGBoost/LightGBM models output 2 values: [labels, probabilities]
        # We want probabilities for consistency with sklearn predict_proba
        if len(outputs) == 2:
            # Output 0: labels (int64), Output 1: probabilities (float32)
            probabilities = outputs[1]

            # If binary classification with 2 columns, take positive class
            if len(probabilities.shape) == 2 and probabilities.shape[1] == 2:
                return probabilities[:, 1]
            else:
                return probabilities.flatten()
        else:
            # Single output - handle different shapes
            predictions = outputs[0]

            # If binary classification with 2 columns, take positive class
            if len(predictions.shape) == 2 and predictions.shape[1] == 2:
                predictions = predictions[:, 1]
            # If single column, flatten
            elif len(predictions.shape) == 2 and predictions.shape[1] == 1:
                predictions = predictions.flatten()

            return predictions

    def benchmark_inference(
        self,
        original_model: Any,
        onnx_model_path: str,
        test_features: np.ndarray,
        num_iterations: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark original vs ONNX model inference.

        Args:
            original_model: Original trained model
            onnx_model_path: Path to ONNX model
            test_features: Test features
            num_iterations: Number of iterations for timing

        Returns:
            Dictionary with timing metrics and speedup
        """
        # Benchmark original model
        start = time.time()
        for _ in range(num_iterations):
            if hasattr(original_model, 'predict_proba'):
                _ = original_model.predict_proba(test_features)
            else:
                _ = original_model.predict(test_features)
        original_time = time.time() - start

        # Benchmark ONNX model
        session = self.load_onnx_model(onnx_model_path)
        start = time.time()
        for _ in range(num_iterations):
            _ = self.predict_with_onnx(session, test_features)
        onnx_time = time.time() - start

        # Calculate metrics
        original_time_ms = (original_time / num_iterations) * 1000
        onnx_time_ms = (onnx_time / num_iterations) * 1000
        speedup = original_time / onnx_time

        n_samples = len(test_features)
        original_throughput = (n_samples * num_iterations) / original_time
        onnx_throughput = (n_samples * num_iterations) / onnx_time

        results = {
            'original_time_ms': original_time_ms,
            'onnx_time_ms': onnx_time_ms,
            'speedup': speedup,
            'original_throughput': original_throughput,
            'onnx_throughput': onnx_throughput
        }

        logger.info(
            f"Benchmark Results ({num_iterations} iterations):\n"
            f"  Original: {original_time_ms:.2f} ms/prediction "
            f"({original_throughput:.0f} pred/sec)\n"
            f"  ONNX:     {onnx_time_ms:.2f} ms/prediction "
            f"({onnx_throughput:.0f} pred/sec)\n"
            f"  Speedup:  {speedup:.2f}x"
        )

        return results

    def benchmark_multiple_formats(
        self,
        original_model: Any,
        onnx_fp32_path: str,
        onnx_int8_path: str,
        test_features: np.ndarray,
        num_iterations: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """
        Benchmark original, ONNX FP32, and ONNX INT8 models.

        Args:
            original_model: Original trained model
            onnx_fp32_path: Path to FP32 ONNX model
            onnx_int8_path: Path to INT8 quantized model
            test_features: Test features
            num_iterations: Number of iterations

        Returns:
            Dictionary with metrics for each model format
        """
        results = {}

        # Benchmark original
        start = time.time()
        for _ in range(num_iterations):
            if hasattr(original_model, 'predict_proba'):
                _ = original_model.predict_proba(test_features)
            else:
                _ = original_model.predict(test_features)
        original_time = time.time() - start

        results['original'] = {
            'time_ms': (original_time / num_iterations) * 1000,
            'throughput': (len(test_features) * num_iterations) / original_time
        }

        # Benchmark ONNX FP32
        fp32_session = self.load_onnx_model(onnx_fp32_path)
        start = time.time()
        for _ in range(num_iterations):
            _ = self.predict_with_onnx(fp32_session, test_features)
        fp32_time = time.time() - start

        results['onnx_fp32'] = {
            'time_ms': (fp32_time / num_iterations) * 1000,
            'throughput': (len(test_features) * num_iterations) / fp32_time
        }

        # Benchmark ONNX INT8
        int8_session = self.load_onnx_model(onnx_int8_path)
        start = time.time()
        for _ in range(num_iterations):
            _ = self.predict_with_onnx(int8_session, test_features)
        int8_time = time.time() - start

        results['onnx_int8'] = {
            'time_ms': (int8_time / num_iterations) * 1000,
            'throughput': (len(test_features) * num_iterations) / int8_time
        }

        logger.info(
            f"Multi-Format Benchmark:\n"
            f"  Original:  {results['original']['time_ms']:.2f} ms "
            f"({results['original']['throughput']:.0f} pred/sec)\n"
            f"  ONNX FP32: {results['onnx_fp32']['time_ms']:.2f} ms "
            f"({results['onnx_fp32']['throughput']:.0f} pred/sec)\n"
            f"  ONNX INT8: {results['onnx_int8']['time_ms']:.2f} ms "
            f"({results['onnx_int8']['throughput']:.0f} pred/sec)"
        )

        return results

    def benchmark_with_percentiles(
        self,
        onnx_model_path: str,
        test_features: np.ndarray,
        num_iterations: int = 100
    ) -> Dict[str, float]:
        """
        Benchmark ONNX model with latency percentiles.

        Args:
            onnx_model_path: Path to ONNX model
            test_features: Test features
            num_iterations: Number of iterations

        Returns:
            Dictionary with p50, p95, p99 latency
        """
        session = self.load_onnx_model(onnx_model_path)

        # Run iterations and collect timings
        latencies = []
        for _ in range(num_iterations):
            start = time.time()
            _ = self.predict_with_onnx(session, test_features)
            latencies.append((time.time() - start) * 1000)  # Convert to ms

        # Calculate percentiles
        latencies = np.array(latencies)
        results = {
            'p50_ms': np.percentile(latencies, 50),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'mean_ms': np.mean(latencies),
            'std_ms': np.std(latencies)
        }

        logger.info(
            f"Latency Percentiles ({num_iterations} iterations):\n"
            f"  p50: {results['p50_ms']:.2f} ms\n"
            f"  p95: {results['p95_ms']:.2f} ms\n"
            f"  p99: {results['p99_ms']:.2f} ms\n"
            f"  Mean: {results['mean_ms']:.2f} ± {results['std_ms']:.2f} ms"
        )

        return results

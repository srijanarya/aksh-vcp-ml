"""
Arize Phoenix Observability for RAG System

Monitors:
- RAG query performance
- Embedding quality
- Retrieval accuracy
- Response generation

Usage:
    from src.observability.phoenix_monitor import start_phoenix_monitoring

    start_phoenix_monitoring()
    # Your RAG queries will now be monitored
"""

import logging
import os
from typing import Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Phoenix availability check
PHOENIX_AVAILABLE = False
try:
    import phoenix as px
    from phoenix.trace import using_project
    from phoenix.otel import register
    PHOENIX_AVAILABLE = True
except ImportError:
    logger.warning("phoenix not installed. Observability will be disabled.")


class PhoenixMonitor:
    """
    Arize Phoenix monitoring for RAG system

    Features:
    - Trace RAG queries end-to-end
    - Monitor embedding generation
    - Track retrieval performance
    - Measure response quality
    """

    def __init__(self, project_name: str = "vcp-rag-system"):
        """
        Initialize Phoenix monitoring

        Args:
            project_name: Name for Phoenix project
        """
        self.project_name = project_name
        self.enabled = PHOENIX_AVAILABLE
        self._session = None

        if self.enabled:
            try:
                # Start Phoenix in the background
                self._session = px.launch_app()
                logger.info(f"Phoenix monitoring started: http://localhost:6006")
                logger.info(f"Project: {project_name}")

                # Register Phoenix as OTEL tracer
                register(project_name=project_name)

            except Exception as e:
                logger.warning(f"Phoenix initialization failed: {e}")
                self.enabled = False
        else:
            logger.warning("Phoenix not available - install: pip install arize-phoenix-otel")

    @contextmanager
    def trace_rag_query(self, query: str, metadata: Optional[dict] = None):
        """
        Context manager to trace a RAG query

        Args:
            query: The query being executed
            metadata: Additional metadata to log

        Usage:
            with monitor.trace_rag_query("What was TCS revenue?"):
                result = rag_engine.query("What was TCS revenue?")
        """
        if not self.enabled:
            yield
            return

        try:
            with using_project(self.project_name):
                # Phoenix will automatically capture LlamaIndex operations
                logger.debug(f"Tracing query: {query[:50]}...")
                yield
        except Exception as e:
            logger.warning(f"Phoenix tracing failed: {e}")
            yield

    def stop(self):
        """Stop Phoenix monitoring"""
        if self._session:
            try:
                self._session.stop()
                logger.info("Phoenix monitoring stopped")
            except:
                pass

    def get_dashboard_url(self) -> str:
        """Get Phoenix dashboard URL"""
        return "http://localhost:6006" if self.enabled else "Phoenix not available"

    @property
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.enabled


# Global monitor instance
_phoenix_monitor_instance: Optional[PhoenixMonitor] = None


def start_phoenix_monitoring(project_name: str = "vcp-rag-system") -> PhoenixMonitor:
    """
    Start Phoenix monitoring (singleton)

    Args:
        project_name: Name for Phoenix project

    Returns:
        PhoenixMonitor instance
    """
    global _phoenix_monitor_instance

    if _phoenix_monitor_instance is None:
        _phoenix_monitor_instance = PhoenixMonitor(project_name=project_name)

    return _phoenix_monitor_instance


def get_phoenix_monitor() -> Optional[PhoenixMonitor]:
    """Get existing Phoenix monitor instance"""
    return _phoenix_monitor_instance


def stop_phoenix_monitoring():
    """Stop Phoenix monitoring"""
    global _phoenix_monitor_instance

    if _phoenix_monitor_instance:
        _phoenix_monitor_instance.stop()
        _phoenix_monitor_instance = None

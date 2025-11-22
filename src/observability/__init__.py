"""
Observability Module - Phoenix + AgentOps Integration

Provides unified monitoring for:
- RAG queries (Phoenix)
- Multi-agent workflows (AgentOps)
- System health metrics

Usage:
    from src.observability import start_monitoring, monitor_workflow

    # Start all monitoring
    start_monitoring()

    # Monitor a workflow
    with monitor_workflow("vcp-analysis", symbol="TCS"):
        result = run_analysis("TCS")
"""

from src.observability.phoenix_monitor import (
    PhoenixMonitor,
    start_phoenix_monitoring,
    get_phoenix_monitor,
    stop_phoenix_monitoring
)

from src.observability.agentops_monitor import (
    AgentOpsMonitor,
    init_agentops,
    get_agentops_monitor
)

from contextlib import contextmanager
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = [
    'PhoenixMonitor',
    'AgentOpsMonitor',
    'start_monitoring',
    'monitor_workflow',
    'get_monitoring_status',
    'stop_monitoring'
]


def start_monitoring(
    project_name: str = "vcp-rag-system",
    agentops_api_key: Optional[str] = None,
    enable_phoenix: bool = True,
    enable_agentops: bool = True
) -> Dict[str, Any]:
    """
    Start all monitoring systems

    Args:
        project_name: Phoenix project name
        agentops_api_key: AgentOps API key (optional)
        enable_phoenix: Enable Phoenix RAG monitoring
        enable_agentops: Enable AgentOps workflow monitoring

    Returns:
        Dict with monitoring status
    """
    status = {
        "phoenix": {"enabled": False, "url": None},
        "agentops": {"enabled": False}
    }

    # Start Phoenix
    if enable_phoenix:
        try:
            phoenix = start_phoenix_monitoring(project_name=project_name)
            status["phoenix"]["enabled"] = phoenix.is_enabled
            status["phoenix"]["url"] = phoenix.get_dashboard_url()
            logger.info(f"Phoenix monitoring: {'enabled' if phoenix.is_enabled else 'disabled'}")
        except Exception as e:
            logger.warning(f"Phoenix startup failed: {e}")

    # Start AgentOps
    if enable_agentops:
        try:
            agentops = init_agentops(api_key=agentops_api_key)
            status["agentops"]["enabled"] = agentops.is_enabled
            logger.info(f"AgentOps monitoring: {'enabled' if agentops.is_enabled else 'disabled'}")
        except Exception as e:
            logger.warning(f"AgentOps startup failed: {e}")

    return status


@contextmanager
def monitor_workflow(
    workflow_name: str,
    **metadata
):
    """
    Context manager to monitor a complete workflow

    Args:
        workflow_name: Name of the workflow
        **metadata: Additional workflow metadata

    Usage:
        with monitor_workflow("vcp-analysis", symbol="TCS"):
            result = run_analysis("TCS")
    """
    agentops = get_agentops_monitor()
    phoenix = get_phoenix_monitor()

    # Start workflow tracking
    if agentops and agentops.is_enabled:
        agentops.start_workflow(workflow_name, metadata)

    try:
        # Phoenix automatically tracks RAG operations
        if phoenix and phoenix.is_enabled:
            with phoenix.trace_rag_query(f"Workflow: {workflow_name}", metadata):
                yield
        else:
            yield

        # End workflow successfully
        if agentops and agentops.is_enabled:
            agentops.end_workflow(workflow_name, status="Success", metadata=metadata)

    except Exception as e:
        # End workflow with failure
        if agentops and agentops.is_enabled:
            agentops.end_workflow(
                workflow_name,
                status="Fail",
                metadata={"error": str(e), **metadata}
            )
        raise


def get_monitoring_status() -> Dict[str, Any]:
    """
    Get current monitoring status

    Returns:
        Dict with status of all monitoring systems
    """
    phoenix = get_phoenix_monitor()
    agentops = get_agentops_monitor()

    return {
        "phoenix": {
            "enabled": phoenix.is_enabled if phoenix else False,
            "url": phoenix.get_dashboard_url() if phoenix else None
        },
        "agentops": {
            "enabled": agentops.is_enabled if agentops else False
        }
    }


def stop_monitoring():
    """Stop all monitoring systems"""
    stop_phoenix_monitoring()
    logger.info("All monitoring stopped")

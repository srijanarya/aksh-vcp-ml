"""
AgentOps Workflow Monitoring

Monitors:
- Multi-agent workflow execution
- Agent performance metrics
- Workflow success/failure rates
- Cost tracking

Usage:
    from src.observability.agentops_monitor import init_agentops

    session = init_agentops()
    # Your workflow will now be monitored
    session.end_session("Success")
"""

import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# AgentOps availability check
AGENTOPS_AVAILABLE = False
try:
    import agentops
    AGENTOPS_AVAILABLE = True
except ImportError:
    logger.warning("agentops not installed. Workflow monitoring will be disabled.")


class AgentOpsMonitor:
    """
    AgentOps monitoring for multi-agent workflows

    Features:
    - Track workflow execution
    - Monitor agent performance
    - Cost analysis
    - Success/failure tracking
    """

    def __init__(self, api_key: Optional[str] = None, tags: Optional[list] = None):
        """
        Initialize AgentOps monitoring

        Args:
            api_key: AgentOps API key (defaults to env var)
            tags: Tags for this session
        """
        self.enabled = AGENTOPS_AVAILABLE
        self.session = None
        self.api_key = api_key or os.getenv("AGENTOPS_API_KEY")

        if self.enabled and self.api_key:
            try:
                # Initialize AgentOps
                agentops.init(
                    api_key=self.api_key,
                    tags=tags or ["vcp-workflow", "financial-analysis"]
                )
                self.session = agentops
                logger.info("AgentOps monitoring initialized")

            except Exception as e:
                logger.warning(f"AgentOps initialization failed: {e}")
                self.enabled = False
        else:
            if not self.api_key:
                logger.warning("AGENTOPS_API_KEY not set, monitoring disabled")
            else:
                logger.warning("AgentOps not available - install: pip install agentops")
            self.enabled = False

    def start_workflow(self, workflow_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Start tracking a workflow

        Args:
            workflow_name: Name of the workflow
            metadata: Additional workflow metadata
        """
        if not self.enabled or not self.session:
            return

        try:
            # Record workflow start event
            self.session.record(
                agentops.Event(
                    event_type="workflow_start",
                    params={
                        "workflow_name": workflow_name,
                        "timestamp": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                )
            )
            logger.debug(f"Workflow started: {workflow_name}")

        except Exception as e:
            logger.warning(f"Failed to record workflow start: {e}")

    def record_agent_action(
        self,
        agent_name: str,
        action: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """
        Record an agent action

        Args:
            agent_name: Name of the agent
            action: Action performed
            result: Action result metadata
        """
        if not self.enabled or not self.session:
            return

        try:
            self.session.record(
                agentops.Action(
                    action_type=action,
                    params={
                        "agent_name": agent_name,
                        "timestamp": datetime.now().isoformat(),
                        **(result or {})
                    }
                )
            )
            logger.debug(f"Agent action recorded: {agent_name} - {action}")

        except Exception as e:
            logger.warning(f"Failed to record agent action: {e}")

    def end_workflow(
        self,
        workflow_name: str,
        status: str = "Success",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        End tracking a workflow

        Args:
            workflow_name: Name of the workflow
            status: Workflow status (Success/Fail)
            metadata: Additional metadata
        """
        if not self.enabled or not self.session:
            return

        try:
            self.session.end_session(
                end_state=status,
                end_state_reason=metadata.get("reason") if metadata else None
            )
            logger.info(f"Workflow ended: {workflow_name} - {status}")

        except Exception as e:
            logger.warning(f"Failed to end workflow: {e}")

    @property
    def is_enabled(self) -> bool:
        """Check if monitoring is enabled"""
        return self.enabled


# Global monitor instance
_agentops_monitor_instance: Optional[AgentOpsMonitor] = None


def init_agentops(
    api_key: Optional[str] = None,
    tags: Optional[list] = None
) -> AgentOpsMonitor:
    """
    Initialize AgentOps monitoring (singleton)

    Args:
        api_key: AgentOps API key
        tags: Session tags

    Returns:
        AgentOpsMonitor instance
    """
    global _agentops_monitor_instance

    if _agentops_monitor_instance is None:
        _agentops_monitor_instance = AgentOpsMonitor(api_key=api_key, tags=tags)

    return _agentops_monitor_instance


def get_agentops_monitor() -> Optional[AgentOpsMonitor]:
    """Get existing AgentOps monitor instance"""
    return _agentops_monitor_instance

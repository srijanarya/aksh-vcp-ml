"""
Multi-Agent Workflow System

Sequential and parallel agent orchestration for VCP financial research.
"""

from agents.workflows.vcp_workflow import (
    VCPWorkflow,
    WorkflowResult,
    get_vcp_workflow
)

__all__ = [
    'VCPWorkflow',
    'WorkflowResult',
    'get_vcp_workflow'
]

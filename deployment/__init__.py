"""
VCP ML Platform - Autonomous Deployment System

Complete deployment automation for the VCP ML Platform.

Features:
- Pre-deployment validation
- Staging & production deployment
- Smoke tests
- Health monitoring
- Automatic rollback
- Notifications

Author: VCP Financial Research Team
Created: 2025-11-14
"""

from .agents import (
    PreDeploymentValidator,
    DeploymentOrchestrator,
    SmokeTestRunner,
    DeploymentMonitor,
    RollbackAgent,
)

from .tools import (
    DockerManager,
    EnvironmentManager,
    NotificationManager,
)

__version__ = "1.0.0"

__all__ = [
    # Agents
    'PreDeploymentValidator',
    'DeploymentOrchestrator',
    'SmokeTestRunner',
    'DeploymentMonitor',
    'RollbackAgent',

    # Tools
    'DockerManager',
    'EnvironmentManager',
    'NotificationManager',
]

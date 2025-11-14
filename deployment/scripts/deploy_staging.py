#!/usr/bin/env python3
"""
Autonomous deployment to staging environment

Usage: python deployment/scripts/deploy_staging.py

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from deployment.agents.deployment_orchestrator import DeploymentOrchestrator


def main():
    """Deploy to staging environment"""
    print("="*80)
    print("VCP ML PLATFORM - STAGING DEPLOYMENT")
    print("="*80)
    print()

    orchestrator = DeploymentOrchestrator(environment="staging")
    result = orchestrator.deploy()

    print("\n" + "="*80)
    if result.success:
        print("✅ STAGING DEPLOYMENT SUCCESSFUL!")
        print("="*80)
        print(f"Environment: {result.environment}")
        print(f"Version: {result.version}")
        print(f"URL: {result.url}")
        print(f"Health Status: {result.health_status}")
        print(f"Deployment ID: {result.deployment_id}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print()
        print("Next steps:")
        print("1. Verify application at: {result.url}")
        print("2. Check health: {result.url}/api/v1/health")
        print("3. View docs: {result.url}/docs")
        print()
        return 0
    else:
        print("❌ STAGING DEPLOYMENT FAILED!")
        print("="*80)
        print(f"Error: {result.error}")
        print(f"Deployment ID: {result.deployment_id}")
        print()
        return 1


if __name__ == "__main__":
    exit(main())

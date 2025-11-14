#!/usr/bin/env python3
"""
Autonomous deployment to production environment

Requires staging deployment to pass first

Usage: python deployment/scripts/deploy_production.py

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from deployment.agents.deployment_orchestrator import DeploymentOrchestrator
from deployment.agents.rollback_agent import RollbackAgent


def main():
    """Deploy to production environment"""
    print("="*80)
    print("VCP ML PLATFORM - PRODUCTION DEPLOYMENT")
    print("="*80)
    print()
    print("⚠️  WARNING: This will deploy to PRODUCTION")
    print()

    # Confirm production deployment
    response = input("Continue with production deployment? (yes/no): ")
    if response.lower() != 'yes':
        print("Deployment cancelled")
        return 0

    # Save current state for rollback
    print("\n📦 Saving current state for rollback...")
    rollback = RollbackAgent()
    rollback.save_deployment_state(
        version="pre_deploy_backup",
        image_tag="vcp-ml:current",
        backup_data=False
    )

    # Deploy to production
    print("\n🚀 Starting production deployment...")
    orchestrator = DeploymentOrchestrator(environment="production")
    result = orchestrator.deploy()

    print("\n" + "="*80)
    if result.success:
        print("✅ PRODUCTION DEPLOYMENT SUCCESSFUL!")
        print("="*80)
        print(f"Environment: {result.environment}")
        print(f"Version: {result.version}")
        print(f"URL: {result.url}")
        print(f"Health Status: {result.health_status}")
        print(f"Deployment ID: {result.deployment_id}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        print()
        print("Production deployment complete!")
        print()
        return 0
    else:
        print("❌ PRODUCTION DEPLOYMENT FAILED!")
        print("="*80)
        print(f"Error: {result.error}")
        print()
        print("Initiating automatic rollback...")

        rollback_result = rollback.execute_rollback("pre_deploy_backup")
        if rollback_result.success:
            print("✅ Rollback successful")
        else:
            print(f"❌ Rollback failed: {rollback_result.message}")

        return 1


if __name__ == "__main__":
    exit(main())

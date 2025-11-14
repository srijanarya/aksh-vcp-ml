#!/usr/bin/env python3
"""
Quick Deployment Script

Fastest path to deployment (skips Docker build for speed)

Usage: python deployment/scripts/quick_deploy.py [staging|production]

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from deployment.agents.pre_deployment_validator import PreDeploymentValidator
from deployment.agents.smoke_test_runner import SmokeTestRunner


def quick_deploy(environment: str = "staging"):
    """
    Quick deployment (validation + smoke tests only)

    Args:
        environment: Target environment
    """
    print("="*80)
    print(f"VCP ML PLATFORM - QUICK DEPLOYMENT ({environment.upper()})")
    print("="*80)
    print()

    # Step 1: Quick validation (skip Docker)
    print("📋 Step 1: Quick Validation (skipping Docker build)")
    print("-"*80)

    validator = PreDeploymentValidator()
    report = validator.validate_all(skip_docker=True)

    if not report.overall_passed:
        print(f"\n❌ Validation failed: {report.failed_checks} checks failed")
        for result in report.results:
            if not result.passed:
                print(f"  - {result.check_name}: {result.message}")
        return 1

    print(f"✅ Validation passed ({report.passed_checks}/{report.total_checks} checks)")
    print()

    # Step 2: Check if API is already running
    print("🔍 Step 2: Checking API Status")
    print("-"*80)

    port = 8001 if environment == "staging" else 8000
    url = f"http://localhost:{port}"

    import requests
    try:
        response = requests.get(f"{url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API already running at {url}")
        else:
            print(f"⚠️  API responded but health check failed")
    except:
        print(f"❌ API not running at {url}")
        print(f"   Start with: uvicorn api.main:app --host 0.0.0.0 --port {port}")
        return 1

    print()

    # Step 3: Run smoke tests
    print("🧪 Step 3: Running Smoke Tests")
    print("-"*80)

    runner = SmokeTestRunner(base_url=url)
    smoke_report = runner.run_all_smoke_tests()

    if not smoke_report.overall_passed:
        print(f"\n❌ Smoke tests failed: {smoke_report.failed_tests} tests failed")
        for result in smoke_report.results:
            if not result.passed:
                print(f"  - {result.test_name}: {result.message}")
        return 1

    print(f"✅ Smoke tests passed ({smoke_report.passed_tests}/{smoke_report.total_tests} tests)")
    print(f"📊 Average response time: {smoke_report.avg_response_time_ms:.2f}ms")
    print()

    # Success
    print("="*80)
    print("✅ QUICK DEPLOYMENT VERIFIED!")
    print("="*80)
    print(f"Environment: {environment}")
    print(f"URL: {url}")
    print(f"Health: {url}/api/v1/health")
    print(f"Docs: {url}/docs")
    print()

    return 0


def main():
    """Main entry point"""
    environment = sys.argv[1] if len(sys.argv) > 1 else "staging"

    if environment not in ["staging", "production"]:
        print("Usage: python quick_deploy.py [staging|production]")
        return 1

    return quick_deploy(environment)


if __name__ == "__main__":
    exit(main())

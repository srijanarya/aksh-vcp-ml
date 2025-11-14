"""
Agent 2: Deployment Orchestrator

Coordinates complete deployment workflow:
1. Pre-deployment validation
2. Docker build
3. Deploy to staging
4. Run smoke tests
5. Deploy to production
6. Monitor deployment
7. Send notifications

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import time
import subprocess
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .pre_deployment_validator import PreDeploymentValidator
from .smoke_test_runner import SmokeTestRunner
from .deployment_monitor import DeploymentMonitor
from .rollback_agent import RollbackAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentResult:
    """Complete deployment result"""
    success: bool
    environment: str
    version: str
    url: str
    health_status: str
    deployment_id: str
    timestamp: str
    duration_seconds: float
    error: Optional[str] = None
    details: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class DeploymentOrchestrator:
    """
    Deployment orchestration agent

    Coordinates complete deployment workflow
    """

    def __init__(
        self,
        environment: str = "staging",
        project_root: Optional[Path] = None
    ):
        """
        Initialize deployment orchestrator

        Args:
            environment: Target environment (staging/production)
            project_root: Project root directory
        """
        self.environment = environment
        self.project_root = project_root or Path.cwd()
        self.deployment_id = f"deploy_{environment}_{int(time.time())}"

        # Initialize agents
        self.validator = PreDeploymentValidator(self.project_root)
        self.rollback_agent = RollbackAgent()

        # Environment-specific configuration
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load environment-specific configuration"""
        if self.environment == "production":
            return {
                'port': 8000,
                'workers': 4,
                'image_tag': f'vcp-ml:prod-{int(time.time())}',
                'container_name': 'vcp-ml-production',
                'monitoring_duration': 300,  # 5 minutes
                'smoke_test_url': 'http://localhost:8000'
            }
        else:  # staging
            return {
                'port': 8001,
                'workers': 2,
                'image_tag': f'vcp-ml:staging-{int(time.time())}',
                'container_name': 'vcp-ml-staging',
                'monitoring_duration': 60,  # 1 minute
                'smoke_test_url': 'http://localhost:8001'
            }

    def deploy(self) -> DeploymentResult:
        """
        Execute complete deployment workflow

        Returns:
            DeploymentResult with deployment details
        """
        logger.info(f"🚀 Starting deployment to {self.environment}")
        logger.info(f"📋 Deployment ID: {self.deployment_id}")
        start_time = time.time()

        try:
            # Step 1: Pre-deployment validation
            logger.info("\n" + "="*80)
            logger.info("STEP 1: PRE-DEPLOYMENT VALIDATION")
            logger.info("="*80)

            validation_report = self.validator.validate_all(skip_docker=False)
            if not validation_report.overall_passed:
                return DeploymentResult(
                    success=False,
                    environment=self.environment,
                    version="unknown",
                    url="",
                    health_status="validation_failed",
                    deployment_id=self.deployment_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - start_time,
                    error="Pre-deployment validation failed",
                    details={'validation_report': validation_report.to_dict()}
                )

            logger.info("✅ Pre-deployment validation passed")

            # Step 2: Build Docker image
            logger.info("\n" + "="*80)
            logger.info("STEP 2: BUILD DOCKER IMAGE")
            logger.info("="*80)

            build_success = self._build_docker_image()
            if not build_success:
                return DeploymentResult(
                    success=False,
                    environment=self.environment,
                    version=self.config['image_tag'],
                    url="",
                    health_status="build_failed",
                    deployment_id=self.deployment_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - start_time,
                    error="Docker build failed"
                )

            logger.info(f"✅ Docker image built: {self.config['image_tag']}")

            # Step 3: Save current state (for rollback)
            logger.info("\n" + "="*80)
            logger.info("STEP 3: SAVE DEPLOYMENT STATE")
            logger.info("="*80)

            current_container = self._get_current_container()
            self.rollback_agent.save_deployment_state(
                version="previous",
                image_tag="vcp-ml:previous" if not current_container else "vcp-ml:current",
                container_id=current_container,
                backup_data=False  # Skip data backup for speed
            )

            # Step 4: Deploy container
            logger.info("\n" + "="*80)
            logger.info(f"STEP 4: DEPLOY TO {self.environment.upper()}")
            logger.info("="*80)

            container_id = self._deploy_container()
            if not container_id:
                return DeploymentResult(
                    success=False,
                    environment=self.environment,
                    version=self.config['image_tag'],
                    url="",
                    health_status="deploy_failed",
                    deployment_id=self.deployment_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - start_time,
                    error="Container deployment failed"
                )

            logger.info(f"✅ Container deployed: {container_id[:12]}")

            # Wait for startup
            logger.info("⏳ Waiting for API to start (30 seconds)...")
            time.sleep(30)

            # Step 5: Run smoke tests
            logger.info("\n" + "="*80)
            logger.info("STEP 5: RUN SMOKE TESTS")
            logger.info("="*80)

            smoke_runner = SmokeTestRunner(base_url=self.config['smoke_test_url'])
            smoke_report = smoke_runner.run_all_smoke_tests()

            if not smoke_report.overall_passed:
                logger.error("❌ Smoke tests failed - triggering rollback")
                self._trigger_rollback("Smoke tests failed")

                return DeploymentResult(
                    success=False,
                    environment=self.environment,
                    version=self.config['image_tag'],
                    url=self.config['smoke_test_url'],
                    health_status="smoke_tests_failed",
                    deployment_id=self.deployment_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - start_time,
                    error="Smoke tests failed",
                    details={'smoke_report': smoke_report.to_dict()}
                )

            logger.info("✅ Smoke tests passed")

            # Step 6: Monitor deployment
            logger.info("\n" + "="*80)
            logger.info("STEP 6: MONITOR DEPLOYMENT")
            logger.info("="*80)

            monitor = DeploymentMonitor(base_url=self.config['smoke_test_url'])
            monitoring_result = monitor.monitor_deployment(
                deployment_id=self.deployment_id,
                duration=self.config['monitoring_duration']
            )

            if not monitoring_result.passed:
                logger.error("❌ Monitoring failed - triggering rollback")
                self._trigger_rollback("Health monitoring failed")

                return DeploymentResult(
                    success=False,
                    environment=self.environment,
                    version=self.config['image_tag'],
                    url=self.config['smoke_test_url'],
                    health_status="monitoring_failed",
                    deployment_id=self.deployment_id,
                    timestamp=datetime.now().isoformat(),
                    duration_seconds=time.time() - start_time,
                    error="Deployment monitoring failed",
                    details={'monitoring_result': monitoring_result.to_dict()}
                )

            logger.info("✅ Monitoring completed successfully")

            # Step 7: Deployment complete
            duration = time.time() - start_time

            logger.info("\n" + "="*80)
            logger.info("DEPLOYMENT COMPLETE!")
            logger.info("="*80)
            logger.info(f"Environment: {self.environment}")
            logger.info(f"Version: {self.config['image_tag']}")
            logger.info(f"URL: {self.config['smoke_test_url']}")
            logger.info(f"Duration: {duration:.2f}s")

            return DeploymentResult(
                success=True,
                environment=self.environment,
                version=self.config['image_tag'],
                url=self.config['smoke_test_url'],
                health_status="healthy",
                deployment_id=self.deployment_id,
                timestamp=datetime.now().isoformat(),
                duration_seconds=duration,
                details={
                    'container_id': container_id,
                    'validation_report': validation_report.to_dict(),
                    'smoke_report': smoke_report.to_dict(),
                    'monitoring_result': monitoring_result.to_dict()
                }
            )

        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}", exc_info=True)
            return DeploymentResult(
                success=False,
                environment=self.environment,
                version=self.config['image_tag'],
                url="",
                health_status="error",
                deployment_id=self.deployment_id,
                timestamp=datetime.now().isoformat(),
                duration_seconds=time.time() - start_time,
                error=str(e)
            )

    def _build_docker_image(self) -> bool:
        """Build Docker image"""
        try:
            logger.info(f"Building image: {self.config['image_tag']}")
            result = subprocess.run(
                ['docker', 'build', '-t', self.config['image_tag'], '.'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Docker build error: {e}")
            return False

    def _deploy_container(self) -> Optional[str]:
        """Deploy Docker container"""
        try:
            # Stop existing container if running
            existing = self._get_current_container()
            if existing:
                logger.info(f"Stopping existing container: {existing[:12]}")
                subprocess.run(['docker', 'stop', existing], check=True)
                subprocess.run(['docker', 'rm', existing], check=True)

            # Start new container
            logger.info(f"Starting container on port {self.config['port']}")
            result = subprocess.run(
                [
                    'docker', 'run', '-d',
                    '-p', f"{self.config['port']}:8000",
                    '--name', self.config['container_name'],
                    '-v', f"{self.project_root}/data:/app/data",
                    self.config['image_tag']
                ],
                capture_output=True,
                text=True,
                check=True
            )
            container_id = result.stdout.strip()
            return container_id

        except Exception as e:
            logger.error(f"Container deployment error: {e}")
            return None

    def _get_current_container(self) -> Optional[str]:
        """Get current running container ID"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.config["container_name"]}', '--format', '{{.ID}}'],
                capture_output=True,
                text=True
            )
            container_id = result.stdout.strip()
            return container_id if container_id else None
        except:
            return None

    def _trigger_rollback(self, reason: str):
        """Trigger deployment rollback"""
        logger.error(f"🔄 Triggering rollback: {reason}")
        rollback_result = self.rollback_agent.execute_rollback("previous")

        if rollback_result.success:
            logger.info("✅ Rollback successful")
        else:
            logger.error(f"❌ Rollback failed: {rollback_result.message}")


if __name__ == "__main__":
    """Run deployment orchestrator"""
    import sys

    environment = sys.argv[1] if len(sys.argv) > 1 else "staging"

    orchestrator = DeploymentOrchestrator(environment=environment)
    result = orchestrator.deploy()

    if result.success:
        print(f"\n✅ DEPLOYMENT SUCCESSFUL")
        print(f"Environment: {result.environment}")
        print(f"URL: {result.url}")
        print(f"Duration: {result.duration_seconds:.2f}s")
        exit(0)
    else:
        print(f"\n❌ DEPLOYMENT FAILED")
        print(f"Error: {result.error}")
        exit(1)

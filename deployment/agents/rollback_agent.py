"""
Agent 5: Rollback Agent

Handles deployment rollbacks:
- Save deployment state
- Execute rollback
- Verify rollback success

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentState:
    """Deployment state snapshot"""
    version: str
    timestamp: str
    image_tag: str
    container_id: Optional[str] = None
    port: int = 8000
    data_backup_path: Optional[str] = None


@dataclass
class RollbackResult:
    """Result of rollback operation"""
    success: bool
    message: str
    previous_version: str
    new_version: str
    timestamp: str
    details: Optional[Dict] = None


class RollbackAgent:
    """
    Rollback agent

    Handles deployment rollbacks safely
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize rollback agent

        Args:
            state_dir: Directory to store deployment states
        """
        self.state_dir = state_dir or Path.cwd() / 'deployment' / 'state'
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save_deployment_state(
        self,
        version: str,
        image_tag: str,
        container_id: Optional[str] = None,
        backup_data: bool = False
    ) -> DeploymentState:
        """
        Save current deployment state

        Args:
            version: Version identifier
            image_tag: Docker image tag
            container_id: Running container ID
            backup_data: Whether to backup data directory

        Returns:
            DeploymentState object
        """
        logger.info(f"💾 Saving deployment state: {version}")

        data_backup_path = None
        if backup_data:
            # Backup data directory
            data_dir = Path.cwd() / 'data'
            if data_dir.exists():
                backup_dir = self.state_dir / f"data_backup_{version}_{int(datetime.now().timestamp())}"
                shutil.copytree(data_dir, backup_dir)
                data_backup_path = str(backup_dir)
                logger.info(f"  📦 Data backed up to {backup_dir}")

        state = DeploymentState(
            version=version,
            timestamp=datetime.now().isoformat(),
            image_tag=image_tag,
            container_id=container_id,
            data_backup_path=data_backup_path
        )

        # Save state to file
        state_file = self.state_dir / f"state_{version}.json"
        with open(state_file, 'w') as f:
            json.dump(asdict(state), f, indent=2)

        logger.info(f"  ✅ State saved to {state_file}")
        return state

    def load_deployment_state(self, version: str) -> Optional[DeploymentState]:
        """
        Load deployment state from file

        Args:
            version: Version to load

        Returns:
            DeploymentState if found, None otherwise
        """
        state_file = self.state_dir / f"state_{version}.json"

        if not state_file.exists():
            logger.error(f"State file not found: {state_file}")
            return None

        with open(state_file, 'r') as f:
            data = json.load(f)
            return DeploymentState(**data)

    def execute_rollback(self, target_version: str) -> RollbackResult:
        """
        Execute rollback to specific version

        Args:
            target_version: Version to rollback to

        Returns:
            RollbackResult with rollback details
        """
        logger.info(f"🔄 Executing rollback to version: {target_version}")

        # Load target state
        target_state = self.load_deployment_state(target_version)
        if not target_state:
            return RollbackResult(
                success=False,
                message=f"Target version {target_version} not found",
                previous_version="unknown",
                new_version=target_version,
                timestamp=datetime.now().isoformat()
            )

        try:
            # Get current container
            current_container = self._get_current_container()

            # Stop current container
            if current_container:
                logger.info(f"  🛑 Stopping current container: {current_container}")
                subprocess.run(['docker', 'stop', current_container], check=True)
                subprocess.run(['docker', 'rm', current_container], check=True)

            # Start container with target image
            logger.info(f"  🚀 Starting container with image: {target_state.image_tag}")
            result = subprocess.run(
                [
                    'docker', 'run', '-d',
                    '-p', f'{target_state.port}:8000',
                    '--name', f'vcp-ml-{target_version}',
                    target_state.image_tag
                ],
                capture_output=True,
                text=True,
                check=True
            )
            new_container_id = result.stdout.strip()

            # Restore data if backup exists
            if target_state.data_backup_path:
                logger.info(f"  📦 Restoring data from backup...")
                data_dir = Path.cwd() / 'data'
                if data_dir.exists():
                    shutil.rmtree(data_dir)
                shutil.copytree(target_state.data_backup_path, data_dir)

            # Wait for health check
            logger.info("  🏥 Waiting for health check...")
            time.sleep(10)

            return RollbackResult(
                success=True,
                message=f"Successfully rolled back to {target_version}",
                previous_version=current_container or "unknown",
                new_version=target_version,
                timestamp=datetime.now().isoformat(),
                details={
                    'new_container_id': new_container_id,
                    'image_tag': target_state.image_tag
                }
            )

        except subprocess.CalledProcessError as e:
            return RollbackResult(
                success=False,
                message=f"Rollback failed: {e}",
                previous_version="unknown",
                new_version=target_version,
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            return RollbackResult(
                success=False,
                message=f"Rollback error: {e}",
                previous_version="unknown",
                new_version=target_version,
                timestamp=datetime.now().isoformat()
            )

    def verify_rollback(self, target_version: str) -> bool:
        """
        Verify rollback was successful

        Args:
            target_version: Expected version after rollback

        Returns:
            True if rollback verified, False otherwise
        """
        logger.info(f"✓ Verifying rollback to {target_version}...")

        try:
            # Check container is running
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name=vcp-ml-{target_version}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True
            )

            if 'Up' in result.stdout:
                logger.info("  ✅ Container is running")
                return True
            else:
                logger.error("  ❌ Container not running")
                return False

        except Exception as e:
            logger.error(f"  ❌ Verification failed: {e}")
            return False

    def _get_current_container(self) -> Optional[str]:
        """Get current running container ID"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'ancestor=vcp-ml', '--format', '{{.ID}}'],
                capture_output=True,
                text=True
            )
            container_id = result.stdout.strip()
            return container_id if container_id else None
        except:
            return None


if __name__ == "__main__":
    """Test rollback agent"""
    import sys
    import time

    if len(sys.argv) < 2:
        print("Usage: python rollback_agent.py <target_version>")
        exit(1)

    target_version = sys.argv[1]

    agent = RollbackAgent()
    result = agent.execute_rollback(target_version)

    if result.success:
        print(f"\n✅ ROLLBACK SUCCESSFUL")
        print(f"Rolled back to version: {target_version}")
        verified = agent.verify_rollback(target_version)
        if verified:
            print("✓ Rollback verified")
        exit(0)
    else:
        print(f"\n❌ ROLLBACK FAILED")
        print(f"Error: {result.message}")
        exit(1)

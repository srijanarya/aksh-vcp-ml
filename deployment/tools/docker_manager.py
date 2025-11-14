"""
Tool 1: Docker Manager

Manages Docker operations:
- Build images
- Push to registry
- Deploy containers
- Stop containers

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import subprocess
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerManager:
    """Docker operations manager"""

    def build_image(self, tag: str, dockerfile: str = "Dockerfile", context: str = ".") -> str:
        """
        Build Docker image

        Args:
            tag: Image tag
            dockerfile: Path to Dockerfile
            context: Build context directory

        Returns:
            Image ID if successful

        Raises:
            RuntimeError: If build fails
        """
        logger.info(f"🐳 Building Docker image: {tag}")

        try:
            result = subprocess.run(
                ['docker', 'build', '-t', tag, '-f', dockerfile, context],
                capture_output=True,
                text=True,
                check=True,
                timeout=300
            )

            # Extract image ID from output
            for line in result.stdout.split('\n'):
                if 'Successfully built' in line:
                    image_id = line.split()[-1]
                    logger.info(f"✅ Image built: {image_id}")
                    return image_id

            logger.warning("Image built but ID not found in output")
            return tag

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Build failed: {e.stderr}")
            raise RuntimeError(f"Docker build failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Docker build timed out after 300 seconds")

    def push_image(self, tag: str, registry: Optional[str] = None) -> bool:
        """
        Push image to registry

        Args:
            tag: Image tag to push
            registry: Registry URL (optional)

        Returns:
            True if successful
        """
        full_tag = f"{registry}/{tag}" if registry else tag
        logger.info(f"📤 Pushing image: {full_tag}")

        try:
            # Tag image if registry specified
            if registry:
                subprocess.run(
                    ['docker', 'tag', tag, full_tag],
                    check=True,
                    capture_output=True
                )

            # Push image
            result = subprocess.run(
                ['docker', 'push', full_tag],
                capture_output=True,
                text=True,
                check=True,
                timeout=600
            )

            logger.info(f"✅ Image pushed: {full_tag}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Push failed: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Push timed out after 600 seconds")
            return False

    def deploy_container(
        self,
        tag: str,
        port: int = 8000,
        name: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, str]] = None,
        detached: bool = True
    ) -> str:
        """
        Deploy Docker container

        Args:
            tag: Image tag to deploy
            port: Host port to expose
            name: Container name
            env_vars: Environment variables
            volumes: Volume mappings (host:container)
            detached: Run in detached mode

        Returns:
            Container ID if successful

        Raises:
            RuntimeError: If deployment fails
        """
        logger.info(f"🚀 Deploying container: {tag}")

        cmd = ['docker', 'run']

        if detached:
            cmd.append('-d')

        if name:
            cmd.extend(['--name', name])

        cmd.extend(['-p', f'{port}:8000'])

        # Add environment variables
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(['-e', f'{key}={value}'])

        # Add volumes
        if volumes:
            for host_path, container_path in volumes.items():
                cmd.extend(['-v', f'{host_path}:{container_path}'])

        cmd.append(tag)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )

            container_id = result.stdout.strip()
            logger.info(f"✅ Container deployed: {container_id[:12]}")
            return container_id

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Deployment failed: {e.stderr}")
            raise RuntimeError(f"Container deployment failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Container deployment timed out")

    def stop_container(self, container_id: str, remove: bool = True) -> bool:
        """
        Stop running container

        Args:
            container_id: Container ID or name
            remove: Also remove container

        Returns:
            True if successful
        """
        logger.info(f"🛑 Stopping container: {container_id[:12]}")

        try:
            # Stop container
            subprocess.run(
                ['docker', 'stop', container_id],
                check=True,
                capture_output=True,
                timeout=30
            )

            # Remove container if requested
            if remove:
                subprocess.run(
                    ['docker', 'rm', container_id],
                    check=True,
                    capture_output=True,
                    timeout=10
                )
                logger.info(f"✅ Container stopped and removed: {container_id[:12]}")
            else:
                logger.info(f"✅ Container stopped: {container_id[:12]}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Stop failed: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Stop timed out")
            return False

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """
        Get container logs

        Args:
            container_id: Container ID or name
            tail: Number of lines to retrieve

        Returns:
            Container logs
        """
        try:
            result = subprocess.run(
                ['docker', 'logs', '--tail', str(tail), container_id],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout + result.stderr
        except:
            return ""

    def is_container_running(self, container_id: str) -> bool:
        """
        Check if container is running

        Args:
            container_id: Container ID or name

        Returns:
            True if running
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'id={container_id}', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 'Up' in result.stdout
        except:
            return False


if __name__ == "__main__":
    """Test Docker manager"""
    manager = DockerManager()

    # Build test image
    try:
        image_id = manager.build_image(tag="test:latest")
        print(f"✅ Built image: {image_id}")

        # Deploy container
        container_id = manager.deploy_container(
            tag="test:latest",
            port=8000,
            name="test-container"
        )
        print(f"✅ Deployed container: {container_id[:12]}")

        # Stop container
        manager.stop_container(container_id)
        print(f"✅ Stopped container")

    except Exception as e:
        print(f"❌ Error: {e}")

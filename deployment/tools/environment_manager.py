"""
Tool 2: Environment Manager

Manages environment configuration:
- Load environment files
- Validate environment variables
- Set environment variables

Author: VCP Financial Research Team
Created: 2025-11-14
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Environment configuration manager"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize environment manager

        Args:
            config_dir: Directory containing .env files
        """
        self.config_dir = config_dir or Path.cwd() / 'deployment' / 'config'

    def load_env_file(self, env: str = "staging") -> Dict[str, str]:
        """
        Load environment file

        Args:
            env: Environment name (staging/production)

        Returns:
            Dictionary of environment variables

        Raises:
            FileNotFoundError: If env file not found
        """
        env_file = self.config_dir / f".env.{env}"

        if not env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {env_file}")

        logger.info(f"📄 Loading environment file: {env_file}")

        env_vars = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        logger.info(f"✅ Loaded {len(env_vars)} environment variables")
        return env_vars

    def validate_env_vars(self, required: List[str]) -> bool:
        """
        Validate all required environment variables are set

        Args:
            required: List of required variable names

        Returns:
            True if all required vars are set
        """
        logger.info(f"🔍 Validating {len(required)} required environment variables...")

        missing = []
        for var in required:
            if not os.getenv(var):
                missing.append(var)

        if missing:
            logger.error(f"❌ Missing required variables: {', '.join(missing)}")
            return False

        logger.info(f"✅ All required variables are set")
        return True

    def set_env_vars(self, vars: Dict[str, str]):
        """
        Set environment variables

        Args:
            vars: Dictionary of variables to set
        """
        logger.info(f"⚙️  Setting {len(vars)} environment variables...")

        for key, value in vars.items():
            os.environ[key] = value

        logger.info(f"✅ Environment variables set")

    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable with optional default

        Args:
            key: Variable name
            default: Default value if not set

        Returns:
            Variable value or default
        """
        return os.getenv(key, default)

    def create_env_file(self, env: str, vars: Dict[str, str]):
        """
        Create new environment file

        Args:
            env: Environment name
            vars: Variables to write
        """
        env_file = self.config_dir / f".env.{env}"
        logger.info(f"📝 Creating environment file: {env_file}")

        with open(env_file, 'w') as f:
            f.write(f"# Environment configuration for {env}\n")
            f.write(f"# Generated: {os.popen('date').read().strip()}\n\n")

            for key, value in vars.items():
                f.write(f"{key}={value}\n")

        logger.info(f"✅ Environment file created with {len(vars)} variables")


if __name__ == "__main__":
    """Test environment manager"""
    manager = EnvironmentManager()

    # Create sample staging env
    staging_vars = {
        'ENVIRONMENT': 'staging',
        'API_HOST': '0.0.0.0',
        'API_PORT': '8001',
        'LOG_LEVEL': 'DEBUG',
        'DATABASE_PATH': '/data/staging/vcp_trading_local.db',
        'MODEL_REGISTRY_PATH': '/data/staging/model_registry.db',
    }

    manager.create_env_file('staging', staging_vars)

    # Load and validate
    loaded_vars = manager.load_env_file('staging')
    print(f"✅ Loaded {len(loaded_vars)} variables")

    # Set environment
    manager.set_env_vars(loaded_vars)

    # Validate
    required = ['ENVIRONMENT', 'API_HOST', 'API_PORT']
    is_valid = manager.validate_env_vars(required)
    print(f"✅ Validation: {'PASSED' if is_valid else 'FAILED'}")

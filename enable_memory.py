#!/usr/bin/env python3
"""
Enable Memori Memory System for VCP Financial Research

This script enables global memory for all agents in the VCP trading system.
Run this once at application startup or as a standalone test.

Usage:
    python enable_memory.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger

# Configure loguru for better output
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)


def main():
    """Enable global memory system"""
    logger.info("=" * 70)
    logger.info("VCP Financial Research - Memori Memory Integration")
    logger.info("=" * 70)

    # Check environment
    logger.info("Checking environment...")

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("OPENAI_API_KEY not set - memory features may be limited")
    else:
        logger.success("OPENAI_API_KEY found ✓")

    # Import memory module
    logger.info("Importing memory modules...")
    try:
        from src.memory import enable_global_memory, get_memori_instance, MemoriConfig
        logger.success("Memory modules imported successfully ✓")
    except Exception as e:
        logger.error(f"Failed to import memory modules: {e}")
        return 1

    # Enable global memory
    logger.info("Enabling global memory system...")
    try:
        enable_global_memory()
        logger.success("Global memory enabled ✓")
    except Exception as e:
        logger.error(f"Failed to enable global memory: {e}")
        return 1

    # Test memory instance creation
    logger.info("Testing memory instance creation...")
    try:
        test_memori = get_memori_instance(
            namespace="test",
            user_id="test_user"
        )
        if test_memori:
            logger.success("Memory instance created successfully ✓")
            logger.info(f"Database: {MemoriConfig.get_database_url()}")
        else:
            logger.warning("Memory instance creation returned None")
            return 1
    except Exception as e:
        logger.error(f"Failed to create memory instance: {e}")
        return 1

    # Test orchestrator integration
    logger.info("Testing MLMasterOrchestrator integration...")
    try:
        from agents.ml.ml_master_orchestrator import MLMasterOrchestrator

        orchestrator = MLMasterOrchestrator()

        if orchestrator.memori:
            logger.success("Orchestrator memory integration successful ✓")
            logger.info(f"Orchestrator has access to memory system")
        else:
            logger.warning("Orchestrator memory is None - check initialization")

    except Exception as e:
        logger.error(f"Failed to test orchestrator: {e}")
        logger.exception("Full traceback:")
        return 1

    # Summary
    logger.info("=" * 70)
    logger.success("Memory system integration complete!")
    logger.info("=" * 70)
    logger.info("Next steps:")
    logger.info("1. Agents will now remember past interactions")
    logger.info("2. VCP patterns will be stored in memory")
    logger.info("3. Earnings data context will be preserved")
    logger.info("4. Strategies will learn from past results")
    logger.info("")
    logger.info(f"Memory database: {MemoriConfig.MEMORY_DB_PATH}")
    logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

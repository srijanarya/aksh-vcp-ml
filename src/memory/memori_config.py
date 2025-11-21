"""
Memori Configuration for VCP Financial Research System

This module provides configuration and initialization for Memori memory engine,
enabling persistent memory across agent interactions.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path
from loguru import logger

try:
    from memori import Memori
    MEMORI_AVAILABLE = True
except ImportError:
    logger.warning("Memori SDK not installed. Memory features will be disabled.")
    MEMORI_AVAILABLE = False


class MemoriConfig:
    """Configuration for Memori memory system"""

    # Default paths
    DATA_DIR = Path("/Users/srijan/Desktop/aksh/data")
    MEMORY_DB_PATH = DATA_DIR / "agent_memory.db"

    # Memory modes
    CONSCIOUS_INGEST = True  # Load essential context at startup
    AUTO_INGEST = True       # Dynamic search per query

    # Namespaces for different agent types
    NAMESPACE_ORCHESTRATOR = "ml_orchestrator"
    NAMESPACE_DATA_COLLECTOR = "data_collector"
    NAMESPACE_FEATURE_ENGINEER = "feature_engineer"
    NAMESPACE_TRAINING = "ml_training"
    NAMESPACE_INFERENCE = "ml_inference"
    NAMESPACE_MONITORING = "ml_monitoring"
    NAMESPACE_BACKTESTING = "backtesting"
    NAMESPACE_SHARED = "vcp_system_global"

    # Performance settings
    MEMORY_SEARCH_LIMIT = 5  # Top N memories to retrieve
    MEMORY_RETENTION_DAYS = 90  # Days to keep memories

    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        # Check environment variable first
        db_url = os.getenv("MEMORI_DATABASE_CONNECTION")
        if db_url:
            return db_url

        # Use default SQLite path
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{cls.MEMORY_DB_PATH}"

    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key for memory processing"""
        return os.getenv("OPENAI_API_KEY") or os.getenv("MEMORI_OPENAI_API_KEY")


# Singleton instance for global memory
_global_memori_instance: Optional[Memori] = None


def get_memori_instance(
    namespace: str = MemoriConfig.NAMESPACE_SHARED,
    user_id: str = "vcp_trading_system",
    conscious_ingest: bool = MemoriConfig.CONSCIOUS_INGEST,
    auto_ingest: bool = MemoriConfig.AUTO_INGEST,
    force_new: bool = False,
) -> Optional[Memori]:
    """
    Get or create a Memori instance for agent memory

    Args:
        namespace: Memory namespace for isolation
        user_id: User ID for multi-tenant support
        conscious_ingest: Enable short-term working memory
        auto_ingest: Enable dynamic search per query
        force_new: Force creation of new instance

    Returns:
        Memori instance or None if not available

    Example:
        >>> memori = get_memori_instance(namespace="ml_training")
        >>> if memori:
        >>>     memori.enable()
    """
    global _global_memori_instance

    if not MEMORI_AVAILABLE:
        logger.warning("Memori SDK not available - memory features disabled")
        return None

    # Return existing instance if available
    if _global_memori_instance is not None and not force_new:
        return _global_memori_instance

    try:
        # Get configuration
        database_url = MemoriConfig.get_database_url()
        api_key = MemoriConfig.get_openai_api_key()

        if not api_key:
            logger.warning(
                "No OpenAI API key found. Set OPENAI_API_KEY environment variable "
                "for full memory functionality."
            )

        # Create Memori instance
        memori = Memori(
            database_connect=database_url,
            conscious_ingest=conscious_ingest,
            auto_ingest=auto_ingest,
            user_id=user_id,
            namespace=namespace,
            openai_api_key=api_key,
        )

        logger.info(
            f"Memori initialized: database={database_url}, "
            f"namespace={namespace}, conscious={conscious_ingest}, "
            f"auto={auto_ingest}"
        )

        # Store as global instance
        _global_memori_instance = memori

        return memori

    except Exception as e:
        logger.error(f"Failed to initialize Memori: {e}")
        return None


def create_agent_memory(
    agent_name: str,
    agent_type: str,
    namespace: Optional[str] = None,
) -> Optional[Memori]:
    """
    Create memory instance for a specific agent

    Args:
        agent_name: Name of the agent (e.g., "MLTrainingAgent")
        agent_type: Type of agent for namespace selection
        namespace: Override namespace (optional)

    Returns:
        Memori instance configured for the agent

    Example:
        >>> memory = create_agent_memory(
        ...     agent_name="MLTrainingAgent",
        ...     agent_type="training"
        ... )
    """
    # Map agent types to namespaces
    namespace_map = {
        "orchestrator": MemoriConfig.NAMESPACE_ORCHESTRATOR,
        "data_collector": MemoriConfig.NAMESPACE_DATA_COLLECTOR,
        "feature_engineer": MemoriConfig.NAMESPACE_FEATURE_ENGINEER,
        "training": MemoriConfig.NAMESPACE_TRAINING,
        "inference": MemoriConfig.NAMESPACE_INFERENCE,
        "monitoring": MemoriConfig.NAMESPACE_MONITORING,
        "backtesting": MemoriConfig.NAMESPACE_BACKTESTING,
    }

    # Use provided namespace or map from agent type
    ns = namespace or namespace_map.get(agent_type, MemoriConfig.NAMESPACE_SHARED)

    # Create unique user_id for agent
    user_id = f"{agent_type}_{agent_name}"

    logger.info(f"Creating memory for {agent_name} with namespace={ns}")

    return get_memori_instance(
        namespace=ns,
        user_id=user_id,
        force_new=True,
    )


def search_memory(
    query: str,
    memori_instance: Optional[Memori] = None,
    limit: int = MemoriConfig.MEMORY_SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Search memory for relevant past interactions

    Args:
        query: Search query
        memori_instance: Memori instance (uses global if None)
        limit: Maximum number of results

    Returns:
        List of relevant memories

    Example:
        >>> results = search_memory("best hyperparameters for XGBoost")
        >>> for memory in results:
        ...     print(memory['content'])
    """
    if not MEMORI_AVAILABLE:
        logger.debug("Memori not available - skipping memory search")
        return []

    # Use provided instance or global
    memori = memori_instance or _global_memori_instance

    if memori is None:
        logger.warning("No Memori instance available for search")
        return []

    try:
        # Search memory (implementation depends on Memori API)
        # This is a placeholder - actual implementation may vary
        logger.debug(f"Searching memory: {query}")

        # TODO: Implement actual memory search using Memori API
        # For now, return empty list
        return []

    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        return []


def enable_global_memory():
    """
    Enable global memory for all agent interactions

    Call this once at application startup to enable memory
    for all agents using the default configuration.

    Example:
        >>> from src.memory import enable_global_memory
        >>> enable_global_memory()
    """
    memori = get_memori_instance()
    if memori:
        try:
            memori.enable()
            logger.info("Global memory enabled for all agents")
        except Exception as e:
            logger.error(f"Failed to enable global memory: {e}")
    else:
        logger.warning("Could not enable global memory - Memori not available")


def disable_global_memory():
    """
    Disable global memory

    Useful for testing or when memory is not needed.
    """
    global _global_memori_instance

    if _global_memori_instance:
        try:
            # Memori doesn't have explicit disable - just clear instance
            _global_memori_instance = None
            logger.info("Global memory disabled")
        except Exception as e:
            logger.error(f"Failed to disable global memory: {e}")


# Convenience function for quick memory queries
def remember(query: str) -> List[Dict[str, Any]]:
    """
    Quick memory search - simplified API

    Args:
        query: What to remember

    Returns:
        Relevant memories

    Example:
        >>> memories = remember("What stocks had VCP patterns last month?")
    """
    return search_memory(query)

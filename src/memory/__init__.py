"""
Memory module for VCP Financial Research System

This module provides Memori integration for persistent agent memory,
enabling intelligent learning across sessions.
"""

from .memori_config import (
    get_memori_instance,
    MemoriConfig,
    create_agent_memory,
    search_memory,
    enable_global_memory,
    disable_global_memory,
    remember,
)

__all__ = [
    "get_memori_instance",
    "MemoriConfig",
    "create_agent_memory",
    "search_memory",
    "enable_global_memory",
    "disable_global_memory",
    "remember",
]

"""
Monitoring Package (Epic 5)

Provides monitoring and alerting capabilities:
- Performance monitoring (Story 5.1)
- Data drift detection (Story 5.2)
- Model degradation alerts (Story 5.3)
- Structured logging (Story 5.4)
- Metrics dashboard (Story 5.5)

Author: VCP ML Team
Created: 2025-11-14
"""

from monitoring.performance_monitor import PerformanceMonitor, get_metrics_text

__all__ = [
    'PerformanceMonitor',
    'get_metrics_text',
]

__version__ = '1.0.0'

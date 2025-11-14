"""
Tools Library - Reusable utility functions for ML agents

Tools are pure functions that agents can use for common tasks:
- BhavCopy downloading and parsing
- PDF downloading with caching and retry
- ISIN-based matching for BSE→NSE mapping
- Fuzzy name matching with configurable thresholds
- Rate limiting with token bucket algorithm
- Database utilities for SQLite operations
- Data validation utilities

Each tool is independently testable and follows single responsibility principle.

Author: VCP Financial Research Team
Version: 1.0.0
"""

from .bhav_copy_downloader import download_bse_bhav_copy, download_nse_bhav_copy, parse_bhav_copy
from .pdf_downloader import download_pdf, download_pdf_with_retry, cache_pdf
from .isin_matcher import match_by_isin, build_isin_index
from .fuzzy_name_matcher import fuzzy_match_companies, clean_company_name
from .rate_limiter import RateLimiter, respect_rate_limit
from .db_utils import get_db_connection, execute_query, bulk_insert
from .validation_utils import validate_ohlc, validate_financials, validate_date_range

__all__ = [
    # BhavCopy tools
    "download_bse_bhav_copy",
    "download_nse_bhav_copy",
    "parse_bhav_copy",

    # PDF tools
    "download_pdf",
    "download_pdf_with_retry",
    "cache_pdf",

    # Matching tools
    "match_by_isin",
    "build_isin_index",
    "fuzzy_match_companies",
    "clean_company_name",

    # Rate limiting
    "RateLimiter",
    "respect_rate_limit",

    # Database utilities
    "get_db_connection",
    "execute_query",
    "bulk_insert",

    # Validation
    "validate_ohlc",
    "validate_financials",
    "validate_date_range",
]

__version__ = "1.0.0"

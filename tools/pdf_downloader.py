"""
PDF Downloader - Download and cache financial PDFs with retry logic

Downloads quarterly earnings PDFs from BSE website with:
- Exponential backoff retry (3 attempts)
- Cache management (avoid re-downloading)
- Rate limiting (2 req/s)
- Timeout handling (30s default)

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
import time
import hashlib
import requests
from pathlib import Path
from typing import Optional
from .rate_limiter import BSE_RATE_LIMITER, respect_rate_limit

logger = logging.getLogger(__name__)


def download_pdf(
    url: str,
    save_path: Optional[Path] = None,
    timeout: int = 30
) -> Optional[Path]:
    """
    Download PDF from URL (single attempt).

    Args:
        url: PDF URL to download
        save_path: Optional path to save PDF (if None, use temp file)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Path to downloaded PDF file, or None if download failed

    Raises:
        requests.RequestException: If download fails

    Example:
        pdf_path = download_pdf(
            "https://www.bseindia.com/xml-data/corpfiling/AttachLive/12345.pdf",
            save_path=Path("/tmp/financials/12345.pdf")
        )
    """
    if save_path is None:
        # Generate temp filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        save_path = Path(f"/tmp/{url_hash}.pdf")

    # Ensure parent directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Downloading PDF: {url}")

        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "application/pdf,*/*"
            },
            stream=True  # Stream for large files
        )
        response.raise_for_status()

        # Verify content type
        content_type = response.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            logger.warning(f"Unexpected content type: {content_type} for URL: {url}")

        # Write to file
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = save_path.stat().st_size
        logger.info(f"Downloaded PDF: {save_path} ({file_size:,} bytes)")

        return save_path

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"PDF not found (404): {url}")
        elif e.response.status_code == 403:
            logger.warning(f"Access forbidden (403): {url}")
        else:
            logger.error(f"HTTP error downloading PDF: {e}")
        return None

    except requests.Timeout:
        logger.error(f"Timeout downloading PDF: {url}")
        return None

    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        return None


def download_pdf_with_retry(
    url: str,
    save_path: Optional[Path] = None,
    max_retries: int = 3,
    timeout: int = 30,
    backoff_factor: float = 2.0,
    respect_rate_limits: bool = True
) -> Optional[Path]:
    """
    Download PDF with exponential backoff retry.

    Args:
        url: PDF URL to download
        save_path: Optional path to save PDF
        max_retries: Maximum retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30)
        backoff_factor: Exponential backoff multiplier (default: 2.0)
        respect_rate_limits: If True, use rate limiter (default: True)

    Returns:
        Path to downloaded PDF file, or None if all retries failed

    Retry Strategy:
        - Attempt 1: Immediate
        - Attempt 2: Wait backoff_factor^1 seconds (2s default)
        - Attempt 3: Wait backoff_factor^2 seconds (4s default)
        - Attempt 4: Wait backoff_factor^3 seconds (8s default)

    Example:
        pdf_path = download_pdf_with_retry(
            "https://www.bseindia.com/xml-data/corpfiling/AttachLive/12345.pdf",
            max_retries=3,
            backoff_factor=2.0
        )
        if pdf_path:
            print(f"Success: {pdf_path}")
        else:
            print("Failed after 3 retries")
    """
    for attempt in range(max_retries):
        try:
            # Apply rate limiting (except on retries to avoid double-limiting)
            if respect_rate_limits and attempt == 0:
                respect_rate_limit(BSE_RATE_LIMITER, operation_name=f"Download PDF {url[:50]}...")

            # Attempt download
            result = download_pdf(url, save_path, timeout)

            if result:
                if attempt > 0:
                    logger.info(f"PDF download succeeded on retry {attempt + 1}/{max_retries}")
                return result

        except Exception as e:
            logger.warning(f"PDF download attempt {attempt + 1}/{max_retries} failed: {e}")

        # Exponential backoff before retry
        if attempt < max_retries - 1:
            wait_time = backoff_factor ** (attempt + 1)
            logger.info(f"Retrying in {wait_time:.1f}s... ({attempt + 1}/{max_retries} attempts)")
            time.sleep(wait_time)

    logger.error(f"PDF download failed after {max_retries} attempts: {url}")
    return None


def cache_pdf(
    url: str,
    cache_dir: str = "/tmp/pdf_cache",
    force_refresh: bool = False,
    max_retries: int = 3
) -> Optional[Path]:
    """
    Download and cache PDF (avoid re-downloading if exists).

    Args:
        url: PDF URL to download
        cache_dir: Directory to cache PDFs
        force_refresh: If True, re-download even if cached (default: False)
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        Path to cached PDF file, or None if download failed

    Cache Strategy:
        - Filename: MD5 hash of URL (first 16 chars) + .pdf
        - Cache hit: Return existing file immediately
        - Cache miss: Download with retry and cache

    Example:
        # First call: downloads and caches
        pdf1 = cache_pdf("https://example.com/q1_fy25.pdf")

        # Second call: returns cached file (no download)
        pdf2 = cache_pdf("https://example.com/q1_fy25.pdf")

        # Force refresh
        pdf3 = cache_pdf("https://example.com/q1_fy25.pdf", force_refresh=True)
    """
    # Generate cache filename from URL
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    pdf_path = cache_path / f"{url_hash}.pdf"

    # Check cache hit (unless force refresh)
    if not force_refresh and pdf_path.exists():
        file_size = pdf_path.stat().st_size
        logger.info(f"Cache HIT: {pdf_path} ({file_size:,} bytes)")
        return pdf_path

    # Cache miss - download with retry
    logger.info(f"Cache MISS: Downloading {url}")
    result = download_pdf_with_retry(
        url,
        save_path=pdf_path,
        max_retries=max_retries
    )

    if result:
        logger.info(f"Cached PDF: {pdf_path}")

    return result


def get_cached_pdf_path(url: str, cache_dir: str = "/tmp/pdf_cache") -> Optional[Path]:
    """
    Get cached PDF path without downloading (check only).

    Args:
        url: PDF URL
        cache_dir: Cache directory

    Returns:
        Path to cached PDF if exists, None otherwise

    Example:
        cached_path = get_cached_pdf_path("https://example.com/report.pdf")
        if cached_path:
            print(f"Already cached: {cached_path}")
        else:
            print("Not cached, need to download")
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()[:16]
    pdf_path = Path(cache_dir) / f"{url_hash}.pdf"

    if pdf_path.exists():
        return pdf_path
    return None


def clear_pdf_cache(cache_dir: str = "/tmp/pdf_cache", older_than_days: Optional[int] = None) -> int:
    """
    Clear PDF cache directory.

    Args:
        cache_dir: Cache directory to clear
        older_than_days: Only delete files older than N days (None = delete all)

    Returns:
        Number of files deleted

    Example:
        # Delete all cached PDFs
        deleted = clear_pdf_cache()

        # Delete PDFs older than 30 days
        deleted = clear_pdf_cache(older_than_days=30)
    """
    cache_path = Path(cache_dir)

    if not cache_path.exists():
        logger.info(f"Cache directory doesn't exist: {cache_dir}")
        return 0

    deleted_count = 0
    current_time = time.time()
    cutoff_time = current_time - (older_than_days * 86400) if older_than_days else 0

    for pdf_file in cache_path.glob("*.pdf"):
        file_age = current_time - pdf_file.stat().st_mtime

        if older_than_days is None or file_age > (older_than_days * 86400):
            try:
                pdf_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted cached PDF: {pdf_file}")
            except Exception as e:
                logger.error(f"Failed to delete {pdf_file}: {e}")

    logger.info(f"Cleared {deleted_count} PDFs from cache: {cache_dir}")
    return deleted_count


def get_cache_stats(cache_dir: str = "/tmp/pdf_cache") -> dict:
    """
    Get cache statistics.

    Args:
        cache_dir: Cache directory

    Returns:
        Dictionary with cache statistics:
        - total_files: Number of cached PDFs
        - total_size_bytes: Total cache size in bytes
        - total_size_mb: Total cache size in MB
        - oldest_file: Oldest cached file path
        - newest_file: Newest cached file path

    Example:
        stats = get_cache_stats()
        print(f"Cache: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB")
    """
    cache_path = Path(cache_dir)

    if not cache_path.exists():
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "oldest_file": None,
            "newest_file": None
        }

    pdf_files = list(cache_path.glob("*.pdf"))
    total_size = sum(f.stat().st_size for f in pdf_files)

    if pdf_files:
        oldest = min(pdf_files, key=lambda f: f.stat().st_mtime)
        newest = max(pdf_files, key=lambda f: f.stat().st_mtime)
    else:
        oldest = newest = None

    return {
        "total_files": len(pdf_files),
        "total_size_bytes": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "oldest_file": oldest,
        "newest_file": newest
    }


if __name__ == "__main__":
    # Demo: PDF downloading with cache
    logging.basicConfig(level=logging.INFO)

    print("=== PDF Downloader Demo ===\n")

    # Test URL (BSE sample - may not exist)
    test_url = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/sample.pdf"

    print("1. Download with retry:")
    pdf1 = download_pdf_with_retry(test_url, max_retries=2)
    if pdf1:
        print(f"  Downloaded: {pdf1}")
    else:
        print("  Download failed (expected for sample URL)")

    print("\n2. Cache PDF:")
    pdf2 = cache_pdf(test_url, cache_dir="/tmp/demo_pdf_cache")
    if pdf2:
        print(f"  Cached: {pdf2}")

    print("\n3. Cache stats:")
    stats = get_cache_stats("/tmp/demo_pdf_cache")
    print(f"  Files: {stats['total_files']}")
    print(f"  Size: {stats['total_size_mb']:.2f} MB")

    print("\n4. Clear cache:")
    deleted = clear_pdf_cache("/tmp/demo_pdf_cache")
    print(f"  Deleted: {deleted} files")

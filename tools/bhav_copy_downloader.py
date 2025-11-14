"""
BhavCopy Downloader - Download and parse daily market data from BSE/NSE

BhavCopy files contain end-of-day OHLC prices, volume, and circuit information
for all listed stocks. Published daily by exchanges after market close.

BSE Format: EQ{DDMMYY}_CSV.ZIP (e.g., EQ131124_CSV.ZIP for Nov 13, 2024)
NSE Format: cm{DDMMMYYYY}bhav.csv.zip (e.g., cm13NOV2024bhav.csv.zip)

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
import zipfile
import io
import csv
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from .rate_limiter import BSE_RATE_LIMITER, NSE_RATE_LIMITER, respect_rate_limit

logger = logging.getLogger(__name__)


def download_bse_bhav_copy(
    date: str,
    cache_dir: str = "/tmp/bhav_copy_cache",
    timeout: int = 30
) -> Optional[Path]:
    """
    Download BSE BhavCopy file for a given date.

    Args:
        date: Date string in YYYY-MM-DD format (e.g., "2024-11-13")
        cache_dir: Directory to cache downloaded files
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Path to downloaded CSV file, or None if download failed

    Raises:
        ValueError: If date format is invalid
        requests.RequestException: If download fails after retries

    Example:
        csv_path = download_bse_bhav_copy("2024-11-13")
        if csv_path:
            print(f"Downloaded to: {csv_path}")
    """
    # Parse and validate date
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date}'. Expected YYYY-MM-DD: {e}")

    # BSE BhavCopy URL format: EQ{DDMMYY}_CSV.ZIP
    # Example: https://www.bseindia.com/download/BhavCopy/Equity/EQ131124_CSV.ZIP
    date_str = dt.strftime("%d%m%y")  # 131124
    filename = f"EQ{date_str}_CSV.ZIP"
    url = f"https://www.bseindia.com/download/BhavCopy/Equity/{filename}"

    # Setup cache directory
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    csv_filename = f"BSE_EQ{date_str}.CSV"
    csv_path = cache_path / csv_filename

    # Check if already cached
    if csv_path.exists():
        logger.info(f"Using cached BSE BhavCopy: {csv_path}")
        return csv_path

    # Download with rate limiting
    respect_rate_limit(BSE_RATE_LIMITER, operation_name=f"Download BSE {date}")

    try:
        logger.info(f"Downloading BSE BhavCopy from: {url}")
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        response.raise_for_status()

        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # BSE ZIP contains single CSV file
            csv_files = [f for f in zf.namelist() if f.endswith('.CSV')]
            if not csv_files:
                logger.error(f"No CSV file found in {filename}")
                return None

            # Extract to cache
            csv_content = zf.read(csv_files[0])
            csv_path.write_bytes(csv_content)

        logger.info(f"Downloaded BSE BhavCopy: {csv_path} ({len(csv_content)} bytes)")
        return csv_path

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"BSE BhavCopy not found for {date} (possibly holiday/weekend)")
        else:
            logger.error(f"Failed to download BSE BhavCopy: {e}")
        return None

    except Exception as e:
        logger.error(f"Error downloading BSE BhavCopy: {e}")
        return None


def download_nse_bhav_copy(
    date: str,
    cache_dir: str = "/tmp/bhav_copy_cache",
    timeout: int = 30
) -> Optional[Path]:
    """
    Download NSE BhavCopy file for a given date.

    Args:
        date: Date string in YYYY-MM-DD format (e.g., "2024-11-13")
        cache_dir: Directory to cache downloaded files
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Path to downloaded CSV file, or None if download failed

    Raises:
        ValueError: If date format is invalid
        requests.RequestException: If download fails after retries

    Example:
        csv_path = download_nse_bhav_copy("2024-11-13")
        if csv_path:
            print(f"Downloaded to: {csv_path}")
    """
    # Parse and validate date
    try:
        dt = datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date}'. Expected YYYY-MM-DD: {e}")

    # NSE BhavCopy URL format: cm{DDMMMYYYY}bhav.csv.zip
    # Example: https://archives.nseindia.com/content/historical/EQUITIES/2024/NOV/cm13NOV2024bhav.csv.zip
    date_str_lower = dt.strftime("%d%b%Y").upper()  # 13NOV2024
    month_str = dt.strftime("%b").upper()  # NOV
    year_str = dt.strftime("%Y")  # 2024

    filename = f"cm{date_str_lower}bhav.csv.zip"
    url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_str}/{month_str}/{filename}"

    # Setup cache directory
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    csv_filename = f"NSE_cm{date_str_lower}bhav.csv"
    csv_path = cache_path / csv_filename

    # Check if already cached
    if csv_path.exists():
        logger.info(f"Using cached NSE BhavCopy: {csv_path}")
        return csv_path

    # Download with rate limiting
    respect_rate_limit(NSE_RATE_LIMITER, operation_name=f"Download NSE {date}")

    try:
        logger.info(f"Downloading NSE BhavCopy from: {url}")
        response = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        response.raise_for_status()

        # Extract CSV from ZIP
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # NSE ZIP contains single CSV file
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files:
                logger.error(f"No CSV file found in {filename}")
                return None

            # Extract to cache
            csv_content = zf.read(csv_files[0])
            csv_path.write_bytes(csv_content)

        logger.info(f"Downloaded NSE BhavCopy: {csv_path} ({len(csv_content)} bytes)")
        return csv_path

    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"NSE BhavCopy not found for {date} (possibly holiday/weekend)")
        else:
            logger.error(f"Failed to download NSE BhavCopy: {e}")
        return None

    except Exception as e:
        logger.error(f"Error downloading NSE BhavCopy: {e}")
        return None


def parse_bhav_copy(
    csv_path: Path,
    exchange: str = "BSE"
) -> List[Dict]:
    """
    Parse BhavCopy CSV file into structured records.

    Args:
        csv_path: Path to downloaded BhavCopy CSV file
        exchange: Exchange name ("BSE" or "NSE")

    Returns:
        List of dictionaries with normalized fields:
        {
            "exchange": "BSE" or "NSE",
            "symbol": "TCS" or "500570",
            "isin": "INE467B01029",
            "open": 3500.0,
            "high": 3550.0,
            "low": 3480.0,
            "close": 3540.0,
            "volume": 1234567,
            "date": "2024-11-13",
            "is_circuit": False  # True if hit upper/lower circuit
        }

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If exchange is invalid

    Example:
        records = parse_bhav_copy(Path("/tmp/BSE_EQ131124.CSV"), exchange="BSE")
        print(f"Parsed {len(records)} records")
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"BhavCopy file not found: {csv_path}")

    if exchange not in ("BSE", "NSE"):
        raise ValueError(f"Invalid exchange: {exchange}. Must be 'BSE' or 'NSE'")

    records = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                if exchange == "BSE":
                    # BSE CSV columns: SC_CODE, SC_NAME, OPEN, HIGH, LOW, CLOSE, ...
                    record = {
                        "exchange": "BSE",
                        "symbol": row.get("SC_CODE", "").strip(),
                        "name": row.get("SC_NAME", "").strip(),
                        "isin": row.get("ISIN_CODE", "").strip(),
                        "open": float(row.get("OPEN", 0) or 0),
                        "high": float(row.get("HIGH", 0) or 0),
                        "low": float(row.get("LOW", 0) or 0),
                        "close": float(row.get("CLOSE", 0) or 0),
                        "volume": int(row.get("NO_OF_SHRS", 0) or 0),
                        "date": _parse_bse_date(csv_path.name),  # Extract from filename
                        "is_circuit": False  # Need to compare with prev close to detect
                    }

                elif exchange == "NSE":
                    # NSE CSV columns: SYMBOL, SERIES, OPEN, HIGH, LOW, CLOSE, ...
                    series = row.get("SERIES", "").strip()

                    # Only include equity series (EQ, BE, BZ, etc.)
                    if series not in ("EQ", "BE", "BZ"):
                        continue

                    record = {
                        "exchange": "NSE",
                        "symbol": row.get("SYMBOL", "").strip(),
                        "name": row.get("SYMBOL", "").strip(),  # NSE doesn't provide full name
                        "isin": row.get("ISIN", "").strip(),
                        "open": float(row.get("OPEN", 0) or 0),
                        "high": float(row.get("HIGH", 0) or 0),
                        "low": float(row.get("LOW", 0) or 0),
                        "close": float(row.get("CLOSE", 0) or 0),
                        "volume": int(row.get("TOTTRDQTY", 0) or 0),
                        "date": _parse_nse_date(csv_path.name),
                        "is_circuit": False
                    }

                # Skip records with invalid prices
                if record["close"] <= 0:
                    continue

                records.append(record)

        logger.info(f"Parsed {len(records)} records from {csv_path.name}")
        return records

    except Exception as e:
        logger.error(f"Error parsing BhavCopy {csv_path}: {e}")
        return []


def _parse_bse_date(filename: str) -> str:
    """
    Extract date from BSE filename: BSE_EQ131124.CSV -> 2024-11-13

    Args:
        filename: BSE BhavCopy filename

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    # Extract date part: EQ131124 -> 131124
    date_part = filename.replace("BSE_", "").replace("EQ", "").replace("_CSV.CSV", "").replace(".CSV", "")

    # Parse DDMMYY format
    dt = datetime.strptime(date_part, "%d%m%y")
    return dt.strftime("%Y-%m-%d")


def _parse_nse_date(filename: str) -> str:
    """
    Extract date from NSE filename: NSE_cm13NOV2024bhav.csv -> 2024-11-13

    Args:
        filename: NSE BhavCopy filename

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    # Extract date part: cm13NOV2024bhav.csv -> 13NOV2024
    date_part = filename.replace("NSE_", "").replace("cm", "").replace("bhav.csv", "")

    # Parse DDMMMYYYY format
    dt = datetime.strptime(date_part, "%d%b%Y")
    return dt.strftime("%Y-%m-%d")


if __name__ == "__main__":
    # Demo: Download and parse BhavCopy
    logging.basicConfig(level=logging.INFO)

    print("=== BSE BhavCopy ===")
    bse_path = download_bse_bhav_copy("2024-11-13")
    if bse_path:
        records = parse_bhav_copy(bse_path, exchange="BSE")
        print(f"Sample records: {records[:3]}")

    print("\n=== NSE BhavCopy ===")
    nse_path = download_nse_bhav_copy("2024-11-13")
    if nse_path:
        records = parse_bhav_copy(nse_path, exchange="NSE")
        print(f"Sample records: {records[:3]}")

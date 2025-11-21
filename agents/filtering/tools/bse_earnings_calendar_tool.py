#!/usr/bin/env python3
"""
BSE Earnings Calendar Tool

Scrapes BSE website for upcoming earnings announcements to enable pre-filtering
of stocks before expensive API calls.

Goal: Reduce stock universe by 70% by only analyzing stocks with earnings in next 7-14 days
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class BSEEarningsCalendarTool:
    """
    Tool to fetch and cache earnings announcements from BSE

    Features:
    - Scrapes BSE corporate announcements API
    - Filters for earnings-related announcements
    - Caches results in SQLite (24h TTL)
    - Provides 7-day and 14-day lookforward windows
    """

    # BSE reverse-engineered endpoints
    BSE_ANNOUNCEMENT_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
    BSE_RESULT_URL = "https://api.bseindia.com/BseIndiaAPI/api/Result/w"

    # Earnings-related keywords
    EARNINGS_KEYWORDS = [
        'result', 'earnings', 'financial', 'quarterly', 'q1', 'q2', 'q3', 'q4',
        'fy', 'profit', 'loss', 'statement', 'board meeting', 'financials'
    ]

    def __init__(self, db_path: str = "data/earnings_calendar.db"):
        """
        Initialize BSE earnings calendar tool

        Args:
            db_path: Path to SQLite database for caching
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

        # Session for requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        })

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Earnings announcements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS earnings_calendar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bse_code TEXT NOT NULL,
                company_name TEXT NOT NULL,
                announcement_type TEXT,
                announcement_date DATE NOT NULL,
                details TEXT,
                scraped_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bse_code, announcement_date, announcement_type)
            )
        """)

        # Create index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_earnings_date
            ON earnings_calendar(announcement_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_earnings_code
            ON earnings_calendar(bse_code)
        """)

        conn.commit()
        conn.close()

        logger.info(f"Database initialized at {self.db_path}")

    def fetch_bse_announcements(
        self,
        from_date: datetime,
        to_date: datetime,
        force_refresh: bool = False
    ) -> List[Dict]:
        """
        Fetch earnings announcements from BSE for date range

        Args:
            from_date: Start date
            to_date: End date
            force_refresh: If True, bypass cache and fetch fresh data

        Returns:
            List of announcement dictionaries
        """
        # Check cache first
        if not force_refresh:
            cached = self._get_cached_announcements(from_date, to_date)
            if cached:
                logger.info(f"Cache hit: {len(cached)} announcements from {from_date.date()} to {to_date.date()}")
                return cached

        logger.info(f"Fetching BSE announcements from {from_date.date()} to {to_date.date()}")

        announcements = []

        # Fetch from BSE API (iterate day by day to handle pagination)
        current_date = from_date
        while current_date <= to_date:
            try:
                daily_announcements = self._fetch_daily_announcements(current_date)
                announcements.extend(daily_announcements)
                logger.info(f"  {current_date.date()}: {len(daily_announcements)} announcements")

                # Rate limiting
                import time
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error fetching {current_date.date()}: {e}")

            current_date += timedelta(days=1)

        # Cache results
        if announcements:
            self._cache_announcements(announcements)

        return announcements

    def _fetch_daily_announcements(self, date: datetime) -> List[Dict]:
        """
        Fetch announcements for a single day

        Args:
            date: Date to fetch

        Returns:
            List of announcement dictionaries
        """
        # Try Result API first (board meetings for earnings)
        params = {
            'strCat': '-1',
            'strPrevDate': date.strftime('%Y%m%d'),
            'strScrip': '',
            'strSearch': 'S',
            'strToDate': date.strftime('%Y%m%d'),
            'strType': 'C'
        }

        announcements = []

        try:
            response = self.session.get(self.BSE_RESULT_URL, params=params, timeout=10)
            response.raise_for_status()

            # Handle potential JSON parsing errors
            try:
                data = response.json()
            except json.JSONDecodeError as je:
                logger.error(f"Malformed JSON from BSE Result API for date {date}: {je}")
                logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
                data = {}

            if 'Table' in data and isinstance(data['Table'], list):
                for item in data['Table']:
                    # Filter for earnings-related announcements
                    announcement_text = f"{item.get('SLONGNAME', '')} {item.get('PURPOSE', '')}".lower()

                    if any(keyword in announcement_text for keyword in self.EARNINGS_KEYWORDS):
                        announcements.append({
                            'bse_code': item.get('SCRIP_CD', ''),
                            'company_name': item.get('SLONGNAME', ''),
                            'announcement_type': 'BOARD_MEETING',
                            'announcement_date': date.strftime('%Y-%m-%d'),
                            'details': item.get('PURPOSE', '')
                        })

        except requests.Timeout:
            logger.warning(f"BSE Result API timeout for date {date}")
        except requests.RequestException as e:
            logger.warning(f"Network error fetching from Result API for date {date}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching from Result API for date {date}: {e}")

        # Also try Announcement API
        try:
            ann_params = {
                'strCat': '-1',
                'strPrevDate': date.strftime('%Y%m%d'),
                'strScrip': '',
                'strSearch': 'S',
                'strToDate': date.strftime('%Y%m%d')
            }

            response = self.session.get(self.BSE_ANNOUNCEMENT_URL, params=ann_params, timeout=10)
            response.raise_for_status()

            # Handle potential JSON parsing errors
            try:
                data = response.json()
            except json.JSONDecodeError as je:
                logger.error(f"Malformed JSON from BSE Announcement API for date {date}: {je}")
                logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
                data = {}

            if 'Table' in data and isinstance(data['Table'], list):
                for item in data['Table']:
                    announcement_text = f"{item.get('SLONGNAME', '')} {item.get('HEADLINE', '')} {item.get('NSSUBJECT', '')}".lower()

                    if any(keyword in announcement_text for keyword in self.EARNINGS_KEYWORDS):
                        announcements.append({
                            'bse_code': item.get('SCRIP_CD', ''),
                            'company_name': item.get('SLONGNAME', ''),
                            'announcement_type': 'ANNOUNCEMENT',
                            'announcement_date': date.strftime('%Y-%m-%d'),
                            'details': item.get('HEADLINE', '')
                        })

        except requests.Timeout:
            logger.warning(f"BSE Announcement API timeout for date {date}")
        except requests.RequestException as e:
            logger.warning(f"Network error fetching from Announcement API for date {date}: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error fetching from Announcement API for date {date}: {e}")

        return announcements

    def _get_cached_announcements(
        self,
        from_date: datetime,
        to_date: datetime
    ) -> Optional[List[Dict]]:
        """
        Get cached announcements for date range

        Args:
            from_date: Start date
            to_date: End date

        Returns:
            List of cached announcements or None if cache miss
        """
        # Check if cache is fresh (< 24 hours old)
        cache_age_limit = datetime.now() - timedelta(hours=24)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Check if we have fresh data for the date range
        cursor.execute("""
            SELECT COUNT(DISTINCT announcement_date)
            FROM earnings_calendar
            WHERE announcement_date BETWEEN ? AND ?
            AND scraped_at > ?
        """, (
            from_date.strftime('%Y-%m-%d'),
            to_date.strftime('%Y-%m-%d'),
            cache_age_limit.isoformat()
        ))

        cached_days = cursor.fetchone()[0]
        expected_days = (to_date - from_date).days + 1

        # Only use cache if we have all days
        if cached_days < expected_days:
            conn.close()
            return None

        # Fetch cached data
        cursor.execute("""
            SELECT bse_code, company_name, announcement_type, announcement_date, details
            FROM earnings_calendar
            WHERE announcement_date BETWEEN ? AND ?
            AND scraped_at > ?
            ORDER BY announcement_date ASC
        """, (
            from_date.strftime('%Y-%m-%d'),
            to_date.strftime('%Y-%m-%d'),
            cache_age_limit.isoformat()
        ))

        announcements = []
        for row in cursor.fetchall():
            announcements.append({
                'bse_code': row[0],
                'company_name': row[1],
                'announcement_type': row[2],
                'announcement_date': row[3],
                'details': row[4]
            })

        conn.close()
        return announcements

    def _cache_announcements(self, announcements: List[Dict]):
        """
        Cache announcements in database

        Args:
            announcements: List of announcement dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        for ann in announcements:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO earnings_calendar
                    (bse_code, company_name, announcement_type, announcement_date, details, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ann['bse_code'],
                    ann['company_name'],
                    ann['announcement_type'],
                    ann['announcement_date'],
                    ann['details'],
                    datetime.now().isoformat()
                ))
            except Exception as e:
                logger.warning(f"Error caching announcement: {e}")

        conn.commit()
        conn.close()

        logger.info(f"Cached {len(announcements)} announcements")

    def get_stocks_with_upcoming_earnings(
        self,
        days_ahead: int = 7,
        force_refresh: bool = False
    ) -> List[str]:
        """
        Get list of BSE codes with earnings in next N days

        Args:
            days_ahead: Number of days to look forward (default: 7)
            force_refresh: If True, bypass cache

        Returns:
            List of BSE stock codes
        """
        from_date = datetime.now()
        to_date = from_date + timedelta(days=days_ahead)

        announcements = self.fetch_bse_announcements(from_date, to_date, force_refresh)

        # Extract unique BSE codes
        bse_codes = list(set(ann['bse_code'] for ann in announcements if ann['bse_code']))

        logger.info(f"Found {len(bse_codes)} stocks with earnings in next {days_ahead} days")
        return bse_codes

    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old cached announcements

        Args:
            days_to_keep: Keep data from last N days
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM earnings_calendar
            WHERE scraped_at < ?
        """, (cutoff_date.isoformat(),))

        deleted_count = cursor.rowcount
        conn.commit()

        # VACUUM to reclaim space
        cursor.execute("VACUUM")
        conn.close()

        logger.info(f"Cleaned up {deleted_count} old announcements")


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)

    tool = BSEEarningsCalendarTool()

    # Get stocks with earnings in next 7 days
    stocks = tool.get_stocks_with_upcoming_earnings(days_ahead=7)

    print(f"\n{len(stocks)} stocks with earnings in next 7 days:")
    for code in stocks[:10]:
        print(f"  - {code}")

    if len(stocks) > 10:
        print(f"  ... and {len(stocks) - 10} more")

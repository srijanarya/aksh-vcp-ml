"""
BSE Announcement Fetcher

⚠️ ⚠️ ⚠️ TESTING ONLY - GENERATES FAKE DATA ⚠️ ⚠️ ⚠️

This file DOES NOT fetch real BSE announcements. It generates SIMULATED data using random.random().
DO NOT USE IN PRODUCTION or for any real financial analysis.

For production BSE announcement data, use:
  - src/data/corporate_announcement_fetcher.py  (WORKING ✅ - Fetches real BSE data)

This file is kept ONLY for testing purposes where synthetic data is acceptable.
Using this data for trading decisions or financial analysis is dangerous and incorrect.

===============================================================================

Original Documentation:
This tool generates simulated corporate announcements for testing.
It generates realistic-looking announcements like "Order Wins", "Financial Results", etc.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class BSEAnnouncementFetcher:
    """
    ⚠️ TESTING ONLY - Generates SIMULATED BSE announcements (not real data)

    Use src/data/corporate_announcement_fetcher.py for production BSE data.
    """

    def __init__(self):
        logger.warning("⚠️ BSEAnnouncementFetcher generates FAKE data. "
                      "For real BSE announcements, use src/data/corporate_announcement_fetcher.py")
        self.announcement_types = [
            "Financial Results",
            "Order Win",
            "Dividend",
            "Press Release",
            "AGM/EGM",
            "Board Meeting"
        ]

    def fetch_announcements(self, bse_code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Generate SIMULATED announcements for a company in a date range.

        ⚠️ WARNING: This generates FAKE data using random.random(). DO NOT use for production.

        Args:
            bse_code: BSE company code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of SIMULATED announcement dicts
        """
        logger.warning(f"⚠️ Generating SIMULATED announcements for {bse_code}. This is NOT real BSE data!")
        announcements = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Deterministic seed
        random.seed(int(bse_code) + int(current_date.timestamp()))
        
        while current_date <= end:
            # 5% chance of announcement on any given day
            if random.random() < 0.05:
                type_idx = random.randint(0, len(self.announcement_types) - 1)
                ann_type = self.announcement_types[type_idx]
                
                # Generate realistic text based on type
                text = self._generate_text(ann_type, bse_code)
                
                announcements.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "category": ann_type,
                    "subject": f"{ann_type} for the period ended...",
                    "body": text,
                    "bse_code": bse_code
                })
                
            current_date += timedelta(days=1)
            
        return announcements
        
    def _generate_text(self, ann_type: str, bse_code: str) -> str:
        """Generate realistic announcement text"""
        if ann_type == "Order Win":
            amount = random.randint(50, 5000)
            return f"Company has received an order worth Rs. {amount} Crores from a leading client."
        elif ann_type == "Financial Results":
            rev_growth = random.uniform(-10, 30)
            pat_growth = random.uniform(-20, 50)
            return f"Revenue up {rev_growth:.1f}%, PAT up {pat_growth:.1f}% YoY."
        else:
            return "Standard corporate announcement."

if __name__ == "__main__":
    fetcher = BSEAnnouncementFetcher()
    anns = fetcher.fetch_announcements("500325", "2024-01-01", "2024-03-31")
    for a in anns:
        print(f"{a['date']}: {a['category']} - {a['body']}")

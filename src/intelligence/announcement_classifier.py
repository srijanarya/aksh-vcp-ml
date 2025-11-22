"""
Announcement Classifier

Categorizes corporate announcements into actionable types.
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AnnouncementClassifier:
    """
    Classifies announcements based on title, category, and description.
    """
    
    # Categories
    CAT_EARNINGS = "EARNINGS"
    CAT_ORDER = "ORDER_WIN"
    CAT_CAPEX = "CAPEX"
    CAT_PROMOTER = "PROMOTER_ACTION"
    CAT_GENERAL = "GENERAL"

    # Internal pattern keys (unique for dictionary, but return same category)
    _PAT_EARNINGS = "_EARNINGS"
    _PAT_EARNINGS_CALLS = "_EARNINGS_CALLS"
    _PAT_BOARD_MEETING_RESULTS = "_BOARD_MEETING_RESULTS"

    def __init__(self):
        # Regex patterns for classification
        self.patterns = {
            self._PAT_EARNINGS: [
                r"financial result", r"unaudited result", r"audited result",
                r"quarterly result", r"half.?yearly result", r"annual result",
                r"q[1-4].*fy\d{2}", r"financials.*quarter", r"standalone.*result",
                r"consolidated.*result", r"result.*quarter",
                r"submission.*financial", r"submission.*result",
                r"intimation.*result", r"result.*ended"
            ],
            self._PAT_EARNINGS_CALLS: [
                # Separate category for earnings calls (has transcripts, not always data)
                r"earnings call", r"earnings.*transcript", r"investor.*call"
            ],
            self._PAT_BOARD_MEETING_RESULTS: [
                # Board meetings that specifically mention results
                r"board meeting.*result", r"board meeting.*financial",
                r"board meeting.*quarter", r"board meeting.*unaudited"
            ],
            self.CAT_ORDER: [
                r"order.*win", r"bagged.*order", r"contract.*awarded", 
                r"letter of acceptance", r"letter of intent", r"received.*order",
                r"secured.*order", r"work order", r"purchase order",
                r"award of contract", r"bagged.*contract"
            ],
            self.CAT_CAPEX: [
                r"capacity expansion", r"new plant", r"greenfield project",
                r"brownfield expansion", r"commissioning of", r"commercial production"
            ],
            self.CAT_PROMOTER: [
                r"insider trading", r"acquisition of shares", r"disposal of shares",
                r"promoter group", r"substantial acquisition"
            ]
        }

    def classify(self, announcement: Dict) -> str:
        """
        Determine the category of an announcement with improved precision.
        """
        title = announcement.get('title', '').lower()
        category = announcement.get('category', '').lower()
        description = announcement.get('description', '').lower()
        text = f"{title} {category} {description}"

        logger.debug(f"Classifying: title='{title[:50]}...', category='{category}', desc_len={len(description)}")
        logger.debug(f"Combined text: {text[:100]}...")

        # Check Order Wins (High Priority - specific signals)
        for pattern in self.patterns[self.CAT_ORDER]:
            if re.search(pattern, text):
                logger.debug(f"MATCHED ORDER pattern: {pattern}")
                return self.CAT_ORDER

        # Check Board Meeting Results (specific earnings board meetings)
        for pattern in self.patterns[self._PAT_BOARD_MEETING_RESULTS]:
            if re.search(pattern, text):
                logger.debug(f"MATCHED BOARD_MEETING_RESULTS pattern: {pattern}")
                return self.CAT_EARNINGS

        # Check Earnings (specific result announcements)
        for pattern in self.patterns[self._PAT_EARNINGS]:
            match = re.search(pattern, text)
            if match:
                logger.debug(f"MATCHED EARNINGS pattern: {pattern} at position {match.start()}-{match.end()}")
                logger.debug(f"Matched text: '{match.group()}'")
                return self.CAT_EARNINGS
            else:
                logger.debug(f"NO MATCH for pattern: {pattern}")

        # Check Earnings Calls (lower priority - often just transcripts)
        for pattern in self.patterns[self._PAT_EARNINGS_CALLS]:
            if re.search(pattern, text):
                logger.debug(f"MATCHED EARNINGS_CALLS pattern: {pattern}")
                # Only mark as EARNINGS if description mentions "result" or "financial"
                if re.search(r"result|financial|quarter|unaudited", description):
                    logger.debug("Secondary validation passed - returning EARNINGS")
                    return self.CAT_EARNINGS
                logger.debug("Secondary validation failed - returning GENERAL")
                return self.CAT_GENERAL  # Just a transcript, not actual results

        # Check Capex
        for pattern in self.patterns[self.CAT_CAPEX]:
            if re.search(pattern, text):
                logger.debug(f"MATCHED CAPEX pattern: {pattern}")
                return self.CAT_CAPEX

        # Check Promoter Action
        for pattern in self.patterns[self.CAT_PROMOTER]:
            if re.search(pattern, text):
                logger.debug(f"MATCHED PROMOTER pattern: {pattern}")
                return self.CAT_PROMOTER

        logger.debug("NO PATTERNS MATCHED - returning GENERAL")
        return self.CAT_GENERAL

if __name__ == "__main__":
    # Test the classifier
    classifier = AnnouncementClassifier()
    
    test_cases = [
        {"title": "Outcome of Board Meeting - Financial Results", "category": "Result"},
        {"title": "Company has bagged an order worth Rs 500 Cr", "category": "Company Update"},
        {"title": "Receipt of Letter of Acceptance from NHAI", "category": "Company Update"},
        {"title": "Commissioning of new ethanol plant", "category": "Company Update"},
        {"title": "Resignation of Independent Director", "category": "Company Update"}
    ]
    
    print("Testing Classifier:")
    for case in test_cases:
        cat = classifier.classify(case)
        print(f"'{case['title']}' -> {cat}")

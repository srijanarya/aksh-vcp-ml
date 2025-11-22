#!/usr/bin/env python3
"""Test if dictionary keys are being overwritten"""

CAT_EARNINGS = "EARNINGS"
CAT_EARNINGS_CALLS = "EARNINGS"  # Same value!
CAT_BOARD_MEETING_RESULTS = "EARNINGS"  # Same value!

patterns = {
    CAT_EARNINGS: ["pattern1", "pattern2"],
    CAT_EARNINGS_CALLS: ["pattern3", "pattern4"],
    CAT_BOARD_MEETING_RESULTS: ["pattern5", "pattern6"]
}

print("Dictionary keys:", list(patterns.keys()))
print("Number of keys:", len(patterns))
print("patterns['EARNINGS']:", patterns["EARNINGS"])
print()
print("This shows the last assignment wins - earlier patterns get overwritten!")

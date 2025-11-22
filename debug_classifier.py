#!/usr/bin/env python3
"""
Debug classifier to trace execution flow
"""
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.intelligence.announcement_classifier import AnnouncementClassifier

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)

# Create classifier
classifier = AnnouncementClassifier()

# Test with the problematic announcement
test_announcement = {
    'title': 'Progrex Ventures Ltd - 531265 - Submission Of  Financial Results For The Quarter /Half Year Ended On 30.09.2025.',
    'category': 'Result',
    'description': ''
}

print("=" * 80)
print("DEBUGGING CLASSIFIER")
print("=" * 80)
print(f"Title: {test_announcement['title']}")
print(f"Category: {test_announcement['category']}")
print(f"Description: {test_announcement['description']}")
print("=" * 80)
print()

result = classifier.classify(test_announcement)

print()
print("=" * 80)
print(f"FINAL RESULT: {result}")
print("=" * 80)

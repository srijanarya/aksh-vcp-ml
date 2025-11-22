from src.intelligence.intelligence_extractor import IntelligenceExtractor
import logging

logging.basicConfig(level=logging.INFO)

extractor = IntelligenceExtractor()

test_cases = [
    "Company has bagged an order worth Rs. 500 Crores from NHAI.",
    "Received order of INR 1,200.50 Cr for road construction.",
    "Awarded contract by Tata Power for Rs 50 Lakhs.",
    "Secured work order worth 45 Million from US Client.",
    "Order win of Rs. 10.5 Bn for export."
]

print("Testing Regex Extraction:")
for text in test_cases:
    data = extractor._extract_order_details(text)
    print(f"Input: {text}")
    print(f"Output: {data}\n")

"""
Sentiment Analyzer - Analyze sentiment from earnings announcements

Analyzes text from BSE announcements, quarterly reports, and news to classify
sentiment as POSITIVE, NEGATIVE, or NEUTRAL. Used as ML feature for predicting
market reaction to earnings.

Requires LLM API (OpenAI/Anthropic) or local sentiment model.

Author: VCP Financial Research Team
Version: 1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def classify_sentiment(
    text: str,
    keywords_based: bool = True
) -> Tuple[str, float, Dict]:
    """
    Classify sentiment of financial text.

    Args:
        text: Text to analyze (earnings report, announcement, etc.)
        keywords_based: If True, use keyword matching; if False, use LLM (default: True)

    Returns:
        Tuple of:
        - sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL"
        - confidence: Score between 0.0 - 1.0
        - details: Dictionary with diagnostic info

    Keyword-Based Approach:
        - Positive keywords: growth, increase, strong, exceeded, record, robust
        - Negative keywords: decline, loss, weak, missed, lower, challenging

    LLM-Based Approach (if keywords_based=False):
        - Requires OpenAI/Anthropic API key
        - More accurate but slower and costs money

    Example:
        text = "Company reported strong revenue growth of 25% with record profits"
        sentiment, confidence, details = classify_sentiment(text)
        print(f"Sentiment: {sentiment} ({confidence:.2f})")
    """
    details = {
        "method": "keywords" if keywords_based else "llm",
        "positive_signals": 0,
        "negative_signals": 0,
        "neutral_signals": 0
    }

    if keywords_based:
        # Keyword-based sentiment (fast, free, less accurate)
        positive_keywords = [
            r"\bgrowth\b", r"\bincrease\b", r"\bstrong\b", r"\bexceeded\b",
            r"\brecord\b", r"\brobust\b", r"\bimproved\b", r"\boutperform\b",
            r"\bpositive\b", r"\bgains\b", r"\bhigh(?:er)?\b", r"\bup\b"
        ]

        negative_keywords = [
            r"\bdecline\b", r"\bloss\b", r"\bweak\b", r"\bmissed\b",
            r"\blower\b", r"\bchallenging\b", r"\bdifficult\b", r"\bdown\b",
            r"\bnegative\b", r"\bfall\b", r"\bdropp?(?:ed)?\b", r"\bslump\b"
        ]

        text_lower = text.lower()

        # Count positive signals
        for pattern in positive_keywords:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            details["positive_signals"] += matches

        # Count negative signals
        for pattern in negative_keywords:
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            details["negative_signals"] += matches

        # Classify based on signal balance
        total_signals = details["positive_signals"] + details["negative_signals"]

        if total_signals == 0:
            sentiment = "NEUTRAL"
            confidence = 0.5
        elif details["positive_signals"] > details["negative_signals"]:
            sentiment = "POSITIVE"
            confidence = min(0.5 + (details["positive_signals"] / max(total_signals, 1)) * 0.5, 1.0)
        elif details["negative_signals"] > details["positive_signals"]:
            sentiment = "NEGATIVE"
            confidence = min(0.5 + (details["negative_signals"] / max(total_signals, 1)) * 0.5, 1.0)
        else:
            sentiment = "NEUTRAL"
            confidence = 0.5

    else:
        # LLM-based sentiment (placeholder - requires API integration)
        logger.warning("LLM-based sentiment not implemented. Falling back to keywords.")
        return classify_sentiment(text, keywords_based=True)

    logger.debug(
        f"Sentiment: {sentiment} (confidence: {confidence:.2f}, "
        f"pos: {details['positive_signals']}, neg: {details['negative_signals']})"
    )

    return sentiment, confidence, details


def analyze_earnings_sentiment(
    announcement_text: str,
    financial_data: Optional[Dict] = None
) -> Dict:
    """
    Analyze sentiment from earnings announcement with financial context.

    Args:
        announcement_text: Text from BSE announcement or earnings report
        financial_data: Optional dict with revenue, profit, EPS for context

    Returns:
        Dictionary with comprehensive sentiment analysis:
        {
            "text_sentiment": "POSITIVE",
            "text_confidence": 0.85,
            "financials_sentiment": "POSITIVE",  # Based on YoY growth
            "combined_sentiment": "POSITIVE",
            "combined_confidence": 0.90,
            "rationale": "Strong revenue growth + positive language"
        }

    Example:
        announcement = "Q1 FY25: Revenue up 25%, Net Profit increased 30%"
        financials = {"revenue": 1000, "net_profit": 150, "revenue_yoy_growth": 25.0}

        analysis = analyze_earnings_sentiment(announcement, financials)
        print(f"Combined sentiment: {analysis['combined_sentiment']}")
    """
    # Analyze text sentiment
    text_sentiment, text_conf, text_details = classify_sentiment(announcement_text)

    result = {
        "text_sentiment": text_sentiment,
        "text_confidence": text_conf,
        "text_details": text_details,
        "financials_sentiment": None,
        "combined_sentiment": text_sentiment,
        "combined_confidence": text_conf,
        "rationale": []
    }

    # Analyze financial sentiment (if provided)
    if financial_data:
        fin_sentiment = _classify_financial_sentiment(financial_data)
        result["financials_sentiment"] = fin_sentiment["sentiment"]
        result["rationale"].append(fin_sentiment["rationale"])

        # Combine text and financial sentiment
        if text_sentiment == fin_sentiment["sentiment"]:
            # Agreement - boost confidence
            result["combined_sentiment"] = text_sentiment
            result["combined_confidence"] = min(text_conf + 0.15, 1.0)
            result["rationale"].append("Text and financials align")
        else:
            # Disagreement - trust financials more (numbers don't lie)
            result["combined_sentiment"] = fin_sentiment["sentiment"]
            result["combined_confidence"] = 0.70  # Moderate confidence
            result["rationale"].append("Text/financials mismatch (trusting numbers)")

    result["rationale"] = " | ".join(result["rationale"]) if result["rationale"] else "Text analysis only"

    logger.info(
        f"Earnings sentiment: {result['combined_sentiment']} "
        f"(confidence: {result['combined_confidence']:.2f})"
    )

    return result


def _classify_financial_sentiment(financial_data: Dict) -> Dict:
    """
    Classify sentiment based on financial metrics.

    Args:
        financial_data: Dict with revenue, profit, EPS, YoY growth rates

    Returns:
        Dict with sentiment classification
    """
    sentiment = "NEUTRAL"
    rationale = []

    # Check YoY growth rates
    revenue_growth = financial_data.get("revenue_yoy_growth", 0)
    profit_growth = financial_data.get("profit_yoy_growth", 0)

    if revenue_growth > 15 and profit_growth > 15:
        sentiment = "POSITIVE"
        rationale.append(f"Strong growth (Rev: {revenue_growth:.1f}%, Profit: {profit_growth:.1f}%)")
    elif revenue_growth < -5 or profit_growth < -10:
        sentiment = "NEGATIVE"
        rationale.append(f"Declining metrics (Rev: {revenue_growth:.1f}%, Profit: {profit_growth:.1f}%)")
    else:
        sentiment = "NEUTRAL"
        rationale.append("Moderate growth")

    return {
        "sentiment": sentiment,
        "rationale": " ".join(rationale)
    }


if __name__ == "__main__":
    # Demo: Sentiment analysis
    logging.basicConfig(level=logging.INFO)

    print("=== Sentiment Analyzer Demo ===\n")

    # Test 1: Positive sentiment
    print("1. Positive earnings announcement:")
    text1 = """
    TCS reports strong Q1 FY25 results with revenue growth of 25% YoY.
    Net profit increased by 30% to ₹850 Crores. EPS improved to ₹15.5.
    The company exceeded analyst expectations and raised FY25 guidance.
    """

    sentiment, conf, details = classify_sentiment(text1)
    print(f"   Sentiment: {sentiment} (confidence: {conf:.2f})")
    print(f"   Positive signals: {details['positive_signals']}")
    print(f"   Negative signals: {details['negative_signals']}")

    # Test 2: Negative sentiment
    print("\n2. Negative earnings announcement:")
    text2 = """
    Company reports weak Q2 results with revenue decline of 8% YoY.
    Net profit fell by 15% due to challenging market conditions.
    Management cited difficult operating environment and lower demand.
    """

    sentiment, conf, details = classify_sentiment(text2)
    print(f"   Sentiment: {sentiment} (confidence: {conf:.2f})")
    print(f"   Positive signals: {details['positive_signals']}")
    print(f"   Negative signals: {details['negative_signals']}")

    # Test 3: Combined analysis
    print("\n3. Combined earnings sentiment (text + financials):")
    announcement = "Q1 FY25 results show robust performance across all segments"
    financials = {
        "revenue": 1000,
        "net_profit": 200,
        "revenue_yoy_growth": 28.5,
        "profit_yoy_growth": 35.2
    }

    analysis = analyze_earnings_sentiment(announcement, financials)
    print(f"   Text sentiment: {analysis['text_sentiment']}")
    print(f"   Financial sentiment: {analysis['financials_sentiment']}")
    print(f"   Combined: {analysis['combined_sentiment']} ({analysis['combined_confidence']:.2f})")
    print(f"   Rationale: {analysis['rationale']}")

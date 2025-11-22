# FX-008: Sentiment Analyzer

**Project**: BMAD Portfolio Management System
**Functional Requirement**: FR-3 (Sentiment Integration)
**Priority**: MEDIUM
**Created**: November 19, 2025
**Status**: Specification

---

## Table of Contents

1. [Overview](#overview)
2. [User Story](#user-story)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Sentiment Sources](#sentiment-sources)
5. [Technical Specification](#technical-specification)
6. [LLM Integration](#llm-integration)
7. [Test Cases](#test-cases)
8. [Performance Requirements](#performance-requirements)

---

## Overview

### Purpose

Analyze news sentiment and adjust position sizing accordingly. Positive sentiment → Increase position by 10%, Negative → Decrease by 10%.

### User Requirement

**User said**: *"In the project Trium Finance platform, we already have all the news and news API keys. You can use that news fetching from that project and make our system sentiment aware."*

### Why Sentiment Matters

**Example: RELIANCE Buy Signal**

**Without Sentiment**:
- Kelly suggests: ₹15,000 position

**With Positive Sentiment** (+0.6):
- News: "Reliance announces record profits"
- Sentiment adjustment: +10%
- Final position: ₹15,000 × 1.10 = **₹16,500**

**With Negative Sentiment** (-0.7):
- News: "Reliance faces regulatory scrutiny"
- Sentiment adjustment: -10%
- Final position: ₹15,000 × 0.90 = **₹13,500**

---

## User Story

**As** the Portfolio Manager
**I want** news sentiment integrated into position sizing
**So that** I increase positions when sentiment is positive and reduce when negative

### Success Criteria

1. Fetch news from Trium Finance API
2. Score sentiment using LLM (GPT-4 or Claude)
3. Adjust positions by ±10% based on sentiment
4. Cache sentiment for 1 hour (avoid redundant API calls)

---

## Acceptance Criteria

### Must Have

✅ **AC-1**: Fetch news for specific symbol from Trium Finance API
✅ **AC-2**: Use LLM (GPT-4 or Claude) to score sentiment (-1 to +1)
✅ **AC-3**: Weight recent news higher (decay older news)
✅ **AC-4**: Weight credible sources higher (ET, Mint > blogs)
✅ **AC-5**: Return aggregated sentiment score (-1 to +1)
✅ **AC-6**: Adjust position sizing by sentiment × 10%
✅ **AC-7**: Cache sentiment for 1 hour per symbol

### Should Have

⭕ **AC-8**: Classify news by topic (earnings, regulations, M&A)
⭕ **AC-9**: Alert on extreme sentiment (< -0.7 or > +0.7)
⭕ **AC-10**: Track sentiment history over time

### Nice to Have

🔵 **AC-11**: Multi-source sentiment (Twitter, Reddit)
🔵 **AC-12**: Sentiment momentum (is sentiment improving?)

---

## Sentiment Sources

### Primary: Trium Finance API

**Location**: `/Users/srijan/vcp/trium_finance/`

**API Keys**: Already configured in Trium project

**Endpoints**:
- `/api/news/symbol/{symbol}` - Get news for symbol
- `/api/news/date/{date}` - Get news for date
- `/api/news/search?q={query}` - Search news

**News Object**:
```json
{
  "article_id": "123456",
  "title": "Reliance announces record Q4 earnings",
  "description": "Reliance Industries posted record profits...",
  "source": "Economic Times",
  "published_at": "2025-11-19T08:30:00Z",
  "url": "https://economictimes.com/...",
  "symbols": ["RELIANCE"],
  "tags": ["earnings", "positive"]
}
```

---

## Technical Specification

### Class: `SentimentAnalyzer`

```python
# intelligence/sentiment_analyzer.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List
import requests
import openai  # or anthropic
import logging
import hashlib
import json

@dataclass
class NewsArticle:
    """News article data"""
    article_id: str
    title: str
    description: str
    source: str
    published_at: datetime
    url: str
    symbols: List[str]

@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    symbol: str
    sentiment_score: float  # -1 (bearish) to +1 (bullish)
    confidence: float  # 0-1
    news_count: int
    articles: List[NewsArticle]
    timestamp: datetime

class SentimentAnalyzer:
    """
    Analyze news sentiment using Trium Finance + LLM

    Flow:
    1. Fetch news from Trium Finance API
    2. Score each article with LLM (-1 to +1)
    3. Weight by recency and source credibility
    4. Return aggregated sentiment
    """

    def __init__(
        self,
        trium_api_base: str,
        trium_api_key: str,
        llm_provider: str = "openai",  # or "anthropic"
        llm_api_key: str = None,
        cache_ttl: int = 3600,  # 1 hour
    ):
        """
        Initialize sentiment analyzer

        Args:
            trium_api_base: Trium Finance API base URL
            trium_api_key: Trium Finance API key
            llm_provider: 'openai' or 'anthropic'
            llm_api_key: LLM API key
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.trium_api_base = trium_api_base
        self.trium_api_key = trium_api_key
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key
        self.cache_ttl = cache_ttl

        self.logger = logging.getLogger(__name__)

        # Sentiment cache
        self.cache = {}  # {symbol: (sentiment_result, cached_at)}

        # Source credibility weights
        self.source_weights = {
            "Economic Times": 1.0,
            "Mint": 1.0,
            "Business Standard": 0.9,
            "MoneyControl": 0.8,
            "Reuters": 1.0,
            "Bloomberg": 1.0,
            "default": 0.5,  # Blogs, unknown sources
        }

        # Initialize LLM client
        if llm_provider == "openai":
            openai.api_key = llm_api_key
        elif llm_provider == "anthropic":
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=llm_api_key)

    def analyze_symbol(
        self,
        symbol: str,
        lookback_hours: int = 24,
        use_cache: bool = True,
    ) -> SentimentResult:
        """
        Analyze sentiment for a symbol

        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            lookback_hours: How many hours back to fetch news (default: 24)
            use_cache: Use cached result if available (default: True)

        Returns:
            SentimentResult object
        """
        # Check cache
        if use_cache and symbol in self.cache:
            cached_result, cached_at = self.cache[symbol]
            age = (datetime.now() - cached_at).total_seconds()

            if age < self.cache_ttl:
                self.logger.info(
                    f"Using cached sentiment for {symbol} "
                    f"(age: {age:.0f}s)"
                )
                return cached_result

        # Fetch news from Trium Finance
        articles = self._fetch_news(symbol, lookback_hours)

        if not articles:
            self.logger.warning(f"No news found for {symbol}")
            return SentimentResult(
                symbol=symbol,
                sentiment_score=0.0,  # Neutral
                confidence=0.0,
                news_count=0,
                articles=[],
                timestamp=datetime.now(),
            )

        # Score each article with LLM
        scored_articles = []
        for article in articles:
            score = self._score_article(article)
            scored_articles.append((article, score))

        # Calculate weighted sentiment
        sentiment_score = self._calculate_weighted_sentiment(scored_articles)

        # Confidence based on number of articles
        confidence = min(len(articles) / 10, 1.0)  # Max at 10+ articles

        result = SentimentResult(
            symbol=symbol,
            sentiment_score=sentiment_score,
            confidence=confidence,
            news_count=len(articles),
            articles=articles,
            timestamp=datetime.now(),
        )

        # Cache result
        self.cache[symbol] = (result, datetime.now())

        self.logger.info(
            f"{symbol} sentiment: {sentiment_score:+.2f} "
            f"({len(articles)} articles, confidence: {confidence:.2%})"
        )

        return result

    def _fetch_news(self, symbol: str, lookback_hours: int) -> List[NewsArticle]:
        """Fetch news from Trium Finance API"""
        url = f"{self.trium_api_base}/api/news/symbol/{symbol}"

        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=lookback_hours)

        params = {
            "start_date": start_time.isoformat(),
            "end_date": end_time.isoformat(),
        }

        headers = {
            "Authorization": f"Bearer {self.trium_api_key}",
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            news_data = response.json()

            articles = []
            for item in news_data.get("articles", []):
                article = NewsArticle(
                    article_id=item["article_id"],
                    title=item["title"],
                    description=item.get("description", ""),
                    source=item["source"],
                    published_at=datetime.fromisoformat(item["published_at"]),
                    url=item["url"],
                    symbols=item.get("symbols", []),
                )
                articles.append(article)

            self.logger.info(f"Fetched {len(articles)} articles for {symbol}")
            return articles

        except requests.RequestException as e:
            self.logger.error(f"Error fetching news for {symbol}: {e}")
            return []

    def _score_article(self, article: NewsArticle) -> float:
        """
        Score article sentiment using LLM

        Returns:
            Sentiment score: -1 (very bearish) to +1 (very bullish)
        """
        if self.llm_provider == "openai":
            return self._score_article_openai(article)
        elif self.llm_provider == "anthropic":
            return self._score_article_anthropic(article)
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _score_article_openai(self, article: NewsArticle) -> float:
        """Score article using OpenAI GPT-4"""
        prompt = f"""
Analyze the sentiment of this news article for stock trading.

Title: {article.title}
Description: {article.description}

Return ONLY a number between -1 and +1:
- -1: Very bearish (bad news, stock will likely fall)
- -0.5: Somewhat bearish
- 0: Neutral (no clear impact)
- +0.5: Somewhat bullish
- +1: Very bullish (great news, stock will likely rise)

Consider:
- Earnings beats/misses
- Regulatory issues
- Partnerships, acquisitions
- Management changes
- Product launches

Return ONLY the number, no explanation.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a financial sentiment analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,  # Deterministic
                max_tokens=10,
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text)

            # Clamp to [-1, 1]
            score = max(-1.0, min(1.0, score))

            self.logger.debug(
                f"Article: '{article.title[:50]}...' → Score: {score:+.2f}"
            )

            return score

        except Exception as e:
            self.logger.error(f"Error scoring article with OpenAI: {e}")
            return 0.0  # Neutral on error

    def _score_article_anthropic(self, article: NewsArticle) -> float:
        """Score article using Anthropic Claude"""
        prompt = f"""
Analyze the sentiment of this news article for stock trading.

Title: {article.title}
Description: {article.description}

Return ONLY a number between -1 and +1:
- -1: Very bearish (bad news)
- 0: Neutral
- +1: Very bullish (great news)

Return ONLY the number.
"""

        try:
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                temperature=0.0,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )

            score_text = message.content[0].text.strip()
            score = float(score_text)

            # Clamp to [-1, 1]
            score = max(-1.0, min(1.0, score))

            return score

        except Exception as e:
            self.logger.error(f"Error scoring article with Anthropic: {e}")
            return 0.0

    def _calculate_weighted_sentiment(
        self,
        scored_articles: List[tuple[NewsArticle, float]],
    ) -> float:
        """
        Calculate weighted average sentiment

        Weights:
        - Recency: Recent articles weighted higher (exponential decay)
        - Source: Credible sources weighted higher

        Formula:
        weighted_sentiment = sum(score × recency_weight × source_weight) / sum(weights)
        """
        now = datetime.now()

        weighted_sum = 0.0
        total_weight = 0.0

        for article, score in scored_articles:
            # Recency weight (exponential decay, half-life = 12 hours)
            age_hours = (now - article.published_at).total_seconds() / 3600
            recency_weight = 0.5 ** (age_hours / 12)

            # Source weight
            source_weight = self.source_weights.get(
                article.source,
                self.source_weights["default"]
            )

            # Combined weight
            weight = recency_weight * source_weight

            weighted_sum += score * weight
            total_weight += weight

            self.logger.debug(
                f"Article: {article.title[:40]}... | "
                f"Score: {score:+.2f} | Age: {age_hours:.1f}h | "
                f"Source: {article.source} | Weight: {weight:.3f}"
            )

        if total_weight == 0:
            return 0.0

        weighted_sentiment = weighted_sum / total_weight

        # Clamp to [-1, 1]
        weighted_sentiment = max(-1.0, min(1.0, weighted_sentiment))

        return weighted_sentiment

    def analyze_news_period(
        self,
        start_time: datetime,
        end_time: datetime,
        symbols: List[str] = None,
    ) -> float:
        """
        Analyze sentiment for a time period (e.g., overnight 8 PM - 9 AM)

        Args:
            start_time: Period start
            end_time: Period end
            symbols: List of symbols to analyze (default: general market)

        Returns:
            Aggregated sentiment score
        """
        # Fetch news for time period
        url = f"{self.trium_api_base}/api/news/date"

        params = {
            "start_date": start_time.isoformat(),
            "end_date": end_time.isoformat(),
        }

        if symbols:
            params["symbols"] = ",".join(symbols)

        headers = {"Authorization": f"Bearer {self.trium_api_key}"}

        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            news_data = response.json()
            articles = [
                NewsArticle(
                    article_id=item["article_id"],
                    title=item["title"],
                    description=item.get("description", ""),
                    source=item["source"],
                    published_at=datetime.fromisoformat(item["published_at"]),
                    url=item["url"],
                    symbols=item.get("symbols", []),
                )
                for item in news_data.get("articles", [])
            ]

            if not articles:
                return 0.0  # Neutral

            # Score all articles
            scored_articles = [
                (article, self._score_article(article))
                for article in articles
            ]

            # Calculate weighted sentiment
            sentiment = self._calculate_weighted_sentiment(scored_articles)

            return sentiment

        except requests.RequestException as e:
            self.logger.error(f"Error fetching news for period: {e}")
            return 0.0
```

---

## LLM Integration

### Prompt Engineering

**Critical**: The LLM prompt must be precise to get consistent sentiment scores.

**Good Prompt**:
```
Analyze the sentiment of this news article for stock trading.

Title: {title}
Description: {description}

Return ONLY a number between -1 and +1:
- -1: Very bearish (bad news, stock will likely fall)
- 0: Neutral (no clear impact)
- +1: Very bullish (great news, stock will likely rise)

Consider:
- Earnings beats/misses
- Regulatory issues
- Partnerships, acquisitions

Return ONLY the number, no explanation.
```

**Bad Prompt**:
```
Is this article positive or negative?

{article}
```
(Too vague, will get inconsistent responses)

---

## Position Sizing Adjustment

### Integration with Kelly Sizer

```python
# position_sizing/kelly_sizer.py
from intelligence.sentiment_analyzer import SentimentAnalyzer

class KellyPositionSizer:
    def __init__(self, ...):
        self.sentiment_analyzer = SentimentAnalyzer(...)

    def calculate_position_size(self, signal, ...):
        # Get sentiment
        sentiment_result = self.sentiment_analyzer.analyze_symbol(
            signal["symbol"],
            lookback_hours=24,
        )

        sentiment_score = sentiment_result.sentiment_score

        # Adjust Kelly by sentiment
        # Sentiment -1 to +1 → Adjustment -10% to +10%
        kelly_adjusted = kelly * (1 + sentiment_score * 0.10)

        # Example:
        # - Sentiment +0.6 → Kelly × 1.06 (6% increase)
        # - Sentiment -0.8 → Kelly × 0.92 (8% decrease)
```

---

## Test Cases

### TC-001: Positive News

```python
def test_positive_news_sentiment(mocker):
    analyzer = SentimentAnalyzer(
        trium_api_base="http://trium.api",
        trium_api_key="key",
        llm_provider="openai",
        llm_api_key="openai_key",
    )

    # Mock Trium API
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "articles": [
            {
                "article_id": "1",
                "title": "Reliance announces record Q4 earnings",
                "description": "Profits up 25%...",
                "source": "Economic Times",
                "published_at": "2025-11-19T08:00:00",
                "url": "http://...",
                "symbols": ["RELIANCE"],
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    # Mock LLM (returns positive score)
    mocker.patch.object(analyzer, "_score_article", return_value=0.8)

    result = analyzer.analyze_symbol("RELIANCE")

    assert result.sentiment_score > 0.5  # Positive
    assert result.news_count == 1
```

### TC-002: Negative News

```python
def test_negative_news_sentiment(mocker):
    analyzer = SentimentAnalyzer(...)

    # Mock negative news
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        "articles": [
            {
                "title": "Reliance faces regulatory scrutiny",
                "description": "Fines expected...",
                "source": "Reuters",
                ...
            }
        ]
    }
    mocker.patch("requests.get", return_value=mock_response)

    # Mock LLM (returns negative score)
    mocker.patch.object(analyzer, "_score_article", return_value=-0.7)

    result = analyzer.analyze_symbol("RELIANCE")

    assert result.sentiment_score < -0.5  # Negative
```

### TC-003: Cache Effectiveness

```python
def test_sentiment_cache():
    analyzer = SentimentAnalyzer(..., cache_ttl=3600)

    # First call (cache miss)
    result1 = analyzer.analyze_symbol("RELIANCE")

    # Second call (cache hit)
    with mocker.patch("requests.get") as mock_api:
        result2 = analyzer.analyze_symbol("RELIANCE")

        # API should NOT be called (cached)
        mock_api.assert_not_called()

    assert result1.sentiment_score == result2.sentiment_score
```

### TC-004: Recency Weighting

```python
def test_recency_weighting():
    analyzer = SentimentAnalyzer(...)

    # Article 1: Recent (1 hour ago), score +0.8
    # Article 2: Old (24 hours ago), score -0.8

    # Weighted sentiment should favor recent article
    # Expected: Positive (recent article has higher weight)

    # Implementation test would mock articles with different ages
```

---

## Performance Requirements

### PR-1: Sentiment Calculation Speed

**Requirement**: < 5 seconds per symbol (includes LLM calls)

**Optimization**:
- Batch LLM calls (score 10 articles in 1 request)
- Cache results for 1 hour

### PR-2: API Rate Limits

**Trium Finance API**: 100 requests/minute
**OpenAI API**: 60 requests/minute (GPT-4)

**Solution**: Batch articles, use caching

---

## Implementation Checklist

- [ ] Create `intelligence/sentiment_analyzer.py`
- [ ] Find Trium Finance API credentials in `/Users/srijan/vcp/trium_finance/`
- [ ] Integrate OpenAI/Anthropic LLM
- [ ] Write 8 unit tests
- [ ] Test with real news articles
- [ ] Calibrate sentiment→position adjustment (±10%)
- [ ] Implement caching (1 hour TTL)
- [ ] Integrate with Kelly Position Sizer
- [ ] Document API usage
- [ ] Performance test (<5s per symbol)

---

**Document Status**: ✅ Complete
**Review Status**: Pending User Approval
**Next**: Create STORY documents (User Stories)

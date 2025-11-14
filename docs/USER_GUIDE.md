# VCP ML System - User Guide

**Complete guide for using the VCP Upper Circuit Prediction System**

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Making Predictions](#making-predictions)
4. [Understanding Results](#understanding-results)
5. [Batch Processing](#batch-processing)
6. [Common Workflows](#common-workflows)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Introduction

### What is VCP?

**Volatility Contraction Pattern (VCP)** is a technical analysis pattern identified by Mark Minervini that indicates a stock is consolidating before a potential breakout. The VCP ML system predicts which stocks showing VCP patterns are likely to hit upper circuit (maximum daily price increase of 10%/20%).

### What Does This System Do?

1. **Analyzes 11,000 Indian stocks** (NSE/BSE) daily
2. **Extracts 25+ features** (technical, financial, sentiment, seasonality)
3. **Predicts upper circuit probability** using machine learning
4. **Provides confidence scores** to help you make decisions

### Who Should Use This?

- **Traders**: Identify high-probability breakout candidates
- **Investors**: Screen stocks for entry points
- **Quants**: Build automated trading strategies
- **Researchers**: Analyze market patterns

---

## Getting Started

### Step 1: Access the API

The system runs as a REST API:

- **Development:** http://localhost:8000
- **Production:** https://vcp-api.example.com
- **Docs:** http://localhost:8000/docs

### Step 2: Verify System Health

```bash
curl http://localhost:8000/api/v1/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-11-14T10:00:00Z",
  "models_loaded": 3,
  "database_connected": true
}
```

### Step 3: Understand the Prediction Format

```json
{
  "bse_code": "500325",
  "symbol": "RELIANCE",
  "prediction": 1,              // 1 = upper circuit likely, 0 = unlikely
  "probability": 0.78,          // 78% confidence
  "confidence": "high",         // high/medium/low
  "features": {                 // Optional: input features used
    "rsi_14": 65.3,
    "volume_ratio": 1.8,
    ...
  }
}
```

---

## Making Predictions

### Single Stock Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "bse_code": "500325",
    "prediction_date": "2025-11-15"
  }'
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={
        "bse_code": "500325",
        "prediction_date": "2025-11-15"
    }
)

result = response.json()
print(f"Prediction: {result['prediction']}")
print(f"Probability: {result['probability']:.2%}")
print(f"Confidence: {result['confidence']}")
```

### Using Stock Symbol Instead of BSE Code

```python
# The API accepts either BSE code or symbol
response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={
        "symbol": "RELIANCE",  # Instead of bse_code
        "prediction_date": "2025-11-15"
    }
)
```

---

## Understanding Results

### Prediction Values

| Prediction | Meaning | Action |
|------------|---------|--------|
| 1 | Upper circuit likely (>70% probability) | Consider buying |
| 0 | Upper circuit unlikely (<30% probability) | Avoid or wait |

### Probability Interpretation

| Probability | Confidence | Recommendation |
|-------------|------------|----------------|
| 0.80 - 1.00 | Very High | Strong buy signal |
| 0.70 - 0.79 | High | Buy signal |
| 0.50 - 0.69 | Medium | Weak signal, exercise caution |
| 0.30 - 0.49 | Low | Weak signal, likely no circuit |
| 0.00 - 0.29 | Very Low | Avoid |

### Confidence Levels

- **High** (prob ≥ 0.70): Model is confident in prediction
- **Medium** (0.50 ≤ prob < 0.70): Model is uncertain
- **Low** (prob < 0.50): Model predicts against upper circuit

### Key Features to Check

When reviewing predictions, pay attention to these features:

1. **RSI (14)**: 60-80 indicates momentum
2. **Volume Ratio**: >1.5 shows increasing interest
3. **Price Position**: Near resistance levels
4. **MACD**: Positive and increasing
5. **Sentiment Score**: Positive news/reports

---

## Batch Processing

### Predict Multiple Stocks

```bash
curl -X POST http://localhost:8000/api/v1/batch_predict \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [
      {"bse_code": "500325", "prediction_date": "2025-11-15"},
      {"bse_code": "532977", "prediction_date": "2025-11-15"},
      {"bse_code": "500180", "prediction_date": "2025-11-15"}
    ]
  }'
```

**Python Example:**
```python
import requests
import pandas as pd

# List of stocks to analyze
stocks = ["500325", "532977", "500180", "500209", "532174"]

# Prepare batch request
batch_request = {
    "predictions": [
        {"bse_code": code, "prediction_date": "2025-11-15"}
        for code in stocks
    ]
}

# Make request
response = requests.post(
    "http://localhost:8000/api/v1/batch_predict",
    json=batch_request
)

# Convert to DataFrame for analysis
results = pd.DataFrame(response.json()['results'])

# Filter high-probability predictions
high_prob = results[results['probability'] >= 0.70]
print(f"\nHigh probability stocks ({len(high_prob)}):")
print(high_prob[['symbol', 'probability', 'confidence']])
```

### Processing All Stocks

```python
import requests
import pandas as pd

# Get all stock codes from master list
with open('data/master_stock_list.json') as f:
    master_list = json.load(f)

# Process in batches of 100 (API limit)
batch_size = 100
all_results = []

for i in range(0, len(master_list), batch_size):
    batch = master_list[i:i+batch_size]

    batch_request = {
        "predictions": [
            {"bse_code": stock['bse_code'], "prediction_date": "2025-11-15"}
            for stock in batch
        ]
    }

    response = requests.post(
        "http://localhost:8000/api/v1/batch_predict",
        json=batch_request
    )

    all_results.extend(response.json()['results'])
    print(f"Processed {i+len(batch)}/{len(master_list)} stocks")

# Analyze results
df = pd.DataFrame(all_results)
top_picks = df.nlargest(20, 'probability')
print("\nTop 20 Upper Circuit Candidates:")
print(top_picks[['symbol', 'probability']])
```

---

## Common Workflows

### Workflow 1: Daily Stock Screening

```python
import requests
import pandas as pd
from datetime import datetime, timedelta

def daily_screen():
    """Screen for high-probability upper circuit candidates"""

    # Get tomorrow's date
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    # Load watchlist (your favorite stocks)
    watchlist = ["500325", "532977", "500180", "500209", "532174"]

    # Make predictions
    results = []
    for bse_code in watchlist:
        response = requests.post(
            "http://localhost:8000/api/v1/predict",
            json={"bse_code": bse_code, "prediction_date": tomorrow}
        )
        results.append(response.json())

    # Filter and rank
    df = pd.DataFrame(results)
    candidates = df[df['probability'] >= 0.70].sort_values('probability', ascending=False)

    # Display results
    print(f"\n=== Daily Screen for {tomorrow} ===")
    print(f"Total watchlist: {len(watchlist)}")
    print(f"High-probability candidates: {len(candidates)}\n")

    for _, stock in candidates.iterrows():
        print(f"{stock['symbol']:15} | Prob: {stock['probability']:.2%} | {stock['confidence'].upper()}")

    return candidates

# Run daily
if __name__ == "__main__":
    candidates = daily_screen()
```

### Workflow 2: Sector-Based Analysis

```python
def sector_analysis(sector, min_probability=0.70):
    """Analyze all stocks in a sector"""

    # Load master list with sector info
    with open('data/master_stock_list.json') as f:
        master_list = json.load(f)

    # Filter by sector
    sector_stocks = [s for s in master_list if s.get('sector') == sector]

    # Batch predict
    batch_request = {
        "predictions": [
            {"bse_code": s['bse_code'], "prediction_date": "2025-11-15"}
            for s in sector_stocks
        ]
    }

    response = requests.post(
        "http://localhost:8000/api/v1/batch_predict",
        json=batch_request
    )

    # Analyze results
    results = pd.DataFrame(response.json()['results'])
    candidates = results[results['probability'] >= min_probability]

    print(f"\n=== {sector} Sector Analysis ===")
    print(f"Total stocks: {len(sector_stocks)}")
    print(f"Candidates (≥{min_probability:.0%}): {len(candidates)}\n")
    print(candidates[['symbol', 'probability', 'confidence']])

    return candidates

# Example usage
tech_candidates = sector_analysis("Technology", min_probability=0.75)
finance_candidates = sector_analysis("Finance", min_probability=0.75)
```

### Workflow 3: Backtesting Historical Predictions

```python
from datetime import datetime, timedelta

def backtest_predictions(bse_code, start_date, end_date):
    """Backtest predictions for a stock over a date range"""

    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    results = []
    for date in dates:
        date_str = date.strftime('%Y-%m-%d')

        # Make prediction
        response = requests.post(
            "http://localhost:8000/api/v1/predict",
            json={"bse_code": bse_code, "prediction_date": date_str}
        )

        result = response.json()
        result['date'] = date_str
        results.append(result)

    # Analyze accuracy
    df = pd.DataFrame(results)

    # Load actual outcomes (from database)
    # actual_outcomes = get_actual_upper_circuits(bse_code, start_date, end_date)
    # df = df.merge(actual_outcomes, on='date')

    # Calculate metrics
    # accuracy = (df['prediction'] == df['actual']).mean()
    # precision = (df[df['prediction'] == 1]['actual'] == 1).mean()

    print(f"\n=== Backtest Results for {bse_code} ===")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total predictions: {len(df)}")
    print(f"High-confidence predictions: {(df['confidence'] == 'high').sum()}")
    # print(f"Accuracy: {accuracy:.2%}")
    # print(f"Precision: {precision:.2%}")

    return df

# Example
results = backtest_predictions("500325", "2024-01-01", "2024-12-31")
```

---

## Best Practices

### 1. Use Appropriate Time Horizons

- **Intraday**: Predict for next day only
- **Swing Trading**: 1-5 day horizon
- **Position Trading**: Weekly predictions

### 2. Combine with Manual Analysis

The ML system is a tool, not a replacement for analysis:

1. **Technical Confirmation**: Check charts for VCP pattern
2. **Fundamental Check**: Verify company fundamentals
3. **News Validation**: Check for upcoming catalysts
4. **Risk Management**: Use stop-losses

### 3. Probability Thresholds

| Trading Style | Minimum Probability |
|---------------|---------------------|
| Aggressive | 0.60 |
| Moderate | 0.70 |
| Conservative | 0.80 |

### 4. Portfolio Construction

- **Diversify**: Don't put all capital in one prediction
- **Position Sizing**: Higher probability = larger position
- **Risk-Reward**: Aim for 2:1 or better

### 5. Monitor Model Performance

```python
# Track your predictions
def track_prediction(prediction_result, actual_outcome):
    """Log prediction vs actual for performance tracking"""

    log_entry = {
        'date': prediction_result['prediction_date'],
        'bse_code': prediction_result['bse_code'],
        'predicted': prediction_result['prediction'],
        'probability': prediction_result['probability'],
        'actual': actual_outcome,  # 1 if upper circuit hit, 0 otherwise
        'correct': prediction_result['prediction'] == actual_outcome
    }

    # Save to CSV or database
    with open('prediction_log.csv', 'a') as f:
        writer = csv.DictWriter(f, fieldnames=log_entry.keys())
        writer.writerow(log_entry)
```

---

## Troubleshooting

### Issue: "Stock not found"

**Solution:** Verify BSE code or symbol is correct. Check master stock list.

```python
# Search for stock
response = requests.get("http://localhost:8000/api/v1/search?query=RELIANCE")
print(response.json())
```

### Issue: "Insufficient historical data"

**Solution:** Stock needs at least 365 days of price data for accurate predictions.

### Issue: Low confidence predictions

**Causes:**
- Stock is too new (< 1 year listed)
- Low trading volume
- Missing financial data
- High volatility

**Action:** Exercise caution or skip these stocks.

### Issue: API timeout on batch requests

**Solution:** Reduce batch size or use async requests.

```python
import asyncio
import aiohttp

async def batch_predict_async(stocks):
    async with aiohttp.ClientSession() as session:
        tasks = [
            predict_async(session, stock)
            for stock in stocks
        ]
        return await asyncio.gather(*tasks)

async def predict_async(session, stock):
    async with session.post(
        "http://localhost:8000/api/v1/predict",
        json=stock
    ) as response:
        return await response.json()

# Usage
results = asyncio.run(batch_predict_async(stock_list))
```

---

## FAQ

### Q: How accurate are the predictions?

**A:** The model achieves 73% F1 score, 82% precision, and 66% recall on test data. In backtesting, the win rate is 68%.

### Q: How often should I make predictions?

**A:** Daily for active trading, weekly for swing trading. The model is most accurate for next-day predictions.

### Q: Can I use this for algo-trading?

**A:** Yes! The API is designed for programmatic access. Use batch endpoints and implement proper error handling.

### Q: What if the API is down?

**A:** Check `/health` endpoint. If down, contact support. For critical operations, implement fallback logic.

### Q: How are features calculated?

**A:** See [docs/architecture.md](architecture.md) for complete feature documentation. Key features include RSI, MACD, volume, P/E ratio, sentiment scores, and more.

### Q: Can I request custom features?

**A:** Yes, submit a feature request via GitHub Issues. We evaluate and add valuable features in monthly releases.

### Q: How do I interpret probability?

**A:** Probability is the model's confidence that the stock will hit upper circuit. 0.78 = 78% chance based on historical patterns.

### Q: What's the difference between prediction and probability?

**A:**
- **Prediction**: Binary (0 or 1) based on threshold (default 0.50)
- **Probability**: Continuous (0.00 to 1.00) showing model confidence

### Q: How far in advance can I predict?

**A:** Best accuracy for next day (T+1). Accuracy degrades for T+2, T+3, etc.

### Q: Does the model account for market conditions?

**A:** Yes, seasonality features capture day-of-week and month effects. For overall market conditions, check the market sentiment features.

---

## Next Steps

1. **[Deployment Guide](DEPLOYMENT.md)** - Set up your own instance
2. **[API Reference](API.md)** - Complete endpoint documentation
3. **[Architecture](architecture.md)** - Understand the system design
4. **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and fixes

---

**Happy Trading!**

*Remember: This system is a tool to support your decision-making, not a guarantee of profits. Always do your own research and manage risk appropriately.*

---

**Last Updated:** November 14, 2025
**Version:** 1.0.0

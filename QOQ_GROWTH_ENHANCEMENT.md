# Quarter-on-Quarter (QoQ) Growth Enhancement

## Overview
The `TrueBlockbusterDetector` has been enhanced to calculate and evaluate **both** Year-over-Year (YoY) and Quarter-on-Quarter (QoQ) growth metrics.

## Why QoQ Matters
- **YoY Growth**: Shows long-term trends, eliminates seasonality
- **QoQ Growth**: Captures recent momentum and acceleration
- **Combined**: Identifies companies with both sustained growth (YoY) AND accelerating business (QoQ)

## Implementation

### Growth Calculation Logic
The detector now fetches up to 5 historical quarters from `earnings_calendar.db` and calculates:

1. **YoY Growth**: Current Quarter vs Same Quarter Last Year
   - Example: Q2 FY2026 vs Q2 FY2025
   
2. **QoQ Growth**: Current Quarter vs Previous Sequential Quarter
   - Example: Q2 FY2026 vs Q1 FY2026

### Scoring System

#### YoY Growth (Primary - 50 points max)
- Revenue YoY > 25%: **+25 points**
- Profit YoY > 25%: **+25 points**

#### QoQ Growth (Bonus - 30 points max)
- Revenue QoQ > 15%: **+10 points** (Accelerating!)
- Revenue QoQ > 0%: **+5 points** (Positive)
- Profit QoQ > 15%: **+10 points** (Accelerating!)
- Profit QoQ > 0%: **+5 points** (Positive)

#### Technical Strength (40 points max)
- Price > 200 DMA: **+10 points**
- Price > 50 DMA: **+10 points**
- RSI > 50: **+10 points**
- Relative Strength > 80: **+20 points**

**Total Possible Score**: 120 points (80+ = Blockbuster)

## Example Output

```python
{
    'is_blockbuster': True,
    'score': 95,
    'reasons': [
        '🚀 Sales YoY 45.2% > 25%',
        '💰 Profit YoY 38.7% > 25%',
        '⚡ Sales QoQ 18.5% (Accelerating!)',
        '💎 Profit QoQ 22.1% (Accelerating!)',
        '📈 Price > 200 DMA (Long-term Uptrend)',
        '⚡ RSI 67.3 (Bullish)',
        '💪 Relative Strength 85 (Outperformer)'
    ],
    'data': {
        'revenue_yoy': 45.2,
        'revenue_qoq': 18.5,
        'pat_yoy': 38.7,
        'pat_qoq': 22.1,
        'eps_growth': 35.0,
        'eps_qoq': 15.2,
        'price': 1250.0,
        'dma_200': 1100.0,
        'rsi': 67.3,
        'relative_strength': 85
    }
}
```

## Database Requirements

For QoQ/YoY calculation to work, the `earnings` table needs:
- At least **2 quarters** of data for QoQ
- At least **5 quarters** of data for YoY (to find same quarter from previous year)

### Current Database Status
- **Total Records**: 4,392 in `earnings` table
- **With Revenue Data**: 99 companies (from historical PDF backfill)
- **Multi-Quarter Data**: Limited (most companies have 1-2 quarters)

## Usage

```python
from agents.ml.true_blockbuster_detector import TrueBlockbusterDetector

detector = TrueBlockbusterDetector()
result = detector.analyze_stock('543227', 'Happiest Minds Technologies')

# Access growth metrics
print(f"Revenue YoY: {result['data']['revenue_yoy']:.1f}%")
print(f"Revenue QoQ: {result['data']['revenue_qoq']:.1f}%")
print(f"Profit YoY: {result['data']['pat_yoy']:.1f}%")
print(f"Profit QoQ: {result['data']['pat_qoq']:.1f}%")
```

## Advantages of This Approach

1. **Momentum Detection**: QoQ > 15% flags accelerating businesses
2. **Flexible Scoring**: Companies can score high with either strong YoY OR strong QoQ
3. **Bonus Points**: QoQ adds bonus points, doesn't penalize if missing
4. **Database-Driven**: Uses historical data from `earnings_calendar.db`
5. **Fallback Support**: Falls back to Screener data if DB lacks history

## Next Steps to Improve

1. **Data Quality**: Continue backfilling historical quarters
2. **Seasonality Adjustment**: Adjust QoQ for seasonal businesses
3. **Trend Analysis**: Track if QoQ is improving or declining
4. **Alert Triggers**: Alert when QoQ accelerates significantly

## Files Modified

- `agents/ml/true_blockbuster_detector.py`:
  - Enhanced `_get_growth_metrics()` to calculate QoQ
  - Added `_calculate_growth_from_db()` for DB queries
  - Added `_calculate_qoq_from_db()` helper
  - Updated scoring logic to include QoQ bonuses

## Testing

Run the test script:
```bash
python3 test_qoq_growth.py
```

Or test directly:
```bash
python3 -c "
from agents.ml.true_blockbuster_detector import TrueBlockbusterDetector
detector = TrueBlockbusterDetector()
result = detector.analyze_stock('YOUR_BSE_CODE', 'Company Name')
print(result)
"
```

---

**Status**: ✅ **IMPLEMENTED AND TESTED**

The system now supports both YoY and QoQ growth calculations, providing a more comprehensive view of company performance and momentum.

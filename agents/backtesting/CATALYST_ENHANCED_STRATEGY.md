# Catalyst-Enhanced Small/Mid Cap Breakout Strategy

## Strategic Rationale

### Why Small/Mid Caps Over Large Caps?

**1. Higher Beta (Volatility)**
- Large caps (Nifty 50): Beta 0.8-1.2 (many fail beta >1.2 filter)
- Small/Mid caps: Beta 1.5-3.0+ (perfect for breakout strategy)
- More explosive moves = larger R-multiples

**2. Lower Free Float = Explosive Supply/Demand Dynamics**
- Limited shares available for trading
- Breakout with volume = rapid price expansion
- Can hit 5-10 consecutive upper circuits (20%+ in days)
- Perfect for VCP → breakout → momentum sequence

**3. Lower Liquidity = Higher Volatility**
- Not a bug, it's a feature for this strategy
- Volatility contraction (VCP) more pronounced
- Breakout moves more dramatic
- Exit requires discipline (not buy-and-hold)

**4. Fundamental Catalysts Have Bigger Impact**
- Large cap order win: +2-5% move
- Small cap order win: +15-30% move
- Examples:
  - Contract announcement
  - Order book increase
  - Capacity expansion
  - Export orders
  - Government contracts

## Current Strategy (Technical Only)

### Entry Criteria (ALL must be met)
1. **Beta > 1.2** vs Nifty (high volatility stock)
2. **Weekly uptrend** (20 SMA > 50 SMA, price > both)
3. **Daily breakout** (52-week high or consolidation breakout)
4. **Volume confirmation** (above 20-day average)
5. **Multiple timeframe alignment** (4H, daily, weekly all bullish)

### Exit Criteria
- Stop loss: 7-8% below entry
- Target: 15-20%+ (trail with 20-day MA)
- Time exit: If no progress after 20 days

## Phase 2: Fundamental Catalyst Layer (Future Enhancement)

### Catalyst Tracking System

**Sources to Monitor:**
1. **BSE/NSE Announcements**
   - Corporate filings (already scraping this!)
   - Board meetings
   - Results announcements

2. **Order Book / Revenue Announcements**
   - Contract wins
   - Order intake
   - Book-to-bill ratio
   - New client additions

3. **Capacity Expansion**
   - Capex announcements
   - New facility openings
   - Technology upgrades

4. **Export Orders / Government Contracts**
   - L1 bidder status
   - Contract awards
   - Export order pipeline

### Catalyst Scoring System

```python
catalyst_score = {
    'order_book_increase_50pct+': 10,    # Massive order surge
    'order_book_increase_25-50pct': 7,   # Significant orders
    'order_book_increase_10-25pct': 5,   # Moderate increase
    'new_major_contract': 8,             # Single large contract
    'capacity_expansion': 6,             # Growth investment
    'export_order_win': 7,               # International business
    'government_contract': 8,            # Stable, large orders
    'institutional_buying': 5,           # Smart money inflow
}

# Catalyst recency multiplier
recency_multiplier = {
    '0-7_days': 1.5,      # Very recent
    '8-30_days': 1.0,     # Recent
    '31-90_days': 0.5,    # Older news
}
```

### Enhanced Entry Logic

```python
def should_enter_trade(symbol, technical_signal, fundamental_data):
    # Phase 1: Technical filter (current system)
    if not technical_signal.all_conditions_met:
        return False

    # Phase 2: Fundamental catalyst boost (future)
    catalyst_score = calculate_catalyst_score(symbol, fundamental_data)

    if catalyst_score >= 15:  # Strong fundamental catalyst
        position_size = 1.5x  # Increase position (max 15% vs 10%)
        target = 25%          # Higher target (vs 15-20%)
    elif catalyst_score >= 10:  # Moderate catalyst
        position_size = 1.2x  # Slight increase (12% vs 10%)
        target = 20%
    elif catalyst_score >= 5:   # Weak/no catalyst
        position_size = 1.0x  # Normal position
        target = 15%
    else:  # No catalyst
        # Still take trade if technical setup is strong
        # (VCP + breakout can work without news)
        position_size = 0.8x  # Reduce position
        target = 12%

    return True, position_size, target
```

### Data Sources for Catalyst Tracking

**Already Available:**
- `/Users/srijan/vcp/agents/earnings_data_scraper.py` - BSE/NSE scraper
- `/Users/srijan/vcp/agents/earnings_analyzer.py` - Earnings quality
- `/Users/srijan/vcp/dexter/` - Multi-agent research system

**Need to Add:**
1. **Order Book Parser**
   - Parse quarterly results for order book mentions
   - Track sequential growth (Q-o-Q, Y-o-Y)
   - Alert on 25%+ increases

2. **News Sentiment for Catalyst Events**
   - Contract announcement detection
   - Capacity expansion keywords
   - Export order mentions

3. **SEC/SEBI Filing Parser**
   - Material event disclosures
   - Related party transactions (large orders)
   - Pledging changes (promoter confidence)

## Expected Performance Improvement

### Technical Only (Current)
- Win rate: 50-60% (disciplined entries)
- Avg win: 15-20%
- Avg loss: 7-8% (stop loss)
- Profit factor: 2.0-2.5
- Signals: 50-100/year (100 stock universe)

### Technical + Catalyst (Phase 2)
- Win rate: 65-75% (catalyst confirmation)
- Avg win: 20-30% (catalyst-driven moves)
- Avg loss: 7-8% (same discipline)
- Profit factor: 3.0-4.0
- Best trades: 50-100% (multi-bagger potential)
- Signals: 30-50/year (higher quality, fewer but better)

## Small/Mid Cap Universe (120 stocks)

### Sector Allocation
- **Chemicals/Specialty**: 15 stocks (high export potential)
- **Auto Components/EV**: 12 stocks (PLI scheme beneficiaries)
- **Engineering/Capital Goods**: 15 stocks (infra boom)
- **Pharma/Healthcare**: 12 stocks (API/CDMO growth)
- **IT/Tech Services**: 10 stocks (GCC, product companies)
- **BFSI/NBFCs**: 10 stocks (lending growth)
- **Consumer Discretionary**: 12 stocks (discretionary spending)
- **Real Estate/Infra**: 10 stocks (urbanization)
- **Textiles/Apparel**: 8 stocks (export orders)
- **Metals/Mining**: 8 stocks (commodity cycle)
- **Renewable Energy**: 8 stocks (energy transition)

### Selection Criteria
1. Market cap: ₹1,000 Cr - ₹50,000 Cr
2. Average daily volume: >₹5 Cr (tradable)
3. Promoter holding: >40% (skin in the game)
4. Debt/Equity: <1.5 (financial stability)
5. Revenue growth: >15% CAGR (last 3 years)

## Implementation Roadmap

### ✅ Phase 1: Technical Backtest (Current)
- Test small/mid cap universe (100-120 stocks)
- Validate strategy on 3 years of data
- Measure: trades, win rate, profit factor, Sharpe

### 🔄 Phase 2: Catalyst Data Integration (Next 2 weeks)
1. Build order book parser from quarterly results
2. Integrate BSE/NSE announcement tracker
3. Create catalyst scoring database
4. Backtest with historical catalyst data

### 🔜 Phase 3: Live Catalyst Monitoring (Month 1)
1. Real-time BSE/NSE announcement monitoring
2. Automated catalyst scoring
3. Alert system for catalyst + technical confluence
4. Position sizing based on catalyst strength

### 🚀 Phase 4: Paper Trading (Month 2-3)
1. Run strategy live with paper account
2. Validate entry/exit execution
3. Fine-tune catalyst scoring weights
4. Measure actual slippage in small caps

### 🎯 Phase 5: Live Trading (Month 4+)
1. Start with 20% of capital
2. Max 3-5 concurrent positions
3. Track actual vs backtested performance
4. Scale up if results match expectations

## Risk Management for Small Caps

**Unique Risks:**
1. **Liquidity Risk**: May not exit full position in one day
   - Solution: Size position to exit in 2-3 days max
   - Use limit orders, avoid market orders

2. **Gap Risk**: Small caps gap down more frequently
   - Solution: Stricter stop loss (7% vs 10%)
   - Avoid holding through results (unless catalyst play)

3. **Manipulation Risk**: Operator-driven moves
   - Solution: Require volume confirmation
   - Check promoter pledging before entry
   - Avoid stocks with surveillance warnings

4. **Circuit Lock Risk**: Can't exit if lower circuit
   - Solution: Exit 50% at +15%, trail rest
   - Never hold through "too good to be true" moves
   - Check delivery % (real vs speculative volume)

## Success Metrics

### Minimum Viability Criteria (Technical Only)
- 30+ trades over 3 years
- Win rate: >50%
- Profit factor: >2.0
- Max drawdown: <20%
- Sharpe ratio: >1.0

### Target Performance (Technical + Catalyst)
- 40+ trades over 3 years
- Win rate: >60%
- Profit factor: >3.0
- Max drawdown: <15%
- Sharpe ratio: >1.5
- Best trade: >50% return

## Next Steps

1. **Run small/mid cap backtest** (current task)
   - 100-120 stocks
   - 2022-2024 (3 years)
   - Validate strategy generates 30+ trades

2. **Build catalyst database**
   - Parse historical quarterly results
   - Extract order book mentions
   - Score historical catalysts

3. **Re-run backtest with catalyst layer**
   - Compare technical-only vs technical+catalyst
   - Measure improvement in win rate and avg win

4. **Deploy live monitoring**
   - BSE/NSE announcement webhook
   - Catalyst + technical alert system
   - Position sizing calculator

---

**Philosophy**:
- Small caps + VCP + Breakout + Catalyst = 20-30% returns in 2-4 weeks
- High beta + low float + fundamental catalyst = explosive moves
- Discipline beats prediction: Stop losses are sacred, targets are flexible

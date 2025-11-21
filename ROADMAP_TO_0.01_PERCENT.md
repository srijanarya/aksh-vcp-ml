# Roadmap to "0.01%" Blockbuster Intelligence System

## 1. Current System Status (Audit)

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| **ML Prediction API** | ✅ Deployed | AWS LightSail (13.200.109.29) | Running `vcp-ml-api`, but using placeholder models. Port 8002 needs opening. |
| **Blockbuster Scanner** | ⚠️ Local Only | `scan_blockbusters.py` | Runs on your local machine. Not yet automated on AWS. |
| **OCR Extraction** | ✅ Ready | `indian_pdf_extractor.py` | Can read scanned PDFs. Integrated into local workflow. |
| **Data Verification** | ✅ Ready | `DataAccuracyValidator` | Cross-checks BSE, Screener, and DB. |
| **Telegram Alerts** | ✅ Ready | `tools/telegram_bot.py` | Sends formatted alerts. |
| **"Big Order" Parsing** | ❌ Missing | N/A | No system to read "Order Bagged" announcements yet. |
| **Historical Data** | ⚠️ Insufficient | `earnings_calendar.db` | Only ~100 records. Need 5-10 years for backtesting. |

---

## 2. The "0.01%" Parameters (The Secret Sauce)

To find the top 0.01% of stocks (the "True Blockbusters"), we need to filter for **Confluence**.

### A. Fundamental Explosiveness (Quarterly)
1.  **Sales Growth (YoY)**: > 25% (Ideally > 50% for super-winners)
2.  **Profit Growth (YoY)**: > 25% (Must track sales)
3.  **EPS Growth (YoY)**: > 20%
4.  **Sequential Acceleration (QoQ)**: > 15% (New feature!)
5.  **Margin Expansion**: OPM increasing vs last year (Shows pricing power)

### B. Technical Strength (Daily/Weekly)
6.  **Relative Strength (RS)**: > 80 (Outperforming 80% of market)
7.  **Trend Template**: Price > 50DMA > 200DMA (Stage 2 Uptrend)
8.  **Volume Surge**: Volume > 50-day Avg on up-days (Institutional Buying)
9.  **Consolidation**: Breakout from a sound base (VCP, Cup & Handle) - *ML Model handles this*

### C. The "X-Factor" (Real-Time Catalysts)
10. **"Big Order" Wins**: Contracts > 10-20% of annual revenue.
11. **Capex Announcements**: Capacity expansion finishing soon.
12. **Promoter Buying**: Open market purchases.

---

## 3. Data Requirements for Backtesting

To scientifically prove and tune this system, we need:

1.  **Historical Financials (10 Years)**:
    *   Quarterly Results (Sales, PAT, EPS, OPM) for all NSE/BSE stocks.
    *   *Current Status*: We have ~100 records. Need ~50,000+ (10 years x 4 quarters x 1500 stocks).
    
2.  **Historical Price Data (10 Years)**:
    *   Daily OHLCV adjusted for splits/bonuses.
    *   *Current Status*: Yahoo Fetcher can get this, but we need to cache it systematically.

3.  **Historical Announcements (The Missing Link)**:
    *   Dates and text of "Order Wins", "Press Releases".
    *   *Why*: To correlate price surges with news events.
    *   *Current Status*: **Missing**.

---

## 4. Execution Plan (Next Steps)

### Phase 1: The "Big Order" Hunter (High Priority)
*   **Goal**: Catch stocks *before* earnings when they announce big wins.
*   **Action**: Build `CorporateAnnouncementFetcher` that:
    *   Scrapes BSE/NSE "Corporate Announcements" in real-time.
    *   Uses NLP/Regex to filter for: "Order", "Contract", "Awarded", "Bagged".
    *   Extracts value (e.g., "Rs 500 Cr").
    *   Calculates "Order vs Market Cap" impact.

### Phase 2: Massive Data Backfill
*   **Goal**: Get the data needed for backtesting.
*   **Action**:
    *   Write a robust scraper for Screener.in / BSE to pull 10 years of quarterly data.
    *   Store in a proper SQL database (PostgreSQL recommended over SQLite for this scale).

### Phase 3: AWS Automation
*   **Goal**: Make it run 24/7 without your laptop.
*   **Action**:
    *   Move `scan_blockbusters.py` to the AWS LightSail server.
    *   Set up a Cron Job to run it every 15 minutes.
    *   Configure the "Big Order" fetcher to run continuously.

### Phase 4: The "Intelligence" Layer
*   **Goal**: "Intelligent Actionable Intelligence".
*   **Action**:
    *   Train the ML model on the 10-year dataset.
    *   Teach it to recognize the *combination* of "Big Order" + "Technical Breakout".

## Summary
We have the **Engine** (Scanner, OCR, Validator) and the **Chassis** (AWS Server), but we are missing the **Fuel** (Historical Data) and the **Radar** (Real-time Announcement Parsing).

**Recommendation**: Focus immediately on **Phase 1 (Big Order Hunter)** and **Phase 2 (Data Backfill)**.

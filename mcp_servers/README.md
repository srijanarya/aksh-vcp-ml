# MCP Server Configurations

## Overview

MCP (Model Context Protocol) servers provide external API integrations for the ML system. These are third-party services that agents can call for real-time data and functionality.

**Architecture**: Tools (internal) → Skills (domain logic) → MCP (external APIs)

## Required MCP Servers

### 1. **yfinance MCP Server**
**Purpose**: Fallback stock price data when BSE/NSE BhavCopy is unavailable

**Configuration**:
```json
{
  "name": "yfinance",
  "type": "python-library",
  "package": "yfinance==0.2.35",
  "endpoints": [
    "get_historical_data",
    "get_current_price",
    "get_company_info"
  ],
  "rate_limit": "5 req/s",
  "cost": "Free (no API key required)"
}
```

**Usage Example**:
```python
import yfinance as yf

# Fetch TCS historical data (NSE)
ticker = yf.Ticker("TCS.NS")
hist = ticker.history(start="2024-01-01", end="2024-11-13")

# Fallback to BSE if NSE fails
if hist.empty:
    ticker = yf.Ticker("500570.BO")  # TCS BSE code
    hist = ticker.history(start="2024-01-01", end="2024-11-13")
```

**Integration Point**: `tools/bhav_copy_downloader.py` can use yfinance as fallback

---

### 2. **Telegram Bot MCP Server**
**Purpose**: Receive real-time BSE earnings alerts (critical for real-time inference)

**Configuration**:
```json
{
  "name": "telegram-bse-bot",
  "type": "telegram-webhook",
  "bot_token": "${TELEGRAM_BOT_TOKEN}",
  "channel_id": "@bse_announcements",
  "webhook_url": "https://your-server.com/telegram/webhook",
  "message_types": [
    "earnings_announcement",
    "board_meeting",
    "financial_results"
  ]
}
```

**Setup Instructions**:
1. Create Telegram bot via [@BotFather](https://t.me/botfather)
2. Get bot token: `/newbot` → `@your_bot_name`
3. Subscribe bot to BSE announcement channels
4. Configure webhook to receive messages
5. Parse messages for company name, earnings date, PDF URLs

**Message Format** (BSE Telegram):
```
🔔 BSE Announcement
Company: TCS LIMITED (500570)
Subject: Financial Results - Q1 FY25
Date: 2024-11-13 17:35
PDF: https://www.bseindia.com/xml-data/corpfiling/AttachLive/12345.pdf
```

**Integration Point**: `agents/ml/ml_inference_agent.py` listens to Telegram webhook

---

### 3. **BSE Corporate Filing API** (Future)
**Purpose**: Structured access to BSE announcements (alternative to Telegram scraping)

**Status**: ⚠️ **NOT PUBLICLY AVAILABLE**
- BSE does not provide public API for corporate filings
- Must use web scraping or Telegram monitoring
- If API becomes available, integrate here

**Configuration** (hypothetical):
```json
{
  "name": "bse-corporate-api",
  "type": "rest-api",
  "base_url": "https://api.bseindia.com/v1/",
  "auth_type": "api_key",
  "api_key": "${BSE_API_KEY}",
  "endpoints": {
    "get_announcements": "/corporate/announcements",
    "get_financials": "/corporate/financials/{company_code}",
    "get_pdf": "/corporate/filings/{filing_id}/pdf"
  },
  "rate_limit": "60 req/min",
  "cost": "Paid (hypothetical)"
}
```

**Current Alternative**: Use `tools/bhav_copy_downloader.py` for historical data + Telegram for real-time

---

### 4. **NSE API** (Future)
**Purpose**: Real-time NSE stock prices and announcements

**Status**: ⚠️ **LIMITED PUBLIC ACCESS**
- NSE removed public APIs in 2021
- Unofficial APIs exist but unreliable
- BhavCopy (ZIP files) still available for historical data

**Configuration** (if using unofficial API):
```json
{
  "name": "nse-unofficial",
  "type": "rest-api",
  "base_url": "https://www.nseindia.com/api/",
  "auth_type": "cookie-based",
  "headers": {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "application/json"
  },
  "endpoints": {
    "quote": "/quote-equity?symbol={symbol}",
    "historical": "/historical/cm/equity?symbol={symbol}"
  },
  "rate_limit": "2 req/s (conservative)",
  "reliability": "Low (frequent changes)"
}
```

**Current Alternative**: Use `tools/bhav_copy_downloader.py` (reliable, official NSE data)

---

## MCP Server Priority

### Phase 1 (Current): **Tools-Only Approach**
- ✅ BhavCopy downloader (no MCP needed)
- ✅ PDF downloader (no MCP needed)
- ✅ SQLite databases (local, no MCP)

**Rationale**: Historical data collection (Epic 1) doesn't need real-time APIs

### Phase 2 (Epic 4 - Real-Time Inference): **MCP Required**
- 🔴 **CRITICAL**: Telegram Bot MCP for BSE alerts
- 🟡 **NICE-TO-HAVE**: yfinance MCP for missing data

### Phase 3 (Future Optimization):
- 🟢 **FUTURE**: Official BSE/NSE APIs (if they become available)

---

## Implementation Guide

### Adding yfinance MCP

**File**: `mcp_servers/yfinance_mcp.py`

```python
"""
yfinance MCP Server - Wrapper for yfinance library
"""

import yfinance as yf
from typing import Dict, List, Optional
from tools.rate_limiter import YFINANCE_RATE_LIMITER, respect_rate_limit

class YFinanceMCP:
    """MCP wrapper for yfinance library"""

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        exchange: str = "NSE"
    ) -> List[Dict]:
        """
        Fetch historical OHLCV data from Yahoo Finance.

        Args:
            symbol: Stock symbol (TCS, INFY, etc.)
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            exchange: "NSE" or "BSE"

        Returns:
            List of OHLCV dictionaries
        """
        # Apply rate limiting
        respect_rate_limit(YFINANCE_RATE_LIMITER, operation_name=f"yfinance {symbol}")

        # Format ticker
        if exchange == "NSE":
            ticker_symbol = f"{symbol}.NS"
        elif exchange == "BSE":
            ticker_symbol = f"{symbol}.BO"
        else:
            raise ValueError(f"Invalid exchange: {exchange}")

        # Fetch data
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(start=start_date, end=end_date)

        # Convert to list of dicts
        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
                "source": "yfinance"
            })

        return records
```

### Adding Telegram Bot MCP

**File**: `mcp_servers/telegram_mcp.py`

```python
"""
Telegram MCP Server - Listen for BSE announcements
"""

import os
import re
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from typing import Callable, Dict

class TelegramBSEMonitor:
    """Monitor Telegram channels for BSE announcements"""

    def __init__(self, bot_token: str, callback: Callable):
        self.bot_token = bot_token
        self.callback = callback
        self.app = Application.builder().token(bot_token).build()

        # Add message handler
        handler = MessageHandler(filters.TEXT, self.handle_message)
        self.app.add_handler(handler)

    async def handle_message(self, update: Update, context):
        """Process incoming Telegram messages"""
        text = update.message.text

        # Parse BSE announcement
        announcement = self._parse_bse_announcement(text)

        if announcement:
            # Trigger callback (ML inference)
            await self.callback(announcement)

    def _parse_bse_announcement(self, text: str) -> Dict:
        """Extract structured data from BSE announcement text"""

        # Extract company code
        code_match = re.search(r'\((\d{6})\)', text)
        company_code = code_match.group(1) if code_match else None

        # Extract PDF URL
        pdf_match = re.search(r'(https://www\.bseindia\.com/.*?\.pdf)', text)
        pdf_url = pdf_match.group(1) if pdf_match else None

        # Extract subject
        subject_match = re.search(r'Subject: (.+?)$', text, re.MULTILINE)
        subject = subject_match.group(1) if subject_match else None

        if company_code and pdf_url and "Financial Results" in text:
            return {
                "company_code": company_code,
                "pdf_url": pdf_url,
                "subject": subject,
                "source": "telegram",
                "requires_inference": True
            }

        return None

    def start(self):
        """Start polling for messages"""
        self.app.run_polling()
```

---

## Environment Variables

Add to `.env` file:

```bash
# yfinance (no key required - library only)
# No configuration needed

# Telegram Bot
TELEGRAM_BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHANNEL_ID="@bse_announcements"

# BSE API (when available)
# BSE_API_KEY="your_api_key_here"

# NSE API (when available)
# NSE_API_KEY="your_api_key_here"
```

---

## Testing MCP Servers

### Test yfinance:
```bash
python mcp_servers/yfinance_mcp.py
```

### Test Telegram Bot:
```bash
python mcp_servers/telegram_mcp.py
```

---

## Next Steps

1. ✅ **Phase 1 (Current)**: Use Tools only (no MCP needed for Epic 1)
2. ⏳ **Phase 2 (Epic 4)**: Implement Telegram MCP for real-time inference
3. 🔮 **Phase 3 (Future)**: Add official APIs if they become available

---

**Last Updated**: 2025-11-13
**Status**: MCP documentation complete, implementation pending for Epic 4

"""
Telegram Blockbuster Alert Bot

Sends investment-grade blockbuster alerts to Telegram when new quarterly
results are announced.
"""

import logging
import requests
import os
import sys
from typing import Dict, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from agents.ml.blockbuster_detector import BlockbusterDetector

logger = logging.getLogger(__name__)

class TelegramBlockbusterBot:
    """Send blockbuster alerts via Telegram"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Initialize Telegram bot
        
        Args:
            bot_token: Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)
            chat_id: Telegram chat ID (or set TELEGRAM_CHAT_ID env var)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token:
            logger.warning("No Telegram bot token found. Alerts will be logged only.")
        if not self.chat_id:
            logger.warning("No Telegram chat ID found. Alerts will be logged only.")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.detector = BlockbusterDetector()
    
    def send_blockbuster_alert(self, result: Dict) -> bool:
        """
        Send a blockbuster alert to Telegram
        
        Args:
            result: Dictionary from BlockbusterDetector.analyze_company()
            
        Returns:
            True if sent successfully
        """
        message = self._format_message(result)
        
        # Log the message
        logger.info(f"Blockbuster Alert:\n{message}")
        
        # Send to Telegram if configured
        if self.bot_token and self.chat_id:
            return self._send_telegram_message(message)
        else:
            logger.warning("Telegram not configured. Alert logged only.")
            return False
    
    def _format_message(self, result: Dict) -> str:
        """
        Format blockbuster alert message
        
        Creates investment-grade alert with clear action items
        """
        # Emoji indicators
        score = result['blockbuster_score']
        if score >= 90:
            indicator = "🔥🔥🔥"
            signal = "VERY STRONG BUY"
        elif score >= 75:
            indicator = "🚀🚀"
            signal = "STRONG BUY"
        elif score >= 60:
            indicator = "🚀"
            signal = "BUY"
        else:
            indicator = "📊"
            signal = "WATCH"
        
        message = f"""
{indicator} BLOCKBUSTER ALERT {indicator}

📈 {result['company_name']}
{'='*40}

🏢 Company Details:
   BSE: {result['bse_code'] or 'N/A'}
   NSE: {result['nse_symbol'] or 'N/A'}

📊 Quarter: {result['quarter_text']} ({result['quarter']} FY{result['fy_year']})

💰 Financial Metrics:
   Revenue: ₹{result['revenue']:.0f} Cr ({result['revenue_yoy']:+.1f}% YoY)
   PAT: ₹{result['pat']:.0f} Cr ({result['pat_yoy']:+.1f}% YoY)
   EPS: ₹{result['eps']:.2f} ({result['eps_growth']:+.1f}% YoY)

✅ Criteria Met:
   {result['criteria_met']}

⭐ Blockbuster Score: {score}/100

🎯 Signal: {signal}

⏰ Action: Consider position within 24-48 hours
📅 Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
Powered by VCP ML Blockbuster Detector
"""
        return message.strip()
    
    def _send_telegram_message(self, message: str) -> bool:
        """Send message via Telegram API"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'  # or 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Telegram alert sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram alert: {e}")
            return False
    
    def process_new_companies(self, companies: list):
        """
        Process a list of companies and send blockbuster alerts
        
        Args:
            companies: List of dicts with 'url', 'name', 'bse_code', 'nse_symbol'
        """
        blockbusters_found = 0
        
        for company in companies:
            logger.info(f"Analyzing {company['name']}...")
            
            is_blockbuster, result = self.detector.analyze_company(
                company['url'],
                company.get('name'),
                company.get('bse_code'),
                company.get('nse_symbol')
            )
            
            if is_blockbuster:
                blockbusters_found += 1
                logger.info(f"🚀 Blockbuster found: {company['name']} (Score: {result['blockbuster_score']})")
                self.send_blockbuster_alert(result)
            else:
                logger.info(f"📊 Standard result: {company['name']}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Scan complete: {blockbusters_found} blockbusters found out of {len(companies)} companies")
        logger.info(f"{'='*60}")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize bot
    bot = TelegramBlockbusterBot()
    
    # Test with sample companies
    test_companies = [
        {
            'url': 'RELIANCE',
            'name': 'Reliance Industries',
            'bse_code': '500325',
            'nse_symbol': 'RELIANCE'
        },
        {
            'url': 'TCS',
            'name': 'Tata Consultancy Services',
            'bse_code': '532540',
            'nse_symbol': 'TCS'
        },
        {
            'url': 'NAVINFLUOR',
            'name': 'Navin Fluorine',
            'bse_code': '532504',
            'nse_symbol': 'NAVINFLUOR'
        }
    ]
    
    print("=" * 80)
    print("TELEGRAM BLOCKBUSTER BOT - TEST RUN")
    print("=" * 80)
    print(f"\nTelegram configured: {bool(bot.bot_token and bot.chat_id)}")
    if not (bot.bot_token and bot.chat_id):
        print("\n⚠️  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print("   to send actual Telegram alerts. For now, alerts will be logged.\n")
    
    # Process companies
    bot.process_new_companies(test_companies)

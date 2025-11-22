"""
Telegram Bot Tool

Simple wrapper for sending messages to Telegram.
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class TelegramBot:
    """Simple Telegram Bot for sending messages"""
    
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.token or not self.chat_id:
            logger.warning("Telegram credentials missing. Messages will be logged only.")
            
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to the configured chat"""
        if not self.token or not self.chat_id:
            logger.info(f"Telegram (Simulated): {message}")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

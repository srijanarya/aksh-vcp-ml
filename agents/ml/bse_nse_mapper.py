"""
BSE-NSE Mapper - Maps BSE Scrip Codes to NSE Symbols

This module provides functionality to map between exchange identifiers.
It uses a local mapping database or CSV file.

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import logging
import csv
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class BSENSEMapper:
    """
    Maps BSE codes to NSE symbols.
    """
    
    def __init__(self, mapping_file_path: str = None):
        self.mapping = {}
        if mapping_file_path and os.path.exists(mapping_file_path):
            self._load_mapping(mapping_file_path)
        else:
            # Default/Fallback mapping for common stocks
            self.mapping = {
                "500325": "RELIANCE",
                "532540": "TCS",
                "500209": "INFY",
                "500180": "HDFCBANK",
                "532174": "ICICIBANK",
                "500696": "HINDUNILVR",
                "500247": "KOTAKBANK",
                "500182": "HEROMOTOCO",
                "500520": "M&M",
                "500510": "LT"
            }
            
    def _load_mapping(self, file_path: str):
        """Load mapping from CSV"""
        try:
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'BSE_CODE' in row and 'NSE_SYMBOL' in row:
                        self.mapping[row['BSE_CODE']] = row['NSE_SYMBOL']
        except Exception as e:
            logger.error(f"Failed to load mapping file: {e}")

    def get_nse_symbol(self, bse_code: str) -> Optional[str]:
        """Get NSE symbol for a BSE code"""
        return self.mapping.get(str(bse_code))

    def get_bse_code(self, nse_symbol: str) -> Optional[str]:
        """Get BSE code for an NSE symbol"""
        for code, symbol in self.mapping.items():
            if symbol == nse_symbol:
                return code
        return None

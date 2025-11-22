"""
Log Analysis Skill - Specialized patterns for parsing system logs

This module provides regex patterns and logic to interpret:
1. Announcement Intelligence logs
2. Systemd service logs
3. Application tracebacks

Author: VCP Financial Research Team
Created: 2025-11-21
"""

import re
from typing import Dict, List, Any

class LogAnalyzer:
    """Analyzes log content for specific patterns"""
    
    PATTERNS = {
        "connection_error": r"Connection refused|Connection timed out|Network is unreachable",
        "auth_error": r"Authentication failed|Permission denied|403 Forbidden|401 Unauthorized",
        "pdf_error": r"PDF|PyPDF2|pdfplumber|Cannot read PDF",
        "db_error": r"sqlite3|OperationalError|Database locked",
        "memory_error": r"MemoryError|Out of memory|Kill process",
        "bse_fetch": r"Fetching announcements from BSE",
        "new_announcement": r"New Announcement:",
        "extraction_success": r"Successfully extracted|Extraction complete",
    }
    
    @classmethod
    def analyze_line(cls, line: str) -> Dict[str, Any]:
        """Analyze a single log line and return detected categories"""
        results = {
            "timestamp": cls._extract_timestamp(line),
            "level": cls._extract_level(line),
            "categories": []
        }
        
        for category, pattern in cls.PATTERNS.items():
            if re.search(pattern, line, re.IGNORECASE):
                results["categories"].append(category)
                
        return results
        
    @classmethod
    def summarize_logs(cls, log_lines: List[str]) -> Dict[str, int]:
        """Summarize a list of log lines by category"""
        summary = {cat: 0 for cat in cls.PATTERNS.keys()}
        summary["total_lines"] = len(log_lines)
        summary["errors"] = 0
        
        for line in log_lines:
            analysis = cls.analyze_line(line)
            for cat in analysis["categories"]:
                summary[cat] += 1
                
            if analysis["level"] in ["ERROR", "CRITICAL"]:
                summary["errors"] += 1
                
        return summary

    @staticmethod
    def _extract_timestamp(line: str) -> str:
        """Extract timestamp from standard log format"""
        # Matches 2025-11-21 06:28:32
        match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)
        return match.group(0) if match else ""

    @staticmethod
    def _extract_level(line: str) -> str:
        """Extract log level"""
        match = re.search(r" - (INFO|WARNING|ERROR|CRITICAL|DEBUG) - ", line)
        return match.group(1) if match else "UNKNOWN"

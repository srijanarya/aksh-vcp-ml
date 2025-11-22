"""
Circuit Identifier Tool

Identifies actual upper circuit events from price data using proper thresholds.
Upper circuits in Indian markets are typically 10-20% price moves with exchange-imposed limits.

Author: VCP Financial Research Team
Created: 2025-11-19
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def identify_circuits(
    db_path: str,
    threshold: float = 10.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict]:
    """
    Identify upper circuit events from price movements database.
    
    Args:
        db_path: Path to price_movements.db
        threshold: Minimum price change % to consider as circuit (default: 10.0)
        start_date: Start date for analysis (YYYY-MM-DD)
        end_date: End date for analysis (YYYY-MM-DD)
        
    Returns:
        List of circuit events with details
    """
    conn = sqlite3.connect(db_path)
    
    # Build query
    query = """
        SELECT 
            p1.bse_code,
            p1.date as circuit_date,
            p1.close as prev_close,
            p2.close as circuit_close,
            ((p2.close - p1.close) / p1.close * 100) as pct_change,
            p2.volume
        FROM price_movements p1
        JOIN price_movements p2 
            ON p1.bse_code = p2.bse_code 
            AND date(p2.date) = date(p1.date, '+1 day')
        WHERE ((p2.close - p1.close) / p1.close * 100) >= ?
    """
    
    params = [threshold]
    
    if start_date:
        query += " AND p2.date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND p2.date <= ?"
        params.append(end_date)
    
    query += " ORDER BY pct_change DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    circuits = df.to_dict('records')
    
    logger.info(f"Found {len(circuits)} circuit events with threshold >= {threshold}%")
    
    return circuits


def validate_circuit(
    db_path: str,
    bse_code: str,
    date: str,
    threshold: float = 10.0
) -> Tuple[bool, Optional[float]]:
    """
    Validate if a specific date had an upper circuit event.
    
    Args:
        db_path: Path to price_movements.db
        bse_code: BSE company code
        date: Date to check (YYYY-MM-DD)
        threshold: Minimum price change % (default: 10.0)
        
    Returns:
        Tuple of (is_circuit, price_change_pct)
    """
    conn = sqlite3.connect(db_path)
    
    query = """
        SELECT 
            ((p2.close - p1.close) / p1.close * 100) as pct_change
        FROM price_movements p1
        JOIN price_movements p2 
            ON p1.bse_code = p2.bse_code 
            AND date(p2.date) = date(p1.date, '+1 day')
        WHERE p1.bse_code = ?
          AND p2.date = ?
    """
    
    cursor = conn.cursor()
    cursor.execute(query, (bse_code, date))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return False, None
    
    pct_change = row[0]
    is_circuit = pct_change >= threshold
    
    return is_circuit, pct_change


def get_circuit_statistics(
    db_path: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    threshold: float = 10.0
) -> Dict:
    """
    Get statistics about circuit events.
    
    Args:
        db_path: Path to price_movements.db
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        threshold: Minimum price change % (default: 10.0)
        
    Returns:
        Dictionary with circuit statistics
    """
    circuits = identify_circuits(db_path, threshold, start_date, end_date)
    
    if not circuits:
        return {
            "total_circuits": 0,
            "avg_price_change": 0.0,
            "max_price_change": 0.0,
            "companies_affected": 0
        }
    
    df = pd.DataFrame(circuits)
    
    stats = {
        "total_circuits": len(circuits),
        "avg_price_change": df['pct_change'].mean(),
        "max_price_change": df['pct_change'].max(),
        "min_price_change": df['pct_change'].min(),
        "companies_affected": df['bse_code'].nunique(),
        "circuits_by_company": df['bse_code'].value_counts().to_dict()
    }
    
    return stats


def get_circuit_dates_for_company(
    db_path: str,
    bse_code: str,
    threshold: float = 10.0
) -> List[str]:
    """
    Get all circuit dates for a specific company.
    
    Args:
        db_path: Path to price_movements.db
        bse_code: BSE company code
        threshold: Minimum price change % (default: 10.0)
        
    Returns:
        List of dates (YYYY-MM-DD) when company hit circuit
    """
    circuits = identify_circuits(db_path, threshold)
    company_circuits = [c for c in circuits if c['bse_code'] == bse_code]
    
    return [c['circuit_date'] for c in company_circuits]


if __name__ == "__main__":
    # Demo usage
    db_path = "/Users/srijan/Desktop/aksh/data/price_movements.db"
    
    print("=== Circuit Identifier Demo ===\n")
    
    # Find all circuits with 10% threshold
    circuits = identify_circuits(db_path, threshold=10.0)
    print(f"Found {len(circuits)} circuits with 10% threshold")
    
    if circuits:
        print("\nTop 5 circuits:")
        for i, circuit in enumerate(circuits[:5], 1):
            print(f"{i}. {circuit['bse_code']} on {circuit['circuit_date']}: "
                  f"{circuit['pct_change']:.2f}% change")
    
    # Get statistics
    stats = get_circuit_statistics(db_path, threshold=10.0)
    print(f"\n=== Circuit Statistics ===")
    print(f"Total circuits: {stats['total_circuits']}")
    print(f"Average price change: {stats['avg_price_change']:.2f}%")
    print(f"Max price change: {stats['max_price_change']:.2f}%")
    print(f"Companies affected: {stats['companies_affected']}")

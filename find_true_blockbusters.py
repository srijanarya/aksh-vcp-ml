#!/usr/bin/env python3
"""
TRUE BLOCKBUSTER FINDER - Top 5-10 Quarterly Performers

This finds the absolute best performing stocks in a quarter,
not just those meeting arbitrary thresholds.

True Blockbusters = Top 0.2% of market performers
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Tuple
import json
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrueBlockbusterFinder:
    """
    Finds the ACTUAL top 5-10 best performing stocks in the market
    based on quarterly results.
    """

    def __init__(self):
        self.results_cache = []

    def find_quarter_blockbusters(self,
                                 quarter: str = "Q2",
                                 fiscal_year: str = "2024",
                                 top_n: int = 10) -> pd.DataFrame:
        """
        Find the TOP N best performing stocks for a specific quarter.

        Not based on thresholds, but absolute ranking!
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"FINDING TRUE BLOCKBUSTERS - {quarter} FY{fiscal_year}")
        logger.info(f"{'='*80}")

        all_companies = []

        # 1. Check historical_financials.db
        if Path("data/historical_financials.db").exists():
            conn = sqlite3.connect("data/historical_financials.db")

            # Get all companies with data for this quarter and previous year
            query = """
            WITH current_quarter AS (
                SELECT
                    company_name,
                    bse_code,
                    revenue,
                    pat,
                    eps
                FROM quarterly_results
                WHERE quarter = ? AND fiscal_year = ?
                AND revenue IS NOT NULL AND pat IS NOT NULL
            ),
            previous_year AS (
                SELECT
                    company_name,
                    bse_code,
                    revenue as prev_revenue,
                    pat as prev_pat,
                    eps as prev_eps
                FROM quarterly_results
                WHERE quarter = ? AND fiscal_year = ?
                AND revenue IS NOT NULL AND pat IS NOT NULL
            )
            SELECT
                c.*,
                p.prev_revenue,
                p.prev_pat,
                p.prev_eps
            FROM current_quarter c
            JOIN previous_year p ON c.bse_code = p.bse_code
            """

            prev_year = str(int(fiscal_year) - 1)
            df = pd.read_sql(query, conn, params=(quarter, fiscal_year, quarter, prev_year))
            conn.close()

            for _, row in df.iterrows():
                revenue_growth = ((row['revenue'] - row['prev_revenue']) / abs(row['prev_revenue'])) * 100 if row['prev_revenue'] else 0
                pat_growth = ((row['pat'] - row['prev_pat']) / abs(row['prev_pat'])) * 100 if row['prev_pat'] else 0

                all_companies.append({
                    'company_name': row['company_name'],
                    'bse_code': row['bse_code'],
                    'quarter': quarter,
                    'fiscal_year': fiscal_year,
                    'revenue': row['revenue'],
                    'pat': row['pat'],
                    'eps': row['eps'],
                    'revenue_growth': revenue_growth,
                    'pat_growth': pat_growth,
                    'composite_score': self._calculate_composite_score(revenue_growth, pat_growth)
                })

        # 2. Check earnings_calendar.db
        if Path("data/earnings_calendar.db").exists():
            conn = sqlite3.connect("data/earnings_calendar.db")

            # Similar query for earnings database
            query = """
            SELECT DISTINCT
                company_name,
                bse_code,
                revenue,
                profit as pat,
                eps
            FROM earnings_results
            WHERE quarter = ? AND fiscal_year = ?
            AND extraction_status = 'completed'
            AND revenue IS NOT NULL AND profit IS NOT NULL
            """

            df = pd.read_sql(query, conn, params=(quarter, fiscal_year))

            # For each company, get YoY data
            for _, row in df.iterrows():
                prev_query = """
                SELECT revenue, profit as pat, eps
                FROM earnings_results
                WHERE bse_code = ? AND quarter = ? AND fiscal_year = ?
                AND extraction_status = 'completed'
                """

                prev_year = str(int(fiscal_year) - 1)
                prev_df = pd.read_sql(prev_query, conn, params=(row['bse_code'], quarter, prev_year))

                if not prev_df.empty:
                    prev = prev_df.iloc[0]
                    revenue_growth = ((row['revenue'] - prev['revenue']) / abs(prev['revenue'])) * 100 if prev['revenue'] else 0
                    pat_growth = ((row['pat'] - prev['pat']) / abs(prev['pat'])) * 100 if prev['pat'] else 0

                    # Check if already added
                    if not any(c['bse_code'] == row['bse_code'] for c in all_companies):
                        all_companies.append({
                            'company_name': row['company_name'],
                            'bse_code': row['bse_code'],
                            'quarter': quarter,
                            'fiscal_year': fiscal_year,
                            'revenue': row['revenue'],
                            'pat': row['pat'],
                            'eps': row['eps'],
                            'revenue_growth': revenue_growth,
                            'pat_growth': pat_growth,
                            'composite_score': self._calculate_composite_score(revenue_growth, pat_growth)
                        })

            conn.close()

        if not all_companies:
            logger.warning("No companies found with complete YoY data")
            return pd.DataFrame()

        # Convert to DataFrame and RANK
        df = pd.DataFrame(all_companies)

        # Sort by composite score (best performers first)
        df = df.sort_values('composite_score', ascending=False)

        # Add ranking
        df['rank'] = range(1, len(df) + 1)

        # Calculate percentile
        df['percentile'] = 100 - (df['rank'] / len(df) * 100)

        logger.info(f"\nTotal companies analyzed: {len(df)}")
        logger.info(f"Finding TOP {top_n} performers (top {top_n/len(df)*100:.1f}% of market)")

        # Get true blockbusters (top N)
        blockbusters = df.head(top_n).copy()

        # Mark as true blockbusters
        blockbusters['is_true_blockbuster'] = True

        return blockbusters

    def _calculate_composite_score(self, revenue_growth: float, pat_growth: float) -> float:
        """
        Calculate a composite score for ranking.

        Weighted: 40% revenue growth, 60% profit growth
        (Profit growth is more important for blockbusters)
        """
        return (revenue_growth * 0.4) + (pat_growth * 0.6)

    def display_true_blockbusters(self, df: pd.DataFrame):
        """Display the true blockbusters in a formatted way"""

        print("\n" + "="*100)
        print(f"🏆 TRUE BLOCKBUSTERS - TOP {len(df)} QUARTERLY PERFORMERS 🏆")
        print("="*100)

        for _, row in df.iterrows():
            rank_emoji = "🥇" if row['rank'] == 1 else "🥈" if row['rank'] == 2 else "🥉" if row['rank'] == 3 else "🏆"

            print(f"\n{rank_emoji} RANK #{row['rank']} - {row['company_name']}")
            print(f"   BSE Code: {row['bse_code']}")
            print(f"   📈 Revenue Growth: {row['revenue_growth']:+.1f}%")
            print(f"   💰 PAT Growth: {row['pat_growth']:+.1f}%")
            print(f"   📊 Composite Score: {row['composite_score']:.1f}")
            print(f"   🎯 Percentile: Top {100-row['percentile']:.1f}% of market")
            print(f"   💵 Revenue: ₹{row['revenue']:.0f} Cr | PAT: ₹{row['pat']:.0f} Cr")

        print("\n" + "="*100)
        print("INSIGHTS:")
        print("="*100)

        avg_rev_growth = df['revenue_growth'].mean()
        avg_pat_growth = df['pat_growth'].mean()

        print(f"📊 Average Revenue Growth of Top {len(df)}: {avg_rev_growth:+.1f}%")
        print(f"💰 Average PAT Growth of Top {len(df)}: {avg_pat_growth:+.1f}%")
        print(f"🎯 These represent the top {len(df)/5000*100:.2f}% of the Indian stock market")
        print(f"⚡ Minimum growth to be blockbuster: Revenue {df['revenue_growth'].min():+.1f}%, PAT {df['pat_growth'].min():+.1f}%")

        # Compare with our old threshold approach
        old_blockbusters = df[(df['revenue_growth'] > 15) & (df['pat_growth'] > 20)]
        print(f"\n📈 Using old thresholds (Rev>15%, PAT>20%): Would find {len(old_blockbusters)} companies")
        print(f"🎯 True blockbuster approach: Finds exactly the TOP {len(df)} performers")

    def compare_quarters(self, quarters: List[Tuple[str, str]], top_n: int = 10):
        """Compare blockbusters across multiple quarters"""

        all_quarters_data = []

        for quarter, fiscal_year in quarters:
            df = self.find_quarter_blockbusters(quarter, fiscal_year, top_n)
            if not df.empty:
                df['quarter_label'] = f"{quarter} FY{fiscal_year}"
                all_quarters_data.append(df)

        if not all_quarters_data:
            logger.warning("No data found for any quarters")
            return

        combined = pd.concat(all_quarters_data, ignore_index=True)

        print("\n" + "="*100)
        print("📊 MULTI-QUARTER BLOCKBUSTER COMPARISON")
        print("="*100)

        # Find repeat blockbusters
        company_counts = combined['bse_code'].value_counts()
        repeat_blockbusters = company_counts[company_counts > 1]

        if not repeat_blockbusters.empty:
            print("\n🔥 CONSISTENT BLOCKBUSTERS (appeared multiple times):")
            for bse_code, count in repeat_blockbusters.items():
                company_name = combined[combined['bse_code'] == bse_code].iloc[0]['company_name']
                quarters = combined[combined['bse_code'] == bse_code]['quarter_label'].tolist()
                print(f"  • {company_name} ({bse_code}): {count} quarters")
                print(f"    Quarters: {', '.join(quarters)}")

        # Best overall performer
        best = combined.loc[combined['composite_score'].idxmax()]
        print(f"\n🏆 BEST OVERALL PERFORMER:")
        print(f"  {best['company_name']} in {best['quarter_label']}")
        print(f"  Revenue Growth: {best['revenue_growth']:+.1f}% | PAT Growth: {best['pat_growth']:+.1f}%")


def main():
    """Main function to find true blockbusters"""

    finder = TrueBlockbusterFinder()

    # Find blockbusters for latest quarter we have data for
    print("\n" + "="*100)
    print("TRUE BLOCKBUSTER FINDER - Finding Market Leaders, Not Just Good Performers")
    print("="*100)

    # Try Q2 FY2024 (most recent complete quarter likely)
    blockbusters = finder.find_quarter_blockbusters("Q2", "2024", top_n=10)

    if not blockbusters.empty:
        finder.display_true_blockbusters(blockbusters)

        # Save to file
        output_file = "TRUE_BLOCKBUSTERS_Q2_FY2024.json"
        blockbusters.to_json(output_file, orient='records', indent=2)
        print(f"\n✅ Results saved to {output_file}")
    else:
        print("\n⚠️ No data found for Q2 FY2024, trying Q1 FY2024...")
        blockbusters = finder.find_quarter_blockbusters("Q1", "2024", top_n=10)

        if not blockbusters.empty:
            finder.display_true_blockbusters(blockbusters)

    # Compare multiple quarters if we have data
    print("\n\nComparing multiple quarters...")
    quarters_to_compare = [
        ("Q1", "2024"),
        ("Q2", "2024"),
        ("Q4", "2023"),
        ("Q3", "2023")
    ]

    finder.compare_quarters(quarters_to_compare, top_n=5)


if __name__ == "__main__":
    main()
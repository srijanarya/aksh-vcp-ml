"""
Screener.in API Client for Quarterly Financial Data

Fetches fundamental data from screener.in to calculate accurate
blockbuster metrics with historical context.
"""

import requests
import pandas as pd
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class ScreenerClient:
    """Client for fetching data from screener.in"""
    
    BASE_URL = "https://www.screener.in"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
    
    def search_company(self, query: str) -> Optional[Dict]:
        """
        Search for company by name or BSE code
        
        Returns:
            Dict with company_id and name if found
        """
        try:
            url = f"{self.BASE_URL}/api/company/search/?q={query}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                return {
                    'company_id': data[0]['id'],
                    'name': data[0]['name'],
                    'url': data[0]['url']
                }
            return None
        except Exception as e:
            logger.error(f"Error searching for {query}: {e}")
            return None
    
    def get_quarterly_results(self, company_url: str, num_quarters: int = 5) -> pd.DataFrame:
        """
        Fetch quarterly financial results by scraping HTML
        
        Args:
            company_url: Company URL slug (e.g., 'RELIANCE' for Reliance Industries)
            num_quarters: Number of recent quarters to fetch
            
        Returns:
            DataFrame with columns: quarter, fy_year, revenue, pat, eps
        """
        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Add delay between requests to avoid rate limiting
                if attempt > 0:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retry {attempt + 1}/{max_retries} after {delay}s delay...")
                    time.sleep(delay)
                else:
                    # Small delay even on first attempt
                    time.sleep(1.5)
                
                url = f"{self.BASE_URL}/company/{company_url}/consolidated/"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
            
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the quarterly results table
                results_section = soup.find('section', id='quarters')
                if not results_section:
                    logger.error("Could not find quarterly results section")
                    return pd.DataFrame()
                
                table = results_section.find('table', class_='data-table')
                if not table:
                    logger.error("Could not find results table")
                    return pd.DataFrame()

                # Parse table headers (quarters)
                headers = []
                header_row = table.find('thead').find('tr')
                for th in header_row.find_all('th')[1:num_quarters+1]:  # Skip first empty th
                    quarter_text = th.get_text(strip=True)
                    headers.append(quarter_text)

                # Parse table rows
                quarters_data = {h: {} for h in headers}

                tbody = table.find('tbody')
                for row in tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) < 2:
                        continue

                    metric_name = cells[0].get_text(strip=True).lower()

                    # Extract values for each quarter
                    for i, header in enumerate(headers):
                        if i + 1 < len(cells):
                            value_text = cells[i + 1].get_text(strip=True)
                            value = self._parse_number(value_text)

                            # Map metric names
                            if 'sales' in metric_name or 'revenue' in metric_name:
                                quarters_data[header]['revenue'] = value
                            elif 'operating profit' in metric_name or 'opm %' in metric_name:
                                quarters_data[header]['opm'] = value
                            elif 'net profit' in metric_name and 'margin' not in metric_name:
                                quarters_data[header]['pat'] = value
                            elif 'eps' in metric_name:
                                quarters_data[header]['eps'] = value

                # Convert to DataFrame
                quarters = []
                for i, (quarter_text, data) in enumerate(quarters_data.items()):
                    # Parse quarter text (e.g., "Sep 2024" -> Q2 FY2025)
                    quarter_info = self._parse_quarter_text(quarter_text)
                    quarters.append({
                        'quarter': quarter_info['quarter'],
                        'fy_year': quarter_info['fy_year'],
                        'quarter_text': quarter_text,
                        'revenue': data.get('revenue', 0),
                        'pat': data.get('pat', 0),
                        'eps': data.get('eps', 0),
                        'opm': data.get('opm', 0),
                        'index': i  # 0=most recent
                    })

                df = pd.DataFrame(quarters)
                logger.info(f"Fetched {len(df)} quarters for {company_url}")
                return df  # Success - return results
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    # Rate limit exceeded - retry with backoff
                    logger.warning(f"Rate limited (429) for {company_url}, attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for {company_url}")
                        return pd.DataFrame()
                    continue  # Retry
                else:
                    # Other HTTP error - don't retry
                    logger.error(f"HTTP error {e.response.status_code} for {company_url}: {e}")
                    return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error fetching quarters for {company_url}: {e}")
                if attempt == max_retries - 1:
                    return pd.DataFrame()
                # Retry on other errors too
                continue
        
        # Should not reach here, but just in case
        return pd.DataFrame()
    
    def _parse_number(self, text: str) -> float:
        """Parse number from text, handling , and -"""
        if not text or text == '-' or text == '':
            return 0.0
        try:
            # Remove commas
            text = text.replace(',', '')
            return float(text)
        except:
            return 0.0
    
    def _parse_quarter_text(self, quarter_text: str) -> Dict:
        """
        Parse quarter text like 'Sep 2024' or 'Mar 2025'
        Returns: {'quarter': 'Q2', 'fy_year': 2025}
        """
        monthstr = quarter_text.split()[0][:3].lower()
        year = int(quarter_text.split()[1])
        
        # Map month to quarter and FY year
        month_to_q = {
            'mar': ('Q4', year),      # Mar = Q4 of FY ending that year
            'jun': ('Q1', year + 1),  # Jun = Q1 of next FY
            'sep': ('Q2', year + 1),  # Sep = Q2 of next FY
            'dec': ('Q3', year + 1),  # Dec = Q3 of next FY
        }
        
        quarter, fy_year = month_to_q.get(monthstr, ('Q?', year))
        
        return {
            'quarter': quarter,
            'fy_year': fy_year
        }
    
    def get_company_by_bse_code(self, bse_code: str) -> Optional[Dict]:
        """
        Get company details by BSE code
        
        First tries direct BSE code search, then company name lookup
        """
        # Try BSE code directly
        result = self.search_company(bse_code)
        if result:
            return result
        
        # If not found, you may need to search by company name
        # This would require a mapping from BSE code to name
        logger.warning(f"Could not find company for BSE code: {bse_code}")
        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = ScreenerClient()
    
    # Test with Reliance
    print("Fetching Reliance quarterly data...")
    quarters = client.get_quarterly_results("RELIANCE", num_quarters=5)
    
    if not quarters.empty:
        print(f"\nQuarterly Results ({len(quarters)} quarters):")
        print(quarters[['quarter_text', 'quarter', 'fy_year', 'revenue', 'pat', 'eps']].to_string(index=False))
        
        # Calculate YoY growth
        if len(quarters) >= 5:
            current = quarters.iloc[0]
            yoy = quarters.iloc[4]  # Same quarter last year
            
            revenue_yoy = ((current['revenue'] - yoy['revenue']) / yoy['revenue']) * 100 if yoy['revenue'] > 0 else 0
            pat_yoy = ((current['pat'] - yoy['pat']) / yoy['pat']) * 100 if yoy['pat'] > 0 else 0
            
            print(f"\nYoY Growth (vs {yoy['quarter_text']}):")
            print(f"  Revenue: {revenue_yoy:+.2f}%")
            print(f"  PAT: {pat_yoy:+.2f}%")
            print(f"  EPS: ₹{current['eps']:.2f}")
            
            # Check blockbuster
            is_blockbuster = revenue_yoy > 15.0 and pat_yoy > 20.0 and current['eps'] > 0
            print(f"\n🚀 Blockbuster: {is_blockbuster}")
            if is_blockbuster:
                print(f"   ✅ Revenue growth {revenue_yoy:.1f}% > 15%")
                print(f"   ✅ PAT growth {pat_yoy:.1f}% > 20%")
                print(f"   ✅ EPS ₹{current['eps']:.2f} > 0")
    else:
        print("No quarterly data found")

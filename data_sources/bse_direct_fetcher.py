"""
BSE Direct Data Fetcher
Fetches official data directly from BSE website
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Optional, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp

class BSEDirectFetcher:
    """Fetch data directly from BSE official sources"""

    def __init__(self):
        self.base_url = "https://www.bseindia.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.bseindia.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_company_info(self, bse_code: str) -> Optional[Dict]:
        """
        Fetch company information from BSE

        Args:
            bse_code: BSE scrip code (e.g., "532540")

        Returns:
            Company info with timestamp
        """
        try:
            url = f"{self.base_url}/stock-share-price/stockreach_financials.aspx"
            params = {
                'scripcode': bse_code,
                'expandable': 'quarterly'
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = {
                'bse_code': bse_code,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'BSE_DIRECT',
                'status': 'success'
            }

            # Parse HTML for company info
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract company name
            name_elem = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblCompanyName'})
            if name_elem:
                data['company_name'] = name_elem.text.strip()

            return data

        except Exception as e:
            return {
                'bse_code': bse_code,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'BSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }

    def fetch_latest_results(self, bse_code: str) -> Optional[Dict]:
        """
        Fetch latest quarterly results from BSE

        Returns:
            Dict with quarterly results and metadata
        """
        try:
            # BSE API endpoint for financial results
            url = f"{self.base_url}/corporates/results.aspx"
            params = {
                'Code': bse_code,
                'Company': '',
                'qtr': '1',  # Latest quarter
                'RType': 'Q'  # Quarterly
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            timestamp = DataTimestamp.create_timestamp()

            # Look for results table
            results_table = soup.find('table', {'class': 'viewTable'})

            if not results_table:
                return {
                    'bse_code': bse_code,
                    'fetch_timestamp': timestamp,
                    'source': 'BSE_DIRECT',
                    'status': 'no_data',
                    'message': 'No quarterly results found'
                }

            # Parse table headers and data
            headers = []
            quarters_data = []

            # Get headers (quarters)
            header_row = results_table.find('tr')
            if header_row:
                for th in header_row.find_all('th')[1:]:  # Skip first column
                    headers.append(th.text.strip())

            # Parse financial data rows
            for row in results_table.find_all('tr')[1:]:
                cells = row.find_all('td')
                if cells:
                    metric_name = cells[0].text.strip()

                    if 'Revenue' in metric_name or 'Sales' in metric_name:
                        revenues = [self._parse_number(cell.text) for cell in cells[1:]]
                        quarters_data.append(('revenue', revenues))

                    elif 'Net Profit' in metric_name and 'Margin' not in metric_name:
                        profits = [self._parse_number(cell.text) for cell in cells[1:]]
                        quarters_data.append(('net_profit', profits))

                    elif 'EPS' in metric_name and 'Diluted' not in metric_name:
                        eps_values = [self._parse_number(cell.text) for cell in cells[1:]]
                        quarters_data.append(('eps', eps_values))

            # Structure the data
            result = {
                'bse_code': bse_code,
                'fetch_timestamp': timestamp,
                'source': 'BSE_DIRECT',
                'status': 'success',
                'quarters': headers,
                'financial_data': {}
            }

            # Organize by quarter
            for i, quarter_label in enumerate(headers[:5]):  # Take latest 5 quarters
                quarter_data = {}
                for metric, values in quarters_data:
                    if i < len(values):
                        quarter_data[metric] = values[i]

                result['financial_data'][quarter_label] = quarter_data

            # Calculate YoY growth if we have 5 quarters
            if len(headers) >= 5:
                latest = result['financial_data'].get(headers[0], {})
                year_ago = result['financial_data'].get(headers[4], {})

                if latest.get('revenue') and year_ago.get('revenue'):
                    result['revenue_yoy'] = ((latest['revenue'] - year_ago['revenue']) /
                                            abs(year_ago['revenue'])) * 100

                if latest.get('net_profit') and year_ago.get('net_profit'):
                    result['profit_yoy'] = ((latest['net_profit'] - year_ago['net_profit']) /
                                           abs(year_ago['net_profit'])) * 100

            return result

        except Exception as e:
            return {
                'bse_code': bse_code,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'BSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }

    def fetch_announcements(self, bse_code: str, days_back: int = 30) -> List[Dict]:
        """
        Fetch recent corporate announcements

        Args:
            bse_code: BSE scrip code
            days_back: Number of days to look back

        Returns:
            List of announcements with timestamps
        """
        try:
            # BSE announcements API
            url = f"{self.base_url}/api/AnnGetData/w"

            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
            to_date = datetime.now().strftime('%Y%m%d')

            params = {
                'strCat': '-1',
                'strPrevDate': from_date,
                'strScrip': bse_code,
                'strSearch': 'P',
                'strToDate': to_date,
                'strType': 'C'
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return []

            announcements = []
            data = response.json() if response.text else {}

            if 'Table' in data:
                for item in data['Table']:
                    ann = {
                        'bse_code': bse_code,
                        'announcement_date': item.get('NEWS_DT', ''),
                        'subject': item.get('NEWSSUB', ''),
                        'category': item.get('CAT_NAME', ''),
                        'fetch_timestamp': DataTimestamp.create_timestamp(),
                        'source': 'BSE_DIRECT'
                    }

                    # Check if it's an earnings announcement
                    subject_lower = ann['subject'].lower()
                    if any(keyword in subject_lower for keyword in
                          ['result', 'earnings', 'financial', 'quarter']):
                        ann['is_earnings'] = True

                    announcements.append(ann)

            return announcements

        except Exception as e:
            return [{
                'bse_code': bse_code,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'BSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }]

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse Indian number format (with Cr, Lakh, etc.)"""
        try:
            text = text.strip().replace(',', '')

            if 'Cr' in text or 'cr' in text:
                number = float(re.sub(r'[^0-9.-]', '', text))
                return number  # Already in crores
            elif 'Lakh' in text or 'lakh' in text or 'Lac' in text:
                number = float(re.sub(r'[^0-9.-]', '', text))
                return number / 100  # Convert lakh to crores
            else:
                # Plain number
                return float(re.sub(r'[^0-9.-]', '', text))
        except:
            return None


# Test the fetcher
if __name__ == "__main__":
    fetcher = BSEDirectFetcher()

    # Test with TCS
    print("Testing BSE Direct Fetcher with TCS (532540)")
    print("-" * 60)

    # Fetch company info
    info = fetcher.fetch_company_info("532540")
    if info:
        print(f"Company: {info.get('company_name', 'N/A')}")
        print(f"Source: {info['source']}")
        print(f"Fetched at: {info['fetch_timestamp']['timestamp']}")

    # Fetch latest results
    print("\nFetching latest quarterly results...")
    results = fetcher.fetch_latest_results("532540")
    if results and results.get('status') == 'success':
        print(f"Quarters available: {results.get('quarters', [])[:3]}")
        print(f"Revenue YoY: {results.get('revenue_yoy', 'N/A'):.1f}%"
              if results.get('revenue_yoy') else "Revenue YoY: N/A")
        print(f"Profit YoY: {results.get('profit_yoy', 'N/A'):.1f}%"
              if results.get('profit_yoy') else "Profit YoY: N/A")

    # Fetch announcements
    print("\nFetching recent announcements...")
    announcements = fetcher.fetch_announcements("532540", days_back=30)
    earnings_ann = [a for a in announcements if a.get('is_earnings')]
    print(f"Total announcements: {len(announcements)}")
    print(f"Earnings announcements: {len(earnings_ann)}")
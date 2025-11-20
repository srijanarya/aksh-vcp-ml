"""
NSE Direct Data Fetcher
Fetches official data directly from NSE website
"""

import requests
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp

class NSEDirectFetcher:
    """Fetch data directly from NSE official sources"""

    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Get cookie first
        self._initialize_session()

    def _initialize_session(self):
        """Initialize NSE session with required cookies"""
        try:
            # Visit homepage to get cookies
            self.session.get(self.base_url, timeout=10)
        except:
            pass

    def fetch_company_info(self, nse_symbol: str) -> Optional[Dict]:
        """
        Fetch company information from NSE

        Args:
            nse_symbol: NSE symbol (e.g., "TCS")

        Returns:
            Company info with timestamp
        """
        try:
            url = f"{self.base_url}/api/quote-equity"
            params = {'symbol': nse_symbol.upper()}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            info = data.get('info', {})
            metadata = data.get('metadata', {})
            price_info = data.get('priceInfo', {})

            result = {
                'nse_symbol': nse_symbol.upper(),
                'company_name': info.get('companyName', ''),
                'isin': info.get('isin', ''),
                'industry': metadata.get('industry', ''),
                'sector': metadata.get('sector', ''),
                'market_cap': metadata.get('marketCap', 0),
                'current_price': price_info.get('lastPrice', 0),
                'change_percent': price_info.get('pChange', 0),
                'volume': price_info.get('totalTradedVolume', 0),
                '52_week_high': price_info.get('week52High', 0),
                '52_week_low': price_info.get('week52Low', 0),
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'NSE_DIRECT',
                'status': 'success'
            }

            return result

        except Exception as e:
            return {
                'nse_symbol': nse_symbol,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'NSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }

    def fetch_financial_results(self, nse_symbol: str) -> Optional[Dict]:
        """
        Fetch financial results from NSE

        Args:
            nse_symbol: NSE symbol

        Returns:
            Financial results with metadata
        """
        try:
            url = f"{self.base_url}/api/results-comparision"
            params = {'symbol': nse_symbol.upper()}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            timestamp = DataTimestamp.create_timestamp()

            # Parse results
            results = data.get('results', [])

            if not results:
                return {
                    'nse_symbol': nse_symbol,
                    'fetch_timestamp': timestamp,
                    'source': 'NSE_DIRECT',
                    'status': 'no_data'
                }

            # Structure the quarterly data
            quarterly_data = []

            for quarter in results[:5]:  # Last 5 quarters
                q_data = {
                    'period': quarter.get('period', ''),
                    'revenue': self._parse_value(quarter.get('income', 0)),
                    'expenditure': self._parse_value(quarter.get('expenditure', 0)),
                    'operating_profit': self._parse_value(quarter.get('operatingProfit', 0)),
                    'other_income': self._parse_value(quarter.get('otherIncome', 0)),
                    'interest': self._parse_value(quarter.get('interest', 0)),
                    'depreciation': self._parse_value(quarter.get('depreciation', 0)),
                    'profit_before_tax': self._parse_value(quarter.get('profitBeforeTax', 0)),
                    'tax': self._parse_value(quarter.get('tax', 0)),
                    'net_profit': self._parse_value(quarter.get('netProfit', 0)),
                    'eps': self._parse_value(quarter.get('dilutedEps', 0))
                }
                quarterly_data.append(q_data)

            # Calculate YoY growth
            yoy_growth = {}
            if len(quarterly_data) >= 5:
                latest = quarterly_data[0]
                year_ago = quarterly_data[4]

                if latest['revenue'] and year_ago['revenue']:
                    yoy_growth['revenue_yoy'] = ((latest['revenue'] - year_ago['revenue']) /
                                                 abs(year_ago['revenue'])) * 100

                if latest['net_profit'] and year_ago['net_profit']:
                    yoy_growth['profit_yoy'] = ((latest['net_profit'] - year_ago['net_profit']) /
                                                abs(year_ago['net_profit'])) * 100

                if latest['eps'] and year_ago['eps']:
                    yoy_growth['eps_yoy'] = ((latest['eps'] - year_ago['eps']) /
                                            abs(year_ago['eps'])) * 100

            # Calculate QoQ growth
            qoq_growth = {}
            if len(quarterly_data) >= 2:
                latest = quarterly_data[0]
                previous = quarterly_data[1]

                if latest['revenue'] and previous['revenue']:
                    qoq_growth['revenue_qoq'] = ((latest['revenue'] - previous['revenue']) /
                                                 abs(previous['revenue'])) * 100

                if latest['net_profit'] and previous['net_profit']:
                    qoq_growth['profit_qoq'] = ((latest['net_profit'] - previous['net_profit']) /
                                                abs(previous['net_profit'])) * 100

            result = {
                'nse_symbol': nse_symbol,
                'fetch_timestamp': timestamp,
                'source': 'NSE_DIRECT',
                'status': 'success',
                'quarterly_results': quarterly_data,
                'yoy_growth': yoy_growth,
                'qoq_growth': qoq_growth
            }

            return result

        except Exception as e:
            return {
                'nse_symbol': nse_symbol,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'NSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }

    def fetch_corporate_announcements(self, nse_symbol: str, days_back: int = 30) -> List[Dict]:
        """
        Fetch corporate announcements from NSE

        Args:
            nse_symbol: NSE symbol
            days_back: Number of days to look back

        Returns:
            List of announcements
        """
        try:
            url = f"{self.base_url}/api/announcements"

            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%m-%Y')
            to_date = datetime.now().strftime('%d-%m-%Y')

            params = {
                'index': 'equities',
                'symbol': nse_symbol.upper(),
                'from_date': from_date,
                'to_date': to_date
            }

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return []

            announcements = []
            data = response.json() if response.text else []

            for item in data:
                ann = {
                    'nse_symbol': nse_symbol,
                    'announcement_date': item.get('date', ''),
                    'subject': item.get('desc', ''),
                    'attachment': item.get('attchmntFile', ''),
                    'fetch_timestamp': DataTimestamp.create_timestamp(),
                    'source': 'NSE_DIRECT'
                }

                # Check if it's an earnings announcement
                subject_lower = ann['subject'].lower()
                if any(keyword in subject_lower for keyword in
                      ['result', 'earning', 'financial', 'quarter', 'audited', 'unaudited']):
                    ann['is_earnings'] = True

                announcements.append(ann)

            return announcements

        except Exception as e:
            return [{
                'nse_symbol': nse_symbol,
                'fetch_timestamp': DataTimestamp.create_timestamp(),
                'source': 'NSE_DIRECT',
                'status': 'error',
                'error': str(e)
            }]

    def _parse_value(self, value) -> Optional[float]:
        """Parse numeric value"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                return float(value.replace(',', ''))
            return None
        except:
            return None


# Test the fetcher
if __name__ == "__main__":
    fetcher = NSEDirectFetcher()

    # Test with TCS
    print("Testing NSE Direct Fetcher with TCS")
    print("-" * 60)

    # Fetch company info
    info = fetcher.fetch_company_info("TCS")
    if info and info.get('status') == 'success':
        print(f"Company: {info.get('company_name')}")
        print(f"Sector: {info.get('sector')}")
        print(f"Current Price: ₹{info.get('current_price')}")
        print(f"Market Cap: ₹{info.get('market_cap')} Cr")
        print(f"52W High/Low: ₹{info.get('52_week_high')} / ₹{info.get('52_week_low')}")
        print(f"Source: {info['source']}")
        print(f"Fetched at: {info['fetch_timestamp']['timestamp']}")

    # Fetch financial results
    print("\nFetching financial results...")
    results = fetcher.fetch_financial_results("TCS")
    if results and results.get('status') == 'success':
        print(f"Quarters available: {len(results.get('quarterly_results', []))}")

        yoy = results.get('yoy_growth', {})
        if yoy:
            print(f"YoY Growth:")
            print(f"  Revenue: {yoy.get('revenue_yoy', 0):.1f}%")
            print(f"  Profit: {yoy.get('profit_yoy', 0):.1f}%")
            print(f"  EPS: {yoy.get('eps_yoy', 0):.1f}%")

        qoq = results.get('qoq_growth', {})
        if qoq:
            print(f"QoQ Growth:")
            print(f"  Revenue: {qoq.get('revenue_qoq', 0):.1f}%")
            print(f"  Profit: {qoq.get('profit_qoq', 0):.1f}%")

    # Fetch announcements
    print("\nFetching corporate announcements...")
    announcements = fetcher.fetch_corporate_announcements("TCS", days_back=30)
    earnings_ann = [a for a in announcements if a.get('is_earnings')]
    print(f"Total announcements: {len(announcements)}")
    print(f"Earnings announcements: {len(earnings_ann)}")
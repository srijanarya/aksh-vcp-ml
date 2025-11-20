"""
Enhanced Screener.in Data Fetcher with Robust Error Handling
Provides reliable financial data extraction with validation and fallback mechanisms
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Any
import time
import re
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.fiscal_year_utils import IndianFiscalYear, DataTimestamp


class ScreenerEnhancedFetcher:
    """
    Enhanced Screener.in fetcher with:
    - Robust error handling
    - Rate limiting
    - Data validation
    - Fallback mechanisms
    - Comprehensive logging
    """

    def __init__(self, rate_limit_seconds: float = 1.0):
        self.base_url = "https://www.screener.in"
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.retry_count = 3
        self.timeout = 15

    def _enforce_rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - time_since_last)
        self.last_request_time = time.time()

    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic and error handling

        Returns:
            Response object or None if all retries fail
        """
        for attempt in range(self.retry_count):
            try:
                self._enforce_rate_limit()

                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 404:
                    print(f"Company not found: {url}")
                    return None
                else:
                    print(f"HTTP {response.status_code} for {url}")

            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt + 1}/{self.retry_count}")
            except requests.exceptions.ConnectionError:
                print(f"Connection error on attempt {attempt + 1}/{self.retry_count}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                print(f"Unexpected error: {e}")

        return None

    def fetch_company_data(self, company_code: str) -> Optional[Dict]:
        """
        Fetch comprehensive company data from Screener.in

        Args:
            company_code: NSE symbol or BSE code

        Returns:
            Dict with company data and confidence scores
        """
        timestamp = DataTimestamp.create_timestamp()

        # Try different URL patterns
        urls_to_try = [
            f"{self.base_url}/company/{company_code}/",
            f"{self.base_url}/company/{company_code.upper()}/",
            f"{self.base_url}/company/{company_code.lower()}/"
        ]

        response = None
        for url in urls_to_try:
            response = self._make_request(url)
            if response:
                break

        if not response:
            return {
                'company_code': company_code,
                'fetch_timestamp': timestamp,
                'source': 'SCREENER_ENHANCED',
                'status': 'error',
                'error': 'Failed to fetch data after retries'
            }

        try:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract company info
            company_data = {
                'company_code': company_code,
                'fetch_timestamp': timestamp,
                'source': 'SCREENER_ENHANCED',
                'status': 'success'
            }

            # Extract company name
            name_elem = soup.find('h1', {'class': 'h2'})
            if name_elem:
                company_data['company_name'] = name_elem.text.strip()

            # Extract key ratios section
            ratios = self._extract_ratios(soup)
            if ratios:
                company_data['ratios'] = ratios

            # Extract quarterly results
            quarterly = self._extract_quarterly_results(soup)
            if quarterly:
                company_data['quarterly_results'] = quarterly

                # Calculate YoY and QoQ
                growth = self._calculate_growth_metrics(quarterly)
                company_data.update(growth)

            # Extract annual results
            annual = self._extract_annual_results(soup)
            if annual:
                company_data['annual_results'] = annual

            # Extract shareholding pattern
            shareholding = self._extract_shareholding(soup)
            if shareholding:
                company_data['shareholding'] = shareholding

            # Data quality assessment
            company_data['data_completeness'] = self._assess_data_completeness(company_data)
            company_data['confidence_score'] = self._calculate_confidence(company_data)

            return company_data

        except Exception as e:
            return {
                'company_code': company_code,
                'fetch_timestamp': timestamp,
                'source': 'SCREENER_ENHANCED',
                'status': 'error',
                'error': f'Parse error: {str(e)}'
            }

    def _extract_ratios(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract key financial ratios"""
        try:
            ratios = {}

            # Find the ratios section
            ratio_items = soup.find_all('li', {'class': 'flex flex-space-between'})

            for item in ratio_items:
                name_elem = item.find('span', {'class': 'name'})
                value_elem = item.find('span', {'class': 'nowrap value'})

                if name_elem and value_elem:
                    name = name_elem.text.strip()
                    value = value_elem.text.strip()

                    # Parse common ratios
                    if 'Market Cap' in name:
                        ratios['market_cap'] = self._parse_indian_number(value)
                    elif 'Current Price' in name:
                        ratios['current_price'] = self._parse_number(value)
                    elif 'P/E' in name and 'PEG' not in name:
                        ratios['pe_ratio'] = self._parse_number(value)
                    elif 'P/B' in name or 'Book Value' in name:
                        ratios['pb_ratio'] = self._parse_number(value)
                    elif 'Dividend Yield' in name:
                        ratios['dividend_yield'] = self._parse_number(value)
                    elif 'ROE' in name or 'ROCE' in name:
                        ratios['roe'] = self._parse_number(value)
                    elif 'EPS' in name:
                        ratios['eps'] = self._parse_number(value)

            return ratios if ratios else None

        except Exception as e:
            print(f"Error extracting ratios: {e}")
            return None

    def _extract_quarterly_results(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract quarterly financial results"""
        try:
            quarterly = []

            # Find quarterly results table
            tables = soup.find_all('table', {'class': 'data-table'})

            for table in tables:
                # Check if it's quarterly table
                headers = table.find_all('th')
                if any('quarter' in h.text.lower() for h in headers):
                    rows = table.find_all('tr')

                    # Extract quarters from header
                    quarters = []
                    for th in headers[1:]:  # Skip first column
                        quarter_text = th.text.strip()
                        if quarter_text and quarter_text != '':
                            quarters.append(quarter_text)

                    # Extract data for each metric
                    metrics = {}
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_all('td')
                        if cells:
                            metric_name = cells[0].text.strip()

                            if 'Sales' in metric_name or 'Revenue' in metric_name:
                                metric_key = 'revenue'
                            elif 'Operating Profit' in metric_name:
                                metric_key = 'operating_profit'
                            elif 'Net Profit' in metric_name:
                                metric_key = 'net_profit'
                            elif 'EPS' in metric_name:
                                metric_key = 'eps'
                            else:
                                continue

                            values = []
                            for cell in cells[1:len(quarters)+1]:
                                value = self._parse_number(cell.text.strip())
                                values.append(value)

                            metrics[metric_key] = values

                    # Structure quarterly data
                    for i, quarter in enumerate(quarters[:5]):  # Last 5 quarters
                        quarter_data = {'quarter': quarter}
                        for metric, values in metrics.items():
                            if i < len(values):
                                quarter_data[metric] = values[i]
                        quarterly.append(quarter_data)

                    break

            return quarterly if quarterly else None

        except Exception as e:
            print(f"Error extracting quarterly results: {e}")
            return None

    def _extract_annual_results(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract annual financial results"""
        try:
            annual = []

            # Find annual results section
            sections = soup.find_all('section', {'id': 'profit-loss'})

            for section in sections:
                table = section.find('table', {'class': 'data-table'})
                if table:
                    headers = table.find_all('th')
                    years = [h.text.strip() for h in headers[1:] if h.text.strip()]

                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if cells and len(cells) > 1:
                            metric_name = cells[0].text.strip()

                            if 'Sales' in metric_name:
                                for i, year in enumerate(years[:3]):  # Last 3 years
                                    if i + 1 < len(cells):
                                        annual.append({
                                            'year': year,
                                            'revenue': self._parse_indian_number(cells[i+1].text)
                                        })

            return annual if annual else None

        except Exception as e:
            print(f"Error extracting annual results: {e}")
            return None

    def _extract_shareholding(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract shareholding pattern"""
        try:
            shareholding = {}

            # Find shareholding section
            sections = soup.find_all('section', {'id': 'shareholding'})

            for section in sections:
                rows = section.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        holder = cells[0].text.strip()
                        percentage = self._parse_number(cells[-1].text.strip())

                        if 'Promoter' in holder:
                            shareholding['promoter'] = percentage
                        elif 'FII' in holder or 'Foreign' in holder:
                            shareholding['fii'] = percentage
                        elif 'DII' in holder or 'Domestic' in holder:
                            shareholding['dii'] = percentage
                        elif 'Public' in holder:
                            shareholding['public'] = percentage

            return shareholding if shareholding else None

        except Exception as e:
            print(f"Error extracting shareholding: {e}")
            return None

    def _calculate_growth_metrics(self, quarterly: List[Dict]) -> Dict:
        """Calculate YoY and QoQ growth metrics"""
        growth = {}

        if not quarterly or len(quarterly) < 2:
            return growth

        try:
            # QoQ Growth (latest vs previous quarter)
            latest = quarterly[0]
            previous = quarterly[1]

            if latest.get('revenue') and previous.get('revenue'):
                growth['revenue_qoq'] = ((latest['revenue'] - previous['revenue']) /
                                         abs(previous['revenue'])) * 100

            if latest.get('net_profit') and previous.get('net_profit'):
                growth['profit_qoq'] = ((latest['net_profit'] - previous['net_profit']) /
                                        abs(previous['net_profit'])) * 100

            # YoY Growth (latest vs year-ago quarter)
            if len(quarterly) >= 5:
                year_ago = quarterly[4]

                if latest.get('revenue') and year_ago.get('revenue'):
                    growth['revenue_yoy'] = ((latest['revenue'] - year_ago['revenue']) /
                                            abs(year_ago['revenue'])) * 100

                if latest.get('net_profit') and year_ago.get('net_profit'):
                    growth['profit_yoy'] = ((latest['net_profit'] - year_ago['net_profit']) /
                                           abs(year_ago['net_profit'])) * 100

                if latest.get('eps') and year_ago.get('eps'):
                    growth['eps_yoy'] = ((latest['eps'] - year_ago['eps']) /
                                        abs(year_ago['eps'])) * 100

        except Exception as e:
            print(f"Error calculating growth metrics: {e}")

        return growth

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse number from text, handling various formats"""
        if not text:
            return None

        try:
            # Remove currency symbols and spaces
            text = text.replace('₹', '').replace(',', '').replace('%', '').strip()

            # Handle negative numbers in parentheses
            if '(' in text and ')' in text:
                text = '-' + text.replace('(', '').replace(')', '')

            # Handle blank or N/A values
            if text in ['-', 'N/A', 'NA', '']:
                return None

            return float(text)

        except:
            return None

    def _parse_indian_number(self, text: str) -> Optional[float]:
        """Parse Indian number format (Cr, Lakh, etc.)"""
        if not text:
            return None

        try:
            text = text.replace('₹', '').replace(',', '').strip()

            multiplier = 1
            if 'Cr' in text or 'Crore' in text:
                multiplier = 10000000  # 1 Crore = 10 Million
                text = re.sub(r'Cr.*', '', text)
            elif 'Lakh' in text or 'Lac' in text or 'Lacs' in text:
                multiplier = 100000  # 1 Lakh = 100,000
                text = re.sub(r'La.*', '', text)
            elif 'K' in text:
                multiplier = 1000
                text = text.replace('K', '')
            elif 'M' in text:
                multiplier = 1000000
                text = text.replace('M', '')
            elif 'B' in text:
                multiplier = 1000000000
                text = text.replace('B', '')

            # Handle parentheses for negative
            if '(' in text and ')' in text:
                text = '-' + text.replace('(', '').replace(')', '')

            return float(text) * multiplier

        except:
            return None

    def _assess_data_completeness(self, data: Dict) -> float:
        """Assess how complete the fetched data is (0-100%)"""
        required_fields = [
            'company_name',
            'ratios',
            'quarterly_results',
            'revenue_yoy',
            'profit_yoy'
        ]

        optional_fields = [
            'annual_results',
            'shareholding',
            'eps_yoy',
            'revenue_qoq',
            'profit_qoq'
        ]

        # Check required fields (70% weight)
        required_present = sum(1 for field in required_fields if data.get(field))
        required_score = (required_present / len(required_fields)) * 70

        # Check optional fields (30% weight)
        optional_present = sum(1 for field in optional_fields if data.get(field))
        optional_score = (optional_present / len(optional_fields)) * 30

        return required_score + optional_score

    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate confidence score for the fetched data"""
        confidence = 0

        # Base confidence if successful fetch
        if data.get('status') == 'success':
            confidence = 40

        # Add points for data completeness
        completeness = data.get('data_completeness', 0)
        confidence += completeness * 0.4  # Max 40 points

        # Add points for having growth metrics
        if data.get('revenue_yoy') is not None:
            confidence += 10
        if data.get('profit_yoy') is not None:
            confidence += 10

        # Sanity checks (reduce confidence for suspicious data)
        if data.get('revenue_yoy'):
            if data['revenue_yoy'] < -90 or data['revenue_yoy'] > 1000:
                confidence -= 20  # Suspicious growth rate

        if data.get('profit_yoy'):
            if abs(data['profit_yoy']) > 2000:
                confidence -= 15  # Extremely high change

        # Cap between 0 and 100
        return max(0, min(100, confidence))

    def fetch_peer_comparison(self, company_code: str, peer_codes: List[str]) -> Dict:
        """
        Fetch data for peer comparison

        Args:
            company_code: Primary company code
            peer_codes: List of peer company codes

        Returns:
            Comparison data with all peers
        """
        comparison = {
            'primary': company_code,
            'fetch_timestamp': DataTimestamp.create_timestamp(),
            'companies': {}
        }

        # Fetch primary company
        primary_data = self.fetch_company_data(company_code)
        if primary_data:
            comparison['companies'][company_code] = primary_data

        # Fetch peer companies
        for peer in peer_codes[:5]:  # Limit to 5 peers
            peer_data = self.fetch_company_data(peer)
            if peer_data:
                comparison['companies'][peer] = peer_data

        # Calculate relative metrics
        if len(comparison['companies']) > 1:
            comparison['relative_metrics'] = self._calculate_relative_metrics(comparison['companies'])

        return comparison

    def _calculate_relative_metrics(self, companies: Dict) -> Dict:
        """Calculate relative performance metrics across peers"""
        metrics = {}

        try:
            # Extract key metrics for comparison
            pe_ratios = []
            revenue_growth = []
            profit_growth = []

            for code, data in companies.items():
                if data.get('ratios', {}).get('pe_ratio'):
                    pe_ratios.append((code, data['ratios']['pe_ratio']))

                if data.get('revenue_yoy'):
                    revenue_growth.append((code, data['revenue_yoy']))

                if data.get('profit_yoy'):
                    profit_growth.append((code, data['profit_yoy']))

            # Rank companies
            if pe_ratios:
                pe_ratios.sort(key=lambda x: x[1])
                metrics['pe_ranking'] = pe_ratios

            if revenue_growth:
                revenue_growth.sort(key=lambda x: x[1], reverse=True)
                metrics['revenue_growth_ranking'] = revenue_growth

            if profit_growth:
                profit_growth.sort(key=lambda x: x[1], reverse=True)
                metrics['profit_growth_ranking'] = profit_growth

        except Exception as e:
            print(f"Error calculating relative metrics: {e}")

        return metrics


# Test the enhanced fetcher
if __name__ == "__main__":
    fetcher = ScreenerEnhancedFetcher()

    print("Testing Enhanced Screener Fetcher")
    print("=" * 60)

    # Test with TCS
    print("\nFetching TCS data...")
    tcs_data = fetcher.fetch_company_data("TCS")

    if tcs_data and tcs_data.get('status') == 'success':
        print(f"Company: {tcs_data.get('company_name')}")
        print(f"Data Completeness: {tcs_data.get('data_completeness', 0):.1f}%")
        print(f"Confidence Score: {tcs_data.get('confidence_score', 0):.1f}%")

        if tcs_data.get('revenue_yoy'):
            print(f"Revenue YoY: {tcs_data['revenue_yoy']:.1f}%")
        if tcs_data.get('profit_yoy'):
            print(f"Profit YoY: {tcs_data['profit_yoy']:.1f}%")

        if tcs_data.get('ratios'):
            print(f"P/E Ratio: {tcs_data['ratios'].get('pe_ratio')}")
            print(f"Market Cap: ₹{tcs_data['ratios'].get('market_cap')} Cr")
    else:
        print(f"Error: {tcs_data.get('error')}")

    # Test peer comparison
    print("\n\nTesting Peer Comparison...")
    print("-" * 60)
    comparison = fetcher.fetch_peer_comparison("TCS", ["INFY", "WIPRO", "HCLTECH"])

    if comparison.get('relative_metrics'):
        print("Revenue Growth Ranking:")
        for company, growth in comparison['relative_metrics'].get('revenue_growth_ranking', []):
            print(f"  {company}: {growth:.1f}%")
import requests
import json
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.bseindia.com/',
    'Origin': 'https://www.bseindia.com'
}

def fetch_forthcoming_results():
    """Fetch forthcoming financial results from BSE"""
    url = "https://api.bseindia.com/BseIndiaAPI/api/Result/w"
    try:
        logger.info(f"Fetching forthcoming results from {url}...")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        # Try to parse JSON, handle malformed responses
        try:
            data = response.json()
        except json.JSONDecodeError as je:
            logger.error(f"Malformed JSON from BSE Results API: {je}")
            logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
            return []

        # The API usually returns a list of objects
        if isinstance(data, list):
            logger.info(f"✅ Received {len(data)} forthcoming result entries")
            return data
        else:
            logger.warning("Unexpected data format for forthcoming results")
            return []
    except requests.Timeout:
        logger.error("BSE Results API timeout - network issue or API down")
        return []
    except requests.RequestException as e:
        logger.error(f"Network error fetching forthcoming results: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching forthcoming results: {e}")
        return []

def fetch_board_meetings():
    """Fetch board meetings from BSE"""
    # Note: The endpoint might need parameters or be different.
    # Common endpoint for board meetings: https://api.bseindia.com/BseIndiaAPI/api/Meeting/w?strCat=-1&strPrevDate=20240101&strScrip=&strSearch=P
    # Let's try the simple one first or reverse engineer if needed.
    # Actually, 'Meeting/w' often takes query params. Let's try without first.
    url = "https://api.bseindia.com/BseIndiaAPI/api/Meeting/w"
    params = {
        "strCat": "-1",
        "strPrevDate": datetime.now().strftime("%Y%m%d"),
        "strScrip": "",
        "strSearch": "P"
    }
    try:
        logger.info(f"Fetching board meetings from {url}...")
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()

        # Try to parse JSON, handle malformed responses
        try:
            data = response.json()
        except json.JSONDecodeError as je:
            logger.error(f"❌ Malformed JSON from BSE Meetings API: {je}")
            logger.debug(f"Response text (first 200 chars): {response.text[:200]}")
            logger.warning("BSE Meetings API is currently returning invalid JSON. This is a known BSE API issue.")
            return []

        if isinstance(data, list):
            logger.info(f"✅ Received {len(data)} board meeting entries")
            return data
        else:
            logger.warning("Unexpected data format for board meetings")
            return []
    except requests.Timeout:
        logger.error("BSE Meetings API timeout - network issue or API down")
        return []
    except requests.RequestException as e:
        logger.error(f"Network error fetching board meetings: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching board meetings: {e}")
        return []

def main():
    results = fetch_forthcoming_results()
    meetings = fetch_board_meetings()
    
    print(f"\n--- Forthcoming Results ({len(results)}) ---")
    if results:
        df_results = pd.DataFrame(results)
        print(df_results.head().to_string())
        print(f"Columns: {df_results.columns.tolist()}")
        
    print(f"\n--- Board Meetings ({len(meetings)}) ---")
    if meetings:
        df_meetings = pd.DataFrame(meetings)
        print(df_meetings.head().to_string())
        print(f"Columns: {df_meetings.columns.tolist()}")

if __name__ == "__main__":
    main()

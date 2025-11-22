import requests
import sqlite3
import logging
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/",
    "Origin": "https://www.bseindia.com"
}

def fetch_period(start_date, end_date, page=1):
    """Fetch announcements for a specific period and page"""
    params = {
        "pageno": page,
        "strCat": "-1", # All categories
        "strPrevDate": start_date.strftime("%Y%m%d"),
        "strScrip": "",
        "strSearch": "P",
        "strToDate": end_date.strftime("%Y%m%d"),
        "strType": "C"
    }
    
    try:
        # logger.info(f"Requesting URL: {BSE_URL} Page {page}")
        response = requests.get(BSE_URL, headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "Table" in data:
                return data["Table"]
            else:
                logger.warning(f"No 'Table' in response for page {page}: {data.keys()}")
        else:
            logger.error(f"Status code: {response.status_code} for page {page}")
        return []
    except Exception as e:
        logger.error(f"Error fetching page {page}: {e}")
        return []

def save_to_db(announcements):
    """Save relevant earnings announcements to DB"""
    if not announcements:
        return 0
        
    conn = sqlite3.connect("data/earnings_calendar.db")
    cursor = conn.cursor()
    
    count = 0
    for item in announcements:
        category = item.get("CATEGORYNAME", "")
        # Debug logging for first few items
        if count < 5:
            logger.info(f"Seen category: {category}")
            
        # Filter for Results
        # Check Category, Title (NEWSSUB), and Description (HEADLINE)
        title = item.get("NEWSSUB", "")
        headline = item.get("HEADLINE", "")
        
        keywords = ["Financial Result", "Quarterly Result", "Unaudited", "Audited", "Results", "Earnings"]
        is_result = False
        
        if "Result" in category or "Financial" in category:
            is_result = True
        else:
            # Check keywords in title/headline
            text_to_search = (title + " " + headline).lower()
            if any(k.lower() in text_to_search for k in keywords):
                is_result = True
                
        if is_result:
            try:
                # Parse date
                news_dt = item.get("NEWS_DT") # 2025-11-21T12:34:56.789
                if news_dt:
                    # Handle milliseconds if present
                    if "." in news_dt:
                        news_dt = news_dt.split(".")[0]
                    dt_obj = datetime.strptime(news_dt, "%Y-%m-%dT%H:%M:%S")
                    date_str = dt_obj.strftime("%Y-%m-%d")
                else:
                    continue
                
                bse_code = item.get("SCRIP_CD")
                company_name = item.get("SLONGNAME")
                pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item['ATTACHMENTNAME']}" if item.get("ATTACHMENTNAME") else None
                
                # Insert into earnings_results
                cursor.execute("""
                    INSERT OR IGNORE INTO earnings_results 
                    (company_name, bse_code, announcement_date, quarter, fiscal_year, pdf_url, data_source, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (company_name, bse_code, date_str, "Q3", "FY26", pdf_url, "BSE Historical"))
                
                if cursor.rowcount > 0:
                    count += 1
            except Exception as e:
                logger.error(f"Error inserting {item.get('SLONGNAME')}: {e}")
                
    conn.commit()
    conn.close()
    return count

def main():
    # Backfill from Oct 1, 2025 to Today
    start_date = datetime(2025, 10, 1)
    end_date = datetime.now()
    
    current_start = start_date
    total_synced = 0
    
    logger.info(f"Starting backfill from {start_date.date()} to {end_date.date()}")
    
    while current_start < end_date:
        day_synced = 0
        page = 1
        max_pages = 20 # Safety limit
        
        while page <= max_pages:
            announcements = fetch_period(current_start, current_start, page)
            if not announcements:
                break
                
            synced = save_to_db(announcements)
            day_synced += synced
            
            # If we got less than 50 items, it's the last page
            if len(announcements) < 50:
                break
                
            page += 1
            time.sleep(0.2) # Slight delay between pages
            
        total_synced += day_synced
        logger.info(f"Synced {day_synced} earnings records for {current_start.date()} (Pages: {page})")
        
        current_start += timedelta(days=1)
        
    logger.info(f"Total earnings synced: {total_synced}")

if __name__ == "__main__":
    main()

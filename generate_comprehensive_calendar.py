import requests
import pandas as pd
import sqlite3
import logging
import os
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.bseindia.com/',
    'Origin': 'https://www.bseindia.com'
}

def fetch_bse_forthcoming():
    """Fetch forthcoming results from BSE"""
    url = "https://api.bseindia.com/BseIndiaAPI/api/Result/w"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            df = pd.DataFrame(data)
            # Rename columns to standard format
            df = df.rename(columns={
                'Code': 'bse_code',
                'Security': 'company_name',
                'Date': 'result_date'
            })
            df['source'] = 'BSE Live'
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error fetching BSE data: {e}")
        return pd.DataFrame()

def fetch_local_calendar():
    """Fetch from local earnings_calendar.db"""
    db_path = "data/earnings_calendar.db"
    if not os.path.exists(db_path):
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db_path)
        # Fetch all earnings from Oct 1, 2025 (Start of Q3 FY26)
        query = """
            SELECT bse_code, company_name, announcement_date as result_date
            FROM earnings_results
            WHERE announcement_date >= '2025-10-01'
            ORDER BY announcement_date DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        df['source'] = 'Historical DB'
        return df
    except Exception as e:
        logger.error(f"Error fetching local DB: {e}")
        return pd.DataFrame()

def generate_html(df):
    """Generate beautiful HTML calendar with Tabs and DataTables"""
    
    # Convert date
    df['dt'] = pd.to_datetime(df['result_date'], errors='coerce')
    today = pd.Timestamp.now().normalize()
    
    # Split into Upcoming and Reported
    upcoming_df = df[df['dt'] >= today].sort_values('dt', ascending=True)
    reported_df = df[df['dt'] < today].sort_values('dt', ascending=False)
    
    def generate_table_rows(dataframe):
        rows = ""
        for _, row in dataframe.iterrows():
            date_str = row['result_date']
            source_class = "bg-green-900 text-green-200" if "BSE" in row['source'] else "bg-gray-700 text-gray-300"
            
            rows += f"""
            <tr class="hover:bg-gray-800 transition-colors border-b border-gray-800">
                <td class="p-3 font-medium text-white">{row['company_name']}</td>
                <td class="p-3 text-gray-400 font-mono">{row['bse_code']}</td>
                <td class="p-3 text-blue-400 font-bold">{date_str}</td>
                <td class="p-3"><span class="px-2 py-1 rounded text-xs font-bold {source_class}">{row['source']}</span></td>
                <td class="p-3">
                    <a href="https://www.bseindia.com/stock-share-price/x/y/{row['bse_code']}/" target="_blank" class="text-indigo-400 hover:text-indigo-300 text-sm">View</a>
                </td>
            </tr>
            """
        return rows

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Earnings Calendar</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <style>
        body {{ background-color: #0f172a; color: #e2e8f0; }}
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter, .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_processing, .dataTables_wrapper .dataTables_paginate {{
            color: #94a3b8 !important;
            margin-bottom: 1rem;
        }}
        .dataTables_wrapper .dataTables_paginate .paginate_button {{ color: #94a3b8 !important; }}
        .dataTables_wrapper .dataTables_paginate .paginate_button.current {{ background: #3b82f6 !important; color: white !important; border: none; }}
        table.dataTable tbody tr {{ background-color: transparent !important; }}
        table.dataTable {{ border-bottom: 1px solid #374151 !important; }}
        
        /* Tab Styles */
        .tab-btn {{ cursor: pointer; padding: 10px 20px; border-bottom: 2px solid transparent; color: #94a3b8; }}
        .tab-btn.active {{ border-bottom: 2px solid #3b82f6; color: #3b82f6; font-weight: bold; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    Earnings Calendar
                </h1>
                <p class="text-gray-400 mt-1">Q3 FY26 (Oct-Dec 2025) & Upcoming</p>
            </div>
            <div class="text-right">
                <div class="text-sm text-gray-500">Last Updated</div>
                <div class="text-xl font-mono">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
            </div>
        </div>

        <!-- Tabs -->
        <div class="flex border-b border-gray-800 mb-6">
            <div class="tab-btn active" onclick="switchTab('upcoming')">Upcoming ({len(upcoming_df)})</div>
            <div class="tab-btn" onclick="switchTab('reported')">Reported Results ({len(reported_df)})</div>
        </div>

        <!-- Upcoming Tab -->
        <div id="upcoming" class="tab-content active">
            <div class="bg-gray-900 rounded-xl border border-gray-800 p-4 shadow-2xl">
                <table id="table-upcoming" class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-gray-400 text-sm uppercase tracking-wider border-b border-gray-700">
                            <th class="p-3">Company</th>
                            <th class="p-3">BSE Code</th>
                            <th class="p-3">Date</th>
                            <th class="p-3">Source</th>
                            <th class="p-3">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_table_rows(upcoming_df)}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Reported Tab -->
        <div id="reported" class="tab-content">
            <div class="bg-gray-900 rounded-xl border border-gray-800 p-4 shadow-2xl">
                <table id="table-reported" class="w-full text-left border-collapse">
                    <thead>
                        <tr class="text-gray-400 text-sm uppercase tracking-wider border-b border-gray-700">
                            <th class="p-3">Company</th>
                            <th class="p-3">BSE Code</th>
                            <th class="p-3">Date</th>
                            <th class="p-3">Source</th>
                            <th class="p-3">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_table_rows(reported_df)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="mt-8 text-center text-gray-500 text-sm">
            <p>Data sourced from BSE India Real-time API & Internal Intelligence Database</p>
        </div>
    </div>

    <script>
        $(document).ready(function() {{
            $('#table-upcoming').DataTable({{
                "pageLength": 25,
                "order": [[ 2, "asc" ]], // Sort by Date ascending
                "language": {{ "search": "", "searchPlaceholder": "Search upcoming..." }}
            }});
            
            $('#table-reported').DataTable({{
                "pageLength": 25,
                "order": [[ 2, "desc" ]], // Sort by Date descending
                "language": {{ "search": "", "searchPlaceholder": "Search reported..." }}
            }});
        }});

        function switchTab(tabId) {{
            $('.tab-content').removeClass('active');
            $('#' + tabId).addClass('active');
            $('.tab-btn').removeClass('active');
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""
    
    with open("comprehensive_earnings_calendar.html", "w") as f:
        f.write(html_content)
    logger.info(f"Generated HTML: {len(upcoming_df)} upcoming, {len(reported_df)} reported")

def sync_to_db(df):
    """Sync fetched data to earnings_calendar.db"""
    if df.empty:
        return
        
    db_path = "data/earnings_calendar.db"
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists (just in case)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                bse_code TEXT,
                announcement_date TEXT NOT NULL,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        count = 0
        for _, row in df.iterrows():
            # Check if exists
            cursor.execute("""
                SELECT id FROM earnings 
                WHERE bse_code = ? AND announcement_date = ?
            """, (row['bse_code'], row['result_date']))
            
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO earnings (company_name, bse_code, announcement_date, source, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (row['company_name'], row['bse_code'], row['result_date'], 'BSE Live'))
                count += 1
        
        conn.commit()
        conn.close()
        logger.info(f"Synced {count} new entries to earnings_calendar.db")
    except Exception as e:
        logger.error(f"Error syncing to DB: {e}")

def main():
    logger.info("Fetching BSE data...")
    df_bse = fetch_bse_forthcoming()
    
    # Sync to DB
    sync_to_db(df_bse)
    
    logger.info("Fetching local DB data...")
    df_local = fetch_local_calendar()
    
    # Combine
    dfs = []
    if not df_bse.empty: dfs.append(df_bse)
    if not df_local.empty: dfs.append(df_local)
    
    if dfs:
        final_df = pd.concat(dfs, ignore_index=True)
        # Deduplicate based on code and date
        final_df = final_df.drop_duplicates(subset=['bse_code', 'result_date'])
        generate_html(final_df)
    else:
        logger.warning("No data found from any source")
        # Generate empty but valid HTML
        generate_html(pd.DataFrame(columns=['company_name', 'bse_code', 'result_date', 'source']))

if __name__ == "__main__":
    main()

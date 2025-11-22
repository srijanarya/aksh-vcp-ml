#!/usr/bin/env python3
"""
Generate HTML Dashboard for Announcement Intelligence
"""

import sqlite3
import json
from datetime import datetime

def generate_dashboard():
    # Connect to database
    conn = sqlite3.connect('data/announcement_intelligence.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) as total FROM announcements")
    total_announcements = cursor.fetchone()['total']
    
    cursor.execute("SELECT category, COUNT(*) as count FROM announcements GROUP BY category ORDER BY count DESC")
    category_stats = cursor.fetchall()
    
    cursor.execute("""
        SELECT COUNT(*) as successful 
        FROM extracted_intelligence 
        WHERE status = 'success'
    """)
    successful_extractions = cursor.fetchone()['successful']
    
    # Get recent announcements
    cursor.execute("""
        SELECT a.*, e.intelligence_data, e.status as extraction_status
        FROM announcements a
        LEFT JOIN extracted_intelligence e ON a.id = e.announcement_id
        ORDER BY a.timestamp DESC
        LIMIT 20
    """)
    recent = cursor.fetchall()
    
    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Announcement Intelligence Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .stat-card h3 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: bold;
        }}
        .stat-card p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f8f9ff;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .badge-earnings {{ background: #10b981; color: white; }}
        .badge-order {{ background: #f59e0b; color: white; }}
        .badge-capex {{ background: #3b82f6; color: white; }}
        .badge-promoter {{ background: #8b5cf6; color: white; }}
        .badge-general {{ background: #6b7280; color: white; }}
        .status-success {{ color: #10b981; font-weight: bold; }}
        .status-failed {{ color: #ef4444; }}
        .timestamp {{
            color: #6b7280;
            font-size: 0.9em;
        }}
        .intelligence-data {{
            font-family: 'Courier New', monospace;
            background: #f3f4f6;
            padding: 8px;
            border-radius: 5px;
            font-size: 0.85em;
            max-width: 400px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 Announcement Intelligence Dashboard</h1>
        <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{total_announcements}</h3>
                <p>Total Announcements</p>
            </div>
            <div class="stat-card">
                <h3>{successful_extractions}</h3>
                <p>Successful Extractions</p>
            </div>
            <div class="stat-card">
                <h3>{len(category_stats)}</h3>
                <p>Categories</p>
            </div>
        </div>
        
        <h2>📊 Category Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for cat in category_stats:
        pct = (cat['count'] / total_announcements * 100) if total_announcements > 0 else 0
        badge_class = f"badge-{cat['category'].lower().replace('_', '-')}"
        html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{cat['category']}</span></td>
                    <td>{cat['count']}</td>
                    <td>{pct:.1f}%</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <h2>📰 Recent Announcements</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Company</th>
                    <th>Category</th>
                    <th>Title</th>
                    <th>Extraction</th>
                    <th>Intelligence</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for ann in recent:
        badge_class = f"badge-{ann['category'].lower().replace('_', '-')}"
        status = ann['extraction_status'] or 'pending'
        status_class = 'status-success' if status == 'success' else 'status-failed'
        
        intelligence = ''
        if ann['intelligence_data']:
            try:
                data = json.loads(ann['intelligence_data'])
                if 'value_cr' in data:
                    intelligence = f"₹{data['value_cr']:.2f} Cr"
                    if 'client' in data:
                        intelligence += f" | {data['client'][:30]}..."
                elif 'revenue' in data or 'profit' in data:
                    intelligence = "Financial data extracted"
            except:
                intelligence = "Data available"
        
        html += f"""
                <tr>
                    <td class="timestamp">{ann['timestamp'][:16] if ann['timestamp'] else 'N/A'}</td>
                    <td>{ann['company_name'][:30]}...</td>
                    <td><span class="badge {badge_class}">{ann['category']}</span></td>
                    <td>{ann['title'][:50] if ann['title'] else 'N/A'}...</td>
                    <td class="{status_class}">{status}</td>
                    <td class="intelligence-data">{intelligence}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
    """
    
    conn.close()
    
    # Write to file
    with open('intelligence_dashboard.html', 'w') as f:
        f.write(html)
    
    print("✅ Dashboard generated: intelligence_dashboard.html")
    print("   Open in browser: file:///Users/srijan/Desktop/aksh/intelligence_dashboard.html")

if __name__ == "__main__":
    generate_dashboard()

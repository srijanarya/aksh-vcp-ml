#!/usr/bin/env python3
"""
Dashboard Server for Announcement Intelligence
Serves the dashboard HTML and provides real-time API endpoints
"""

import sqlite3
import json
from datetime import datetime
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

DB_PATH = Path(__file__).parent / 'data' / 'announcement_intelligence.db'
DASHBOARD_PATH = Path(__file__).parent / 'intelligence_dashboard.html'

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def serve_dashboard():
    """Serve the main dashboard HTML"""
    return send_file(DASHBOARD_PATH)

@app.route('/api/announcements')
def get_announcements_api():
    """Get latest announcements data as JSON"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute("SELECT COUNT(*) as total FROM announcements")
        total_announcements = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM announcements 
            GROUP BY category 
            ORDER BY count DESC
        """)
        category_stats = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT COUNT(*) as successful 
            FROM extracted_intelligence 
            WHERE status = 'success'
        """)
        successful_extractions = cursor.fetchone()['successful']
        
        # Get recent announcements
        cursor.execute("""
            SELECT 
                a.id,
                a.timestamp,
                a.company_name,
                a.category,
                a.title,
                e.intelligence_data,
                e.status as extraction_status
            FROM announcements a
            LEFT JOIN extracted_intelligence e ON a.id = e.announcement_id
            ORDER BY a.timestamp DESC
            LIMIT 20
        """)
        recent = []
        for row in cursor.fetchall():
            ann = dict(row)
            # Parse intelligence data
            if ann['intelligence_data']:
                try:
                    ann['intelligence_data'] = json.loads(ann['intelligence_data'])
                except:
                    ann['intelligence_data'] = None
            recent.append(ann)
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_announcements': total_announcements,
                'successful_extractions': successful_extractions,
                'categories': len(category_stats)
            },
            'category_breakdown': category_stats,
            'recent_announcements': recent
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM announcements")
        count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'announcement_count': count,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Announcement Intelligence Dashboard Server")
    print(f"📊 Dashboard: http://localhost:5001")
    print(f"🔌 API: http://localhost:5001/api/announcements")
    print(f"💚 Health: http://localhost:5001/api/health")
    app.run(host='0.0.0.0', port=5001, debug=True)

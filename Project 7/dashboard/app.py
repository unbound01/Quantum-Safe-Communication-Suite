from flask import Flask, render_template, jsonify
import os
import sqlite3
import requests
import json
import time
from datetime import datetime

app = Flask(__name__)

# Configuration from environment variables
DASHBOARD_REFRESH = int(os.environ.get('DASHBOARD_REFRESH', 5))
SIGNER_URL = f"http://signer:{os.environ.get('SIGNER_PORT', 5000)}"
RECEIPTS_URL = f"http://receipts:{os.environ.get('RECEIPTS_PORT', 6000)}"
GATEWAY_URL = f"http://pqc-gateway:{os.environ.get('GATEWAY_PORT', 2525)}"

# Database path
DB_PATH = '/app/dashboard.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emails_sent INTEGER DEFAULT 0,
        pdfs_signed INTEGER DEFAULT 0,
        receipts_generated INTEGER DEFAULT 0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Initialize with default values if empty
    cursor.execute('SELECT COUNT(*) FROM stats')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO stats (emails_sent, pdfs_signed, receipts_generated) VALUES (0, 0, 0)')
    
    conn.commit()
    conn.close()

# Update stats by checking services
def update_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute('SELECT emails_sent, pdfs_signed, receipts_generated FROM stats ORDER BY id DESC LIMIT 1')
        current_stats = cursor.fetchone()
        
        # Try to get receipt count from receipts service
        receipts_count = current_stats[2]  # Default to current value
        try:
            response = requests.get(f"{RECEIPTS_URL}/receipts?limit=1000", timeout=2)
            if response.status_code == 200:
                receipts_data = response.json()
                receipts_count = len(receipts_data)
        except Exception as e:
            print(f"Error fetching receipts: {e}")
        
        # Count PDFs signed (based on receipts with type 'pdf')
        pdfs_signed = current_stats[1]  # Default to current value
        try:
            response = requests.get(f"{RECEIPTS_URL}/receipts?limit=1000", timeout=2)
            if response.status_code == 200:
                receipts_data = response.json()
                pdfs_signed = sum(1 for receipt in receipts_data if receipt.get('type') == 'pdf')
        except Exception as e:
            print(f"Error counting signed PDFs: {e}")
        
        # Count emails sent (based on receipts with type 'email')
        emails_sent = current_stats[0]  # Default to current value
        try:
            response = requests.get(f"{RECEIPTS_URL}/receipts?limit=1000", timeout=2)
            if response.status_code == 200:
                receipts_data = response.json()
                emails_sent = sum(1 for receipt in receipts_data if receipt.get('type') == 'email')
        except Exception as e:
            print(f"Error counting sent emails: {e}")
        
        # Insert new stats record
        cursor.execute(
            'INSERT INTO stats (emails_sent, pdfs_signed, receipts_generated) VALUES (?, ?, ?)',
            (emails_sent, pdfs_signed, receipts_count)
        )
        
        conn.commit()
        conn.close()
        return emails_sent, pdfs_signed, receipts_count
    except Exception as e:
        print(f"Error updating stats: {e}")
        return 0, 0, 0

# Check if services are running
def check_services():
    services = {
        'gateway': {'url': f"{GATEWAY_URL}/health", 'status': 'down'},
        'signer': {'url': f"{SIGNER_URL}/health", 'status': 'down'},
        'receipts': {'url': f"{RECEIPTS_URL}/health", 'status': 'down'}
    }
    
    for service_name, service_info in services.items():
        try:
            response = requests.get(service_info['url'], timeout=2)
            if response.status_code == 200:
                services[service_name]['status'] = 'up'
        except Exception:
            pass
    
    return services

# Routes
@app.route('/')
def index():
    return render_template('index.html', refresh_interval=DASHBOARD_REFRESH)

@app.route('/api/stats')
def get_stats():
    emails_sent, pdfs_signed, receipts_generated = update_stats()
    services = check_services()
    
    return jsonify({
        'emails_sent': emails_sent,
        'pdfs_signed': pdfs_signed,
        'receipts_generated': receipts_generated,
        'services': services,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=int(os.environ.get('DASHBOARD_PORT', 8080)))
from flask import Flask, render_template, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = os.path.expanduser("~/.sunsum/sunsum_core.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transitions')
def get_transitions():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get the last 100 transitions
    cursor.execute('''
        SELECT id, timestamp, event_type, detail, ontology_tag 
        FROM kyinna_events 
        ORDER BY timestamp DESC LIMIT 100
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    transitions = []
    for row in rows:
        transitions.append({
            "id": row['id'],
            "timestamp": row['timestamp'],
            "event_type": row['event_type'],
            "detail": row['detail'],
            "ontology_tag": row['ontology_tag']
        })
    return jsonify(transitions)

@app.route('/api/metrics')
def get_metrics():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Count planned vs unstructured for today
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN detail LIKE '[PLANNED]%' THEN 1 ELSE 0 END) as planned_count,
            SUM(CASE WHEN detail LIKE '[UNSTRUCTURED]%' THEN 1 ELSE 0 END) as unstructured_count,
            COUNT(*) as total_count
        FROM kyinna_events 
        WHERE date(timestamp) = date('now', 'localtime')
    ''')
    row = cursor.fetchone()
    conn.close()
    
    return jsonify({
        "planned": row['planned_count'] or 0,
        "unstructured": row['unstructured_count'] or 0,
        "total": row['total_count'] or 0
    })

def run_dashboard():
    # Run silently on port 5000
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_dashboard()

from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

def get_latest():
    try:
        conn = sqlite3.connect('climate_data.db')
        c = conn.cursor()
        c.execute("""SELECT * FROM readings 
                     ORDER BY timestamp DESC LIMIT 1""")
        row = c.fetchone()
        conn.close()
        return {
            'timestamp': row[0],
            'temperature': round(row[1], 1),
            'humidity': round(row[2], 1)
        } if row else None
    except Exception as e:
        print(f"Error getting latest reading: {e}")
        return None

def get_history(hours=24):
    try:
        conn = sqlite3.connect('climate_data.db')
        c = conn.cursor()
        
        # First get the maximum timestamp
        c.execute("SELECT MAX(timestamp) FROM readings")
        max_timestamp = c.fetchone()[0]
        
        if max_timestamp:
            # Calculate the start time based on the requested hours
            latest_time = datetime.strptime(max_timestamp, '%Y-%m-%d %H:%M:%S')
            start_time = latest_time - timedelta(hours=hours)
            
            # Get data only between start_time and latest_time
            c.execute("""
                SELECT * FROM readings 
                WHERE datetime(timestamp) > datetime(?) 
                AND datetime(timestamp) <= datetime(?)
                ORDER BY timestamp ASC
            """, (start_time.strftime('%Y-%m-%d %H:%M:%S'), 
                 latest_time.strftime('%Y-%m-%d %H:%M:%S')))
            
            rows = c.fetchall()
            conn.close()
            return [{
                'timestamp': r[0],
                'temperature': r[1],
                'humidity': r[2]
            } for r in rows]
        else:
            conn.close()
            return []
            
    except Exception as e:
        print(f"Error getting history: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current')
def current():
    return jsonify(get_latest())

@app.route('/api/history/<int:hours>')
def history(hours):
    return jsonify(get_history(hours))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

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
        
        # Get current time rounded to the minute
        now = datetime.now().replace(second=0, microsecond=0)
        start_time = (now - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:00')
        
        c.execute("""SELECT * FROM readings 
                     WHERE timestamp >= ? 
                     ORDER BY timestamp ASC""", 
                    (start_time,))
        rows = c.fetchall()
        conn.close()
        return [{'timestamp': r[0], 
                 'temperature': r[1], 
                 'humidity': r[2]} for r in rows]
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

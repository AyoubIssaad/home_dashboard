from flask import Flask, render_template, Response, jsonify
import Adafruit_DHT
import json
import time
import sqlite3
from datetime import datetime, timedelta
import threading
import queue

app = Flask(__name__)

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
INTERVAL = 120  # 2 minutes in seconds

# Queue for passing data between background thread and web server
data_queue = queue.Queue()
latest_reading = {'temperature': 'No data', 'humidity': 'No data', 'timestamp': None}

def init_db():
    conn = sqlite3.connect('climate_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (timestamp TEXT, temperature REAL, humidity REAL)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp 
                 ON readings(timestamp)''')
    conn.commit()
    conn.close()

def store_reading(temperature, humidity):
    try:
        conn = sqlite3.connect('climate_data.db')
        c = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:00')  # Round to minute
        
        # Clean old data before inserting new
        c.execute("DELETE FROM readings WHERE timestamp < datetime('now', '-1 day')")
        
        # Insert new reading
        c.execute("INSERT INTO readings VALUES (?, ?, ?)",
                  (timestamp, temperature, humidity))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error storing reading: {e}")

def background_sensor_reading():
    """Background thread function to continuously read sensor data"""
    print("Starting background sensor reading...")
    while True:
        try:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            
            if humidity is not None and temperature is not None:
                data = {
                    'temperature': f'{temperature:.1f}',
                    'humidity': f'{humidity:.1f}',
                    'timestamp': datetime.now().isoformat()
                }
                # Store in database
                store_reading(temperature, humidity)
                
                # Update latest reading
                global latest_reading
                latest_reading = data
                
                # Put in queue for any active web clients
                try:
                    # Put data in queue without blocking
                    data_queue.put_nowait(data)
                except queue.Full:
                    # If queue is full, remove old items
                    try:
                        data_queue.get_nowait()
                    except queue.Empty:
                        pass
                    data_queue.put(data)
            else:
                print("Failed to get sensor reading")
            
            # Wait for next interval
            time.sleep(INTERVAL)
            
        except Exception as e:
            print(f"Error in background reading: {e}")
            time.sleep(INTERVAL)

def get_historical_data():
    try:
        conn = sqlite3.connect('climate_data.db')
        c = conn.cursor()
        c.execute("""SELECT timestamp, temperature, humidity 
                     FROM readings 
                     WHERE timestamp > datetime('now', '-1 day')
                     ORDER BY timestamp ASC""")
        rows = c.fetchall()
        conn.close()
        
        return [{'timestamp': row[0], 
                 'temperature': str(row[1]), 
                 'humidity': str(row[2])} for row in rows]
    except Exception as e:
        print(f"Error getting historical data: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/historical-data')
def historical_data():
    data = get_historical_data()
    return jsonify(data)

def generate_sensor_data():
    """Generator function for SSE"""
    while True:
        try:
            # Get data from queue
            data = data_queue.get(timeout=INTERVAL)
            yield f"data: {json.dumps(data)}\n\n"
        except queue.Empty:
            # If no new data, send latest reading
            yield f"data: {json.dumps(latest_reading)}\n\n"

@app.route('/sensor-stream')
def sensor_stream():
    return Response(generate_sensor_data(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start background thread for sensor reading
    sensor_thread = threading.Thread(target=background_sensor_reading, daemon=True)
    sensor_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

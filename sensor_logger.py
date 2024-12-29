import Adafruit_DHT
import sqlite3
import time
from datetime import datetime

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
INTERVAL = 120  # 2 minutes

def init_db():
    conn = sqlite3.connect('climate_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS readings
                 (timestamp TEXT, temperature REAL, humidity REAL)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_timestamp 
                 ON readings(timestamp)''')
    conn.commit()
    conn.close()

def clean_old_data():
    """Remove data older than 7 days"""
    try:
        conn = sqlite3.connect('climate_data.db')
        c = conn.cursor()
        c.execute("DELETE FROM readings WHERE timestamp < datetime('now', '-7 days')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error cleaning old data: {e}")

def log_reading():
    while True:
        try:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            if humidity is not None and temperature is not None:
                conn = sqlite3.connect('climate_data.db')
                c = conn.cursor()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:00')
                c.execute("INSERT INTO readings VALUES (?, ?, ?)",
                          (timestamp, round(temperature,1), round(humidity,1)))
                conn.commit()
                conn.close()
                print(f"Logged: Temp={temperature:.1f}°C, Humidity={humidity:.1f}%")
                
                # Clean old data once per day (when minutes and hours are 0)
                if datetime.now().hour == 0 and datetime.now().minute == 0:
                    clean_old_data()
            else:
                print("Failed to get sensor reading")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(INTERVAL)

if __name__ == '__main__':
    print("Starting climate monitor logger...")
    init_db()
    log_reading()

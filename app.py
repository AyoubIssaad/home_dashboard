from flask import Flask, render_template, Response
import Adafruit_DHT
import json
import time

app = Flask(__name__)

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4

@app.route('/')
def index():
    return render_template('index.html')

def generate_sensor_data():
    while True:
        try:
            humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
            
            if humidity is not None and temperature is not None:
                data = {
                    'temperature': f'{temperature:.1f}',
                    'humidity': f'{humidity:.1f}'
                }
            else:
                data = {
                    'temperature': 'Error',
                    'humidity': 'Error'
                }
            
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)
            
        except Exception:
            time.sleep(2)  # Wait before retrying

@app.route('/sensor-stream')
def sensor_stream():
    return Response(generate_sensor_data(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

from flask import Flask, render_template
from flask_mqtt import Mqtt

app = Flask(__name__)
app.config['MQTT_BROKER_URL'] = 'broker.hivemq.com'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False

mqtt = Mqtt(app)

@app.route('/')
def index():
    return render_template('index.html')

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('sensor/data')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
    print(data)

if __name__ == '__main__':
    app.run(debug=True)

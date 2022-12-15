import paho.mqtt.client as mqtt
import datetime as dt
import json
from os.path import basename
from testresults import display_results
from testcredentials import DEVICE_ID, DEVICE_PASSWORD

MQTT_HOST_ADDRESS = "192.168.1.114"
MQTT_QoS = 0

NUM_TEST_PACKETS_TO_SEND = 50000

DUMMY_READING = {
    "device_id": DEVICE_ID,
    "password": DEVICE_PASSWORD,
    "time_stamp": "1/17/21 1:12:00+0000",
    "record_version": "1",
    "temperature": "70",
    "humidity": "40"
}


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        return
    print(f"Failed to connect to MQTT broker - result code: {rc}")
    raise RuntimeError


client = mqtt.Client(client_id="STRESS TEST (╯°□°)╯︵┻━┻")
client.on_connect = on_connect

client.connect(MQTT_HOST_ADDRESS, 1883, 60)

start_time = dt.datetime.now()

for packet_count in range(NUM_TEST_PACKETS_TO_SEND):
    new_reading = DUMMY_READING.copy()
    new_reading["time_stamp"] = dt.datetime.now(tz=dt.timezone.utc).strftime("%m/%d/%y %H:%M:%S%z")
    client.publish(f"""{new_reading["device_id"]}/readings""", payload=json.dumps(new_reading), qos=MQTT_QoS)
    client.loop()
    print(f"Sent packet # {packet_count}", end="\r")

finish_time = dt.datetime.now()
client.disconnect()

display_results(start_time, finish_time, NUM_TEST_PACKETS_TO_SEND, basename(__file__))

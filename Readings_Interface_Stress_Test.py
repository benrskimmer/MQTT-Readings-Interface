import paho.mqtt.client as mqtt
import time
import datetime as dt
import json

MQTT_HOST_ADDRESS = "192.168.1.114"
MQTT_QoS = 0

MAX_TEST_PACKETS = 1000
PACKETS_PER_SECOND = 1000 # don't be silly and set this to 0 or you'll get a devide by zero error, dummy...

DUMMY_READING = {"device_id": "00259CACAEBF", "password": "ID26876jX3RWiTBK ", "time_stamp": "1/17/21 1:12:00+0500", "record_version": "1", "temperature": "70", "humidity": "40"}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	pass
	# print("Connected to MQTT broker with result code "+str(rc))

client = mqtt.Client(client_id="STRESS TEST (╯°□°)╯︵┻━┻")
client.on_connect = on_connect

client.connect(MQTT_HOST_ADDRESS, 1883, 60)

packet_count = 0
start_time = dt.datetime.now()

while True:
	new_reading = DUMMY_READING.copy()
	new_reading["time_stamp"] = dt.datetime.now(tz=dt.timezone.utc).strftime("%m/%d/%y %H:%M:%S%z")
	client.publish(new_reading["device_id"]+"/readings", payload=json.dumps(new_reading), qos=MQTT_QoS)
	client.loop()
	# time.sleep(1/PACKETS_PER_SECOND)
	packet_count += 1
	print(f"Sent packet # {packet_count}", end="\r")
	if packet_count >= MAX_TEST_PACKETS:
		break

finish_time = dt.datetime.now()
time_taken = finish_time - start_time
print(f"Total packets sent: {MAX_TEST_PACKETS}")
print(f"Total time taken is {time_taken.total_seconds()} seconds")
print(f"Average packet rate: {MAX_TEST_PACKETS/time_taken.total_seconds()} packets/second")
print(f"Average time per packet: {time_taken.total_seconds()/MAX_TEST_PACKETS} seconds")
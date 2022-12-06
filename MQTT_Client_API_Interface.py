import paho.mqtt.client as mqtt
import requests
import json
from bs4 import BeautifulSoup
import time
import datetime as dt
import pytz

MQTT_HOST_ADDRESS = "192.168.1.114"
DEVICE_API_HOST_ADDRESS = "iot.benrawstron.org"
DEVICE_API_HOST_TIMEOUT_S = 1
MQTT_QoS = 2
VERBOSE = True

LOG_TZ = pytz.timezone("US/Eastern")
REQUEST_RESPONSE_OK	= 200

# The max number of reading's we'll queue before dropping old readings
READING_QUEUE_SIZE_MAX = 1000
reading_queue = []

class Log:
	def __str__(self):
		return "Logging class used to standardize/organize log output"
	def _log(self, type_string, string):
		print(dt.datetime.now(tz=LOG_TZ).strftime("%m/%d/%y %H:%M:%S %Z"), type_string, string)
	def info(self, string):
		self._log("-- Info:", string)
	def warning(self, string):
		self._log("-- Warning:", string)
	def error(self, string):
		self._log("-- Error:", string)
log = Log()
		
def queue_reading(reading):
	if len(reading_queue) >= READING_QUEUE_SIZE_MAX:
		reading_queue.pop(0)
	reading_queue.append(reading)
	log.warning(str(len(reading_queue)) + " queued reading(s)")

def notify_device():
	pass

def post_reading_to_device_API(reading):
	return requests.post("https://"+DEVICE_API_HOST_ADDRESS+"/device/readings", json=reading, timeout=DEVICE_API_HOST_TIMEOUT_S)

def forwarded_reading_accepted(response):
	if response.status_code == REQUEST_RESPONSE_OK:
		return True
	log.warning("BE API rejected reading with status code: " + str(response.status_code))
	# soup = BeautifulSoup(response.content, 'html.parser')
	# print("BE API response:", soup.prettify().strip())
	return False

def forward_reading(reading):
	try:
		response = post_reading_to_device_API(reading)
	except requests.exceptions.RequestException as error:
		queue_reading(reading)
		log.error("Failed to connect to BE API! - Reason: " + str(error))
	else:
		if not forwarded_reading_accepted(response):
			notify_device()
			return
		if VERBOSE:
			if "device_id" in reading.keys():
				log.info("Forwarded reading from device: " + reading["device_id"])
			else:
				log.info("Forwarded reading")

def check_and_forward_queued_readings():
	while reading_queue:
		try:
			response = post_reading_to_device_API(reading_queue[0])
		except requests.exceptions.RequestException:
			break
		else:
			reading_queue.pop(0) # if this is too costly, use a linked list
			if not forwarded_reading_accepted(response):
				notify_device()
		log.info("Dequeued a reading - " + str(len(reading_queue)) + " remaining")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	log.info("Connected to MQTT broker with result code " + str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe("+/readings", qos=MQTT_QoS)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	if "/readings" in msg.topic:
		reading = {}
		try:
			reading = json.loads(" ".join(msg.payload.decode("utf-8").split()).strip("\x00"))
		except (json.decoder.JSONDecodeError, AttributeError):
			log.warning("Received invalid reading")
			notify_device()
		else:
			forward_reading(reading)

client = mqtt.Client(client_id="Readings_Interface", clean_session=False)
client.on_connect = on_connect
client.on_message = on_message

while True:
	try:
		client.connect(MQTT_HOST_ADDRESS, 1883, 60)
	except TimeoutError as error:
		log.error("Failed to connect to MQTT broker! Reason: " + str(error))
	else:
		# Processes network traffic, dispatches callbacks and handles reconnecting.
		while True:
			client.loop()
			check_and_forward_queued_readings()

	# wait a moment and try to connect again
	time.sleep(1)
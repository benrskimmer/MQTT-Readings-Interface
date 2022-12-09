import paho.mqtt.client as mqtt
import requests
import json
from bs4 import BeautifulSoup
import time
import datetime as dt
import pytz
import deviceclient as Device

MQTT_HOST_ADDRESS = "192.168.1.114"
DEVICE_API_HOST_ADDRESS = "iot.benrawstron.org"
DEVICE_API_HOST_TIMEOUT_S = 1
MQTT_QoS = 2
VERBOSE = True

LOG_TZ = pytz.timezone("US/Eastern")
REQUEST_RESPONSE_BAD_REQUEST = 400
REQUEST_RESPONSE_INTERNAL_SERVER_ERROR = 500
# See - https://www.django-rest-framework.org/api-guide/status-codes/

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

def post_reading_to_device_API(reading):
	return requests.post("https://"+DEVICE_API_HOST_ADDRESS+"/device/readings", json=reading, timeout=DEVICE_API_HOST_TIMEOUT_S)

def is_forwarded_reading_faulty(response):
	return True if REQUEST_RESPONSE_BAD_REQUEST <= response.status_code <= REQUEST_RESPONSE_INTERNAL_SERVER_ERROR else False
	# soup = BeautifulSoup(response.content, 'html.parser')
	# print("BE API response:", soup.prettify().strip())

def forward_reading(reading):
	try:
		response = post_reading_to_device_API(reading)
	except requests.exceptions.RequestException as error:
		log.error("Failed to connect to BE API! - Reason: " + str(error))
		queue_reading(reading)
		return

	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError as error:
		if is_forwarded_reading_faulty(response):
			log.warning("BE API rejected reading with status code: " + str(response.status_code))
			if "device_id" in reading.keys():
				device.send_error(reading["device_id"], "Failed to process reading! - API Status Code: " + str(response.status_code) + " Reason: " + str(error))
		else:
			log.warning("Failed to connect to BE API with reason: " + str(error))
			queue_reading(reading)
	else:
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

		try:
			response.raise_for_status()
		except requests.exceptions.HTTPError as error:
			if is_forwarded_reading_faulty(response):
				if "device_id" in reading.keys():
					device.send_error(reading["device_id"], "Failed to process reading! - API Status Code: " + str(response.status_code) + "Reason: " + str(error))
				reading_queue.pop(0) # if this is too costly, use a linked list
				log.info("Dequeued a reading - " + str(len(reading_queue)) + " remaining")
			break
		else:
			reading_queue.pop(0) # if this is too costly, use a linked list
			log.info("Dequeued a reading - " + str(len(reading_queue)) + " remaining")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(mqtt_client, userdata, flags, rc):
	log.info("Connected to MQTT broker with result code " + str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	mqtt_client.subscribe("+/readings", qos=MQTT_QoS)

# The callback for when a PUBLISH message is received from the server.
def on_message(mqtt_client, userdata, msg):
	if "/readings" in msg.topic:
		reading = {}
		try:
			reading = json.loads(" ".join(msg.payload.decode("utf-8").split()).strip("\x00"))
		except (json.decoder.JSONDecodeError, AttributeError):
			log.warning("Received invalid reading")
			notify_device("Invalid Reading")
		else:
			forward_reading(reading)

mqtt_client = mqtt.Client(client_id="Readings_Interface", clean_session=False)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
device = Device.Notifications(mqtt_client)

while True:
	try:
		mqtt_client.connect(MQTT_HOST_ADDRESS, 1883, 60)
	except TimeoutError as error:
		log.error("Failed to connect to MQTT broker! Reason: " + str(error))
	else:
		# Processes network traffic, dispatches callbacks and handles reconnecting.
		while True:
			mqtt_client.loop()
			check_and_forward_queued_readings()

	# wait a moment and try to connect again
	time.sleep(1)
import paho.mqtt.client as mqtt
import requests
import json
# from bs4 import BeautifulSoup
import time
import datetime as dt
import pytz
import argparse
import deviceclient as Device

MQTT_HOST_ADDRESS = "192.168.1.114"
DEVICE_API_HOST_ADDRESS = "iot.benrawstron.org"
DEVICE_API_HOST_TIMEOUT_S = 1
MQTT_QoS = 2

LOG_TZ = pytz.timezone("US/Eastern")
REQUEST_RESPONSE_BAD_REQUEST = 400
REQUEST_RESPONSE_INTERNAL_SERVER_ERROR = 500
# See - https://www.django-rest-framework.org/api-guide/status-codes/

# The max number of reading's we'll queue before dropping old readings
READING_QUEUE_SIZE_MAX = 1000
reading_queue = []

parser = argparse.ArgumentParser(description="MQTT to Device API Readings Interface")
parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose log output")
flags = parser.parse_args()
verbose = flags.verbose


class Log:
    def __str__(self):
        return "Logging class used to standardize/organize log output"

    def _log(self, type_string, string):
        print(f"""{dt.datetime.now(tz=LOG_TZ).strftime("%m/%d/%y %H:%M:%S %Z")} {type_string} {string}""")

    def info(self, string):
        if verbose:
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
    log.warning(f"{len(reading_queue)} queued reading(s)")


def dequeue_reading():
    reading_queue.pop(0)  # if this is too costly, use a linked list
    log.info(f"Dequeued a reading - {len(reading_queue)} remaining")


def post_reading_to_device_API(reading):
    return requests.post(
        f"https://{DEVICE_API_HOST_ADDRESS}/device/readings",
        json=reading,
        timeout=DEVICE_API_HOST_TIMEOUT_S
    )


def is_forwarded_reading_faulty(response):
    return REQUEST_RESPONSE_BAD_REQUEST <= response.status_code <= REQUEST_RESPONSE_INTERNAL_SERVER_ERROR
    # soup = BeautifulSoup(response.content, 'html.parser')
    # print("BE API response:", soup.prettify().strip())


def get_device_id_from_topic(topic):
    return topic.split("/")[0] if "/" in topic else ""


def get_device_id_from_reading(reading):
    return reading["device_id"] if "device_id" in reading.keys() else ""


def does_topic_match_reading_device_id(topic, reading):
    return get_device_id_from_topic(topic) == get_device_id_from_reading(reading)


def get_device_id_from_reading_or_topic(reading, topic):
    return get_device_id_from_topic(topic) or get_device_id_from_reading(reading)


def handle_faulty_reading(reading, message, device_topic=""):
    device_id = get_device_id_from_reading_or_topic(reading, device_topic)
    if not device_id:
        return
    device.send_error(device_id, message)


def notify_device_if_forwarded_reading_is_faulty(reading, response, error):
    if not is_forwarded_reading_faulty(response):
        return
    status_code = response.status_code
    reason = response.content.decode().strip()
    device_message = (
        f"Failed to process reading! - API Status Code: {status_code}"
        f"{f', Reason: {reason}' if reason else ''}"
    )
    log.info(f"BE API rejected reading with status code: {status_code}")
    handle_faulty_reading(reading, device_message)


def handle_failed_request(reading, error):
    log.error(f"Failed to connect to BE API! - Reason: {error}")
    queue_reading(reading)


def forward_reading(reading):
    try:
        response = post_reading_to_device_API(reading)
    except requests.exceptions.RequestException as error:
        handle_failed_request(reading, error)
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        notify_device_if_forwarded_reading_is_faulty(reading, response, error)
        if is_forwarded_reading_faulty(response) is False:
            handle_failed_request(reading, error)
        return

    log.info(f"Forwarded reading from device: {get_device_id_from_reading(reading)}")


def check_and_forward_queued_readings():
    while reading_queue:
        try:
            response = post_reading_to_device_API(reading_queue[0])
        except requests.exceptions.RequestException:
            break

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            notify_device_if_forwarded_reading_is_faulty(reading_queue[0], response, error)
            if is_forwarded_reading_faulty(response) is False:
                break

        dequeue_reading()


# The callback for when the client receives a CONNACK response from the server.
def on_connect(mqtt_client, userdata, flags, rc):
    log.warning(f"Connected to MQTT broker with result code {rc}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    mqtt_client.subscribe("+/readings", qos=MQTT_QoS)


# The callback for when a PUBLISH message is received from the server.
def on_message(mqtt_client, userdata, msg):
    topic_device_id = get_device_id_from_topic(msg.topic)
    if not topic_device_id:
        log.info("A device published to a topic without including its device ID")
        return

    try:
        reading = json.loads(" ".join(msg.payload.decode("utf-8").split()).strip("\x00"))
    except (json.decoder.JSONDecodeError, AttributeError):
        log.info(f"Received invalid reading from device ID: {topic_device_id}")
        handle_faulty_reading({}, "Invalid JSON reading", msg.topic)
        return

    if not does_topic_match_reading_device_id(msg.topic, reading):
        device_id_from_reading = get_device_id_from_reading(reading)
        log.info(f"ID mismatch - Topic {msg.topic} got reading with device ID: {device_id_from_reading}")
        handle_faulty_reading(reading, "Check device ID", msg.topic)
        return

    forward_reading(reading)


mqtt_client = mqtt.Client(client_id="Readings_Interface", clean_session=False)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
device = Device.Notifications(mqtt_client)

while True:
    try:
        mqtt_client.connect(MQTT_HOST_ADDRESS, 1883, 60)
    except TimeoutError as error:
        log.error(f"Failed to connect to MQTT broker! Reason: {error}")
    else:
        # Processes network traffic, dispatches callbacks and handles reconnecting.
        while True:
            mqtt_client.loop()
            check_and_forward_queued_readings()

    # wait a moment and try to connect again
    time.sleep(1)

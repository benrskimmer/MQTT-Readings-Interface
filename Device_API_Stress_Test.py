import requests
import datetime as dt
from os.path import basename
from testresults import display_results
from testcredentials import DEVICE_ID, DEVICE_PASSWORD

DEVICE_API_HOST_ADDRESS = "iot.benrawstron.org"
DEVICE_API_HOST_TIMEOUT_S = 1

NUM_TEST_PACKETS_TO_SEND = 100

DUMMY_READING = {
    "device_id": DEVICE_ID,
    "password": DEVICE_PASSWORD,
    "time_stamp": "1/17/21 1:12:00+0000",
    "record_version": "1",
    "temperature": "70",
    "humidity": "40"
}

start_time = dt.datetime.now()

for packet_count in range(NUM_TEST_PACKETS_TO_SEND):
    new_reading = DUMMY_READING.copy()
    new_reading["time_stamp"] = dt.datetime.now(tz=dt.timezone.utc).strftime("%m/%d/%y %H:%M:%S%z")
    response = requests.post(
        f"https://{DEVICE_API_HOST_ADDRESS}/device/readings",
        json=new_reading,
        timeout=DEVICE_API_HOST_TIMEOUT_S
    )
    response.raise_for_status()
    print(f"Sent packet # {packet_count}", end="\r")

finish_time = dt.datetime.now()

display_results(start_time, finish_time, NUM_TEST_PACKETS_TO_SEND, basename(__file__))

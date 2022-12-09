import requests
import time
import datetime as dt
import json

DEVICE_API_HOST_ADDRESS = "iot.benrawstron.org"
DEVICE_API_HOST_TIMEOUT_S = 1

MAX_TEST_PACKETS = 100
PACKETS_PER_SECOND = 10 # don't be silly and set this to 0 or you'll get a device by zero error dummy...

DUMMY_READING = {"device_id": "00259CACAEBF", "password": "ID26876jX3RWiTBK", "time_stamp": "1/17/21 1:12:00+0500", "record_version": "1", "temperature": "70", "humidity": "40"}

packet_count = 0
start_time = dt.datetime.now()

# Processes network traffic, dispatches callbacks and handles reconnecting.
while True:
	new_reading = DUMMY_READING.copy()
	new_reading["time_stamp"] = dt.datetime.now(tz=dt.timezone.utc).strftime("%m/%d/%y %H:%M:%S%z")
	requests.post("https://"+DEVICE_API_HOST_ADDRESS+"/device/readings", json=new_reading, timeout=DEVICE_API_HOST_TIMEOUT_S)
	#  time.sleep(1/PACKETS_PER_SECOND)
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
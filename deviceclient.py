import paho.mqtt.client as mqtt
import json

class Notifications:
	COLORS = (
		"red"
		"green"
		"blue"
		"yellow"
		"orange"
		"white"
		"cyan"
		"magenta"
	)

	_NOTIFICATION_VERSION = 1

	_NOTIFICATION_TEMPLATE = {"record_version": _NOTIFICATION_VERSION, "type":"info", "message":"", "RGB_LED": "white"}
	
	_DEFAULT_QoS = 0

	def __init__(self, client):
		self.mqtt_client = client

	def __str__(self):
		return "device client used for sending notification messages to IoT device"

	def _send_notification(self, device, payload, qos):
		self.mqtt_client.publish(device+"/info", payload=json.dumps(payload), qos=self._DEFAULT_QoS)

	def _verify_notification_inputs(self, device, message, RGB_LED, qos):
		if type(device) != str:
			raise TypeError("device must be a string")
		if type(message) != str:
			raise TypeError("message must be a string")
		if type(RGB_LED) == list:
			if len(RGB_LED) != 3:
				raise TypeError("RGB LED list must only have 3 values")
			for value in RGB_LED:
				if type(value) != int:
					raise TypeError("RGB LED list values must be integers between 0 and 255")
				if not (0 <= int(value) <= 255):
					raise ValueError("RGB LED list values must be between 0 and 255")
		elif type(RGB_LED) == str:
			if RGB_LED not in self.COLORS:
				raise ValueError("invalid RGB LED color string - see COLORS attribute")
		else:
			raise TypeError("RGB LED must either be a valid color string or a list of RGB integer values")
		if type(qos) != int:
			raise TypeError("MQTT QoS value must be int between 0 and 3")
		if not (0 <= int(qos) <= 3):
			raise ValueError("MQTT QoS value must be int between 0 and 3")

	def _generate_payload(self, device, message, RGB_LED, qos):
		self._verify_notification_inputs(device, message, RGB_LED, qos)
		payload = self._NOTIFICATION_TEMPLATE.copy()
		payload["message"] = message
		payload["RGB_LED"] = RGB_LED
		return payload

	def send_info(self, device, message, RGB_LED="white", qos=_DEFAULT_QoS):
		payload = self._generate_payload(device, message, RGB_LED, qos)
		payload["type"] = "info"
		self._send_notification(device, payload, qos)

	def send_warning(self, device, message, RGB_LED="yellow", qos=_DEFAULT_QoS):
		payload = self._generate_payload(device, message, RGB_LED, qos)
		payload["type"] = "warning"
		self._send_notification(device, payload, qos)

	def send_error(self, device, message, RGB_LED="red", qos=_DEFAULT_QoS):
		payload = self._generate_payload(device, message, RGB_LED, qos)
		payload["type"] = "error"
		self._send_notification(device, payload, qos)
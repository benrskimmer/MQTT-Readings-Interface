| Test | Date | Packets Per Second | Seconds Per Packet | Packets Sent | Total Time (s) | Notes |
|---|---|---|---|---|---|---|
|Device_API_Stress_Test.py|12/14/22 18:27:03-0500|3.99|0.250481|100|25.048058|Using TLS, DNS, development server, single threaded test and device authentication with 200k digest iterations|
|Device_API_Stress_Test.py|12/14/22 18:41:11-0500|4.13|0.242022|100|24.202203|No TLS, using http to local IP, development server, single threaded test and device authentication with 200k digest iterations|
|Device_API_Stress_Test.py|12/14/22 18:51:00-0500|11.82|0.084601|100|8.460122|No TLS, using http to local IP, development server, single threaded test and device authentication dissabled|
|Readings_Interface_Stress_Test.py|12/15/22 12:20:42-0500|6424.98|0.000156|50000|7.782126|MQTT QoS = 0|
|Readings_Interface_Stress_Test.py|12/15/22 12:22:16-0500|5049.8|0.000198|50000|9.901376|MQTT QoS = 1|
|Readings_Interface_Stress_Test.py|12/15/22 12:26:47-0500|4563.43|0.000219|50000|10.956675|MQTT QoS = 2|

from os.path import exists
import datetime as dt
import pytz

FILE_PATH = "BE Performance Results.md"
HEADER = """| Test | Date | Packets Per Second | Seconds Per Packet | Packets Sent | Total Time (s) | Notes |
|---|---|---|---|---|---|---|\n"""


def add_header_if_new_file():
    if exists(FILE_PATH):
        return
    with open(FILE_PATH, 'w+') as results_file:
        results_file.write(HEADER)


def save_results(test_name, date, packets_per_second, time_per_packet, total_packets, total_time, notes):
    add_header_if_new_file()
    with open(FILE_PATH, 'a') as results_file:
        output = f"|{test_name}|{date}|{packets_per_second}|{time_per_packet}|{total_packets}|{total_time}|{notes}|\n"
        results_file.write(output)


def display_results(start_time, finish_time, packets_sent, test_name):
    time_taken = finish_time - start_time
    packet_rate = round(packets_sent/time_taken.total_seconds(), 2)
    time_per_packet = round(time_taken.total_seconds()/packets_sent, 6)
    print(f"Total packets sent: {packets_sent}")
    print(f"Total time taken: {time_taken.total_seconds()} seconds")
    print(f"Average packet rate: {packet_rate} packets/second")
    print(f"Average time per packet: {time_per_packet} seconds")

    print("Would you like to save these results? y/n")
    answer = input()
    if not (answer == "y" or answer == "yes"):
        return

    print("Please list any notes associated with this test run:")
    notes = input()

    save_results(
        test_name=test_name,
        date=dt.datetime.now(tz=pytz.timezone('EST5EDT')).strftime("%m/%d/%y %H:%M:%S%z"),
        packets_per_second=packet_rate,
        time_per_packet=time_per_packet,
        total_packets=packets_sent,
        total_time=time_taken.total_seconds(),
        notes=notes
    )
    print("Saved!")

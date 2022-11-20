import getopt
import math
import sys
import socket
import json
import threading
from enum import Enum

BUFFER_SIZE = 1024
SEGMENT_SIZE = 900
WINDOW_SIZE = 100

HOST = "127.0.0.1"
PORT = 5000
FILE = ""

TIME_OUT = 2000


class WindowType(Enum):
    SEND_ACKED = 1
    SEND_NOT_ACKED_YET = 2
    AVALIABLE_NOT_SEND_YET = 3
    DISABLED_NOT_SEND_YET = 4


def update_to_avaliable(data):
    data["type"] = WindowType.AVALIABLE_NOT_SEND_YET
    return data


def update_to_disable(data):
    data["type"] = WindowType.DISABLED_NOT_SEND_YET
    return data


def update_to_acked(data):
    data["type"] = WindowType.SEND_ACKED
    return data


def update_to_send(data):
    data["type"] = WindowType.SEND_NOT_ACKED_YET
    return data


def main():
    init_message = {
        "file": FILE != "",
        "segment_size": SEGMENT_SIZE,
        "total_data_size": 0,
        "buffer_size": BUFFER_SIZE,
        "total_segments": 0
    }

    server_info = {
        "window_size": 100
    }

    windows = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        sock.settimeout(TIME_OUT)
        if init_message["file"]:
            with open(FILE, "r", encoding="utf-8") as file:
                data = file.read()
        else:
            data = input('>')

        init_message["total_data_size"] = len(data)
        result = init_window(data, init_message["total_data_size"])

        init_message["total_segments"] = result["total_segments"]
        window_buffer = result["window"]

        print(init_message)

        sock.sendall(json.dumps(init_message).encode('utf-8'))
        server_info = json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))
        max_window_size = server_info["max_window_size"]
        # update the max server window size to avaliable
        window_buffer = list(map(update_to_avaliable, window_buffer[0:max_window_size]))

        # print(window_buffer)
        # sock.setblocking(False)
        for index, each in enumerate(window_buffer):
            if each["type"] == WindowType.AVALIABLE_NOT_SEND_YET:
                thread = threading.Thread(target=thread_send, args=(sock, each, index))
                thread.start()
                # thread.join()
                # thread_send(sock, each, index)
        ack = json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))
        print(ack)


def thread_send(sock, data, index):
    sock.sendall(json.dumps({
        "sequence": index,
        "data": data["data"]
    }).encode('utf-8'))
    data["type"] = WindowType.SEND_NOT_ACKED_YET


def init_window(data, length):
    window = []
    loop_times = math.ceil(length / SEGMENT_SIZE)

    for i in range(loop_times):
        window.append({
            "type": WindowType.DISABLED_NOT_SEND_YET,
            "sequence": i,
            "data": data[i * SEGMENT_SIZE:i * SEGMENT_SIZE + SEGMENT_SIZE]
        })
    return {
        "window": window,
        "total_segments": loop_times
    }


def help_msg():
    print("-s or --server to specify the host name\n"
          "-p or --port is the the host port\n"
          "-f or --file is the absolute directory for file to send")


if __name__ == '__main__':
    options = []
    argv = sys.argv[1:]
    try:
        options, args = getopt.getopt(argv, 's:p:f:', ['server=', 'port=', 'file='])
    except getopt.GetoptError as exception:
        print(f"Argument Error : {exception.msg}")
        help_msg()
        sys.exit()

    for opt, arg in options:
        if opt in ('-s', '--server'):
            HOST = arg
        elif opt in ('-p', '--port'):
            PORT = int(arg)
        elif opt in ('-f', '--file'):
            FILE = arg
        else:
            help_msg()

    try:
        main()
    except KeyboardInterrupt:
        print("\nExit\n")
    except Exception as e:
        print(e)
    finally:
        sys.exit()

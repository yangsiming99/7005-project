import copy
import getopt
import math
import sys
import socket
import json
import threading
import time
from enum import Enum

from util import pack_segment

BUFFER_SIZE = 1024
SEGMENT_SIZE = 951
WINDOW_SIZE = 100

HOST = "127.0.0.1"
PORT = 5000
FILE = "words.txt"

TIME_OUT = 20.0


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


def ack_thread(sock, window_buffer):
    ack = json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))
    ack_no = int(ack["ack_no"])
    window_buffer[ack_no]["type"] = WindowType.SEND_ACKED


def main():
    init_message = {
        "file": FILE != "",
        "segment_size": SEGMENT_SIZE,
        "total_data_size": 0,
        "buffer_size": BUFFER_SIZE,
        "total_segments": 0
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        if init_message["file"]:
            with open(FILE, "r", encoding="utf-8") as file:
                data = file.read()
        else:
            data = input('>')

        init_message["total_data_size"] = len(data)
        window_buffer = init_window(data, init_message["total_data_size"])

        init_message["total_segments"] = len(window_buffer)

        print(init_message)

        sock.sendall(json.dumps(init_message).encode('utf-8'))
        server_info = json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))
        # print(server_info)
        # recv_size = server_info["recv_size"]
        # # update the max server window size to avaliable
        # window_buffer[0:recv_size] = list(map(update_to_avaliable, window_buffer[0:recv_size]))

        # thread = threading.Thread(target=ack_thread, args=(sock, window_buffer))
        # thread.daemon = True
        # thread.start()

        # print(window_buffer)
        for index, each in enumerate(window_buffer):
            if each["type"] == WindowType.AVALIABLE_NOT_SEND_YET:
                sock.sendall(pack_segment(index + 1, index, each["data"], init_message["total_segments"] - index))
                each["type"] = WindowType.SEND_NOT_ACKED_YET
                deadline = time.time() + TIME_OUT
                ack = json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))
                print(ack)
                while not ack:
                    if time.time() >= deadline:
                        sock.sendall(
                            pack_segment(index + 1, index, each["data"], init_message["total_segments"] - index)
                        )
                each["type"] = WindowType.SEND_ACKED
                recv_current_window_size = int(ack["window_size"])
                while recv_current_window_size <= 0:
                    recv_current_window_size = int(json.loads(sock.recv(BUFFER_SIZE).decode('utf-8'))["window_size"])


def init_window(data, length):
    window = []
    loop_times = math.ceil(length / SEGMENT_SIZE)

    for i in range(loop_times):
        window.append({
            "type": WindowType.AVALIABLE_NOT_SEND_YET,
            "sequence": i,
            "window_size": WINDOW_SIZE,
            "data": data[i * SEGMENT_SIZE:i * SEGMENT_SIZE + SEGMENT_SIZE]
        })
    return window


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

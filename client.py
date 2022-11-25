import copy
import getopt
import math
import sys
import socket
import json
import threading
import time
from _socket import timeout
from enum import Enum

from Segment import Segment
from util import pack_segment

SEGMENT_SIZE = Segment.MAX_SEGMENT_SIZE

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


def main():
    init_message = {
        "segment_size": SEGMENT_SIZE,
        "total_data_size": 0,
        "packet_size": Segment.PACKET_SIZE,
        "total_segments": 0
    }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        if FILE != "":
            with open(FILE, "r", encoding="utf-8") as file:
                data = file.read()
        else:
            data = input('>')

        init_message["total_data_size"] = len(data)
        init_message["total_segments"] = math.ceil(len(data) / Segment.MAX_SEGMENT_SIZE)

        window_buffer = [{}] * init_message["total_segments"]

        sock.sendall(json.dumps(init_message).encode('utf-8'))
        server_info = json.loads(sock.recv(Segment.PACKET_SIZE).decode('utf-8'))
        init_window_size = server_info["recv_size"]
        # init all to disable
        window_buffer[0:] = list(map(update_to_disable, window_buffer[0:]))
        # set avaliable for window size
        window_buffer[0:init_window_size] = list(map(update_to_avaliable, window_buffer[0:init_window_size]))
        # init sequence number
        sequence_no = 0

        sock.settimeout(TIME_OUT)

        window_size = 0
        # print(window_buffer)
        for index, each in enumerate(window_buffer):
            avaliable_window = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE_NOT_SEND_YET)
            if avaliable_window > 0:
                current_chunk = data[index * SEGMENT_SIZE:index * SEGMENT_SIZE + SEGMENT_SIZE]
                expected_ack = sequence_no + len(current_chunk)
                current_segment = Segment(expected_ack, sequence_no, avaliable_window, index, current_chunk)
                sock.sendall(current_segment.pack_segment())
                each["type"] = WindowType.SEND_NOT_ACKED_YET
                each["data"] = current_segment
                sequence_no += len(current_chunk)
                window_size += 1
            else:
                # update window size
                for ack_index in range(window_size):
                    while True:
                        try:
                            # ack sent data
                            ack_raw = sock.recv(Segment.PACKET_SIZE)
                            break
                        except timeout:
                            # retransmit
                            sock.sendall(window_buffer[index - (window_size - ack_index)])
                    ack = Segment.unpack_segment(ack_raw)
                    # update window buffer
                    window_buffer[ack.segment_index]["type"] = WindowType.SEND_ACKED
                # slide window buffer to right for length of receiver window size
                if ack.window_size > 0:
                    window_buffer[index + 1: index + 1 + ack.window_size] = list(
                        map(update_to_avaliable, window_buffer[index + 1: index + 1 + ack.window_size]))
                # receiver window size not allow to send
                else:
                    while True:
                        ack = Segment.unpack_segment(sock.recv(Segment.PACKET_SIZE))
                        if ack.window_size > 0:
                            window_buffer[index + 1: index + 1 + ack.window_size] = list(
                                map(update_to_avaliable, window_buffer[index + 1: index + 1 + ack.window_size]))
                window_size = 0


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

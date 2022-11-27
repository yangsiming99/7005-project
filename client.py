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

SEGMENT_SIZE = Segment.MAX_SEGMENT_SIZE

HOST = "127.0.0.1"
PORT = 4000
FILE = "words.txt"

TIME_OUT = Segment.TIME_OUT


class WindowType(Enum):
    SEND_ACKED = 1
    SEND_NOT_ACKED_YET = 2
    AVALIABLE_NOT_SEND_YET = 3
    DISABLED_NOT_SEND_YET = 4
    TIME_OUT = 5


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


def retransmit(sock, window_buffer, current_index):
    window_buffer[current_index]["data"].set_retransmit(True)
    sock.sendall(window_buffer[current_index]["data"].pack_segment())
    retransmit_raw = sock.recv(Segment.PACKET_SIZE)
    data = Segment.unpack_segment(retransmit_raw)
    print(data.segment_index, current_index)
    window_buffer[current_index]["type"] = WindowType.SEND_ACKED


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

        window_buffer = [{"type": WindowType.DISABLED_NOT_SEND_YET} for i in range(init_message["total_segments"])]

        sock.sendall(json.dumps(init_message).encode('utf-8'))
        server_info = json.loads(sock.recv(Segment.PACKET_SIZE).decode('utf-8'))
        init_window_size = server_info["recv_size"]
        # set avaliable for window size
        window_buffer[0:init_window_size] = list(map(update_to_avaliable, window_buffer[0:init_window_size]))
        # init sequence number
        sequence_no = 0

        sock.settimeout(TIME_OUT)

        window_size = 0
        index = 0
        # print(window_buffer)
        while index < len(window_buffer):
            avaliable_window = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE_NOT_SEND_YET)
            if avaliable_window > 0:
                current_chunk = data[index * SEGMENT_SIZE:index * SEGMENT_SIZE + SEGMENT_SIZE]
                expected_ack = sequence_no + len(current_chunk)
                current_segment = Segment(expected_ack, sequence_no, avaliable_window, index, False, current_chunk)
                sock.sendall(current_segment.pack_segment())
                print(index, "SEND")
                window_buffer[index]["type"] = WindowType.SEND_NOT_ACKED_YET
                window_buffer[index]["data"] = current_segment
                sequence_no += len(current_chunk)
                window_size += 1
                index += 1
            else:
                ack_index = 0
                # update window size
                while ack_index < window_size:
                    current_index = index - window_size + ack_index
                    try:
                        # ack sent data
                        ack = Segment.unpack_segment(sock.recv(Segment.PACKET_SIZE))
                        if ack.segment_index != current_index:
                            print(ack)
                        # update window buffer
                        window_buffer[current_index]["type"] = WindowType.SEND_ACKED
                        print(ack.segment_index, current_index, "ACK")
                    except timeout:
                        # retransmit
                        print(current_index, "retransmit")
                        retransmit(sock, window_buffer, current_index)
                    ack_index += 1
                # slide window buffer to right for length of receiver window size
                update_window_size = Segment.unpack_segment(sock.recv(Segment.PACKET_SIZE))
                if update_window_size.window_size > 0:
                    window_buffer[index: index + update_window_size.window_size] = list(
                        map(update_to_avaliable, window_buffer[index: index + update_window_size.window_size]))
                    window_size = 0
                    continue
                # receiver window size not allow to send
                else:
                    while True:
                        update_window_size = Segment.unpack_segment(sock.recv(Segment.PACKET_SIZE))
                        # print(update_window_size.window_size)
                        if update_window_size.window_size > 0:
                            window_buffer[index: index + update_window_size.window_size] = list(
                                map(update_to_avaliable,
                                    window_buffer[index: index + update_window_size.window_size]))
                            window_size = 0
                            break


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

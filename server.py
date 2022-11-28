import getopt
import struct
import sys
import socket
import json
import time
from _socket import timeout
from enum import Enum
from threading import Thread

from Segment import Segment
from util import pack_segment

BACK_LOG = 5
PORT = 5000

TIME_OUT = Segment.TIME_OUT


class WindowType(Enum):
    RECV_ACKED = 1
    RECV_NO_ACKED = 2
    AVALIABLE = 3
    DISABLED = 4
    TIMEOUT = 5


def update_to_avaliable(data):
    data["type"] = WindowType.AVALIABLE
    return data


def update_to_disable(data):
    data["type"] = WindowType.DISABLED
    return data


def retransmit(conn, window_buffer, current_index):
    retransmit_raw = conn.recv(Segment.PACKET_SIZE)
    retransmit_data = Segment.unpack_segment(retransmit_raw)
    window_buffer[current_index]["data"] = retransmit_data.data.decode('utf-8')
    window_buffer[current_index]["sequence_no"] = len(retransmit_data.data) + retransmit_data.sequence_no
    window_buffer[current_index]["ack_no"] = retransmit_data.sequence_no
    window_buffer[current_index]["type"] = WindowType.RECV_NO_ACKED


def main():
    buffer_size = 1024
    window_size = Segment.INIT_WINDOW_SIZE
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", PORT))
        sock.listen(BACK_LOG)
        print("Server Waiting for client")
        while True:
            conn, from_addr = sock.accept()
            print(f"Connection from {from_addr} has been established")
            with conn:
                sender_init_message = json.loads(conn.recv(buffer_size).decode('utf-8'))
                buffer_size = sender_init_message["packet_size"]
                total_segments = sender_init_message["total_segments"]
                conn.sendall(json.dumps({
                    "recv_size": window_size,
                }).encode('utf-8'))

                window_buffer = [{"type": WindowType.DISABLED} for i in range(total_segments)]
                window_buffer[0:window_size] = list(map(update_to_avaliable, window_buffer[0:window_size]))

                index = 0
                window = 0
                while True:
                    avaliable_window = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                    if avaliable_window > 0:
                        conn.settimeout(TIME_OUT)
                        try:
                            raw_data = conn.recv(buffer_size)
                            segment = Segment.unpack_segment(raw_data)
                            if segment.retransmit == 1:
                                window_buffer[segment.segment_index]["data"] = segment.data.decode('utf-8')
                                window_buffer[segment.segment_index]["sequence_no"] = len(segment.data) + segment.sequence_no
                                window_buffer[segment.segment_index]["ack_no"] = segment.sequence_no
                                conn.sendall(
                                    Segment(window_buffer[segment.segment_index]["ack_no"],
                                            window_buffer[segment.segment_index]["sequence_no"],
                                            avaliable_window,
                                            segment.segment_index, "").pack_segment()
                                )
                                window_buffer[segment.segment_index]["type"] = WindowType.RECV_ACKED
                                print(segment.segment_index, "RE-DATA")
                            elif segment.retransmit == 2:
                                window_buffer[segment.segment_index]["data"] = segment.data.decode('utf-8')
                                window_buffer[segment.segment_index]["sequence_no"] = len(segment.data) + segment.sequence_no
                                window_buffer[segment.segment_index]["ack_no"] = segment.sequence_no
                                window_buffer[segment.segment_index]["type"] = WindowType.RECV_ACKED
                                print(segment.segment_index, "RE-ACK")
                            else:
                                print(segment.segment_index, index, "RECV")
                                window_buffer[index]["data"] = segment.data.decode('utf-8')
                                window_buffer[index]["type"] = WindowType.RECV_NO_ACKED
                                window_buffer[index]["sequence_no"] = len(segment.data) + segment.sequence_no
                                window_buffer[index]["ack_no"] = segment.sequence_no
                                index += 1
                                window += 1
                        except timeout:
                            print("timeout", index)
                            window_buffer[index]["type"] = WindowType.TIMEOUT
                            index += 1
                            window += 1
                    else:
                        conn.settimeout(0)
                        ack_index = 0
                        while ack_index < window:
                            current_index = index - window + ack_index
                            # not get the data make the ack timeout and sender will resend
                            if window_buffer[current_index]["type"] == WindowType.TIMEOUT:
                                print(current_index, "retransmit")
                                retransmit(conn, window_buffer, current_index)
                            sequence_no = window_buffer[current_index]["sequence_no"]
                            ack_no = window_buffer[current_index]["ack_no"]

                            conn.sendall(
                                Segment(sequence_no, ack_no, avaliable_window,
                                        current_index, "").pack_segment()
                            )
                            print(current_index, "ACK")
                            window_buffer[current_index]["type"] = WindowType.RECV_ACKED
                            # print(window_buffer[current_index]["data"])
                            ack_index += 1

                        window_buffer[index:window_size + index] = list(
                            map(update_to_avaliable, window_buffer[index:window_size + index]))
                        avaliable_window = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                        conn.sendall(
                            Segment(segment.sequence_no, len(segment.data) + segment.sequence_no, avaliable_window,
                                    index, "").pack_segment()
                        )
                        window = 0


def help_msg():
    print("-p or --port to specify the listening port\n")


if __name__ == '__main__':
    options = []
    argv = sys.argv[1:]
    try:
        options, args = getopt.getopt(argv, 'p:', ['port='])
    except getopt.GetoptError as exception:
        print(f"Argument Error : {exception.msg}")
        help_msg()
        sys.exit()

    for opt, arg in options:
        if opt in ('-p', '--port'):
            PORT = int(arg)
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

import getopt
import struct
import sys
import socket
import json
import time
from _socket import timeout
from enum import Enum

from Segment import Segment
from util import pack_segment

BACK_LOG = 5
PORT = 5000

TIME_OUT = 5.0


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


def main():
    buffer_size = 1024
    window_size = 10
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

                conn.settimeout(TIME_OUT)

                index = 0
                window = 0
                while index < total_segments:
                    avaliable_window = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                    if avaliable_window > 0:
                        try:
                            raw_data = conn.recv(buffer_size)
                        except timeout:
                            window_buffer[index]["type"] = WindowType.TIMEOUT
                            continue
                        if raw_data:
                            segment = Segment.unpack_segment(raw_data)
                            window_buffer[index]["data"] = segment.data.decode('utf-8')
                            window_buffer[index]["type"] = WindowType.RECV_NO_ACKED
                            window_buffer[index]["sequence_no"] = len(segment.data) + segment.sequence_no
                            window_buffer[index]["ack_no"] = segment.sequence_no
                            index += 1
                            window += 1
                        else:
                            continue
                    else:
                        for ack_index in range(index - window, index):
                            # not get the data make the ack timeout and sender will resend
                            if window_buffer[ack_index]["type"] == WindowType.TIMEOUT:
                                time.sleep(TIME_OUT)
                                retransmit_raw = sock.recv(Segment.PACKET_SIZE)
                                while not retransmit_raw:
                                    retransmit_raw = sock.recv(Segment.PACKET_SIZE)
                                retransmit = Segment.unpack_segment(retransmit_raw)
                                window_buffer[ack_index]["data"] = retransmit.data.decode('utf-8')
                                window_buffer[ack_index]["type"] = WindowType.RECV_NO_ACKED
                                window_buffer[ack_index]["sequence_no"] = len(retransmit.data) + retransmit.sequence_no
                                window_buffer[ack_index]["ack_no"] = retransmit.sequence_no
                            sequence_no = window_buffer[ack_index]["sequence_no"]
                            ack_no = window_buffer[ack_index]["ack_no"]
                            conn.sendall(
                                Segment(sequence_no, ack_no, avaliable_window,
                                        ack_index, "").pack_segment()
                            )
                            window_buffer[ack_index]["type"] = WindowType.RECV_ACKED
                            print(window_buffer[ack_index]["data"])
                        window_buffer[index + 1:window_size + index + 1] = list(
                            map(update_to_avaliable, window_buffer[index + 1:window_size + index + 1]))
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

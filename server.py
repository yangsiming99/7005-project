import getopt
import struct
import sys
import socket
import json
from enum import Enum

from Segment import Segment
from util import pack_segment

BACK_LOG = 5
PORT = 5000


class WindowType(Enum):
    RECV_ACKED = 1
    RECV_NOT_ACK_YET = 2
    AVALIABLE = 3
    DISABLED = 4


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
                print(total_segments)

                conn.sendall(json.dumps({
                    "recv_size": window_size,
                }).encode('utf-8'))

                window_buffer = [{}] * total_segments
                window_buffer[0:] = list(map(update_to_disable, window_buffer[0:]))
                window_buffer[0:window_size] = list(map(update_to_avaliable, window_buffer[0:window_size]))
                next_expected_sequence_no = 0
                for i in range(total_segments):
                    index = 0
                    while index < window_size:
                        segment = Segment.unpack_segment(conn.recv(buffer_size))
                        window_buffer[i]["type"] = WindowType.RECV_NOT_ACK_YET
                        window_buffer[i]["data"] = segment.data
                        window_buffer[i]["ack_no"] = segment.sequence_no
                        window_buffer[i]["sequence_no"] = len(segment.data) + segment.sequence_no
                        index += 1



                    next_expected_sequence_no += len(data.data)
                    print(data)

                    # sequence = int(data["sequence"])
                    # window_buffer[sequence]["data"] = data["data"]
                    # print(data["data"])
                    # window_buffer[sequence]["type"] = WindowType.RECV_ACKED
                    # count = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                    # conn.sendall(pack_segment(sequence, int(data["ack_no"]), "", count))
                    # if count == 0:
                    #     previous_size = len(window_buffer)
                    #     window_buffer.extend([{}] * WINDOW_SIZE)
                    #     for index in range(previous_size, len(window_buffer)):
                    #         window_buffer[index] = {
                    #             "type": WindowType.AVALIABLE
                    #         }
                    #     count = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                    #     conn.sendall(pack_segment(sequence, int(data["ack_no"]), "", count))


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

import getopt
import sys
import socket
import json
import threading
from enum import Enum

from util import pack_segment

BACK_LOG = 5
BUFFER_SIZE = 1024
WINDOW_SIZE = 100

PORT = 5000


class WindowType(Enum):
    RECV_ACKED = 1
    AVALIABLE = 2
    DISABLED = 3


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", PORT))
        sock.listen(BACK_LOG)
        print("Server Waiting for client")
        while True:
            conn, from_addr = sock.accept()
            print(f"Connection from {from_addr} has been established")
            with conn:
                sender_init_message = json.loads(conn.recv(BUFFER_SIZE).decode('utf-8'))
                sender_buffer_size = sender_init_message["buffer_size"]
                total_segments = sender_init_message["total_segments"]

                conn.sendall(json.dumps({
                    "recv_size": WINDOW_SIZE,
                }).encode('utf-8'))

                window_buffer = [{}] * WINDOW_SIZE
                for i in range(WINDOW_SIZE):
                    window_buffer[i] = {
                        "type": WindowType.AVALIABLE
                    }

                for i in range(total_segments):
                    data_raw = conn.recv(sender_buffer_size).decode('utf-8')
                    data = json.loads(data_raw)
                    sequence = int(data["sequence"])
                    window_buffer[sequence]["data"] = data["data"]
                    print(data["data"])
                    window_buffer[sequence]["type"] = WindowType.RECV_ACKED
                    count = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                    conn.sendall(pack_segment(sequence, int(data["ack_no"]), "", count))
                    if count == 0:
                        previous_size = len(window_buffer)
                        window_buffer.extend([{}] * WINDOW_SIZE)
                        for index in range(previous_size, len(window_buffer)):
                            window_buffer[index] = {
                                "type": WindowType.AVALIABLE
                            }
                        count = sum(1 for i in window_buffer if i["type"] == WindowType.AVALIABLE)
                        conn.sendall(pack_segment(sequence, int(data["ack_no"]), "", count))


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

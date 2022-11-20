import getopt
import sys
import socket
import json
import threading
from enum import Enum

BACK_LOG = 5
BUFFER_SIZE = 1024
WINDOW_SIZE = 1000

PORT = 5000


class WindowType(Enum):
    RECV_ACKED = 1
    RECV_NOT_YET_ACK = 2
    AVALIABLE = 3


def thread_read(conn, sender_buffer_size, window_buffer):
    data = json.loads(conn.recv(sender_buffer_size).decode('utf-8'))
    window_buffer[data["sequence"]]["data"] = data["data"]
    print(data["data"])
    conn.sendall(json.dumps({
        "sequence": data["sequence"] + 1
    }).encode('utf-8'))


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", PORT))
        sock.listen(BACK_LOG)
        print("Waiting for client")
        while True:
            conn, from_addr = sock.accept()
            window_buffer = [{
                "type": WindowType.AVALIABLE,
            }] * WINDOW_SIZE
            sender_buffer_size = 1024
            total_segments = 0
            print(f"Connection from {from_addr} has been established")
            with conn:
                sender_init_message = json.loads(conn.recv(BUFFER_SIZE).decode('utf-8'))
                sender_buffer_size = sender_init_message["buffer_size"]
                total_segments = sender_init_message["total_segments"]
                sender_segment_size = sender_init_message["segment_size"]

                conn.sendall(json.dumps({
                    "max_window_size": WINDOW_SIZE,
                }).encode('utf-8'))

                thread = threading.Thread(target=thread_read, args=(conn, sender_buffer_size, window_buffer))
                thread.start()


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

from threading import Lock
import getopt
import sys
import socket
import json
import threading
from enum import Enum

from util import pack_segment

BACK_LOG = 5
BUFFER_SIZE = 1024

PORT = 4000
REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 5000

DROP_DATA = 0
DROP_ACK = 0

DELAY_DATA = 0
DELAY_ACK = 0


class WindowType(Enum):
    SEND_ACKED = 1
    SEND_NOT_ACKED_YET = 2
    NOT_SEND_YET = 3


# def control_drop():


def proxy_handler(client_sock, window_buffer):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_sock:
        remote_sock.connect((REMOTE_HOST, REMOTE_PORT))
        while True:
            local_buffer = client_sock.recv(BUFFER_SIZE).decode('utf-8')
            if len(local_buffer):
                local_data = json.loads(local_buffer)
                local_data["type"] = WindowType.NOT_SEND_YET
                # print(local_data)
                window_buffer.append(local_buffer)
                remote_sock.sendall(local_buffer.encode('utf-8'))
                local_data["type"] = WindowType.SEND_NOT_ACKED_YET
            remote_buffer = remote_sock.recv(BUFFER_SIZE).decode('utf-8')
            if len(remote_buffer):
                remote_data = json.loads(remote_buffer)
                client_sock.sendall(remote_buffer.encode('utf-8'))
                local_data["type"] = WindowType.SEND_ACKED
                if remote_data.get("window_size") is not None and int(remote_data.get("window_size")) == 0:
                    remote_buffer = remote_sock.recv(BUFFER_SIZE).decode('utf-8')
                    client_sock.sendall(remote_buffer.encode('utf-8'))
            if not len(local_buffer) or not len(remote_buffer):
                # print(window_buffer)
                client_sock.close()
                sys.exit(0)


def update_options():
    input(">")


def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("0.0.0.0", PORT))
        server_sock.listen(BACK_LOG)
        print("Proxy Waiting for client")
        # input_thread = threading.Thread(target=update_options, args=[])
        # input_thread.start()
        while True:
            client, from_addr = server_sock.accept()
            print(f"Connection from sender {from_addr} has been established")
            window_buffer = []
            proxy_thread = threading.Thread(target=proxy_handler, args=(client, window_buffer))
            proxy_thread.daemon = True
            proxy_thread.start()
            # proxy_handler(client)


def remote():
    print("remote")


def main():
    server()


def help_msg():
    print("-p or --port to specify the listening port\n")


if __name__ == '__main__':
    options = []
    argv = sys.argv[1:]
    try:
        options, args = getopt.getopt(argv, 'P:s:p:', ['port=', 'server=', 'server_port'])
    except getopt.GetoptError as exception:
        print(f"Argument Error : {exception.msg}")
        help_msg()
        sys.exit()

    for opt, arg in options:
        if opt in ('-P', '--port'):
            PORT = int(arg)
        if opt in ('-s', '--server'):
            REMOTE_HOST = arg
        elif opt in ('-p', '--server_port'):
            REMOTE_PORT = int(arg)
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

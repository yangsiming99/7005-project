import atexit
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


def proxy_handler(client_sock):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_sock:
        remote_sock.connect((REMOTE_HOST, REMOTE_PORT))
        while True:
            local_buffer = client_sock.recv(BUFFER_SIZE).decode('utf-8')
            if len(local_buffer):
                remote_sock.sendall(local_buffer.encode('utf-8'))
            remote_buffer = remote_sock.recv(BUFFER_SIZE).decode('utf-8')
            if len(remote_buffer):
                client_sock.sendall(remote_buffer.encode('utf-8'))
            if not len(local_buffer) or not len(remote_buffer):
                option = input('>')


def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("0.0.0.0", PORT))
        server_sock.listen(BACK_LOG)
        print("Proxy Waiting for client")
        while True:
            client, from_addr = server_sock.accept()
            # noinspection PyTypeChecker
            # proxy_thread = threading.Thread(target=proxy_handler, args=client)
            # proxy_thread.start()
            proxy_handler(client)


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

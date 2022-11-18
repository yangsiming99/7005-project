import getopt
import sys
import socket
import json
from enum import Enum

BUFFER_SIZE = 1024
WINDOW_SIZE = 100

HOST = "192.168.1.16"
PORT = 5000
FILE = "test.txt"


class WindowType(Enum):
    SEND_ACKED = 1
    SEND_NOT_ACKED_YET = 2
    AVALIABLE_NOT_SEND_YET = 3
    DISABLED_NOT_SEND_YET = 4
    INIT = 5


window = [{
    type: WindowType.INIT,
    "data": None
}] * WINDOW_SIZE


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        with open(FILE, "rb") as file:
            send_data = file.read(BUFFER_SIZE)
            while send_data:
                sock.sendall(send_data)
                send_data = file.read(BUFFER_SIZE)


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

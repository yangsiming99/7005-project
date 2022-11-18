import getopt
import sys
import socket

BACK_LOG = 5
BUFFER_SIZE = 1024

PORT = 5000


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", PORT))
        sock.listen(BACK_LOG)
        print("Waiting for client")
        while True:
            conn, from_addr = sock.accept()
            print(f"Connection from {from_addr} has been established")
            with conn:
                with open("test.txt", "wb") as file:
                    data = conn.recv(BUFFER_SIZE)
                    while data:
                        file.write(data)
                        data = conn.recv(BUFFER_SIZE)


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

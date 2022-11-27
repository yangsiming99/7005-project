import random
import time
import getopt
import sys
import socket
import json

from threading import Thread
from flask import Flask
from enum import Enum
from Segment import Segment

app = Flask(__name__)

BACK_LOG = 5
BUFFER_SIZE = 1024

PORT = 4000
REMOTE_HOST = "127.0.0.1"
REMOTE_PORT = 5000

DROP_DATA = 50
DROP_ACK = 0

DELAY_DATA = 0
DELAY_ACK = 0

TIME_OUT = Segment.TIME_OUT


class WindowType(Enum):
    SEND_ACKED = 1
    SEND_NOT_ACKED_YET = 2
    AVALIABLE_NOT_SEND_YET = 3
    DROP_DATA = 4
    DROP_ACK = 5


def should_delay_data():
    return random.randrange(100) < int(DELAY_DATA)


def should_delay_ack():
    return random.randrange(100) < int(DELAY_ACK)


def should_drop_data():
    return random.randrange(100) < int(DROP_DATA)


def should_drop_ack():
    return random.randrange(100) < int(DROP_ACK)


def update_to_avaliable(data):
    data["type"] = WindowType.AVALIABLE_NOT_SEND_YET
    return data


def retransmit_data(client_sock, buffer_size, remote_sock, data_buffer, ack_index):
    retransmit_raw = client_sock.recv(buffer_size)
    retransmit = Segment.unpack_segment(retransmit_raw)
    print(retransmit.segment_index, "retransmit index", retransmit.retransmit)
    remote_sock.sendall(retransmit_raw)
    retransmit_ack_raw = remote_sock.recv(buffer_size)
    client_sock.sendall(retransmit_ack_raw)
    data_buffer[ack_index]["type"] = WindowType.SEND_ACKED


def proxy_handler(client_sock):
    buffer_size = 1024
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as remote_sock:
        remote_sock.connect((REMOTE_HOST, REMOTE_PORT))
        with client_sock:
            # init connection
            init_raw_message = client_sock.recv(buffer_size)
            sender_init_message = json.loads(init_raw_message.decode('utf-8'))
            buffer_size = sender_init_message["packet_size"]
            total_segments = sender_init_message["total_segments"]
            data_buffer = [{"type": WindowType.AVALIABLE_NOT_SEND_YET} for i in range(total_segments)]
            # send to receiver
            remote_sock.sendall(init_raw_message)
            server_raw_info = remote_sock.recv(buffer_size)
            init_window_size = json.loads(server_raw_info.decode('utf-8'))["recv_size"]
            client_sock.sendall(server_raw_info)

            index = 0
            window = 0
            avaliable_window = init_window_size

            while True:
                if avaliable_window > 0:
                    if should_drop_data():
                        data_buffer[index]["type"] = WindowType.DROP_DATA
                        # print(f"Drop data {index}")
                    else:
                        if should_delay_data():
                            data_buffer[index]["type"] = WindowType.DROP_DATA
                            time.sleep(TIME_OUT)
                        raw_data = client_sock.recv(buffer_size)
                        remote_sock.sendall(raw_data)
                        data_buffer[index]["type"] = WindowType.SEND_NOT_ACKED_YET
                        print(index, "SEND")
                        segment = Segment.unpack_segment(raw_data)
                        data_buffer[index]["sequence_no"] = segment.sequence_no
                        data_buffer[index]["ack_no"] = segment.ack_no
                    index += 1
                    window += 1
                    avaliable_window -= 1
                else:
                    ack_index = 0
                    while ack_index < window:
                        current_index = index - window + ack_index
                        if data_buffer[current_index]["type"] == WindowType.DROP_DATA:
                            print(current_index, "drop data index")
                            retransmit_data(client_sock, buffer_size, remote_sock, data_buffer, current_index)
                        elif should_drop_ack() or should_delay_ack():
                            print(current_index, "drop ack index")
                            retransmit_data(client_sock, buffer_size, remote_sock, data_buffer, current_index)
                        else:
                            raw_ack = remote_sock.recv(buffer_size)
                            client_sock.sendall(raw_ack)
                            print(current_index, "ACKED")
                            data_buffer[current_index]["type"] = WindowType.SEND_ACKED
                        ack_index += 1
                    update_window_size = remote_sock.recv(buffer_size)
                    client_sock.sendall(update_window_size)
                    avaliable_window = Segment.unpack_segment(update_window_size).window_size
                    window = 0


def update_options():
    while True:
        data = input(">>>")
        data_array = data.split()
        if data_array[0].lower() == "delay_data":
            global DELAY_DATA
            DELAY_DATA = data_array[1]
        elif data_array[0].lower() == "delay_ack":
            global DELAY_ACK
            DELAY_ACK = data_array[1]
        elif data_array[0].lower() == "drop_data":
            global DROP_DATA
            DROP_DATA = data_array[1]
        elif data_array[0].lower() == "drop_ack":
            global DROP_ACK
            DROP_ACK = data_array[1]


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("0.0.0.0", PORT))
        server_sock.listen(BACK_LOG)
        print("Proxy Waiting for client")
        input_thread = Thread(target=update_options, args=[])
        input_thread.start()
        while True:
            client, from_addr = server_sock.accept()
            # print(f"Connection from sender {from_addr} has been established")
            proxy_thread = Thread(target=proxy_handler, args=[client])
            # proxy_thread.daemon = True
            proxy_thread.start()


def help_msg():
    print("-p or --port to specify the listening port\n")


@app.route('/metrics')
def hello():
    return 'metrics'


def prometheus():
    app.run(host="0.0.0.0", port=5001)


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
        # graph_thread = Thread(target=prometheus, args=[])
        # graph_thread.start()
        main()
    except KeyboardInterrupt:
        print("\nExit\n")
    except Exception as e:
        print(e)
    finally:
        sys.exit()

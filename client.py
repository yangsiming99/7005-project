import sys
import socket
import json

def main():
  param = set_parameters()
  while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
      sock.settimeout(2)
      sock.connect((param["HOST"], param["PORT"]))
      toSend = input("message: \n")
      send_recv(toSend, sock)

def send_recv(msg, sock):
  complete = False
  while complete == False:
    try:
      sock.send(msg.encode())
      data = sock.recv(1024)
      print(data.decode())
      complete = True
    except socket.timeout as e:
      print(f'message: "{msg}" has timed out')

def set_parameters():
  default = {
    "PORT":5000,
    "HOST": ""
  }

  if "-h" in sys.argv:
    param = sys.argv.index("-c") + 1
    default["cert"] = sys.argv[param]
  else:
    raise "No Host Address Specified"

  if "-p" in sys.argv:
    param = sys.argv.index("-p") + 1
    default["port"] = int(sys.argv[param])
  return default

if __name__ == "__main__":
  main()
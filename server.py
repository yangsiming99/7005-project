import sys
import socket

def main():
  param = set_parameters()
  
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind((socket.gethostname(), param["PORT"]))
    sock.listen(5)

    while True:
      newsocket, fromaddr = sock.accept()
      try:
        print(f"Connection from {fromaddr} has been established")
        data = newsocket.recv(1024)
        print(data.decode())
        
        #comment out this line to test timeout
        newsocket.send(data)
      finally:
        print(f"Connection from {fromaddr} closed")

        #comment out this line to test timeout
        newsocket.close()

def set_parameters():
  default = {
    "PORT": 5000,
  }
  if "-p" in sys.argv:
    param = sys.argv.index("-p") + 1
    default["PORT"] = int(sys.argv[param])
  return default

if __name__ == "__main__":
  main()
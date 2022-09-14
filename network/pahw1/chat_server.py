import socket
import time


PORT = 8000
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ("192.168.43.131", PORT)
server_socket.bind(address)
server_socket.settimeout(10)

while True:
    try:
        now = time.time()
        receive_data, client = server_socket.recvfrom(1024)
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)))
        print("From client%s, sends%s\n" % (client, receive_data))
    except socket.timeout:
        print("tme out")

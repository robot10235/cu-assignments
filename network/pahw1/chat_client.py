import socket
import time

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
PORT = 8000

while True:
      start = time.time()
      print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start)))
      msg=input("input：")
      server_address = ("34.86.185.194", PORT)
      client_socket.sendto(msg.encode(), server_address)
      now = time.time()
      run_time = now-start
      print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)))
      print("run_time: %d seconds\n" %run_time)


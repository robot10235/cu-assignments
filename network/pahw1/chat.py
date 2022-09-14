import socket
import argparse
import threading
import time
import os
#from func_timeout import func_set_timeout

# INTERNAL_IP = '192.168.1.23' # used for test
INTERNAL_IP = '127.0.0.1'
EXTERNAL_IP = '98.15.78.142'  # used for test
REG = '0'  # REG-name-port / REG-name-ip-port
DEREG = '1'  # DEREG-name-port
WEL = '2'  # WEL-msg
ACK = '3'  # ACK-name / ACK-SAVE / ACK-DEREG / ACK-GROUP
CHAT = '4'  # CHAT-name-msg
SAVE = '5'  # SAVE-sendport-sendername-recvip-recvport-recvname-msg-timestamp / SAVE-sendername-sendmsg-time
CHECK = '6'  # CHECK
ALIVE = '7'  # ALIVE-name
ERR = '8'  # ERR-SAVE-msg / ERR-REG-msg
GROUP = '9'  # GROUP-port-msg-time / SAVE-GROUP-sendername-msg-time


class Server:
    def __init__(self, port) -> None:
        self.clients_info = {}
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind(("0.0.0.0", self.port))

    def check_recv(self, client_addr) -> None:
        self.server_socket.settimeout(1)
        try:
            msg, addr = self.server_socket.recvfrom(1024)
            msg = msg.decode()
            split_msg = msg.split('-')
            if len(split_msg) == 2 and split_msg[0] == ALIVE and (addr[0], int(split_msg[1])) == client_addr:
                self.clients_info[client_addr]['ack'] = True
        except socket.timeout:
            return

    def server_check(self, client_addr) -> bool:
        check_msg = CHECK
        self.server_socket.sendto(check_msg.encode(), client_addr)
        self.check_recv(client_addr)
        self.server_socket.settimeout(None)
        ret = self.clients_info[client_addr]['ack']
        self.clients_info[client_addr]['ack'] = False
        return ret

    def broadcast_status(self, client_addr):
        for client_info_key in self.clients_info.keys():
            if client_info_key != client_addr:
                # test
                # client_ip = client_info_key[0]
                client_ip = INTERNAL_IP
                client_port = str(client_info_key[1])
                client_name = self.clients_info[client_info_key]['name']
                client_status = self.clients_info[client_info_key]['online']
                if client_status:
                    update_msg = REG + '-' + client_name + '-' + \
                                 client_ip + '-' + client_port
                else:
                    update_msg = DEREG + '-' + client_name + '-' + \
                                 client_ip + '-' + client_port
                self.server_socket.sendto(update_msg.encode(), client_addr)

    def save_msg(self, recvip, recvport, recvname, msg, group) -> None:
        if group:
            file_name = f'group-{recvip}-{recvport}-{recvname}.txt'
        else:
            file_name = f'{recvip}-{recvport}-{recvname}.txt'
        if not os.path.isfile(file_name):
            f = open(file_name, "w")
        else:
            f = open(file_name, "a")
        f.write(msg)
        f.write('\n')
        f.close()

    def load_msg(self, recvip, recvport, recvname, group) -> None:
        if group:
            file_name = f'group-{recvip}-{recvport}-{recvname}.txt'
        else:
            file_name = f'{recvip}-{recvport}-{recvname}.txt'
        if os.path.isfile(file_name):
            f = open(file_name, 'r')
            lines = f.readlines()
            for line in lines:
                self.server_socket.sendto(line.encode(), (recvip, int(recvport)))
            f.close()
            f = open(file_name, 'w')
            f.write('')
            f.close()

    def recv_ack_group(self) -> None:
        self.server_socket.settimeout(.5)
        while True:
            try:
                msg, addr = self.server_socket.recvfrom(1024)
                msg = msg.decode()
                if len(msg.split('-')) == 2:
                    status_code, port = msg.split('-')[0], msg.split('-')[1]
                    if status_code == ACK:
                        self.clients_info[(addr[0], int(port))]['ack'] = True
            except socket.timeout:
                return

    def server_service(self) -> None:
        while True:
            # wait for client msg
            client_msg, client = self.server_socket.recvfrom(1024)
            client_msg = client_msg.decode()
            client_ip = client[0]
            status_code = client_msg.split('-')[0]
            print(client_msg)   # debug

            # register
            if status_code == REG:
                client_name, client_port = client_msg.split('-')[1], client_msg.split('-')[2]
                client_addr = (client_ip, int(client_port))

                for key, val in self.clients_info.items():
                    if val['name'] == client_name and key != client_addr:
                        err_msg = ERR + '-' + REG + '-' + 'name already exists!'
                        self.server_socket.sendto(err_msg.encode(), client_addr)

                # update table
                if not self.clients_info.get(client_addr, False):
                    self.clients_info[client_addr] = {'name': client_name, 'online': True, 'ack': False}
                else:
                    self.clients_info[client_addr]['online'] = True
                
                # broadcast and display updated table
                for client_info_key in self.clients_info.keys():
                    print(client_info_key, self.clients_info[client_info_key])
                    if self.clients_info[client_info_key]['online']:
                        self.broadcast_status(client_info_key)

                # send offline msg
                self.load_msg(client_ip, client_port, client_name, False)
                self.load_msg(client_ip, client_port, client_name, True)

                # Finally send welcome msg to register
                time.sleep(1)
                welcome_msg = WEL + '-' + 'Welcome, You are registered.'
                self.server_socket.sendto(welcome_msg.encode(), client_addr)

            # dereg
            elif status_code == DEREG:
                # update table
                client_name, client_port = client_msg.split('-')[1], client_msg.split('-')[2]
                client_addr = (client_ip, int(client_port))
                self.clients_info[client_addr]['online'] = False

                # broadcast updated table
                for client_info_key in self.clients_info.keys():
                    print(client_info_key, self.clients_info[client_info_key])
                    if self.clients_info[client_info_key]['online']:
                        self.broadcast_status(client_info_key)

                # send ACK
                ACK_DEREG_msg = ACK + '-' + DEREG
                self.server_socket.sendto(ACK_DEREG_msg.encode(), client_addr)

            # save offline msg
            elif status_code == SAVE:
                split_msg = client_msg.split('-')
                sendport = split_msg[1]
                sender_name = split_msg[2]
                recvip = split_msg[3]
                recvport = split_msg[4]
                recvname = split_msg[5]
                sendmsg = split_msg[6]
                sendtime = split_msg[7]
                is_online = self.server_check((recvip, int(recvport)))

                if is_online:
                    err_msg = ERR + '-' + SAVE + '-' + f'Client {recvname} exists!!'
                    self.server_socket.sendto(err_msg.encode(), (client_ip, int(sendport)))
                    self.broadcast_status((client_ip, int(sendport)))
                else:
                    ack_msg = ACK + '-' + SAVE
                    self.server_socket.sendto(ack_msg.encode(), (client_ip, int(sendport)))
                    save_msg = SAVE + '-' + sender_name + '-' + sendmsg + '-' + sendtime
                    self.save_msg(recvip, recvport, recvname, save_msg, False)

            elif status_code == GROUP:
                sender_port = client_msg.split('-')[1]
                sender_msg = client_msg.split('-')[2]
                send_time = client_msg.split('-')[3]
                sender_addr = (client_ip, int(sender_port))
                if not self.clients_info.get(sender_addr, False):
                    print('invalid client')
                else:
                    groupchat_ack = ACK + '-' + GROUP
                    self.server_socket.sendto(groupchat_ack.encode(), sender_addr)

                    # broadcast
                    sender_name = self.clients_info[sender_addr]['name']
                    for client_info_key in self.clients_info.keys():
                        if client_info_key != sender_addr and self.clients_info[client_info_key]['online']:
                            group_msg = GROUP + '-' + sender_name + '-' + sender_msg
                            self.server_socket.sendto(group_msg.encode(), client_info_key)

                    self.recv_ack_group()
                    self.server_socket.settimeout(None)

                    save_group_msg = SAVE + '-' + GROUP + '-' + sender_name + '-' + sender_msg + '-' + send_time
                    # check and save offline group msg
                    for client_info_key in self.clients_info.keys():
                        if client_info_key != sender_addr:
                            if not self.clients_info[client_info_key]['online']:
                                self.save_msg(client_info_key[0], str(client_info_key[1]),
                                              self.clients_info[client_info_key]['name'], save_group_msg, True)
                            elif not self.clients_info[client_info_key]['ack']:
                                if not self.server_check(client_info_key):
                                    self.save_msg(client_info_key[0], str(client_info_key[1]),
                                                  self.clients_info[client_info_key]['name'], save_group_msg, True)
                            else:
                                self.clients_info[client_info_key]['ack'] = False


class Client:
    def __init__(self, client_name, server_ip, server_port, client_port) -> None:
        self.other_clients_info = {}
        self.client_name = client_name
        self.client_port = client_port
        self.server_ip = server_ip
        self.server_port = server_port
        self.offline = False
        self.groupchat_ack = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind(('0.0.0.0', self.client_port))
        self.offline_flag = False
        self.save_ack = False

    def Chat(self, name, msg) -> None:
        current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        flag = False
        # send to yourself
        if name == self.client_name:
            print('>>> [From ' + name + ': ' + msg + ']')
        else:
            for addr, info in self.other_clients_info.items():
                if info['name'] == name:
                    flag = True
                    break
            if flag:
                if self.other_clients_info[addr]['online']:
                    chat_msg = CHAT + '-' + self.client_name + '-' + msg
                    self.client_socket.sendto(chat_msg.encode(), addr)
                    time.sleep(0.5)
                    if self.other_clients_info[addr]['ACK']:
                        self.other_clients_info[addr]['ACK'] = False
                        print(f'>>> [Message received by {name}.]')
                        return
                    else:
                        print(f'>>> [No ACK from {name}, message sent to server.]')
                else:
                    print(f'>>> [{name} is offline, message sent to server]')

                for i in range(5):
                    # recvip = addr[0]
                    recvip = EXTERNAL_IP  # test
                    recvport = addr[1]
                    save_msg = SAVE + '-' + str(self.client_port) + '-' + self.client_name + '-' + \
                            recvip + '-' + str(recvport) + '-' + name + '-' + msg + '-' + current_time
                    self.client_socket.sendto(save_msg.encode(), (self.server_ip, self.server_port))
                    time.sleep(.5)
                    if self.save_ack:
                        self.save_ack = False
                if not self.save_ack:
                    print('>>> [Server is down.]')
            else:
                print(f'>>> [{name} does not exist]')

    def Dereg(self) -> None:
        dereg_msg = DEREG + '-' + self.client_name + '-' + str(self.client_port)
        for i in range(5):
            self.client_socket.sendto(dereg_msg.encode(), (self.server_ip, self.server_port))
            time.sleep(.5)
            if self.offline:
                break
        # have not received ACK
        if not self.offline:
            self.offline = True
            print('>>> [Server not responding]')
            print('>>> [Existing]')
        else:
            print('>>> [You are Offline. Bye.]')

    def Groupchat(self, msg) -> None:
        current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        group_msg = GROUP + '-' + str(self.client_port) + '-' + msg + '-' + current_time
        for i in range(5):
            self.client_socket.sendto(group_msg.encode(), (self.server_ip, self.server_port))
            time.sleep(.5)
            if self.groupchat_ack:
                break
        if self.groupchat_ack:
            print('>>> [Message received by Server.]')
            self.groupchat_ack = False
        else:
            print('>>> [Server not responding.]')

    def Reg(self, name) -> None:
        self.client_name = name
        self.offline_flag = False
        time.sleep(1)
        reg_msg = REG + '-' + self.client_name + '-' + str(self.client_port)
        self.client_socket.sendto(reg_msg.encode(), (self.server_ip, self.server_port))

    def Recv(self) -> None:
        while True:
            # stop recv msg but still ready to recv when reg
            while self.offline:
                return

            msg, addr = self.client_socket.recvfrom(1024)
            msg = msg.decode()
            status_code = msg.split('-')[0]
            print('\n>>> ')

            # msg send from server
            if addr[0] == self.server_ip:
                # update online client info
                if status_code == REG:
                    client_name = msg.split('-')[1]
                    client_ip = msg.split('-')[2]
                    client_port = msg.split('-')[3]
                    client_addr = (client_ip, int(client_port))
                    self.other_clients_info[client_addr] = {'name': client_name, 'online': True, 'ACK': False}
                    print('>>> [Client table updated.]')

                # update offline client info
                elif status_code == DEREG:
                    client_name = msg.split('-')[1]
                    client_ip = msg.split('-')[2]
                    client_port = msg.split('-')[3]
                    client_addr = (client_ip, int(client_port))
                    self.other_clients_info[client_addr] = {'name': client_name, 'online': False, 'ACK': False}
                    print('>>> [Client table updated.]')

                elif status_code == ACK:
                    # dereg ack from server
                    if msg.split('-')[1] == DEREG:
                        self.offline = True
                    # save offline msg ack from server
                    elif msg.split('-')[1] == SAVE:
                        self.save_ack = True
                        print('>>> [Messages received by the server and saved]')
                    # group msg ack from server
                    elif msg.split('-')[1] == GROUP:
                        self.groupchat_ack = True

                # server check client alive
                elif status_code == CHECK:
                    alive_msg = ALIVE + '-' + str(self.client_port)
                    self.client_socket.sendto(alive_msg.encode(), (self.server_ip, self.server_port))

                # one client is still alive
                elif status_code == ERR:
                    err_status, err_msg = msg.split('-')[1], msg.split('-')[2]
                    if err_status == SAVE:
                        print(f'>>> [{err_msg}]')
                    elif err_status == REG:
                        self.offline = True
                        print(f'>>> [{err_msg}]')
                        print('>>> [Please use reg <new_name> to register again]')

                # offline msg 
                elif status_code == SAVE:
                    if not self.offline_flag:
                        print('>>> [You have messages]')
                        self.offline_flag = True
                    if len(msg.split('-')) == 5 and msg.split('-')[1] == GROUP:
                        sender_name, sender_msg, send_time = msg.split('-')[2], msg.split('-')[3], msg.split('-')[4]
                        print(f'>>> [Channel_Message {sender_name}: {send_time} {sender_msg}].')
                    else:
                        sender_name, sender_msg, send_time = msg.split('-')[1], msg.split('-')[2], msg.split('-')[3]
                        print(f'>>> [{sender_name}: {send_time} {sender_msg}]')

                        # welcome msg
                elif status_code == WEL:
                    print('>>> [' + msg[2:] + ']')

                # group offline msg
                elif status_code == GROUP:
                    ack_msg = ACK + '-' + str(self.client_port)
                    self.client_socket.sendto(ack_msg.encode(), (self.server_ip, self.server_port))
                    sender_name = msg.split('-')[1]
                    sender_msg = msg.split('-')[2]
                    print(f'>>> [Channel_Message {sender_name}: {sender_msg} ].')

            # msg send from client
            else:
                name = msg.split('-')[1]
                if status_code == ACK:
                    for key, value in self.other_clients_info.items():
                        if value['name'] == name and key == addr:
                            self.other_clients_info[key]['ACK'] = True
                            break
                elif status_code == CHAT:
                    for key, value in self.other_clients_info.items():
                        if value['name'] == name and key == addr:
                            ack_msg = ACK + '-' + self.client_name
                            self.client_socket.sendto(ack_msg.encode(), key)
                            break
                    print('\n>>> [From ' + name + ': ' + msg.split('-')[2] + ']')
            print('>>>', end=' ', flush=True)
            time.sleep(1)

    def Main(self) -> None:
        threading.Thread(target=self.Recv).start()
        while True:
            cmd = input('>>> ')
            if cmd == '':
                continue
            func = cmd.split()[0]
            if self.offline:
                if func == 'reg':
                    if len(cmd.split()) <= 1:
                        print('\n>>> [no nickname]')
                    else:
                        self.offline = False
                        threading.Thread(target=self.Recv).start()
                        self.Reg(cmd.split()[1])
                else:
                    print('\n>>> [You are offline, register first]')
            else:
                if func == 'chat':
                    if len(cmd.split()) < 2:
                        print('\n>>> [no receiver name or msg]')
                    else:
                        recv_name, send_msg = cmd.split(' ', 2)[1], cmd.split(' ', 2)[2]
                        self.Chat(recv_name, send_msg) 
                elif func == 'dereg':
                    self.Dereg()
                elif func == 'send_all' and len(cmd.split()) == 2:
                    self.Groupchat(cmd.split(' ', 1)[1])
                else:
                    print('\n>>> [invalid command.]')
            time.sleep(1)


# check whether given ip is valid
def is_valid_ip(ip):
    dot_cnt = 0
    num = ""
    for char in ip:
        if char == '.':
            if len(num) == 0:
                return False
            if len(num) > 1 and num[0] == '0':
                return False
            if int(num) < 0 or int(num) > 255:
                return False
            num = ""
            dot_cnt += 1
            if dot_cnt > 3:
                return False
        elif ord('0') <= ord(char) <= ord('9'):
            num += char
        else:
            return False
    return True


def server_init(server_args):
    port = server_args.server
    if 1024 <= port <= 65535:
        server = Server(port)
        server.server_service()
    else:
        ex = Exception('invalid port number')
        raise ex


def client_init(client_args):
    if len(client_args.client) == 4:
        client_name, server_ip = client_args.client[0], client_args.client[1]
        if is_valid_ip(server_ip):
            server_port, client_port = int(client_args.client[2]), int(client_args.client[3])
            if 1024 <= server_port <= 65535 and 1024 <= client_port <= 65535:
                client = Client(client_name, server_ip, server_port, client_port)
                client.Reg(client_name)
                client.Main()
            else:
                ex = Exception('invalid port')
                raise ex
        else:
            ex = Exception('invalid ip')
            raise ex
    else:
        ex = Exception('need 4 arguments')
        raise ex


if __name__ == "__main__":
    try:
        # pass argument
        parser = argparse.ArgumentParser(description='registration')
        # choose mode server/client
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("-s", "--server", type=int,
                           help='server mode, only needs one server-port argument')
        group.add_argument("-c", "--client", action="extend", nargs="+",
                           help='client mode, needs 4 arguments: client name, server ip, server port, client port. Port number is valid in 1024-65535')
        args = parser.parse_args()
        if args.server:
            server_init(args)
        else:
            client_init(args)
    except Exception as re:
        print(re)

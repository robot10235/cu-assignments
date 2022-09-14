from concurrent.futures import thread
import socket
import random
import argparse
import threading
import time

DV = "0"
LINK = "1"
INF = 1000000
ROUTING_INTERVAL = 30

class DistanceVector:
    def __init__(self, args) -> None:
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.poisoned = False
        self.port = int(args[3])
        self.listen_socket.bind(("0.0.0.0", self.port))
        self.routing_table = {}
        self.neighbors_dv = {}
        self.cost_link = {}
        self.cost_change = 0
        self.cost_flag = False
        self.send_times = 0
        if args[1] == "p":
            self.poisoned = True
        for i in range(4, len(args)-1, 2):
            if args[i] == "last":
                i += 1
                break
            self.routing_table[int(args[i])] = {"distance": int(args[i+1]), "nexthop": int(args[i])}
            self.cost_link[int(args[i])] = int(args[i+1])
            self.neighbors_dv[int(args[i])] = {int(args[i]): 0}
        self.routing_table[self.port] = {"distance": 0}
        if i == len(args)-1 and args[i] != "last":
            self.cost_change = int(args[i])
            self.cost_flag = True
    
    
    def print_routing_table(self) -> None:
        # show routing table through self.routing table
        current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print("[" + current_time + "]" + " " + f"Node {self.port} Routing Table")
        for key in self.routing_table.keys():
            if key == self.port:
                continue
            dist = self.routing_table[key]["distance"]
            print(f"- ({dist}) -> Node {key}", end="")
            if "nexthop" in self.routing_table[key].keys():
                nexthop = self.routing_table[key]["nexthop"]
                if nexthop != key:
                    print(f"; Next hop -> Node {nexthop}", end="")
            print("")


    def update_neighbors_dv(self, neighbor_dv, neighbor_port) -> None:
        for i in range(0, len(neighbor_dv), 2):
            target = int(neighbor_dv[i])
            # the routing table can be also updated to know non neighbor nodes
            if target not in self.routing_table.keys():
                self.routing_table[target] = {}
                self.routing_table[target]["distance"] = INF
            self.neighbors_dv[neighbor_port][target] = int(neighbor_dv[i+1])        
        if self.send_times == 0:
            self.send_times = 1
            self.send_dv()     
        self.compute()


    def compute(self) -> None:
        change = False  # after compution determine if the routing table has been changed
        for node in self.routing_table.keys():
            if node == self.port:
                continue
            temp = self.routing_table[node]["distance"]
            self.routing_table[node]["distance"] = INF
            # bellman-ford
            for neighbor in self.neighbors_dv.keys():
                if node in self.neighbors_dv[neighbor].keys():
                    if self.routing_table[node]["distance"] > self.neighbors_dv[neighbor][node] + self.cost_link[neighbor]:
                        self.routing_table[node]["distance"] = self.neighbors_dv[neighbor][node] + self.cost_link[neighbor]           
                        self.routing_table[node]["nexthop"] = neighbor
            if temp != self.routing_table[node]["distance"]:
                change = True
        self.print_routing_table()             
        if change:
            self.send_dv()
        

    def send_dv(self) -> None:
        # send dv through routing table
        if self.poisoned:
            # poisoned reverse mode, needs to seed inf if next hop is the recver
            for neighbor_port in self.cost_link.keys():
                msg = DV
                for nodes in self.routing_table.keys():
                    msg += "-"
                    msg += str(nodes)
                    msg += "-"
                    if nodes != neighbor_port and "nexthop" in self.routing_table[nodes].keys() \
                        and self.routing_table[nodes]["nexthop"] == neighbor_port:
                        msg += str(INF)
                    else:
                        msg += str(self.routing_table[nodes]["distance"])
                self.listen_socket.sendto(msg.encode(), ("127.0.0.1", neighbor_port))
                current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print("[" + current_time + "]" + " " + f"Message sent from Node {self.port} to Node {neighbor_port}")
        else:
            msg = DV
            for key in self.routing_table.keys():
                msg += "-"
                msg += str(key)
                msg += "-"
                msg += str(self.routing_table[key]["distance"])
            for port in self.cost_link.keys():
                self.listen_socket.sendto(msg.encode(), ("127.0.0.1", port))
                current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                print("[" + current_time + "]" + " " + f"Message sent from Node {self.port} to Node {port}")


    def service(self) -> None:
        # main function of the node, used for recv msg and run sub function
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)
            msg = msg.decode().split('-')
            current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            if msg[0] == DV:
                print("[" + current_time + "]" + " " + f"Message received at Node {self.port} from Node {addr[1]}")
                t1 = threading.Thread(target=self.update_neighbors_dv, args=(msg[1:], addr[1]))
                t1.start()                
            elif msg[0] == LINK:
                print("[" + current_time + "]" + " " + f"Link value message received at Node {self.port} from Node {addr[1]}")
                self.cost_link[addr[1]] = int(msg[1])
                self.compute()
            time.sleep(1)


    def change_cost(self) -> None:
        time.sleep(30)
        if self.cost_flag:
            highest_port = max(self.cost_link.keys())
            self.cost_link[highest_port] = self.cost_change
            current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print("[" + current_time + "]" + " " + f" Node {highest_port} cost updated to {self.cost_change}")
            msg = LINK + "-" + str(self.cost_change)
            self.listen_socket.sendto(msg.encode(), ("127.0.0.1", highest_port))
            print("[" + current_time + "]" + " " + f"Link value message sent from Node {self.port} to Node {highest_port}")
            self.compute()


class LinkState:
    def __init__(self, args) -> None:
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = int(args[3])
        self.listen_socket.bind(("0.0.0.0", self.port))
        self.routing_table = {}
        self.cost_link = {}
        self.network_topology = {}
        self.cost_change = 0
        self.cost_flag = False
        self.update_interval = int(args[2])
        self.seq = 0
        self.send_LSA = False
        self.compute_first = True
        self.wait2compute_start = False
        self.cost_change = 0
        self.cost_flag = False
        for i in range(4, len(args)-1, 2):
            if args[i] == "last":
                i += 1
                break
            self.routing_table[int(args[i])] = {"distance": int(args[i+1]), "nexthop": int(args[i]), "seq": 0}
            self.cost_link[int(args[i])] = int(args[i+1])
            self.network_topology[(min(self.port, int(args[i])), max(self.port, int(args[i])))] = int(args[i+1])
        if i == len(args)-1 and args[i] != "last":
            self.cost_change = int(args[i])
            self.cost_flag = True


    def LSA(self) -> None:
        # send LSA msg through cost_link
        msg = str(self.port) + "-" + str(self.seq)
        self.seq += 1
        for key in self.cost_link.keys():
            msg += "-"
            msg += str(key)
            msg += "-"
            msg += str(self.cost_link[key])
        for neighbor in self.cost_link.keys():
            self.listen_socket.sendto(msg.encode(), ("127.0.0.1", neighbor))        


    def broadcast_LSA(self) -> None:
        # continuously send LSA
        self.send_LSA = True    # notify that the broadcast_LSA has been set up
        while(1):
            self.LSA()
            random.seed()
            time.sleep(self.update_interval + random.random())


    def update_network_topology(self, msg) -> None:
        change = False
        msg_split = msg.split('-')
        send_port, seq = int(msg_split[0]), int(msg_split[1])
        for i in range(2, len(msg_split), 2):
            cur_port = int(msg_split[i])
            edge = (min(send_port, cur_port), max(send_port, cur_port))
            if not self.network_topology.get(edge) or self.network_topology[edge] != int(msg_split[i+1]):
                self.network_topology[edge] = int(msg_split[i+1])
                change = True
            if not self.routing_table.get(cur_port):
                self.routing_table[cur_port] = {"distance": INF, "seq": 0}
        # flooding
        for neighbor in self.cost_link.keys():
            if neighbor != send_port:
                self.listen_socket.sendto(msg.encode(), ("127.0.0.1", neighbor))
        # self.compute_first is the permission of the first computation
        if change and not self.compute_first:
            self.compute()


    def compute(self) -> None:
        vertices = set(self.routing_table.keys())
        # initialization
        for vetex in vertices:
            if self.cost_link.get(vetex):
                self.routing_table[vetex]["distance"] = self.cost_link[vetex]
            else:
                self.routing_table[vetex]["distance"] = INF
        # Loop
        while len(vertices) > 0:
            min_dist = INF
            min_vertex = self.port
            for vertex in vertices:
                if min_dist > self.routing_table[vertex]["distance"]:
                    min_dist = self.routing_table[vertex]["distance"]
                    min_vertex = vertex
            vertices.remove(min_vertex)
            for vertex in vertices:
                vertex_edge = (min(vertex, min_vertex), max(vertex, min_vertex))
                if self.network_topology.get(vertex_edge):
                    if self.routing_table[vertex]["distance"] > self.routing_table[min_vertex]["distance"] + self.network_topology[vertex_edge]:
                        self.routing_table[vertex]["distance"] = self.routing_table[min_vertex]["distance"] + self.network_topology[vertex_edge]
                        self.routing_table[vertex]["nexthop"] = self.routing_table[min_vertex]["nexthop"]
        self.print_routing_table()


    def print_routing_table(self) -> None:
        current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        print("[" + current_time + "]" + " " + f"Node {self.port} Routing Table")
        for key in self.routing_table.keys():
            if key == self.port:
                continue
            dist = self.routing_table[key]["distance"]
            print(f"- ({dist}) -> Node {key}", end="")
            if "nexthop" in self.routing_table[key].keys():
                nexthop = self.routing_table[key]["nexthop"]
                if nexthop != key:
                    print(f"; Next hop -> Node {nexthop}", end="")
            print("")


    def service(self) -> None:
        while True:
            msg, addr = self.listen_socket.recvfrom(1024)
            msg = msg.decode()
            # set timer for the first computation
            if not self.wait2compute_start:
                self.wait2compute_start = True
                t0 = threading.Thread(target=routenode.wait2compute)
                t0.start()
            # ready for the broadcast LSA
            if not self.send_LSA:
                #self.send_LSA = True
                t1 = threading.Thread(target=self.broadcast_LSA)
                t1.start()

            if msg.split('-')[0] == LINK:
                print("[" + current_time + "]" + " " + f"Link value message received at Node {self.port} from Node {addr[1]}")
                self.cost_link[addr[1]] = int(msg.split('-')[1])
                self.network_topology[(min(addr[1], self.port), max(addr[1], self.port))] = int(msg.split('-')[1])
                # when link cost changes, need to send LSA msg immediately
                self.LSA()
                self.compute()
            else:
                LSA_node = int(msg.split('-')[0])
                LSA_seq = int(msg.split('-')[1])
                current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
                # PI algorithm, drop duplicate LSA packet
                if self.routing_table[LSA_node]["seq"] > LSA_seq:
                    print(f'[{current_time}] DUPLICATE LSA packet Received, AND DROPPED:')
                    print(f'- LSA of node {LSA_node}') 
                    print(f'- Sequence number {LSA_seq}')
                    print(f'- Received from {addr[1]}')
                else:
                    print(f'[{current_time}] LSA of Node {LSA_node} with sequence number {LSA_seq} received from Node {addr[1]}')
                    self.routing_table[LSA_node]["seq"] += 1
                    t2 = threading.Thread(target=self.update_network_topology, args=(msg,))
                    t2.start()
            time.sleep(.5)


    def wait2compute(self) -> None:
        time.sleep(ROUTING_INTERVAL)
        self.compute()
        self.compute_first = False


    def change_cost(self) -> None:
        time.sleep(1.2*ROUTING_INTERVAL)
        if self.cost_flag:
            highest_port = max(self.cost_link.keys())
            self.cost_link[highest_port] = self.cost_change
            self.network_topology[(min(highest_port , self.port), max(highest_port, self.port))] = self.cost_change
            current_time = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
            print("[" + current_time + "]" + " " + f"Node {highest_port} cost updated to {self.cost_change}")
            msg = LINK + "-" + str(self.cost_change)
            self.listen_socket.sendto(msg.encode(), ("127.0.0.1", highest_port))
            print("[" + current_time + "]" + " " + f"Link value message sent from Node {self.port} to Node {highest_port}")
            # when link cost changes, need to send LSA msg immediately
            self.LSA()
            self.compute()




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='routenode')
    parser.add_argument("all", nargs="+", type=str)
    args = parser.parse_args().all

    if len(args) < 6:
        raise TypeError("Not enough arguments")
    
    # check integer argument
    try:
        local_port = int(args[3])
    except:
        raise TypeError("invalid local port number")
    if local_port < 1024:
        raise TypeError("invalid local port number")
    for i in range(4, len(args)-1, 2):
        if args[i] == "last":
            i += 1
            break
        if args[i+1] == "last":
            raise TypeError("missing neighbor cost")
        try:
            neighbor_port = int(args[i])
        except:
            raise TypeError("invalid neighbor port number")
        if neighbor_port < 1024:
            raise TypeError("invalid neighbor port number")
        try:
            cost = int(args[i+1])
        except:
            raise TypeError("invalid neighbor cost")
    if i == len(args)-1 and args[i] != "last":
        try:
            int(args[i])
        except:
            raise TypeError("invalid cost change") 

    if (args[1] == "r" or args[1] == "p") and args[0] == "dv":
        routenode = DistanceVector(args)
        routenode.print_routing_table()
        if args[-2] == "last":
            t1 = threading.Thread(target=routenode.change_cost)
            t1.start()
            t2 = threading.Thread(target=routenode.send_dv)
            t2.start()
        elif args[-1] == "last":
            t3 = threading.Thread(target=routenode.send_dv)
            t3.start()
        routenode.service()
    elif args[1] == "r" and args[0] == "ls":
        try:
            if int(args[2]) > 5:
                raise TypeError("invalid update interval time")
        except:
            raise TypeError("invalid update interval") 
        routenode = LinkState(args)    
        routenode.print_routing_table()
        if args[-2] == "last":
            t1 = threading.Thread(target=routenode.change_cost)
            t1.start()
            t2 = threading.Thread(target=routenode.broadcast_LSA)
            t2.start()
        if args[-1] == "last":
            t4 = threading.Thread(target=routenode.broadcast_LSA)
            t4.start()
        routenode.service()
    else:
        raise TypeError("arguments error")


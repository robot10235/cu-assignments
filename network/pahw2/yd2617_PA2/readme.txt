This is a simple routing protocols emulation program.
The emulation routing algorithms are distance vector and link. In particular, distance vector protocol has two modes. One is regular and the other one is Poisoned Reverse. 
Link cost change that results in count to infinity under the regular mode should not result in count to infinity under Poisoned Reverse.


To implement the distance vector algorithm, we need to use a map(dictionary) to store neighbor links weights, a map to store routing table for every node and a map to store neighbors distance vectors.
We can see that the routine table is actually to be the distance vector. For every node, we set one variable send_times to zero to notify whether the node has sent its distance vector at most once.
When the last node has been initialized, the program would send its distance vector to its neighbors. Its neighbors would receive the message, update the neighbors distance vectors
and try to modify its distance vector. If the distance vector has been changed or the send_times is still zero, the node need to send its distance vector to its neighbors. 

For Poisoned Reverse, the key is that when sending the distance vector, the node needs to find whether the for every destination node, except the receiver, the next hop is the receiver. 
If it is, it needs to advertise the receiver that the distance is infinity, otherwise, it would advertise the receiver the true distance.

For Bellman-Ford algorithm, since we have stored the neighbor link weights and the neighbors distance vectors, we can directly use the BF equation.

To implement the link state algorithm, we need to use a map to store neighbor links weights, a map to store routing table for every node and a map to store the network topology.
We can see that LSA is the neight links weights. When the last node is initialized, it would send its LSA to its neighbors, the neightbors would received the LSA,  broadcast it,
update the network topology and send their LSAs if they haven't started to send. In order to make sure the whole network topology has been received, we set large ROUTING_INTERVAL.
After the last node has been initialized, after ROUTING_INTERVAL seconds, the node would compute the routing table automatically. Changing the network topology would also make the 
node to compute the routing table.

For Flooding Mechanism - PI Algorithm, my idea is that for every LSA, we use (Node port,seq) to identify it. If the node has already received the LSA, it would not broadcast it.
(Node port,seq) is recorded in the routing table. For every node, every time it finds a new node, it would set the sequence number to zero. When receiving a LSA, the node would first find
whether the (Node port,seq) has been received, if the LSA is new, it would add the sequence number of the node port by 1. This design would make sure the PI algorithm run properly.

For Dijkstra's algorithm, since we have the whole network topology, we can directly use the Dijksra's algorithm in every node.

The command syntax is:
$ routenode <dv/ls> <r/p> <update-interval> <local-port> <neighbor1-port> <cost-1> <neighbor2-port> <cost-2> ... [last][<cost-change>]

<dv/ls>    Run distance vector or link state algorithm.
<r/p>    Run regular mode or Poisoned Reverse mode in distance vector algorithm. Run only regular mode in link state algorithm.
<update-interval>    Node LSA broadcast period (1-5) seconds
<local-port>    The UDP listening port number (1024-65534) of the node.
<neighbor#>    port The UDP listening port number (1024-65534) of one of the neighboring nodes.
<cost#>    This will be used as the link distance to the neighbor#-port. It is an integer that and represents the cost/weight of the link.
[last]    Indication of the last node information of the network. Upon the input of the command with this argument, the routing message exchanges among the nodes should kick in.
[cost-change]    Indication of the new cost that will be assigned to the link between the last node and its neighbor with the highest port number. 



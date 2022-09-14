## test results	yd2617 Yuning Ding

### Test-case 1

> 1. start server
> 2. start client x(the table should be sent from server to x)
> 3. start client y(the table should be sent from server to x and y)
> 4. start client z(the table should be sent from server to x and y and z)
> 5. chat x -> y, y->z, ... , x ->z (All combinations)
> 6. dereg x (the table should be sent to y, z. x should receive ’ack’)
> 7. chat y->x (this should fail and message should be sent to server, and message has to be saved for x in the
>    server)
> 8. chat z->x (same as above)
> 9. reg x (messages should be sent from server to x, x’s status has to be broadcasted to all the other clients)
> 10. x, y, z : exit



### result

Server will print the message it would received and the clients table. As we can see the table was correct during the test. They could chat each other correctly. And after x registered, it could receive the correct message with timestamp.

![test1_start_chat](C:\Users\28562\Desktop\test1_start_chat.png)

![test1_dereg_chat](C:\Users\28562\Desktop\test1_dereg_chat.png)





### test2

> 1. start server
> 2. start client x (the table should be sent from server to x )
> 3. start client y (the table should be sent from server to x and y)
> 4. dereg y
> 5. server exit
> 6. send message x-> y (will fail with both y and server, so should make 5 attempts and exit)



### result

We could see that x could not find y and the server. It printed 'Server is down.'. Although no information shown in the cmd, x sent message to the server for saving the offline message 5 times. However, server was down and it could not receive them.

![test2](C:\Users\28562\Desktop\test2.png)





### test3

> 1. start server 
>
> 2. start client x (the table should be sent from server to x ) 
> 3. start client y (the table should be sent from server to x and y)
> 4. start client z (the table should be sent from server to x , y and z) 
> 5. send group message x-> y,z



### result

We can see that x sent the group message successfully.

![test3](C:\Users\28562\Desktop\test3.png)
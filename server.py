import socket
import sys
from _thread import *
import threading
#from signal import signal, SIGPIPE, SIG_DFL 
#Ignore SIG_PIPE and don't throw exceptions on it... (http://docs.python.org/library/signal.html)
#signal(SIGPIPE,SIG_DFL)

host = '127.0.0.1'  # Standard loopback interface address (localhost)
port_number = 40001  # Port to listen on (non-privileged ports are > 1023)
#thread_count = 0
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
username_list = {}
user_message_list = {}

def username_check(username):
    return username.isalnum()

def server_data_check(data):
    # SEND [recipient username] Content-length: [length] [message of length given in the header above]
    data_list = []
    st=0
    count = 0
    for i in range(len(data)):
        if(data[i]==" "):
            count+=1
            data_list.append(data[st:i])
            st=i+1
            if(count==4):
                break
    if(data_list[0]!="SEND" or data_list[2]!="Content-length:" or (len(data)-st)!=int(data_list[3])):
        return (False, data_list)
    data_list.append(data[st:])
    print(data_list)
    return (True, data_list)

def brodcast_message(connection, from_username, message_to_sent):
    sucess = True
    for key in username_list:
        if key!= from_username:
            username_list[key].sendall(str.encode(message_to_sent))
            data_recv = username_list[key].recv(2048)
            while(not data_recv):
                #username_list[key].sendall(str.encode(reply))
                data_recv = username_list[key].recv(2048)
            data = data_recv.decode('utf-8')
            if(data[:5]=="ERROR"):
                reply = "ERROR 102 Unable to send\n\n"
                connection.sendall(str.encode(reply))
                sucess = False
                break
    if(sucess):
        connection.sendall(str.encode("SEND all\n\n"))
    return

def threaded_client(connection):
    data_recv = connection.recv(1024)
    while(not data_recv):
        data_recv = connection.recv(1024)
    data = data_recv.decode('utf-8')
    if(data[:11]=="REGISTER TO" and len(data)>=19):
        username = data[16:len(data)-2]
        res = username_check(username)
        if(not res):
            reply = "ERROR 100 Malformed username\n\n"
            connection.sendall(str.encode(reply))
    else:
        reply = "ERROR 101 No user registered\n\n"
        connection.sendall(str.encode(reply))
        res = False
    while(not res):
        data_recv = connection.recv(1024)
        while(not data):
            data_recv = connection.recv(1024)
        data = data_recv.decode('utf-8')
        if(data[:11]=="REGISTER TO" and len(data)>=19):
            username = data[16:len(data)-2]
            res = username_check(username)
            if(not res):
                reply = "ERROR 100 Malformed username\n\n"
                connection.sendall(str.encode(reply))
        else:
            reply = "ERROR 101 No user registered\n\n"
            connection.sendall(str.encode(reply))
            res = False
    if(data[:15] == "REGISTER TOSEND"):
        reply = "REGISTERED TOSEND "+username+"\n\n"
        connection.sendall(str.encode(reply))
        ###
        while True:
            data_recv = connection.recv(2048)
            if(data_recv):
                data = data_recv.decode('utf-8')
                (correct, data_list) = server_data_check(data)
                if(correct):
                    #FORWARD [sender username] Content-length: [length] [message of length given in the header above]
                    if(data_list[1]=="all"):
                        message_to_sent = "FORWARD "+username+" Content-length: "+data_list[3]+" "+data_list[4]
                        start_new_thread(brodcast_message, (connection, username, message_to_sent,))
                    else:
                        if data_list[1] in username_list:
                            reply = "FORWARD "+username+" Content-length: "+data_list[3]+" "+data_list[4]
                            username_list[data_list[1]].sendall(str.encode(reply))
                            data_recv = username_list[data_list[1]].recv(2048)
                            while(not data_recv):
                                #username_list[data_list[1]].sendall(str.encode(reply))
                                data_recv = username_list[data_list[1]].recv(2048)
                            data = data_recv.decode('utf-8')
                            if(data[:9]=="ERROR 103"):
                                reply = "ERROR 102 Unable to send\n\n"
                                connection.sendall(str.encode(reply))
                                username_list[data_list[1]].close()
                                del username_list[data_list[1]]
                                ####doubt###
                            else:
                                print(data)
                                connection.sendall(str.encode("SEND "+data_list[1]+"\n\n"))
                        else:
                            reply = "ERROR 102 Unable to send\n\n"
                            connection.sendall(str.encode(reply))
                else:
                    reply = "ERROR 103 Header Incomplete\n\n"
                    connection.sendall(str.encode(reply))
                    connection.close()
                    if username in username_list:
                        del username_list[username]
                    return
        ###
    elif(data[:15] == "REGISTER TORECV"):
        reply = "REGISTERED TORECV "+username+"\n\n"
        connection.sendall(str.encode(reply))
        username_list[username] = connection
        user_message_list[username] = []
        #thread_count-=1
        return
    else:
        reply = "ERROR 101 No user registered\n\n"
        connection.sendall(str.encode(reply))

if __name__ == '__main__':
    try:
        server_socket.bind((host, port_number))
    except socket.error as e:
        print(str(e))

    server_socket.listen()

    while True:
        client, address = server_socket.accept()
        print('Connected to: ' + address[0] + ':' + str(address[1]))
        start_new_thread(threaded_client, (client, ))
        #thread_count += 1

    server_socket.close()
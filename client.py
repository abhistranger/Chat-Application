import socket
import sys
from _thread import *
import threading
#from signal import signal, SIGPIPE, SIG_DFL 
#Ignore SIG_PIPE and don't throw exceptions on it... (http://docs.python.org/library/signal.html)
#signal(SIGPIPE,SIG_DFL)

def registrationcs(socketn, username):
    socketn.send(str.encode('REGISTER TOSEND '+username+"\n\n"))
    data_recv = socketn.recv(1024)
    while(not data_recv):
        data_recv = connection.recv(1024)
    data = data_recv.decode('utf-8')
    if(data[:6]=="ERROR"):
        print(data)
        sys.exit(1)
    print(data)
    return

def registrationsc(socketn, username):
    socketn.send(str.encode('REGISTER TORECV '+username+"\n\n"))
    data_recv = socketn.recv(1024)
    while(not data_recv):
        data_recv = connection.recv(1024)
    data = data_recv.decode('utf-8')
    if(data[:6]=="ERROR"):
        print(data)
        sys.exit(1)
    print(data)
    return

def parse_send_message(mess):
    if(mess[0]!="@"):
        return (False, [])
    message_list = []
    for i in range(len(mess)):
        if(mess[i]==" "):
            message_list.append(mess[1:i])
            break
    message_list.append(mess[i+1:])
    return (True, message_list)


def send_to_server(connection):
    # SEND [recipient username] Content-length: [length] [message of length given in the header above]
    while True:
        a= sys.stdin.readline()
        if(a[-1]=="\n"):
            (correct, message_list) = parse_send_message(a)
            if(correct):
                message = "SEND "+message_list[0]+" Content-length: "+ str(len(message_list[1]))+" "+message_list[1]
                #print(message)
                connection.sendall(str.encode(message))
                data_recv = connection.recv(2048)
                while(not data_recv):
                    #connection.sendall(str.encode(message))
                    data_recv = connection.recv(2048)
                data = data_recv.decode('utf-8')
                if(data[:9]=="ERROR 103"):
                    print(data)
                    connection.close()
                    return
                elif(data[:5]=="ERROR"):
                    print(data)
                else:
                    print("Delivered Successfully")
            else:
                print("Syntax : @<sender username> <message>")


def forward_data_check(data):
    # FORWARD [sender username] Content-length: [length] [message of length given in the header above]
    correct = True
    data_list = []
    st=0
    count=0
    for i in range(len(data)):
        if(data[i]==" "):
            count+=1
            data_list.append(data[st:i])
            st=i+1
            if(count==4):
                break
    if(len(data_list)!=4 or data_list[0]!="FORWARD" or data_list[2]!="Content-length:" or (not data_list[3].isnumeric())):
        correct = False
        return (correct,[])
    if((len(data)-st)!=int(data_list[3])):
        correct = False
        return (correct,[])
    data_list.append(data[st:])
    return (correct, data_list)

def forward_from_server(connection):
    while True:
        data_recv = connection.recv(2048)
        if(data_recv):
            data = data_recv.decode('utf-8')
            (correct, data_list) = forward_data_check(data)
            if(correct):
                print(data_list[1]+": "+data_list[-1])
                reply = "RECEIVED "+data_list[1]+"\n\n"
                connection.sendall(str.encode(reply))
            else:
                reply = "ERROR 103 Header Incomplete\n\n"
                connection.sendall(str.encode(reply))
                #connection.close()
                #return     


if __name__ == '__main__':
    if(len(sys.argv)) <= 2:
        print("Syntax : client.py <username> <host name>")
        sys.exit(1)
    username = sys.argv[1]
    host_name = sys.argv[2]
    #host_ip_add = sys.argv[2]

    host_ip_add = None
    try:
        host_ip_add = socket.gethostbyname(host_name)
    except socket.gaierror:
        # wrong host name
        print(f'Invalid host name: ', end='')
        print(host_name)
        sys.exit(1)

    port_number1 = 40001
    port_number2 = 40001

    socketcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketsc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    try:
        socketsc.connect((host_ip_add, port_number2))
    except socket.error as e:
        print(str(e))

    registrationcs(socketcs, username)
    registrationsc(socketsc, username)
    print("Registered Successfully")

    thread1 = threading.Thread(target = send_to_server, args=(socketcs,))
    thread2 = threading.Thread(target = forward_from_server, args = (socketsc,))
    #start_new_thread(send_to_server, (socketcs, ))
    #start_new_thread(forward_from_server, (socketsc, ))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()




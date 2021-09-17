import socket
import sys
import threading

def registrationcs(socketn, username):
    socketn.send(str.encode('REGISTER TOSEND '+username+"\n\n"))
    data_recv = socketn.recv(1024)
    while(not data_recv):
        data_recv = socketn.recv(1024)
    data = data_recv.decode('utf-8')
    if(data[:5]=="ERROR"):
        print(data)
        return False
    print(data)
    return True

def registrationsc(socketn, username):
    socketn.send(str.encode('REGISTER TORECV '+username+"\n\n"))
    data_recv = socketn.recv(1024)
    while(not data_recv):
        data_recv = socketn.recv(1024)
    data = data_recv.decode('utf-8')
    if(data[:5]=="ERROR"):
        print(data)
        return False
    print(data)
    return True

def parse_send_message(mess):
    if(mess[0]!="@"):
        return (False, [])
    message_list = []
    for i in range(len(mess)):
        if(mess[i]==" "):
            message_list.append(mess[1:i])
            break
    message_list.append(mess[i+1:])
    if(len(message_list)!=2):
        return (False, [])
    #print(message_list)
    return (True, message_list)


def send_to_server(connection):
    # SEND [recipient username] Content-length: [length] [message of length given in the header above]
    while True:
        a= sys.stdin.readline()
        if(a[-1]=="\n"):
            (correct, message_list) = parse_send_message(a[:-1])
            if(correct):
                message = "SEND "+message_list[0]+"\nContent-length: "+ str(len(message_list[1]))+"\n\n"+message_list[1]
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
                    sys.exit()
                elif(data[:5]=="ERROR"):
                    print(data)
                else:
                    print("Delivered Successfully")
            else:
                print("Syntax : @<sender username> <message>")


def forward_data_check(data):
    # FORWARD [sender username]\nContent-length: [length]\n\n[message of length given in the header above]
    data_list = data.split("\n")
    if(len(data_list)!=4):
        return (False,[])
    sr_list = data_list[0].split(" ")
    cl_list = data_list[1].split(" ")
    if(len(sr_list)!=2 or len(cl_list)!=2 or sr_list[0]!="FORWARD" or cl_list[0]!="Content-length:" or (not cl_list[1].isnumeric()) or int(cl_list[1])!=len(data_list[-1])):
        return (False,[])
    data_list[1]=sr_list[1]
    data_list[2]=cl_list[1]
    #print(data_list)
    return (True, data_list)


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
                connection.close()
                sys.exit()     


if __name__ == '__main__':
    if(len(sys.argv)) <= 2:
        print("Syntax : client.py <username> <host name>")
        sys.exit()
    username = sys.argv[1]
    #host_name = sys.argv[2]
    host_ip_add = sys.argv[2]

    '''host_ip_add = None
    try:
        host_ip_add = socket.gethostbyname(host_name)
    except socket.gaierror:
        # wrong host name
        print(f'Invalid host name: ', end='')
        print(host_name)
        sys.exit(1)'''

    port_number1 = 8006
    port_number2 = 8006

    socketcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketsc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        socketcs.connect((host_ip_add, port_number1))
    except socket.error as e:
        print(str(e))
        sys.exit()

    try:
        socketsc.connect((host_ip_add, port_number2))
    except socket.error as e:
        print(str(e))
        sys.exit()

    flag = registrationcs(socketcs, username)
    if(flag == False):
        socketcs.close()
        socketsc.close()
        sys.exit()
    flag = registrationsc(socketsc, username)
    if(flag == False):
        socketsc.close()
        socketcs.close()
        sys.exit()
    print("Registered Successfully")

    thread1 = threading.Thread(target = send_to_server, args=(socketcs,))
    thread2 = threading.Thread(target = forward_from_server, args = (socketsc,))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()




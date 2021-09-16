import socket
import sys


socketa = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = sys.argv[1]
host_ip = socket.gethostbyname(host_name)
port = int(sys.argv[2])
if(len(sys.argv)>3):
	usrename = sys.argv[3]


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


try:
    socketa.connect((host_ip, port))
except socket.error as e:
    print(str(e))
    exit(1)

send_to_server(socketa)
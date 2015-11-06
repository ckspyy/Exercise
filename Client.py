import socket
import select
import sys
import threading
import signal
import thread

# thread to constantly taking user iniput, dies when main function ends
def usrinput():
    while True:
        try:
            msg = raw_input()
            if not msg:
                sys.stdout.write('please input something.\n')
                sys.stdout.flush()
            client_s.sendall(msg)
        except:
            sys.exit()

# host, port info will be part of input, and error msg will be displayed if input isn't valid    

Host = '192.168.56.1'
Port = 4500
if len (sys.argv) == 3:
    Host = str(sys.argv[1])
    Port = int(sys.argv[2])
else:
    print "Invalid input. Expected format: python Client.py HostIP Port"  
    sys.exit()  
# client socket start to connect to host
client_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_s.settimeout(3)
try :
    client_s.connect((Host, Port))
except :
    print('Error when connect')
    sys.exit()
print('Connected to server at IP:'+str(Host)+', Port:%s. Start sending messages' % Port)

# start the thread for user input monitoring
Receive = threading.Thread(target = usrinput)
Receive.setDaemon(True)
Receive.start()
data = ''
# while loop to continuously receive info from server and shut the client down properly
while True:
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL) # enable control+C exit
        read_sockets = select.select([client_s],[],[])[0]
        for sock in read_sockets:
            data = sock.recv(1024)
        if data =='shutdown':
            print '\nclient shutdown'
            break
        sys.stdout.write(data)
        sys.stdout.flush()
    except:
        print '\nclient shutdown'
        break


        





#import needed modules and intialize global variables
import socket
import datetime
import time
import sys
import threading
import select
import signal
import re

# Autoofftime to check inactive user, BLOCK_TIME to block usr from ip that had 3 failed attemp
Autoofftime = 1800
BLOCK_TIME = 60
Host = ''
Port = 4500
Usrlib = {}
historymsg = {}
offlinemsg = []
Nowblocked = []
Usrrecenttime = {}
Server_threads= []

# function used by thread to auto -disconnect
def Autologout_counter():
    while True:
        for tmpthread in Server_threads:
            if tmpthread.usrloggedin:
                if (datetime.datetime.now() - Usrrecenttime[tmpthread.usr]).total_seconds() > Autoofftime:
                    tmpthread.msgsender('shutdown')
                    print 'auto shut inactive user'+ tmpthread.usr
            time.sleep(5)



# one thread for each server socket connected to clients
class Usrthread(threading.Thread):
    def __init__(self, socketwithclient):
        threading.Thread.__init__(self)
        self.svrsocket = socketwithclient
        self.usrloggedin = False
        self.busystate = False
        self.clientaddress = self.svrsocket.getpeername()
    # start the thread to interact with the users
    def run(self):
        try:
            print 'We have a Connection established from '+self.clientaddress[0]+':'+str(self.clientaddress[1])+' (at '+str(datetime.datetime.now())+')'
            self.usr = self.usrlogin()
            self.usrloggedin = True
            print 'user: '+ self.usr + ' logged in at '+str(datetime.datetime.now())
            # welcom msg and display command options
            self.msgsender('Welcome! The time is '+str(datetime.datetime.now())+'\n\n\nAvaialable command:\nBusy\nshowchathistory\nshowofflinemsg\nbroadcast message <message>'+
                '\nbroadcast user <user> <user> message <message>\nwhoelse\nwholast <number of mins>\nmesasage <user> <message>\nlogout'+
                '\n\nCommand:')
            # while loop to process user input and respond properly
            while True:
                originalmsg = self.msgreceive()
                Usrrecenttime[self.usr] = datetime.datetime.now()
                cmd = originalmsg.split(' ')[0]
                if originalmsg.find('broadcast message')==0:
                    tempmsg = originalmsg[18:]
                    self.usrcmd_broadcast(tempmsg)
                elif originalmsg.find('broadcast user')==0:
                    tempmsg = originalmsg[15:]
                    startindex = tempmsg.find(' message ')
                    for tmpthread in Server_threads:
                        if tempmsg[:startindex].find(tmpthread.usr)+1:
                            tmpthread.msgsender('\n'+self.usr+':'+tempmsg[startindex+9:]+'\nCommand')
                    self.msgsender('Command:')
                elif originalmsg[0:8] == 'message ':
                    self.usrcmd_message(originalmsg[8:])
                elif cmd == 'showchathistory':
                    self.usrcmd_showchathistory()
                elif cmd == 'showofflinemsg': 
                    self.usrcmd_showofflinemsg()
                elif re.findall(r'wholast \d+',originalmsg):
                    self.usrcmd_wholast(re.findall(r'\d+',originalmsg)[0])
                elif originalmsg =='Busy':
                    self.busystate = not self.busystate
                    self.msgsender('Successfully set! Your current "Busy" status is :'+str(self.busystate)+'.\nCommand:')
                elif originalmsg == 'logout':
                    print self.usr + ' requested to logged out at '+str(datetime.datetime.now())
                    self.msgsender('you are logged out')
                    self.clearexitthread()
                elif cmd == 'whoelse':
                    self.usrcmd_whoelse()
                else:
                    self.msgsender('Wrong command,please try again\nCommand:')

        except :
            self.clearexitthread()
    # function for user login
    def usrlogin(self):
        #function to allow user to login with or disconnect for wrong input and user will be blocked after 3 failed trials
        try:
            self.msgsender('Username:')
            usr = self.msgreceive()
            while usr not in Usrlib:
                self.msgsender('User does not exist, please enter again. \nUsername:')
                usr = self.msgreceive()
            # blocked user's client will auto shut down after receiving the error msg
            if [usr, self.clientaddress[0]] in Nowblocked:
                self.msgsender('You are blocked!')
                self.clearexitthread()
            # warning online user that someone is trying to login from somewhere else
            for tmpthread in Server_threads:
                if tmpthread.usrloggedin and tmpthread.usr == usr:
                    self.msgsender('user already logged in\n')
                    tmpthread.msgsender('\n someone is trying to log into your accout from somewhere else\nCommand:')
                    self.clearexitthread()
            # is user is allowed to loggin, the following command will handle password information
            # server side will show related info accordingly
            self.msgsender('Password:')        
            for i in [0,1,2]:
                if Usrlib.get(usr) == self.msgreceive():
                    return usr
                elif i==2: 
                    Nowblocked.append([usr, self.clientaddress[0]])
                    print 'user: ' + usr +' is blocked for '+ str(BLOCK_TIME) + 'secs from ip:'+ self.clientaddress[0] +'\n'
                    self.msgsender('shutdown')
                    time.sleep(BLOCK_TIME)
                    Nowblocked.remove([usr, self.clientaddress[0]])
                    print 'user: ' + usr+' blocking period over from ip:'+self.clientaddress[0]+'\n'
                else: self.msgsender('Wrong Password!\nPasswrod:')            
            self.clearexitthread()
        except KeyboardInterrupt:
            sys.exit()    
    # subfunction send/recceive messages to users, try, except block to increase the stability of this part compared by usring socket.sendall()
    def msgsender(self, msg):
        try:
            self.svrsocket.sendall(msg)
        except:
            return
    # use receive function to stablize and standardize receiving process
    def msgreceive(self):
        try:
            msg = self.svrsocket.recv(1024)
            return msg
        except:
            return

    # clean up the thread for client socket
    def clearexitthread(self):
        # exit the thread. *everytime the thread ends, the related usr's last active time is updated
        try: 
            time.sleep(0.1)
            self.msgsender('shutdown')
            Server_threads.remove(self)
            self.busystate = False
            while self.usrloggedin:
                Usrrecenttime[self.usr] = datetime.datetime.now()
                print self.usr + ' logged out at '+str(datetime.datetime.now())+'\n'
                self.usrloggedin = False
            self.svrsocket.close()
            sys.exit()
        except:
            sys.exit()
    # broadcast function
    def usrcmd_broadcast(self, msg):
        for usr in historymsg:
            historymsg[usr].append(self.usr+'broadcasted:'+msg+' (at '+ str(datetime.datetime.now())+ ')\n')
        for tmpthread in Server_threads:
            if tmpthread.usrloggedin and tmpthread != self and tmpthread.busystate==False:
                tmpthread.msgsender('\n'+self.usr+':'+msg+'\nCommand:')
        self.msgsender('Command:')
    # private message function, with all messages recorded and usrs can retrieve their own on request
    def usrcmd_message(self, originalmsg):
        receiver, msg = (originalmsg+' ').split(' ', 1)
        if receiver in Usrlib:
            for tmpthread in Server_threads:
                if tmpthread.usr == receiver and tmpthread.usrloggedin and tmpthread.busystate==False:
                    t.msgsender('\n'+self.usr+':'+msg+'\nCommand:')
            historymsg[self.usr].append('message '+originalmsg+' (at '+str(datetime.datetime.now())+')\n')
            historymsg[receiver].append(self.usr+':'+msg+' (at '+str(datetime.datetime.now())+')\n')
            offlinemsg.append([receiver, self.usr+':'+msg+' (at '+str(datetime.datetime.now())+')\n'])
        else:
            self.msgsender('the target user is invalid, please check again.\n')
        self.msgsender('Command:')
    # whoelse function    
    def usrcmd_whoelse(self):
        msg = ""
        for tmpthread in Server_threads:
            if tmpthread != self and tmpthread.usrloggedin and  not tmpthread.busystate: msg += tmpthread.usr + '\n'
        self.msgsender(msg+'Command:')
    # wholast function, default to display all usrs that was active within 60mins
    def usrcmd_wholast(self, lasttime):
        msg = ''
        currenttime = datetime.datetime.now()
        if 0<int(lasttime)<60: pass
        else: lasttime = 60
        for usr in Usrrecenttime:
            if (currenttime - Usrrecenttime[usr]).total_seconds() < int(lasttime)*60 :
                msg += usr + '\n'
        self.msgsender(msg+'Command:')
    # show the chat history for respective user 
    def usrcmd_showchathistory(self):
        for recordedmsg in historymsg[self.usr]:
            self.msgsender(recordedmsg)
        self.msgsender('Command:')
    # display offline msgs missed before login
    def usrcmd_showofflinemsg(self):
        for recordedoffmsg in offlinemsg:
            if recordedoffmsg[0] == self.usr: 
                self.msgsender(recordedoffmsg[1])
                offlinemsg.remove(recordedoffmsg)
        self.msgsender('\n Command:')

# Main function below
# reading in existing user account info
keyfile = open("user_pass.txt", "r")
Eachitem = keyfile.read().split()
for i in range(0,len(Eachitem)/2-1):
    Usrlib[Eachitem[i*2]] = Eachitem[i*2+1]
    historymsg[Eachitem[i*2]] = []
    Usrrecenttime[Eachitem[i*2]] = datetime.datetime.now()
keyfile.close()

# Retrieve user input on server port info
if len (sys.argv) == 2:
    Port = int(sys.argv[1])
else:
    print "Invalid argument. Usage: python Server.py port"
    sys.exit()

#start listening socket
Receiving_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    Receiving_socket.bind((Host, Port))
except:
    print('Unsuccessful listening socket setup')
    sys.exit()
Receiving_socket.listen(20)

# a separate thread to continuously check if there are users need to autologoff after a long inactive period
Autologout = threading.Thread(target = Autologout_counter)
Autologout.setDaemon(True)
Autologout.start()

#listening socket keeps runnint to accept new client.
while True:
    try:
        # code to handle graceful control +c exit
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Receivedsocket = Receiving_socket.accept()[0]
        Startnewthread = Usrthread(Receivedsocket)
        # all client socket thread has setDaemon true attribute will auto shut when main function ends
        Startnewthread.setDaemon(True)
        Server_threads.append(Startnewthread)
        Startnewthread.start()
    except:
        print "server shutdown, bye!"
        Receiving_socket.close()
        break

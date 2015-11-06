How to run the chat program. 

- development environment : python 2.7.3 (Windows 8.1 OS, which isn't supposed to impose any big impact)

1. Start Server.py by typing the following:

python Server.py <port number>
e.g. "python Server.py 4500"

2. Start Client.py by typing the following
python Client.py <host server ip> <port number>
e.g. "python Client.py 192.168.56.1 4500"
* when testing, need to input the host IP first(the IP within network which is gained by socket.gethostbyname(socket.gethostname()) command on the server machine using python socket module)


3. Enjoy chatting!  *command list introduction will be printed upon successful login

4. functions summary:
	whoelse:  show all other usrs online
	wholast <x>: show all users active within the last x mins, input is expected to be between 0 to 60 mins, default is 60 mins if input is not meeting requirement.
	broadcast message <message>: broadcasts <message> to all connected usrs
	broadcast user <user> <user> ... <user> message <message>: broadcasts <message> to the list of users
	message <user> <message>: private <message> to a <user>
	logout: log out this user
    *extra features:
	Busy:  change user status to busy or back to normal (stay undisturbed at Busy status and people can't see you using whoelse!:)
	showchathistory: show all your messages sent and received, even including those that are blocked when user away
 	showofflinemsg: show all the missed messages when user is offline
	-online user will be altered if someelse is trying to login for the same account.
	-server screen will show simple logs such as user login/logout time etc.


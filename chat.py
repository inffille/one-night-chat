import socket
import threading
import sys

def wrap_data(data):
	return bytes(data, 'utf-8')

class Server:
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	connections = {}	#conn to name
	users = {}			#name to conn
	def __init__(self):
		self.sock.bind(('0.0.0.0', 10000))
		self.sock.listen(1)

	def sendMsgToAll(self, c, data, wrap=0):
		final_data = ""
		for conn in self.connections.keys():
			if conn is not c:
				if wrap != 0:
					final_data = wrap_data(self.connections.get(c) + ': ') + data
				else:
					final_data = data
				conn.send(final_data)

	def parseNameTo(self, data):
		decData = data.decode('utf-8')
		i = 1
		try:
			while decData[i] != '~':
				i = i + 1
		except IndexError:
			return None, None
		return decData[1:i], decData[i+1:]

	def sendMsgToUser(self, c, my_name, nameTo, dataTo):
		conn = self.users.get(nameTo)
		if conn:
			conn.send(wrap_data('~' + my_name + '~:' + dataTo))
		else:
			data = wrap_data('User \"' + nameTo + '\" does not exist.')
			c.send(data)

	def userQuit(self, c):
		data = wrap_data('User \"' + self.connections.get(c) + '\" has left the room.')
		self.sendMsgToAll(c, data)

	def userEnter(self, c):
		data = wrap_data('User \"' + self.connections.get(c) + '\" has joined the room.')
		self.sendMsgToAll(c, data)
		print('User ' + self.connections.get(c))

	def getUserName(self, c, again=0):
		if again == 1:
			c.send(wrap_data('Sorry, this username is occupied. Enter another name: '))
		name = c.recv(1024)
		dec_name = name.decode('utf-8')
		if dec_name in self.users:
			self.getUserName(c, 1)
		else:
			self.connections[c] = dec_name
			self.users[dec_name] = c
		return dec_name

	def handler(self, c, a):
		dec_name = self.getUserName(c)
		self.userEnter(c)
		while True:
			data = c.recv(1024)
			if not data:
				self.userQuit(c)
				print(str(a[0]) + ':' + str(a[1]), "disconnected")
				self.connections.pop(c)
				self.users.pop(dec_name)
				c.close()
				break
			if data.decode('utf-8')[0] == '~':
				nameTo, dataTo = self.parseNameTo(data)
				if not nameTo:
					err_data = wrap_data('To send personal message to user type \"~<user_name>~\" and a message.')
					c.send(err_data)
				else:
					self.sendMsgToUser(c, dec_name, nameTo, dataTo)
				
			else:
				self.sendMsgToAll(c, data, 1)
	
#	def getUserName(self, c, a):
#		c.send(bytes('Enter your chat name: ', 'utf-8'))
#		name = c.recv(1024)
#		self.connections[c] = str(name)
#		print(str(a[0]) + ':' + str(a[1]), "connected as " + str(name))

	def run(self):
		while True:
			c, a = self.sock.accept()
			cThread = threading.Thread(target=self.handler, args=(c,a))
			cThread.daemon = True
			cThread.start()
			c.send(wrap_data('Hello there! This is an extra simple (but hopefully working) chat. Just type and send a message and everybody in the room will see it. In case you would like to send personal message, type ~<user_name>~[message]. Only <user_name> will see it.\n Have fun and for start, please, enter your chat name: '))
			self.connections[c] = None
			print(str(a[0]) + ':' + str(a[1]), "connected")

class Client:
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def sendMsg(self):
		while True:
			self.sock.send(wrap_data(input("")))

	def __init__(self, address):
		self.sock.connect((address, 10000))

		iThread = threading.Thread(target=self.sendMsg)
		iThread.daemon = True
		iThread.start()

		while True:
			data = self.sock.recv(1024)
			if not data:
				break
			print(data.decode('utf-8'))

if(len(sys.argv) > 1):
	client = Client(sys.argv[1])
else:
	server = Server()
	server.run()

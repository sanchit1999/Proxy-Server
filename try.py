import base64, copy, thread, signal
import socket, sys, os, time, struct
import datetime, json, email.utils, threading

config = {
	'HOST_NAME': '127.0.0.1',
	'BIND_PORT': 20100,
	'MAX_REQUEST_LEN': 1024,
	'BUFFER_SIZE': 100000000,
	'CONNECTION_TIMEOUT' : 20
}

file = open("blacklist.txt","r")
blocked_files = file.readlines()
blocked_list = []

for ips in blocked_files:
	(ip, cidr) = ips.split('/')
	cidr = int(cidr) 
	host_bits = 32 - cidr
	i = struct.unpack('>I', socket.inet_aton(ip))[0]
	start = (i >> host_bits) << host_bits
	end = start | ((1 << host_bits))
	end += 1
	for i in range(start, end):
		blocked_list.append(socket.inet_ntoa(struct.pack('>I',i)))

class Server:

	def __init__(self):

		self.Cache = "./cache"

		if not os.path.isdir(self.Cache):
			os.makedirs(self.Cache)
		
		self.client_name = 1
		
		try:
			signal.signal(signal.SIGINT, self.shutdown)
			self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.server_socket.bind((config['HOST_NAME'], config['BIND_PORT']))
			self.server_socket.listen(100)
		except Exception as e:
			'''error functionality in initializing socket'''
			print e
			quit()

		while True:
			# try except here
			(client_socket, client_address) = self.server_socket.accept()
			thread_ = threading.Thread(
				name = self._getClientName(), 
				target = self.proxy_thread,
				args = (client_socket, client_address))
			thread_.setDaemon(True)
			thread_.start()

	def proxy_thread(self, client_socket, client_address):

		request = client_socket.recv(config['MAX_REQUEST_LEN'])
		first_line = request.split('\n')[0]
		url = first_line.split(' ')[1]
		http_pos = url.find("://")
		temp_index = 0
		if (http_pos==-1):
			temp_index = 0
		else:
			temp_index = http_pos + 3
		temp = url[temp_index:]
		port_pos = temp.find(":")
		webserver_pos = temp.find("/")

		if webserver_pos == -1:
			webserver_pos = len(temp)

		webserver = ""
		port = -1
		if (port_pos == -1 or webserver_pos < port_pos): 
			port = 80 
			webserver = temp[:webserver_pos] 

		else:
			port = int(temp[port_pos + 1 : webserver_pos])
			webserver = temp[:port_pos]
	
		val = socket.gethostbyname(webserver)
		if val in blocked_list:
			client_socket.send("Page Blocked")
			sys.exit(0)

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
		s.settimeout(config['CONNECTION_TIMEOUT'])
		s.connect((webserver, port))

		if webserver in os.listdir('./cache'):
			s.send("GET /" + webserver + " HTTP/1.1\r\nIf-Modified-Since: " + time.ctime(os.path.getmtime('./cache/' + webserver)) + " \r\n\r\n")
		else:
			s.send("GET " + webserver + " HTTP/1.1\r\n\r\n")
		# if filename
		response = s.recv(config['MAX_REQUEST_LEN'])
		# print(response.find("200"))
		# print(webserver)
		# print response
		a1 = os.path.join('./cache', webserver)
		if response.find("200") >= 0:
			fp = open(os.path.join('./cache', webserver) ,'wb')
			while 1:
				if (len(response) == 0):
					break
				client_socket.send(response)
				fp.write(response)
				response += s.recv(config['BUFFER_SIZE'])
				
		elif response.find("304") >= 0:
			fp = open(os.path.join('./cache',webserver), 'rb')
			temp = fp.read(config['BUFFER_SIZE'])
			while(temp):
				client_socket.send(temp)
				temp = fp.read(config['BUFFER_SIZE'])
			fp.close()

		else:
			print("=>Response Status:" , response)
		
		webserver = webserver.replace("/", "__")
		if webserver not in logs:
			logs[webserver] = []
		dt = time.time()
		logs[webserver].append(float(dt))
		if len(logs[webserver])>4:
			del logs[webserver][0]

	def shutdown(self):
		print "shutdown called"
		quit()

	def _getClientName(self):
		self.client_name += 1
		return self.client_name

	# def self.Cache_delete():

	# 	min_time = min(os.path.getmtime(self.Cache + "/" + files) for files in os.listdir(self.Cache))
	# 	last_file = ""
	# 	for files in os.listdir(self.Cache):
	# 		if(os.path.getmtime(self.Cache + "/" + files) == min_time)
	# 			last_file = files[0]

	# 	os.remove(self.Cache + "/" + last_file)		
	
	# def self.Cache_file_info(fileurl):

	# 	if(fileurl[0] == '/'):
	# 		fileurl = fileurl[1:]

	# 	fileurl = fileurl.replace("/", "__")
	# 	path = self.Cache + "/" + fileurl

	# 	if(os.path.isfile(path)):
	#     	ltime = time.strptime(time.ctime(os.path.getmtime(path)), "%a %b %d %H:%M:%S %Y")
	#     	return path, ltime
	# 	else:
	# 		return path, None

	# def self.Cache_file_info(fileurl):

	# 	if(fileurl[0] == '/'):
	# 		fileurl = fileurl[1:]

	# 	fileurl = fileurl.replace("/", "__")
	# 	path = self.Cache + "/" + fileurl

	# 	if(os.path.isfile(path)):
	#     	ltime = time.strptime(time.ctime(os.path.getmtime(path)), "%a %b %d %H:%M:%S %Y")
	#     	return path, ltime
	# 	else:
	# 		return path, None	

	# def add_url(url, client_address):
		
	# 	url = url.replace("/", "__")
	# 	if url in logs:
	# 		curr_time = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
	# 		logs[url].append({
	# 			"mtime" : current_time,
	# 			"client" : json.dumps(client_address)
	# 			})
	# 		if(len(logs[url]) > 3):
	# 			del logs[url][0]

logs = {}
newserver = Server()

		# s.sendall(request)

		# while True:

		#     data = s.recv(config['BUFFER_SIZE'])
		#     if (len(data) > 0):
		   #      client_socket.send(data)
		#     else:
	   
		#         break
	  #   if webserver in os.listdir(self.Cache):
	  #   	s.send("GET /"+ webserver + " HTTP/1.1\r\nIf-Modified-Since: " + time.ctime(os.path.getmtime('./.cache/' + webserver)) + " \r\n\r\n")
	  #   	# t1 = ""
	  #   	# t1 = t1 + "GET /"
	  #   	# t1 = t1 + webserver
	  #   	# t1 = t1 + " HTTP/1.1\r\nIf-Modified-Since: "
	  #   	# t1 = t1 + time.ctime(os.path.getmtime(self.Cache + webserver))
	  #   	# t1 = t1 + " \r\n\r\n"
	  #   	# s.send(t1)
	  #   else:
	  #   	s.send("GET "+ webserver + " HTTP/1.1\r\n\r\n")
	  #   	# t1 = ""
	  #   	# t1 = t1 + "GET "
	  #   	# t1 = t1 + webserver
	  #   	# t1 = t1 + " HTTP/1.1\r\n\r\n"
	  #   	# s.send(t1)

	  #   response = s.recv(config['MAX_REQUEST_LEN'])

	  #   # current_time = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")
	  #   # if webserver not in logs:
		 #   #  logs[url].append({
		 #   #  	"mtime" : current_time,
		 #   #  	})
		 #   #  if(len(logs[url]) > 4):
		 #   #  	del logs[url][0]

	  #   if response.find("200") >= 0:
	  #   	# flag = 0
			# # ctime = time.strptime(time.ctime(), "%a %b %d %H:%M:%S %Y")	
	  # #   	if(ctime - logs[url][-3] < 300):
	  # #   		flag = 1
	  #   	file_pointer = open(os.path.join('./cache', webserver), 'wb')
	  #   	while true:	
	  #   		if(len(response) == 0):
	  #   			break
	  #   		# if(flag == 1):
	  #   		file_pointer.write(response)
	  #   		client_socket.send(response)
	  #   		response = s.recv(config['MAX_REQUEST_LEN'])
	  #   	file_pointer.close()		
	  #   elif response.find("304") >= 0:
	  #   	file_pointer = open(os.path.join('./cache', webserver), 'rb')
	  #   	temp_var = file_pointer.read(config['MAX_REQUEST_LEN'])
	  #   	while(temp_var):
	  #   		client_socket.send(temp_var)
	  #   		temp_var += file_pointer.read(config['MAX_REQUEST_LEN'])
	  #   	file_pointer.close()
		
	  #   else:
	  #   	print "response Status ", response

	  #   s.close()
	  #   client_socket.close()

import socket
import pynedm
import cloudant
import threading

class SocketDisconnect(Exception):
	pass

class UnexpectedReturn(Exception):
	pass

class SocketObj:
	def __init__(self, name, ip, port, protocol="STREAM", term_character="\n", status=False):
		if type == "udp":
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		elif protocol == "tcp":
			s = socket.socket()
		else: log("No valid protocol specified - No socket created!")
		self.n = str(name)
		try:
			self.s.connect((str(ip), port))
			log("Connected to " + self.n + ".")
			self.status=True
		except Exception, e:
			log("Connection to " + self.n + " not possible, reason: %s" % e)
			self.status=False
		self.s = s
		self.tc = term_character
		self.status = status
		self.l = threading.Lock()

	def disconnect(self):
		self.status = False
		self.s.close()
		log("Connection to " + self.n + " closed.")

	def flush_buffer(self):
		astr = ""
		while 1:
			try:
				r = self.s.recv(4096)
				if not r:
					break
				astr += r
				if astr.find(self.tc) != -1:
					break
			except socket.error:
				self.status = False
				raise SocketDisconnect(self.n + "disconnected from socket!")


		return astr.replace(self.tc, "")


	def cmd_and_return(self, cmd, blocking=True, expected_return=""):
		self.l.acquire(blocking)
		self.s.send(str(cmd))
		r = self.flush_buffer()
		self.l.release()
		if r.find(expected_return) == -1:
			log("Unexpected response from " + self.n + " to command '" + str(cmd) + "': " + r)
			raise UnexpectedReturn("No confirmation from " + self.n + "!")
		else:
			r = r.replace(expected_return, "").rstrip().lstrip()
			return r

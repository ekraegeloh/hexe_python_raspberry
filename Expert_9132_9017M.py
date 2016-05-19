import socket
import cloudant
import select
import socketclass
import time

class expert_reader(socketclass.SocketObj):
	def __init__(self, ip, port):
		socketclass.SocketObj.__init__(self, "ExpertDAQ9017", ip, port, "tcp", "\r")
		try:
			welcome = socketclass.SocketObj.flush_buffer(self)
			log("Connected to " + welcome + "\n")
		except: log("Warning: No identification received from " + self.n)
		self.s.settimeout(5.0)

	#dictionary for  the channel names
	global channel_desc
	channel_desc = {
		"0": "hv_monitor_1",
		"1": "hv_monitor_2",
		"2": "hv_current_1",
		"3": "hv_current_2",
		"4": "gas_filling_pressure",
		"5": "CH5",
		"6": "CH6",
		"7": "CH7"
		}
		
	global channel_scale
	channel_scale = {
		"0": 1.0,
		"1": 1.0,
		"2": 2e-4,
		"3": 2e-4,
		"4": 3.44738,
		"5": 1.0,
		"6": 1.0,
		"7": 1.0
		}

	def read_all(self):
		adoc_dict = {}
		try:
		    raw_data = self.cmd_and_return("#00\r", False)#Modbus:"\x01\x04\x00\x00\x00\x08" oder \x00 anfangs?
		except socketclass.SocketDisconnect:
		    socketclass.SocketObj.disconnect(self)
		    time.sleep(1)
		    socketclass.SocketObj.__init__(self, "ExpertDAQ9017", 'hexeserial.2.nedm1', 1025, "tcp", "\r")
		    socketclass.SocketObj.flush_buffer(self)
		    self.s.settimeout(10.0)
		    raw_data = self.cmd_and_return("#00\r", False)
		ai_list = []
		if raw_data == "?00":#Fehler: \x01\x04 + Exception code
			raise UnexpectedReturn("No confirmation from " + self.n + "!")
		else:#data: \x01\x04\x00\x10 + 16 bytes data, 2 bytes per channel, interpret as int(..., 16)
			raw_data=raw_data[1:]
			ch_number =5 
			ai_chars = 7
#			print '------------ ExpertDAQ: ', raw_data
			for i in range(ch_number):
				ai_list.append(raw_data[i*ai_chars:i*ai_chars+ai_chars])
				adoc_dict[channel_desc[str(i)]] = float(ai_list[i])*channel_scale[str(i)]
#				print channel_desc[str(i)] + ": " + ai_list[i] + ' [kV]'
		return adoc_dict

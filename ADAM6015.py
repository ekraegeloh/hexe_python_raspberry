import cloudant
import select
import socketclass

class adam_reader(socketclass.SocketObj):
	def __init__(self, ip, port):
		socketclass.SocketObj.__init__(self, "ADAM6015", ip, port, "udp", "\r")

	#dictionary for  the channel names
	global channel_desc
	channel_desc = {
		"0": "oven_temp1",
		"1": "oven_temp2",
		"2": "laser_temp",
		"3": "CH3",
		"4": "CH4",
		"5": "CH5",
		"6": "CH6",
		"7": "CH7"
		}

	def read_temp(self):
		adoc_dict = {}
		raw_temp = self.cmd_and_return("#01\r", False)
		temp_list = []
		if raw_temp == "?01":
			raise UnexpectedReturn("No confirmation from " + self.n + "!")
		else:
			raw_temp=raw_temp[1:]
			ch_number = 3
			temp_chars = 7
#       	 print '------------ ADAM6015:'
			for i in range(ch_number):
				temp_list.append(raw_temp[i*temp_chars:i*temp_chars+temp_chars])
				adoc_dict[channel_desc[str(i)]] = float(temp_list[i])
#        		 print channel_desc[str(i)] + ": " + temp_list[i] + ' [deg C]'
		return adoc_dict

import socket
import cloudant
import signal
import string
import pynedm
import socketclass

class delta_supply(socketclass.SocketObj):
	def __init__(self, ip_address, port):
		socketclass.SocketObj.__init__(self, "DeltaElectronica Power Supply", ip_address, port)
		try:
			answer = socketclass.SocketObj.cmd_and_return(self, "*IDN?\n")
			log("Connected to " + answer + "\n")
		except: log("Warning: No identification received from " + self.n)

	def read_voltage(self):
		return self.cmd_and_return("MEAS:VOLT?\n", False)

	def read_current(self):
		return self.cmd_and_return("MEAS:CURR?\n", False)

	def set_max_voltage(self, max_voltage):
		self.cmd_and_return("SOUR:VOLT:MAX " + str(max_voltage) +"\n", True, "", False)

	def read_max_voltage(self):
		return self.cmd_and_return("SOUR:VOLT:MAX?\n", False)

	def read_max_current(self):
		return self.cmd_and_return("SOUR:CURR:MAX?\n", False)

	def set_max_current(self, max_current):
		self.cmd_and_return("SOUR:MAX:CURR " + str(max_current) + "\n", True, "", False)

	def set_voltage(self, voltage):
		self.cmd_and_return("SOUR:VOLT " + str(voltage) + "\n", True, "", False)

	def set_current(self, current):
		self.cmd_and_return("SOUR:CURR " + str(current) + "\n", True, "", False)

	def set_output_state(self, state):
		if int(state) == 1: self.cmd_and_return("OUTP ON \n", True, "", False)
		else: self.cmd_and_return("OUTP OFF \n", True, "", False)

	def read_output_state(self):
		return self.cmd_and_return("OUTP?\n")

	def init_laser(self):
		'''
		This function sets the initial values for the laser
		'''
		log("Init state:")
		log("Maximum voltage: " + self.read_max_voltage())
		log("Maximum current: " + self.read_max_current())
		log("Output: " + self.read_output_state())
		log("Setting voltage=8")
		self.set_voltage(8)

def set_laser_current(delta, current):
	'''
	this function sets the laser current via the delta power supply
	'''
	delta.set_current(current)
	return "Laser set to {}A".format(current)

def set_laser_status(delta, state):
	'''
	this funtion enables or disables the output of the laser power supply
	'''
	delta.set_output_state(state)
	return

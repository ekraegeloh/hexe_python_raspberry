# -*- coding: utf-8 -*-
"""
@author: Eva Kraegeloh
"""

import time
import socket

global descriptor_ao
descriptor_ao = ["hv_control_1", "hv_control_2", "heater_flow", "heater_power"]

class adam_setter:
	global adam_ao_tcp
	adam_ao_tcp=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	#0148=0-10V range
	setrange0="#01BE000148\r"
	setrange1="#01BE010148\r"
	setrange2="#01BE020148\r"
	setrange3="#01BE030148\r"

	def connect(self, ip, port):
		try:
			adam_ao_tcp.connect((ip, port))
			print "Connected to ADAM6224"
			return True
		except Exception, e:
			print "Connection to ADAM6224 not possible, reason: %s" % e
			time.sleep(2)
			return False

	def disconnect(self):
		adam_ao_tcp.close()
		print 'Connection to ADAM6224 closed.'

	def set_ranges(self):
		adam_ao_tcp.send("#01BE000148\r")
		adam_ao_tcp.recv(1024)
		adam_ao_tcp.send("#01BE010148\r")
		adam_ao_tcp.recv(1024)
		adam_ao_tcp.send("#01BE020148\r")
		adam_ao_tcp.recv(1024)
		adam_ao_tcp.send("#01BE030148\r")
		adam_ao_tcp.recv(1024)

	def read_ao(self, channel):
			adam_ao_tcp.send("$01BC0" + str(channel) + "\r")
			response = adam_ao_tcp.recv(1024)
			if response == "?01\r": raise Exception("Unknown command")
			else:
				response = response.split("!01")[1]
				response = response.split("\r")[0]
				return response

	def write_ao(self, channel, ao_value):
		hex_no = hex(int(ao_value*4095/10))
		hex_str = hex_no.split('x')[1]
		if len(hex_str) == 0: hex_str = "000"
		if len(hex_str) == 1: hex_str = "00" + hex_str
		if len(hex_str) == 2: hex_str = "0" + hex_str
		adam_ao_tcp.send("#01BC0" + str(channel) + "0" + hex_str + "\r")
		resp = adam_ao_tcp.recv(1024)
		if resp == "!01\r": return True
		if resp == "?01\r": raise Exception("Unknown command")
		else: raise Exception("Couldn't set voltage!")

	def zero_all_ao(self):
		for i in range(4):
			zero_str = "#01BC0" + str(i) + "0000\r"
			adam_ao_tcp.send(zero_str)
			resp = adam_ao_tcp.recv(1024)
			#print resp
			if resp == "?01\r": raise Exception("Unknown command")
			if resp != "!01\r": raise Exception("Couldn't set to zero!")
			time.sleep(0.1)
		adam_ao_tcp.send("#01BC0200CC\r")
		adam_ao_tcp.recv(1024)
		return


def check_aorange(value):
	"""
	checks if given output voltage is in the output range 0-10V
	"""
	if value < 0: value = 0
	if value > 10: value = 10
	return value


def set_high_voltage(adamAO, hvsupply, value):
	"""
	this function sets the given digital output low
	"""
	ao_ch = str(descriptor_ao.index("hv_control_" + str(hvsupply)))
	output = check_aorange(float(value))
	if adamAO.write_ao(ao_ch, output): return "HV supply #{} set to {} kV".format(hvsupply, output)
	else: raise Exception("Error setting HV value")


def set_heater_power(adamAO, unit, value):
	"""
	this function sets the analog output voltage controlling the oven heater power
	"""
	ao_ch = str(descriptor_ao.index("heater_power"))
	#max temperature/maximum voltage
	#print unit
	#print value
	if unit == "C": output = (float(value) - 36.4)/32.3
	if unit == "V": output = value
	else: raise Exception("Unit unknown!")
	output = check_aorange(float(output))
	if output < 0.8: output = 0.0
	if adamAO.write_ao(ao_ch, output): return "Heater power (CH{}) set to {} V.".format(ao_ch, output)
	else: raise Exception("Error setting heater power")

def set_heater_flow(adamAO, value):
	"""
	this function sets the analog output voltage controlling the oven heater flow
	"""
	ao_ch = str(descriptor_ao.index("heater_flow"))
	output = check_aorange(float(value)/10)
	#flow not equal to zero, otherwise the heater turns off for safety reasons
	if float(output) < 0.5: output = "0.5"
	if adamAO.write_ao(ao_ch, output): return "Heater flow (CH{}) set to {} V".format(ao_ch, output)
	else: raise Exception("Error setting heater flow")

def read_aos(adamAO):
	ao = {}
	for i in range(4):
		response = adamAO.read_ao(i)
		if response:
			ao[descriptor_ao[i]]=int(response, 16)*10.0/4095
	return ao


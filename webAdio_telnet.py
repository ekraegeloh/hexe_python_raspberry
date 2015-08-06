# -*- coding: utf-8 -*-
"""
@author: Florian Kuchler
"""

import telnetlib
import signal
import cloudant
#from pprint import pprint as pp
import pynedm
import threading
from socketclass import SocketDisconnect, UnexpectedReturn


#devices connected to the various webadio channels
global descriptor_ai
global descriptor_di
global descriptor_do
descriptor_ai = ["hv_monitor_1", "hv_monitor_2", "hv_current_1", "hv_current_2", "hv_leakage_monitor", "gas_system_pressure", "ai6", "ai7"]
descriptor_ao = ["hv_control_1", "hv_control_2", "heater_flow", "heater_power", "ao4", "ao5", "ao6", "ao7"]
descriptor_di = ["di0","di1", "di2", "di3", "di4", "di5", "di6", "di7"]
descriptor_do = ["field_switch_1","field_switch_2", "field_switch_3", "field_switch_4","hv_enable_1","hv_enable_2", "squid_cooler", "do7"]

class TelnetCommunication:
	def __init__(self, name, ip, pw, term_char="\r\n", prompt=">", adio_ack=" \x1b[34mdone \x1b[0;1m", status=False):
		try:
			tn = telnetlib.Telnet(ip)
			tn.read_until("Password: ")
			tn.write(pw + term_char)
			log(tn.read_until(prompt))
			self.status = True
		except Exception, e:
			log("Connection not possible, reason: %s" % e)
			self.status = False
		self.tn = tn
		self.n = name
		self.tc = term_char
		self.p = prompt
		self.ack = adio_ack
		self.s = status
		self.l = threading.Lock()

	def close(self):
		self.s = False
		self.tn.write("q\r\n")
		self.tn.close()
		log('Connection to ' + self.n + ' closed.')

	def read(self):
		astr = ""
		try:
			astr = self.tn.read_until(self.p, 5)
		except EOFError:
			self.status = False
			raise SocketDisconnect(self.n + "disconnected from socket!")
		return astr.replace(self.tc, "")

	def cmd_and_return(self, cmd, blocking=True, expected_return=""):
		self.l.acquire(blocking)
		try:
			self.tn.write(str(cmd))
		except socket.error:
			self.status = False
			raise SocketDisconnect(self.n + "disconnected from socket!")
		r = self.read()
		self.l.release()
		if r.find(expected_return) == -1:
			log("Unexpected response from " + self.n + " to command '" + str(cmd) + "': " + r)
			raise UnexpectedReturn("No confirmation from " + self.n + "!")
		else:
			r = r.replace(expected_return, "").rstrip().lstrip()
			return r

#the class for the webadio board provides read and write functions
class webadio(TelnetCommunication):
	def __init__(self):
		self.s = False

	def open(self, ip, pw):
		TelnetCommunication.__init__("WebADIO", ip, pw, "\r\n", ">", " \x1b[34mdone \x1b[0;1m", self.s)

#	term_char = "\r\n"
#	prompt = term_char + ">"
#	adio_ack = " \x1b[34mdone \x1b[0;1m" + prompt

	def read_ai(self):
		ai = None
		raw_ai = TelnetCommunication.cmd_and_return("AIA" + self.tc, False)
		ai = str.split(raw_ai)[3::4]
		return {descriptor_ai[i]: float(ai[i]) for i in range(len(ai))}

	def read_di(self):
		di = None
		raw_di = TelnetCommunication.cmd_and_return("DIA" + self.tc, False)
		di = list(filter(str.isdigit, raw_di))
		return {descriptor_di[i]: float(di[i]) for i in range(len(di))}

	def read_ao(self):
		ao = None
		raw_ao = TelnetCommunication.cmd_and_return("AOA" + self.tc, False)
		ao = str.split(raw_ao)[3::4]
		return {descriptor_ao[i]: float(ao[i]) for i in range(len(ao))}

	def write_ao(self, channel, ao_value):
		TelnetCommunication.cmd_and_return("AA" + channel + " [" + ao_value + "]" + self.tc, True, self.ack)
		return True

	def zero_all_ao(self):
		TelnetCommunication.cmd_and_return("SA20" + self.tc, True, self.ack)

	def read_do(self):#change 0 to 1 and 1 to 0!
		do = None
		raw_do = TelnetCommunication.cmd_and_return("DOA" + self.tc, False)
		do_list = list(filter(str.isdigit, raw_do))
		for i in range(len(do_list)):
			if float([do[i]) == 1.0:
				do[descriptor_do[i]] = 0.0
			elif float([do[i]) == 0.0:
				do[descriptor_do[i]] = 1.0
			else: do[descriptor_do[i]] = float(do[i])
		return do

	def activate_do(self, channel):
#		print "Trying to activate channel " + channel
		TelnetCommunication.cmd_and_return("AD" + channel + self.tc, True, self.ack)
		return True

	def deactivate_do(self, channel):
#		print "Trying to deactivate channel " + channel
		TelnetCommunication.cmd_and_return("SD" + channel + self.tc, True, self.ack)
		return True

	def read_all(self):
		ai_dict = self.read_ai()
		#ao_dict = self.read_ao()
		di_dict = self.read_di()
		do_dict = self.read_do()
		#builds dictionary of all acquired data (analog and digital)
		data_dict = ai_dict.copy()
		#data_dict.update(ao_dict)
		#data_dict.update(di_dict)
		data_dict.update(do_dict)
		#build JSON object for database
		#print "\n_____Analog INPUT_____"
		#pp(ai_dict)
		#print "\n_____Analog OUTPUT_____"
		#pp(ao_dict)
		#print "\n_____Digital INPUT_____"
		#pp(di_dict)
		#print "\n_____Digital OUTPUT_____"
		#pp(do_dict)
		return data_dict

def check_aorange(value):
	"""
	checks if given output voltage is in the output range 0-10V
	"""
	if value < 0: value = 0
	if value > 10: value = 10
	return value

#db command functions
def cryo_cooler(adio, state):
	"""
	switches the cooler on and off
	"""
	do_ch = str(descriptor_do.index("squid_cooler"))
	if int(state) == 1:
		if adio.deactivate_do(do_ch): return "Switched SQUID cooler on"
		else: raise Exception("Couldn't switch SQUID cooler on!")
	else:
		if adio.activate_do(do_ch): return "Switched SQUID cooler off"
		else: raise Exception("Couldn't switch SQUID cooler off!")

def set_heater_power(unit, value):
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
	output = str(check_aorange(float(output)))
	if adio.write_ao(ao_ch, output): return "Heater power (CH{}) set to {} V.".format(ao_ch, output)
	else: raise Exception("Error setting heater power")

def set_heater_flow(value):
	"""
	this function sets the analog output voltage controlling the oven heater flow
	"""
	ao_ch = str(descriptor_ao.index("heater_flow"))
	output = str(check_aorange(float(value)/10))
	#flow not equal to zero, otherwise the heater turns off for safety reasons
	if float(output) < 0.5: output = "0.5"
	if adio.write_ao(ao_ch, output): return "Heater flow (CH{}) set to {} V".format(ao_ch, output)
	else: raise Exception("Error setting heater flow")


def field_switch(adio, state):
	"""
	switches the MSR field switch box to either of the two states 0110 (coil 1) or 1001 (coil 2)
	"""
	do_ch0 = str(descriptor_do.index("field_switch_1"))
	do_ch1 = str(descriptor_do.index("field_switch_2"))
	do_ch2 = str(descriptor_do.index("field_switch_3"))
	do_ch3 = str(descriptor_do.index("field_switch_4"))
	if int(state) == 0:
		if adio.deactivate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch0) and adio.activate_do(do_ch1): return "Fields switched off, sources on resistors"
		else: raise Exception("Error switching fields")
	elif int(state) == 1:
		if adio.deactivate_do(do_ch0) and adio.activate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch1): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	elif int(state) == 2:
		if adio.deactivate_do(do_ch1) and adio.activate_do(do_ch3) and adio.deactivate_do(do_ch2) and adio.activate_do(do_ch0): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	else: raise Exception("No valid argument, fields not switched!")

def set_high_voltage(hvsupply, value):
	"""
	this function sets the given digital output low
	"""
	ao_ch = str(descriptor_ao.index("hv_control_" + str(hvsupply)))
	output = str(check_aorange(float(value)))
	if adio.write_ao(ao_ch, output): return "HV supply #{} set to {} kV".format(hvsupply, output)
	else: raise Exception("Error setting HV value")

def hv_state(adio, hvsupply, state):
	"""
	enables or disables the high voltage output
	"""
	do_ch = str(descriptor_do.index("hv_enable_" + str(hvsupply)))
	if int(state) == 1:
		if adio.deactivate_do(do_ch): return "HV supply #{} - output enabled",format(hvsupply)
		else: raise Exception("Error enabling HV output of HV supply #{}".format(hvsupply))
	else:
		if adio.activate_do(do_ch): return "HV supply #{} - output disabled".format(hvsupply)
		else: raise Exception("Error disabling output of HV supply #{}".format(hvsupply))


def dig_init(adio):
#make sure all digital outs are activated, eg. in low state
	for i in range(len(descriptor_do)):
		if descriptor_do[i] == "field_switch_3" or descriptor_do[i] == "field_switch_4":
			adio.deactivate_do(str(i))
		else:
			adio.activate_do(str(i))
	log("WebADIO DO's initialized")


def filter_db_values(adio):
	final_dict = {}
	data_dict = adio.read_all()
	for k in data_dict.keys():
		if len(k) > 3: final_dict[k] = data_dict[k]
	return final_dict

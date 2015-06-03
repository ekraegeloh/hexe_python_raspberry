# -*- coding: utf-8 -*-
"""
@author: Florian Kuchler
"""

import telnetlib
import time
import signal
import cloudant
from pprint import pprint as pp
import pynedm


#devices connected to the various webadio channels
global descriptor_ai
global descriptor_di
global descriptor_do
descriptor_ai = ["hv_monitor_1", "hv_monitor_2", "hv_current_1", "hv_current_2", "hv_leakage_monitor", "gas_system_pressure", "ai6", "ai7"]
#descriptor_ao = ["hv_control_1", "hv_control_2", "heater_flow", "heater_power", "ao4", "ao5", "ao6", "ao7"]
descriptor_di = ["di0","di1", "di2", "di3", "di4", "di5", "di6", "di7"]
descriptor_do = ["field_switch_1","field_switch_2", "field_switch_3", "field_switch_4","hv_enable_1","hv_enable_2", "squid_cooler", "do7"]

#the class for the webadio board provides read and write functions
class webadio:
	global term_char
	global tn
	global prompt
	global adio_ack
	term_char = "\r\n"
	prompt = term_char + ">"
	adio_ack = " \x1b[34mdone \x1b[0;1m" + prompt
	
	tn = telnetlib.Telnet("192.168.1.65")
	

	def login(self, ip_adress, pw):
		#try:
			#tn = telnetlib.Telnet(ip_adress)
		#except Exception, e:
			#print "Connection to WebADIO not possible, reason: %s" % e
			#time.sleep(2)
			#return False
		tn.read_until("Password: ")
		try:
			tn.write(pw + term_char)
			print tn.read_until(prompt)
			return True
		except Exception, e:
			print "Connection not possible, reason: %s" % e
			time.sleep(2)
			return False

	def read_ai(self):
		ai = None
		tn.write("AIA" + term_char)
		time.sleep(0.1)
		raw_ai = tn.read_until(prompt)
		ai = str.split(raw_ai)[3::4]
		return {descriptor_ai[i]: float(ai[i]) for i in range(len(ai))}

	def read_di(self):
		di = None
		tn.write("DIA" + term_char)
		time.sleep(0.1)
		raw_di = tn.read_until(prompt)
		di = list(filter(str.isdigit, raw_di))
		return {descriptor_di[i]: float(di[i]) for i in range(len(di))}

	def read_ao(self):
		ao = None
		tn.write("AOA" + term_char)
		raw_ao = tn.read_until(prompt)
		ao = str.split(raw_ao)[3::4]
		return {descriptor_ao[i]: float(ao[i]) for i in range(len(ao))}

	def write_ao(self, channel, ao_value):
		tn.write("AA" + channel + " [" + ao_value + "]" + term_char)
		if tn.read_until(prompt) == adio_ack: return True
		else: return False

	def zero_all_ao(self):
		tn.write("SA20" + term_char)
		if tn.read_until(promtp) == adio_ack: return True
		else: return False

	def read_do(self):
		do = None
		tn.write("DOA" + term_char)
		time.sleep(0.1)
		raw_do = tn.read_until(prompt)
		do = list(filter(str.isdigit, raw_do))
		return {descriptor_do[i]: float(do[i]) for i in range(len(do))}

	def activate_do(self, channel):
#		print "Trying to activate channel " + channel
		tn.write("AD" + channel + term_char)
#		answer = tn.read_until(prompt)
		if tn.read_until(prompt) == adio_ack:
#			print "Channel " + channel + ": 1"
			return True
		else: return False

	def deactivate_do(self, channel):
#		print "Trying to deactivate channel " + channel
		tn.write("SD" + channel + term_char)
#		answer = tn.read_until(prompt)
		#if tn.read_until(prompt) == (" done" + prompt): return 1
		if tn.read_until(prompt) == adio_ack:
#			print "Channel " + channel + ": 0"
			return True
		else: return False

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

	def close(self):
		tn.write("q\r\n")
		tn.close()
		print 'Connection to WebADIO closed.'

#def check_aorange(value):
	#"""
	#checks if given output voltage is in the output range 0-10V
	#"""
	#if value < 0: value = 0
	#if value > 10: value = 10
	#return value

#db command functions
def cryo_cooler(adio, state):
	"""
	switches the cooler on and off
	"""
	do_ch = str(descriptor_do.index("squid_cooler"))
	if state =="1":
		if adio.deactivate_do(do_ch): return "Switched SQUID cooler on"
		else: raise Exception("Couldn't switch SQUID cooler on!")
	else:
		if adio.activate_do(do_ch): return "Switched SQUID cooler off"
		else: raise Exception("Couldn't switch SQUID cooler off!")

#def set_heater_power(unit, value):
	#"""
	#this function sets the analog output voltage controlling the oven heater power
	#"""
	#ao_ch = str(descriptor_ao.index("heater_power"))
	##max temperature/maximum voltage
	##print unit
	##print value
	#if unit == "C": output = (float(value) - 36.4)/32.3
	#if unit == "V": output = value
	#else: raise Exception("Unit unknown!")
	#output = str(check_aorange(float(output)))
	#if adio.write_ao(ao_ch, output): return "Heater power (CH{}) set to {} V.".format(ao_ch, output)
	#else: raise Exception("Error setting heater power")

#def set_heater_flow(value):
	#"""
	#this function sets the analog output voltage controlling the oven heater flow
	#"""
	#ao_ch = str(descriptor_ao.index("heater_flow"))
	#output = str(check_aorange(float(value)/10))
	##flow not equal to zero, otherwise the heater turns off for safety reasons
	#if float(output) < 0.5: output = "0.5"
	#if adio.write_ao(ao_ch, output): return "Heater flow (CH{}) set to {} V".format(ao_ch, output)
	#else: raise Exception("Error setting heater flow")


def field_switch(adio, state):
	"""
	switches the MSR field switch box to either of the two states 0110 (coil 1) or 1001 (coil 2)
	"""
	do_ch0 = str(descriptor_do.index("field_switch_1"))
	do_ch1 = str(descriptor_do.index("field_switch_2"))
	do_ch2 = str(descriptor_do.index("field_switch_3"))
	do_ch3 = str(descriptor_do.index("field_switch_4"))
	if state == '0':
		if adio.deactivate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch0) and adio.activate_do(do_ch1): return "Fields switched off, sources on resistors"
		else: raise Exception("Error switching fields")
	if state == '1':
		if adio.deactivate_do(do_ch0) and adio.activate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch1): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	if state == '2':
		if adio.deactivate_do(do_ch1) and adio.activate_do(do_ch3) and adio.deactivate_do(do_ch2) and adio.activate_do(do_ch0): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	else: raise Exception("No valid argument, fields not switched!")


def set_magnicon_status(adio, state):
	"""
	switches all magnicon sources on resistors (state 1100), or one on a coil (see field_switch)
	"""
	do_ch0 = str(descriptor_do.index("field_switch_1"))
	do_ch1 = str(descriptor_do.index("field_switch_2"))
	do_ch2 = str(descriptor_do.index("field_switch_3"))
	do_ch3 = str(descriptor_do.index("field_switch_4"))
	if state == '0':
		if adio.deactivate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch0) and adio.activate_do(do_ch1): return "Fields switched off, sources on resistors"
		else: raise Exception("Error switching fields")
	if state == '1':
		if adio.deactivate_do(do_ch0) and adio.activate_do(do_ch2) and adio.deactivate_do(do_ch3) and adio.activate_do(do_ch1): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	if state == '2':
		if adio.deactivate_do(do_ch1) and adio.activate_do(do_ch3) and adio.deactivate_do(do_ch2) and adio.activate_do(do_ch0): return "Fields switched to state {}".format(state)
		else: raise Exception("Error switching fields")
	else: raise Exception("No valid argument, fields not switched!")


#def set_high_voltage(hvsupply, value):
	#"""
	#this function sets the given digital output low
	#"""
	#ao_ch = str(descriptor_ao.index("hv_control_" + str(hvsupply)))
	#output = str(check_aorange(float(value)))
	#if adio.write_ao(ao_ch, output): return "HV supply #{} set to {} kV".format(hvsupply, output)
	#else: raise Exception("Error setting HV value")

def hv_state(adio, hvsupply, state):
	"""
	enables or disables the high voltage output
	"""
	do_ch = str(descriptor_do.index("hv_enable_" + str(hvsupply)))
	if state == "1":
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
	print "WebADIO DO's initialized"


def filter_db_values(adio):
	final_dict = {}
	data_dict = adio.read_all()
	for k in data_dict.keys():
		if len(k) > 3: final_dict[k] = data_dict[k]
	return final_dict

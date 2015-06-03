# -*- coding: utf-8 -*-
"""
@author: Eva Kraegeloh
"""

import time
import socket
import cloudant
import pynedm
import signal
import string


class hameg_supply:
	global hameg_tcp
	hameg_tcp=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	#creating socket via TCP:
	def open_socket(self, ip, port):
		try:
			hameg_tcp.connect((ip, port))
		except Exception, e:
			print 'Connection to HamegHMP4040 not possible, reason: %s' % e
			time.sleep(2)
			return False
		hameg_tcp.send("*IDN?\n")
		time.sleep(0.5)
		print "Connected to " + hameg_tcp.recv(2048)
		hameg_tcp.send("*RST\n")
		time.sleep(0.5)
		print "Device reset."
		hameg_tcp.send("SYST:REM\n")
		return True

	def close_socket(self):
		hameg_tcp.close()
		print 'Connection to HamegHMP4040 closed.'

	def read_volt(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("MEAS:VOLT?\n")
		return string.rstrip(hameg_tcp.recv(1024))

	def read_curr(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("MEAS:CURR?\n")
		return string.rstrip(hameg_tcp.recv(1024))

	def set_volt_max(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("VOLT MAX\n")
		hameg_tcp.send("*WAI\n")
		return

	def read_volt_max(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("VOLT? MAX\n")
		return string.rstrip(hameg_tcp.recv(1024))

	def read_curr_max(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("CURR? MAX\n")
		return string.rstrip(hameg_tcp.recv(1024))

	def set_curr(self, channel, curr):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("CURR " + str(curr) + "\n")
		hameg_tcp.send("*WAI\n")
		hameg_tcp.send("CURR?\n")
		response = float(string.rstrip(hameg_tcp.recv(1024)))
		if response != curr:
			raise ValueError("Not able to set current!")
		else:
			return

	def set_output(self, channel, state):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		if int(state) == 1: hameg_tcp.send("OUTP ON\n")
		else: hameg_tcp.send("OUTP OFF\n")
		return

	def get_output(self, channel):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP?\n")
		return string.rstrip(hameg_tcp.recv(1024))

	def ramp(self, channel, datastring):
		hameg_tcp.send("INST OUT" + str(channel) + "\n")
		time.sleep(0.1)
		hameg_tcp.send("OUTP:SEL ON\n")
		time.sleep(0.1)
		hameg_tcp.send("ARB:CLEAR\n")
		if datastring == "up":
			hameg_tcp.send("ARB:REST 1\n")
		elif datastring == "down":
			hameg_tcp.send(" ARB:REST 2\n")
		else:
			hameg_tcp.send("ARB:DATA " + string.rstrip(datastring) + "\n")
		hameg_tcp.send("*WAI\n")
		hameg_tcp.send("ARB:REP 1\n")
		hameg_tcp.send("ARB:TRAN " + str(channel) + "\n")
		hameg_tcp.send("*WAI\n")
		hameg_tcp.send("OUTP ON\n")
		hameg_tcp.send("ARB:START " + str(channel) + "\n")

#dictionary for coil-channel-relation
global coilchannel
coilchannel = {"pol" : 1, "trans" : 3, "guide" : 4}

#variables for coil currents and ramp time, initialized with standard values
global coil_currents
coil_currents = {1 : 3.1, 2 : 0.0, 3 : 3.1, 4 : 3.1}
global ramp_time
ramp_time = 10 #in s

def set_coil_current(coil, value):
    coil_currents[coil] = value
    return

def set_ramp_time(t):
    ramp_time = t
    return

def set_coil_status(hameg, coil, state):
    ch = coilchannel[coil]
    if ch == 1:
        hameg.set_curr(ch, coil_currents[ch])
        hameg.set_output(ch, state)
        time.sleep(0.1)
        if hameg.get_output(ch) != state:
            raise Exception('Not able to change status!')
        else: return
    else:
        n = 128 #no of data points for abitrary wave form
        stay_time = float(ramp_time)/128
        if stay_time < 0.01: #min time at one point 10ms
            n = int(float(ramp_time)/0.01)
            stay_time = float(ramp_time)/n
        elif stay_time > 60: #max time at one point 60s
            raise Exception('Ramp time too long!')
        curr_step = float(coil_currents[ch])/n
        data_string = ""
        data = []
        i = 0
        while i <= n:
            data.append(32)
            data.append(i*curr_step)
            data.append(stay_time)
            i = i+1
        if state == 1:
            j = 0
            while j < len(data)-1:
                data_string = data_string + str(data[j]) + ","
            data_string = data_string + str(data[-1])
        else:
            j = len(data)-1
            while j > 0:
                data_string = data_string + str(data[j]) + ","
            data_string = data_string + str(data[0])
        hameg.ramp(ch, data_string)
        if state == 0:
            time.wait(n*stay_time)
            hameg.set_output(0)
        return

def read_coil_currents(hameg):
	coil_dict = {}
	try:
		pol_curr = hameg.read_curr(1)
	except:
		pol_curr = False
	try:
		trans_curr = hameg.read_curr(3)
	except:
		trans_current = False
	try:
		guide_curr = hameg.read_curr(4)
	except:
		guide_curr = False
#    print "---Monitor---\nPolarizer coil current: "  + pol_curr + "\nTransport coil current: " + trans_curr + "\nGuide coil current: " + guide_curr
	if pol_curr != False:
		coil_dict['pol_coil_current'] = float(pol_curr)
	if trans_curr != False:
		coil_dict['trans_coil_current'] = float(trans_curr)
	if guide_curr != False:
		coil_dict['guide_coil_current'] = float(guide_curr)
	return coil_dict


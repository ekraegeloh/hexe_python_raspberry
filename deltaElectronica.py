# -*- coding: utf-8 -*-
"""
@author: Florian Kuchler
"""

import socket
import cloudant
import signal
import string
import pynedm
from socketclass import *

class delta_supply(SocketObj):
	def __init__(self):
		self.status = False

	def connect(self, ip_address, port):
		SocketObj.__init__(self, "DeltaElectronica Power Supply", ip_address, port, "tcp", "\n", self.status)
		try:
			answer = SocketObj.cmd_and_return("*IDN?\n")
			log("Connected to " + answer + "\n")
		except: log("Warning: No identification received from DeltaElectronica Power Supply")

	def read_voltage(self):
		return SocketObj.cmd_and_return("MEAS:VOLT?\n", False)

	def read_current(self):
		return SocketObj.cmd_and_return("MEAS:CURR?\n", False)

	def set_max_voltage(self, max_voltage):
		SocketObj.cmd_and_return("SOUR:VOLT:MAX " + str(max_voltage) +"\n")

	def read_max_voltage(self):
		return SocketObj.cmd_and_return("SOUR:VOLT:MAX?\n", False)

	def read_max_current(self):
		return SocketObj.cmd_and_return("SOUR:CURR:MAX?\n", False)

	def set_max_current(self, max_current):
		SocketObj.cmd_and_return("SOUR:MAX:CURR " + str(max_current) + "\n")

	def set_voltage(self, voltage):
		SocketObj.cmd_and_return("SOUR:VOLT " + str(voltage) + "\n")

	def set_current(self, current):
		SocketObj.cmd_and_return("SOUR:CURR " + str(current) + "\n")

	def set_output_state(self, state):
		if int(state) == 1: SocketObj.cmd_and_return("OUTP ON \n")
		else: SocketObj.cmd_and_return("OUTP OFF \n")

	def read_output_state(self):
		return SocketObj.cmd_and_return("OUTP?\n")

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
	return

def set_laser_status(delta, state):
	'''
	this funtion enables or disables the output of the laser power supply
	'''
	delta.set_output_state(state)
	return

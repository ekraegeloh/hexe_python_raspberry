# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 15:51:32 2015

@author: Florian Kuchler
"""

import socket
import cloudant
import select
from socketclass import *

class adam_reader(SocketObj):
	def __init__(self):
		self.status = False

	def connect(self, ip, port):
		SocketObj.__init__(self, "ADAM6015", ip, port, "udp", "\r", self.status)

	#dictionary for  the channel names
	global channel_desc
	channel_desc = {
		"0": "oven_temp1",
		"1": "oven_temp2",
		"2": "CH2",
		"3": "CH3",
		"4": "CH4",
		"5": "CH5",
		"6": "CH6",
		"7": "CH7"
		}

	def read_temp(self):
		adoc_dict = {}
		raw_temp = SocketObj.cmd_and_return("#01\r", False)
		temp_list = []
		if raw_temp == "?01":
			raise UnexpectedReturn("No confirmation from " + self.n + "!")
		else:
			raw_temp=raw_temp[1:]
			ch_number = 2
			temp_chars = 7
#       	 print '------------ ADAM6015:'
			for i in range(ch_number):
				temp_list.append(raw_temp[i*temp_chars:i*temp_chars+temp_chars])
				adoc_dict[channel_desc[str(i)]] = float(temp_list[i])
#        		 print channel_desc[str(i)] + ": " + temp_list[i] + ' [deg C]'
		return adoc_dict

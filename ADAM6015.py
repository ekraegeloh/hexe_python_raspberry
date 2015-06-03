# -*- coding: utf-8 -*-
"""
Created on Wed Feb 25 15:51:32 2015

@author: Florian Kuchler
"""

import time
import socket
import cloudant
import select

class adam_reader:
	global adam_temp_tcp
	adam_temp_tcp=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

	def connect(self, ip, port):
		try:
			adam_temp_tcp.connect((ip, port))
			print "Connected to ADAM6015"
			return True
		except Exception, e:
			print "Connection to ADAM6015 not possible, reason: %s" % e
			time.sleep(2)
			return False

	def disconnect(self):
		adam_temp_tcp.close()
		print 'Connection to ADAM6015 closed.'

	def read_temp(self):
		adoc_dict = {}
		adam_temp_tcp.send("#01\r")
		time.sleep(0.1)
		raw_temp = adam_temp_tcp.recv(1024)
		temp_list = []
		raw_temp=raw_temp[1:]
		ch_number = 2
		temp_chars = 7
#        print '------------ ADAM6015:'
		for i in range(ch_number):
			temp_list.append(raw_temp[i*temp_chars:i*temp_chars+temp_chars])
			adoc_dict[channel_desc[str(i)]] = float(temp_list[i])
#        	 print channel_desc[str(i)] + ": " + temp_list[i] + ' [deg C]'
		return adoc_dict

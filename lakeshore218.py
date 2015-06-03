# -*- coding: utf-8 -*-
"""
Created on Mon Mar 02 11:16:33 2015

@author: Benedikt Krammer
"""

import time
import socket
import cloudant

class lakeshore:
    global ls_tcp
    ls_tcp=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#creating socket via TCP:
    def connect(self, ip, port):
		try:
			ls_tcp.connect((ip, port))
			ls_tcp.send("*IDN? \n")
			time.sleep(0.5)
			print "Connected to " + ls_tcp.recv(1024)
			return True
		except Exception, e:
			print "Connection to Lakeshore218 not possible, reason: %s" % e
			time.sleep(2)
			return False
			
    def disconnect(self):
    	ls_tcp.close()
    	print "Connection to Lakeshore218 closed."

    def read_values(self):
    	adoc_dict={}
    	l = [1, 2, 3, 4, 5, 6 ,7 ,8]
        ls_tcp.send('KRDG?\n')
        time.sleep(0.5)
        val = ls_tcp.recv(1024)
        val = val[1:]
        val = val.partition('\r')[0]
        val = val.split(',+', -1)
#        print "------------------- Lakeshore:"
        for ch in l:
#			 print "Channel" + str(ch) + ":   " + str(val[ch-1]) + "[K]"
    		channel = 'LakeshoreCH'+ str(ch)
    		adoc_dict[channel] = val[ch-1]
    	return adoc_dict

# -*- coding: utf-8 -*-
"""
Created on Mon Mar 02 11:16:33 2015

@author: Benedikt Krammer
"""

import socket
import cloudant
from socketclass import *

class lakeshore(SocketObj):
    def __init__(self):
            self.status = False

    def connect(self, ip, port):
        SocketObj.__init__(self, "Lakeshore218", ip, port, "tcp", "\r", self.status)
        try:
            answer = SocketObj.cmd_and_return("*IDN? \n")
            log("Connected to " + answer + "\n")
        except: log("Warning: No identification received from DeltaElectronica Power Supply")

    def read_values(self):
        adoc_dict={}
        l = [1, 2, 3, 4, 5, 6 ,7 ,8]
        val = SocketObj.cmd_and_return('KRDG?\n', False)
        val = val[1:]
        val = val.split(',+', -1)
#        print "------------------- Lakeshore:"
        for ch in l:
#                        print "Channel" + str(ch) + ":   " + str(val[ch-1]) + "[K]"
                channel = 'LakeshoreCH'+ str(ch)
                adoc_dict[channel] = val[ch-1]
        return adoc_dict

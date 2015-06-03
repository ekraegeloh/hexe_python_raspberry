# -*- coding: utf-8 -*-
"""
@author: Florian Kuchler
"""

import time
import socket
import cloudant
import signal
import string
import pynedm

class delta_supply:
    global delta_tcp
    delta_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, ip_adress, port):
        try:
            delta_tcp.connect((ip_adress, port))
        except Exception, e:
            print "Connection to DeltaElectronica Power Supply not possible, reason: %s" % e
            time.sleep(2)
            return False
        delta_tcp.send("*IDN?\n")
        time.sleep(0.5)
        print "Connected to " + delta_tcp.recv(1024) + "\n"
        delta_tcp.send("*RST\n")
        time.sleep(0.5)
        print "Device reset."
        return True

    def disconnect(self):
        delta_tcp.close()
        print 'Connection to DeltaElectronica Power Supply closed.'

    def read_voltage(self):
        delta_tcp.send("MEAS:VOLT?\n")
        return string.rstrip(delta_tcp.recv(1024), "\n")

    def read_current(self):
        delta_tcp.send("MEAS:CURR?\n")
        return string.rstrip(delta_tcp.recv(1024), "\n")

    def set_max_voltage(self, max_voltage):
        delta_tcp.send("SOUR:VOLT:MAX " + str(max_voltage) +"\n")
        return

    def read_max_voltage(self):
        delta_tcp.send("SOUR:VOLT:MAX?\n")
        return string.rstrip(delta_tcp.recv(1024), "\n")

    def read_max_current(self):
        delta_tcp.send("SOUR:CURR:MAX?\n")
        return string.rstrip(delta_tcp.recv(1024), "\n")

    def set_max_current(self, max_current):
        delta_tcp.send("SOUR:MAX:CURR " + str(max_current) + "\n")

    def set_voltage(self, voltage):
        delta_tcp.send("SOUR:VOLT " + str(voltage) + "\n")

    def set_current(self, current):
        delta_tcp.send("SOUR:CURR " + str(current) + "\n")

    def set_output_state(self, state):
        if state == "1": delta_tcp.send("OUTP ON \n")
        else: delta_tcp.send("OUTP OFF \n")

    def read_output_state(self):
        delta_tcp.send("OUTP?\n")
        return string.rstrip(delta_tcp.recv(1024), "\n")

def init_laser(delta):
    '''
    This function sets the initial values for the laser
    '''
    print "Init state:"
    print "Maximum voltage: " + delta.read_max_voltage()
    print "Maximum current: " + delta.read_max_current()
    print "Output: " + delta.read_output_state()
    print "Setting voltage=8, current=0, output=0"
    delta.set_voltage(8)
    delta.set_current(0)
    delta.set_output_state(False)
    return

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

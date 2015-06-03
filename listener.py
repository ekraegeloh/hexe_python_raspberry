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

import ADAM6015
import lakeshore218
import deltaElectronica
import hamegHMP4040
import ADAM6224
import webAdio_telnet


buf = 1024

#handling strg-c
_should_quit = False

def sigint_handler(signum, frame):
    global _should_quit
    print "Handler received termination signal", signum
    _should_quit = True

signal.signal(signal.SIGINT, sigint_handler)

#database stuff
#acct = cloudant.Account(uri="http://raid.nedm1:5984")
#res = acct.login("hexe_edm", "clu$terXz")
#assert res.status_code == 200
#db = acct["nedm%2Fhexe_edm"] #grab hexe database
#des = db.design("nedm_default")

_server = "http://raid.nedm1:5984/"
_un = "hexe_edm"
_pw = "clu$terXz"
_db = "nedm%2Fhexe_edm"

po = pynedm.ProcessObject(_server, _un, _pw, _db)


adam_tempIP = '192.168.1.64'
adam_tempPort = 1025

lsIP = '192.168.1.51'
lsPort = 100

deltaIP = '192.168.1.70'
deltaPort = 8462

hamegIP = '192.168.1.51'
hamegPort = '300'

adam_aoIP = '192.168.1.67'
adam_aoPort = 1025

##WEBADIO configuration
#IP adress of the IPSES WEB-ADIO board
webadioIP = '192.168.1.65'
webadioPW = 'ipses'

adoc = {
	"type": "data", "value": {}
	}

adamT = ADAM6015.adam_reader()
adamT_connected = False
if adamT.connect(adam_tempIP, adam_tempPort): adamT_connected = True

lakesh = lakeshore218.lakeshore()
lakesh_connected = False
if lakesh.connect(lsIP, lsPort): lakesh_connected = True

#global delta
delta = deltaElectronica.delta_supply()
delta_connected = False
if delta.connect(deltaIP, deltaPort):
	delta_connected = True
	deltaElectronica.init_laser(delta)

hameg = hamegHMP4040.hameg_supply()
hameg_connected = False
if hameg.open_socket(hamegIP, hamegPort): hameg_connected = True

adamAO = ADAM6224.adam_setter()
adamAO_connected = False
if adamAO.connect(adam_aoIP, adam_aoPort):
	adamAO_connected = True
	adamAO.set_ranges()
	adamAO.zero_all_ao()

adio = webAdio_telnet.webadio()
adio_connected = False
if adio.login(webadioIP, webadioPW):
	adio_connected = True
	webAdio_telnet.dig_init(adio)
	
##functions for function dict
def set_heater_power(unit, value):
	ADAM6224.set_heater_power(adamAO, unit, value)
	return
	
def set_heater_flow(value):
	ADAM6224.set_heater_flow(adamAO, value)
	return

def set_laser_status(state):
	deltaElectronica.set_laser_status(delta, state)
	return
	
def set_laser_current(current):
	deltaElectronica.set_laser_current(delta, current)
	return
	
def set_coil_status(coil, state):
	hamegHMP4040.set_coil_status(hameg, coil, state)
	return
	
def hv_state(hvsupply, state):
	webAdio_telnet.hv_state(adio, hvsupply, state)
	return	
	
def set_high_voltage(hvsupply, value):
	ADAM6224.set_high_voltage(adamAO, hvsupply, value)
	return
	
def field_switch(state):
	webAdio_telnet.field_switch(adio, state)
	return
	
def set_magnicon_status(state):
	webAdio_telnet.set_magnicon_status(adio, state)
	return
	
def cryo_cooler(state):
	webAdio_telnet.cryo_cooler(adio, state)
	return
	
		
	
func_dict = {
	'set_oven_temp' : set_heater_power,
	'set_oven_flow' : set_heater_flow,
	'set_laser_status' : set_laser_status,
	'set_laser_current' : set_laser_current,
	'set_coil_status' : set_coil_status,
	'set_coil_current' : hamegHMP4040.set_coil_current,
	'set_ramp_time' : hamegHMP4040.set_ramp_time,
	'enable_high_voltage' : hv_state,
	'set_high_voltage' : set_high_voltage,
	'field_switch' : field_switch,
	'magnicon_to' : set_magnicon_status,
	'cryo_cooler' : cryo_cooler
	}


db_listener = pynedm.listen(func_dict, _db, username=_un, password=_pw, uri=_server)
print "Listening started."

while True:
	
	if adamT_connected:
		adam_temps = adamT.read_temp()
#		print adam_temps
		for Tname in adam_temps:
			adoc["value"][Tname] = float(adam_temps[Tname])

	if lakesh_connected:
		ls_values = lakesh.read_values()
#		print ls_values
		for key in ls_values:
			adoc["value"][key] = float(ls_values[key])

	if delta_connected:
		state = delta.read_output_state()
#		print state
		current = delta.read_current()	
#		print current
		#print "---Monitor---\nVoltage: " + delta.read_voltage() + "\nCurrent: " + current
		adoc['value']['laser_current'] = float(current)
		adoc['value']['laser_status'] = int(state)

	if hameg_connected:
		coil_dict = hamegHMP4040.read_coil_currents(hameg)
		print coil_dict
		for coil in coil_dict:
			adoc["value"][coil] = float(coil_dict[coil])

	if adamAO_connected:
		ao_values = ADAM6224.read_aos(adamAO)
		#print ao_values
		for aos in ao_values:
			adoc["value"][aos] = float(ao_values[aos])

	if adio_connected:
		adio_values = webAdio_telnet.filter_db_values(adio)
#		print adio_values
		for vals in adio_values:
			if vals == "heater_flow": adio_values[vals] = 10*adio_values[vals]
			adoc["value"][vals] = float(adio_values[vals])

	#print adoc
	po.write_document_to_db(adoc)
#	print "Written to DB"
	time.sleep(2)
	if pynedm.should_stop(): break
#    if pynedm.should_stop(): break


print "Quitting script..."
#wait for listener to stop
db_listener.wait()
print "listening stopped"
#close  connections
if adamT_connected: adamT.disconnect()
if lakesh_connected: lakesh.disconnect()
if delta_connected: delta.disconnect()
if hameg_connected: hameg.close_socket()
if adamAO_connected: adamAO.disconnect()
if adio_connected: adio.close()
print "All connections closed."


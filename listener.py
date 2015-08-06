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
#import hamegHMP4040
import ADAM6224
import webAdio_telnet


#handling strg-c
#_should_quit = False

#def sigint_handler(signum, frame):
#    global _should_quit
#    print "Handler received termination signal", signum
#    _should_quit = True

#signal.signal(signal.SIGINT, sigint_handler)

#database stuff
#acct = cloudant.Account(uri="http://raid.nedm1:5984")
#res = acct.login("hexe_edm", "clu$terXz")
#assert res.status_code == 200
#db = acct["nedm%2Fhexe_edm"] #grab hexe database
#des = db.design("nedm_default")

def main():

	#database info
	_server = "http://raid.nedm1:5984/"
	_un = "hexe_edm"
	_pw = "clu$terXz"
	_db = "nedm%2Fhexe_edm"

	#writing documents to DB with:
	po = pynedm.ProcessObject(_server, _un, _pw, _db)

	##info and init for devices
	adam_tempIP = '192.168.1.64'
	adam_tempPort = 1025
	adamT = ADAM6015.adam_reader()

	lsIP = '192.168.1.51'
	lsPort = 100
	lakesh = lakeshore218.lakeshore()

	deltaIP = '192.168.1.70'
	deltaPort = 8462
	delta = deltaElectronica.delta_supply()

	hamegIP = '192.168.1.51'
	hamegPort = '300'

	adam_aoIP = '192.168.1.67'
	adam_aoPort = 1025
	adamAO = ADAM6224.adam_setter()

	webadioIP = '192.168.1.65'
	webadioPW = 'ipses'
	adio = webAdio_telnet.webadio()

	#structure for documents to be written to DB
	adoc = {
		"type": "data", "value": {}
		}

#	hameg = hamegHMP4040.hameg_supply()
#	hameg_connected = False
#	if hameg.open_socket(hamegIP, hamegPort): hameg_connected = True

	##functions for function dict - exception handling by pynedm
	def set_heater_power(unit, value):
		ADAM6224.set_heater_power(adamAO, unit, value)
		webAdio_telnet.set_heater_power(adio, unit, value)
		return

	def set_heater_flow(value):
		ADAM6224.set_heater_flow(adamAO, value)
		webAdio_telnet.set_heater_flow(adio, value)
		return

	def set_laser_status(state):
		deltaElectronica.set_laser_status(delta, state)
		return

	def set_laser_current(current):
		deltaElectronica.set_laser_current(delta, current)
		return

#	def set_coil_status(coil, state):
#		hamegHMP4040.set_coil_status(hameg, coil, state)
#		return

	def hv_state(hvsupply, state):
		webAdio_telnet.hv_state(adio, hvsupply, state)
		return

	def set_high_voltage(hvsupply, value):
		ADAM6224.set_high_voltage(adamAO, hvsupply, value)
		webAdio_telnet.set_high_voltage(adio, hvsupply, value)
		return

	def field_switch(state):
		webAdio_telnet.field_switch(adio, state)
		return

	def cryo_cooler(state):
		webAdio_telnet.cryo_cooler(adio, state)
		return

	##dict to correlate DB commands and functions
	func_dict = {
		'set_oven_temp' : set_heater_power,
		'set_oven_flow' : set_heater_flow,
		'set_laser_status' : set_laser_status,
		'set_laser_current' : set_laser_current,
#		'set_coil_status' : set_coil_status,
#		'set_coil_current' : hamegHMP4040.set_coil_current,
#		'set_ramp_time' : hamegHMP4040.set_ramp_time,
		'enable_high_voltage' : hv_state,
		'set_high_voltage' : set_high_voltage,
		'field_switch' : field_switch,
		'cryo_cooler' : cryo_cooler
		}

	#start listener
	db_listener = pynedm.listen(func_dict, _db, username=_un, password=_pw, uri=_server)
	log("Listening started.")

	#should_quit() true automatically stops listener
	i = 1
	while not should_quit():

		if (i % 150) == 1:				#every 5 minutes
			if not adamT.status:		#if not connected
				try:
					adamT.connect(adam_tempIP, adam_tempPort)
				except Exception, e:
					log("ERROR: %s" % e)

			if not lakesh.status:
				try:
					lakesh.connect(lsIP, lsPort)
				except Exception, e:
					log("ERROR: %s" % e)

			if not delta.status:
				try:
					delta.connect(deltaIP, deltaPort)
					if delta.status:		#if connected - error w/o exception, but status False possible!
					try:
						delta.init_laser()
					except Exception, e:
						log("Couldn't initialize Laser, reason:%s", % e)
						delta.status = False
						delta.disconnect()
				except Exception, e:
					log("ERROR: %s" % e)

			if not adamAO.status:
				try:
					adamAO.connect(adam_aoIP, adam_aoPort)
					if adamAO.status:
						try:
							adamAO.set_ranges()
						except Exception, e:
							log("Warning: Couldn't set ranges for " + adamAO.n)
				except Exception, e:
					log("ERROR: %s" % e)

			if not adio.s:
				try:
					adio.open(webadioIP, webadioPW)
				except Exception, e:
					log("ERROR: %s" % e)


		if adamT.status:					#if connected, try reading
			try:
				adam_temps = adamT.read_temp()
				for Tname in adam_temps:
					adoc["value"][Tname] = float(adam_temps[Tname])
			except Exception, e:
				log("ERROR: %s" % e)

		if lakesh.status:
			try:
				ls_values = lakesh.read_values()
				for key in ls_values:
					adoc["value"][key] = float(ls_values[key])
			except Exception, e:
				log("ERROR: %s" % e)

		if delta.status:
			try:
				state = delta.read_output_state()
				current = delta.read_current()
#				print "---Monitor---\nVoltage: " + delta.read_voltage() + "\nCurrent: " + current
				adoc['value']['laser_current'] = float(current)
				adoc['value']['laser_status'] = int(state)
			except Exception, e:
				log("ERROR: %s" % e)

#		if hameg_connected:
#			coil_dict = hamegHMP4040.read_coil_currents(hameg)
#			log(coil_dict)
#			for coil in coil_dict:
#				adoc["value"][coil] = float(coil_dict[coil])

		if adamAO.status:
			try:
				ao_values = ADAM6224.read_aos(adamAO)
				for aos in ao_values:
					adoc["value"][aos] = float(ao_values[aos])
			except Exception, e:
				log("ERROR: %s" % e)

		if adio.s:
			try:
				adio_values = webAdio_telnet.filter_db_values(adio)
				for vals in adio_values:
					if vals == "heater_flow": adio_values[vals] = 10*adio_values[vals]
					adoc["value"][vals] = float(adio_values[vals])
			except Exception, e:
				log("ERROR: %s" % e)

		#write values to DB
		po.write_document_to_db(adoc)
		#wait 2s until reading next values
		time.sleep(2)

	#when should_quit():
	log("Listening stopped.")
	log("Quitting script...")
	#close  connections
	if adamT.status: adamT.disconnect()
	if lakesh.status: lakesh.disconnect()
	if delta.status: delta.disconnect()
#	if hameg_connected: hameg.close_socket()
	if adamAO.status: adamAO.disconnect()
	if adio.s: adio.close()
	log("All connections closed.")


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
import Expert_9132_9017M as expert
import alicat_mfc



def main():
	#database info
	_server = "http://raid.nedm1:5984/"
	_un = "hexe_edm"
	_pw = "clu$terXz"
	_db = "nedm%2Fhexe_edm"

#writing documents to DB with:
	po = pynedm.ProcessObject(_server, _un, _pw, _db)
#info and init for devices
	mfc_ip = '192.168.1.51'
	mfc_port = 200
	mfc = alicat_mfc.alicat_mfc(mfc_ip, mfc_port)

	adam_tempIP = '192.168.1.64'
	adam_tempPort = 1025
	adamT = ADAM6015.adam_reader(adam_tempIP, adam_tempPort)

	lsIP = '192.168.1.51'
	lsPort = 100
	lakesh = lakeshore218.lakeshore(lsIP, lsPort)

	deltaIP = '192.168.1.70'
	deltaPort = 8462
	delta = deltaElectronica.delta_supply(deltaIP, deltaPort)
	if delta.status:        #if connected - error w/o exception, but status False possible!
		try:
			delta.init_laser()
		except Exception, e:
			log("Couldn't initialize Laser, reason: %s" % e)
			delta.status = False
			delta.disconnect()

	hamegIP = '192.168.1.51'
	hamegPort = 300
	#hameg = hamegHMP4040.hameg_supply()
	#hameg_connected = False
	#if hameg.open_socket(hamegIP, hamegPort): hameg_connected = True

	adam_aoIP = '192.168.1.67'
	adam_aoPort = 1025
	adamAO = ADAM6224.adam_setter(adam_aoIP, adam_aoPort)
	if adamAO.status:
		try:
			adamAO.set_ranges()
		except Exception, e:
			log("Warning: Couldn't set ranges for " + adamAO.n + ", reason: %s" % e)

	expert_aiIP = 'hexeserial.2.nedm1'
	expert_aiPort = 1025
	expertAI = expert.expert_reader(expert_aiIP, expert_aiPort)

	webadioIP = '192.168.1.65'
	webadioPW = 'ipses'
	adio = webAdio_telnet.webadio(webadioIP, webadioPW)
	if adio.s:
		try:
			webAdio_telnet.dig_init(adio)
		except Exception, e:
			log("Warning: Couldn't initialize digital outputs of " + adio.n + ", reason: %s" % e)

##functions for function dict - exception handling by pynedm
	def set_heater_power(unit, value):
		resp = ADAM6224.set_heater_power(adamAO, unit, value)
		webAdio_telnet.set_heater_power(adio, unit, value)
		return resp

	def set_heater_flow(value):
		resp = ADAM6224.set_heater_flow(adamAO, value)
		webAdio_telnet.set_heater_flow(adio, value)
		return resp

	def set_laser_status(state):
		return deltaElectronica.set_laser_status(delta, state)

	def set_laser_current(current):
		return deltaElectronica.set_laser_current(delta, current)

#   def set_coil_status(coil, state):   
#       hamegHMP4040.set_coil_status(hameg, coil, state)
#       return

	def hv_state(hvsupply, state):
		return webAdio_telnet.hv_state(adio, hvsupply, state)

	def set_high_voltage(hvsupply, value):
		resp = ADAM6224.set_high_voltage(adamAO, hvsupply, value)
		webAdio_telnet.set_high_voltage(adio, hvsupply, value)
		return resp

	def set_mfcs(gas_flow_dict):
		return mfc.set_massflow(mfc, gas_flow_dict)

	def field_switch(state):
		webAdio_telnet.field_switch(adio, state)
		return

	def cryo_cooler(state):
		return webAdio_telnet.cryo_cooler(adio, state)

##dict to correlate DB commands and functions
	func_dict = {
		'set_oven_temp' : set_heater_power,
		'set_oven_flow' : set_heater_flow,
		'set_laser_status' : set_laser_status,
		'set_laser_current' : set_laser_current,
	#   'set_coil_status' : set_coil_status,
	#   'set_coil_current' : hamegHMP4040.set_coil_current,
	#   'set_ramp_time' : hamegHMP4040.set_ramp_time,
		'enable_high_voltage' : hv_state,
		'set_high_voltage' : set_high_voltage,
		'set_mfcs' : set_mfcs,
		'field_switch' : field_switch,
		'cryo_cooler' : cryo_cooler
	}

#structure for documents to be written to DB
	adoc = {
		"type": "data", "value": {}
	}

#start listener
	db_listener = pynedm.listen(func_dict, _db, username=_un, password=_pw, uri=_server)
	log("Listening started.")

#should_quit() true automatically stops listener
	i = 1
	while not should_quit():
		if (i % 150) == 0:              #every 5 minutes
			if not adamT.status:        #if not connected
				adamT = ADAM6015.adam_reader(adam_tempIP, adam_tempPort)
			if not lakesh.status:
				lakesh = lakeshore218.lakeshore(lsIP, lsPort)
			if not delta.status:
				delta = deltaElectronica.delta_supply(deltaIP, deltaPort)
				if delta.status:        #if connected - error w/o exception, but status False possible!
					try:
						delta.init_laser()
					except Exception, e:
						log("Couldn't initialize Laser, reason: %s" % e)
						delta.status = False
						delta.disconnect()
			if not adamAO.status:
				adamAO = ADAM6224.adam_setter(adam_aoIP, adam_aoPort)
				if adamAO.status:
					try:
						adamAO.set_ranges()
					except Exception, e:
						log("Warning: Couldn't set ranges for " + adamAO.n)
			if not expertAI.status:
				expertAI = expert.expert_reader(expert_aiIP, expert_aiPort)
			if not adio.s:
				adio = webAdio_telnet.webadio(webadioIP, webadioPW)
			if not mfc.status:
				mfc = alicat_mfc.alicat_mfc(mfc_ip, mfc_port)

		if adamT.status:                    #if connected, try reading
			try:
				adam_temps = adamT.read_temp()
				for Tname in adam_temps:
					adoc["value"][Tname] = float(adam_temps[Tname])
			except Exception, e:
				log(adamT.n + " ERROR: %s" % e)
		if expertAI.status:
			try:
				expert_values = expertAI.read_all()
				for ai in expert_values:
					adoc["value"][ai] = float(expert_values[ai])
			except Exception, e:
				log(expertAI.n + " ERROR: %s" % e)
		if lakesh.status:
			try:
				ls_values = lakesh.read_values()
				for key in ls_values:
					adoc["value"][key] = float(ls_values[key])
			except Exception, e:
				log(lakesh.n + " ERROR: %s" % e)
		if delta.status:
			try:
				state = delta.read_output_state()
				current = delta.read_current()
				#print "---Monitor---\nVoltage: " + delta.read_voltage() + "\nCurrent: " + current
				adoc['value']['laser_current'] = float(current)
				adoc['value']['laser_status'] = int(state)
			except Exception, e:
				log(delta.n + " ERROR: %s" % e)
#       if hameg_connected:
#           coil_dict = hamegHMP4040.read_coil_currents(hameg)
#           log(coil_dict)
#           for coil in coil_dict:
#               adoc["value"][coil] = float(coil_dict[coil])
		if adamAO.status:
			try:
				ao_values = ADAM6224.read_aos(adamAO)
				for aos in ao_values:
					adoc["value"][aos] = float(ao_values[aos])
			except Exception, e:
				log(adamAO.n + " ERROR: %s" % e)
		if adio.s:
			try:
				adio_values = webAdio_telnet.filter_db_values(adio)
				for vals in adio_values:
					if vals == "heater_flow": adio_values[vals] = 10*adio_values[vals]
					adoc["value"][vals] = float(adio_values[vals])
			except Exception, e:
				log(adio.n + " ERROR: %s" % e)
		if mfc.status:
			try:
				mfc_rdg = mfc.read_all()
				for val in mfc_rdg:
					adoc["value"][val] = float(mfc_rdg[val])
			except Exception, e:
				log(mfc.n + " ERROR: %s" % e)
#write values to DB
		po.write_document_to_db(adoc)
#counter
		i=i+1
#wait 2s until reading next values
		time.sleep(2)

#when should_quit():
	log("Listening stopped.")
	log("Quitting script...")
#close  connections
	if adamT.status: adamT.disconnect()
	if lakesh.status: lakesh.disconnect()
	if delta.status: delta.disconnect()
#   if hameg_connected: hameg.close_socket()
	if adamAO.status: adamAO.disconnect()
	if adio.s: adio.close()
	if mfc.status: mfc.disconnect()
	log("All connections closed.")

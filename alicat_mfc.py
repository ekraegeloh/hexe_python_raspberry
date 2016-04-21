import socketclass

global ranges
global mfcs

#identifiers for Helium, Xenon and Nitrogen MFCs
mfcs = {"he": "H", "xe": "X", "n2": "N"}
#max ranges of mfcs in sccm
ranges = {"he":100, "xe":20, "n2":5}

class alicat_mfc(socketclass.SocketObj):
	def __init__(self, ip, port):
		socketclass.SocketObj.__init__(self, "AlicatMFC", ip, port, "tcp", "\r")
	
	def read_all(self):
		#returned values, see manual
		data_format= ["identifier", "pressure", "temp", "vol_flow", "mass_flow", "mass_flow_set", "gas"]
		
		adoc_dict = {}
		for gas in mfcs:
			raw_data = self.cmd_and_return(mfcs[gas] + "\r", False)
			vals = raw_data.split()
			for i in range(1,6):
#                if i == 1: vals[i] = float(vals[i]) * 0.0689476 #convert psi to bar
				adoc_dict["mfc_" + gas + "_" + data_format[i]] = float(vals[i])
		return adoc_dict
		
def check_flow_range(gas, flow):
	if flow>ranges[str(gas)]: raise Exception("Flow rate for {} exceeds MFC's range, abort!".format(gas))#
	else: return flow
	
def set_massflow(mfc, gas_flow_dict):
	cmd_str = ""
	return_str = ""
	for gas in gas_flow_dict:
		flow = check_flow_range(gas, gas_flow_dict[gas])
		value = int(flow*64000/ranges[str(gas)])
		r = mfcs[str(gas)] + str(value) + "\r"
		cmd_str += r
		return_str += "MFC for {} set to {} sccm.\n".format(gas, float(value*ranges[str(gas)]/64000))
	mfc.cmd_and_return(cmd_str) 
	return return_str
			

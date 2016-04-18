import socket
import cloudant
import socketclass

class lakeshore(socketclass.SocketObj):
    def __init__(self, ip, port):
        socketclass.SocketObj.__init__(self, "Lakeshore218", ip, port, "tcp", "\r")
        try:
            answer = socketclass.SocketObj.cmd_and_return(self, "*IDN? \n")
            log("Connected to " + answer[18:] + "\n")
        except Exception, e:
			log("Warning: No identification received from " + self.n)
#		    log("Reason: %s" % e)

    def read_values(self):
        adoc_dict={}
        l = [1, 2, 3, 4, 5, 6 ,7 ,8]
        val = self.cmd_and_return('KRDG?\n', False)
        val = val[1:]
        val = val.split(',+', -1)
#        print "------------------- Lakeshore:"
        for ch in l:
#           print "Channel" + str(ch) + ":   " + str(val[ch-1]) + "[K]"
            channel = 'LakeshoreCH'+ str(ch)
            adoc_dict[channel] = val[ch-1]
        return adoc_dict

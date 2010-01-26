##
# A wrapper over the pysnmp Python module.
#
##

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

import time
import bisect


##
# Wrappers
##

class MibVariable:
	def __init__(self, oid, cb):
		self._cb = cb
		self.oid = oid
	def __cmp__(self, other):
		return cmp(self.oid, other)

class Gauge(MibVariable):
	def __call__(self, protocolVersion):
		ret = 0
		try:
			ret = self._cb()
		except:
			ret = 0
		print "Gauge %s returned: %s" % (self.oid, ret)
		return api.protoModules[protocolVersion].Gauge(ret)

class Counter(MibVariable):
	def __call__(self, protocolVersion):
		ret = 0
		try:
			ret = self._cb()
		except:
			ret = 0
		print "Counter %s returned: %s" % (self.oid, ret)
		return api.protoModules[protocolVersion].Counter(ret)

class String(MibVariable):
	def __call__(self, protocolVersion):
		ret = ""
		try:
			ret = self._cb()
		except:
			ret = ""
		print "String %s returned: %s" % (self.oid, ret)
		return api.protoModules[protocolVersion].OctetString(ret)



##
# Global variable registry
##
mibVariables = []
mibVariablesByOid = {} # indexed by oid

def registerGauge(oid, callback):
	return register(Gauge(convertOid(oid), callback))

def registerCounter(oid, callback):
	return register(Counter(convertOid(oid), callback))

def registerString(oid, callback):
	return register(String(convertOid(oid), callback))

def convertOid(oid):
	"""
	Convers a string oid to a tuple of ints
	(the internal oid representation for pysnmp)
	"""
	return tuple([ int(x) for x in oid.split('.') if x ])

def register(binding):
	"""
	Registers a new variable
	"""
	global mibVariables
	global mibVariablesByOid
	mibVariables.append(binding)
	mibVariablesByOid[binding.oid] = binding
	

##
# Main handler, called upon an SNMP request
##

def mainHandler(transportDispatcher, transportDomain, transportAddress, wholeMsg):
	while wholeMsg:
		msgVer = api.decodeMessageVersion(wholeMsg)
		if api.protoModules.has_key(msgVer):
			pMod = api.protoModules[msgVer]
		else:
			print 'Unsupported SNMP version %s' % msgVer
			return
		reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(), )
		rspMsg = pMod.apiMessage.getResponse(reqMsg)
		rspPDU = pMod.apiMessage.getPDU(rspMsg)		
		reqPDU = pMod.apiMessage.getPDU(reqMsg)
		varBinds = []
		errorIndex = -1
		
		# GET request
		if reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
			print "SNMP GET received..."
			for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
				if mibVariablesByOid.has_key(oid):
					varBinds.append((oid, mibVariablesByOid[oid](msgVer)))
				else:
					# No such instance
					pMod.apiPDU.setNoSuchInstanceError(rspPDU, errorIndex)
					varBinds = pMod.apiPDU.getVarBinds(reqPDU)
					break

		# GET-NEXT request
		elif reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
			print "SNMP GET-NEXT received..."
			# Produce response var-binds
			errorIndex = -1
			for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
				errorIndex = errorIndex + 1
				# Search next OID to report
				nextIdx = bisect.bisect(mibVariables, oid)
				if nextIdx == len(mibVariables):
					# Out of MIB
					pMod.apiPDU.setEndOfMibError(rspPDU, errorIndex)
				else:
					# Report value if OID is found
					varBinds.append((mibVariables[nextIdx].oid, mibVariables[nextIdx](msgVer)))

		else:
			print "Unsupported SNMP request received..."
			# Report unsupported request type
			pMod.apiPDU.setErrorStatus(rspPDU, -1) # we should use something different from -1

		pMod.apiPDU.setVarBinds(rspPDU, varBinds)
		transportDispatcher.sendMessage(encoder.encode(rspMsg), transportDomain, transportAddress)
	return wholeMsg


def main(port = 161):
	transportDispatcher = AsynsockDispatcher()
	transportDispatcher.registerTransport(udp.domainName, udp.UdpSocketTransport().openServerMode(('localhost', port)))
	transportDispatcher.registerRecvCbFun(mainHandler)
	transportDispatcher.jobStarted(1) # this job would never finish
	transportDispatcher.runDispatcher()

def define():
	registerGauge(".1.3.6.1.4.1.12345.1", lambda: 314)
	registerCounter(".1.3.6.1.4.1.12345.2", lambda: int(time.time()))
	registerString(".1.3.6.1.4.1.12345.3", lambda: "this is a random version.")
	

if __name__ == '__main__':
	define()
	main(port = 1161)

# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2010 Sebastien Lefevre and other contributors
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
##

##
# A testerman-oriented wrapper over the pysnmp Python module.
#
##

from pysnmp.carrier.asynsock.dispatch import AsynsockDispatcher
from pysnmp.carrier.asynsock.dgram import udp
from pyasn1.codec.ber import encoder, decoder
from pysnmp.proto import api

import logging
import time
import bisect
import threading

import ConfigManager

# The base OID in private enterprise:
# iso(1) org(1) dod(3) internet(6) private (4) enterprise(1) sl(35135) testerman(1)
# (registered private enterprise number - the testerman(1) is dedicated to testerman)
TESTERMAN_BASE_OID = ".1.1.3.6.1.4.1.35135.1"


################################################################################
# Logging
################################################################################

def getLogger():
	return logging.getLogger('SNMP')
	

################################################################################
# PySNMP Wrappers
################################################################################

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
		getLogger().debug("Gauge %s returned: %s" % (self.oid, ret))
		return api.protoModules[protocolVersion].Gauge(ret)

class Counter(MibVariable):
	def __call__(self, protocolVersion):
		ret = 0
		try:
			ret = self._cb()
		except:
			ret = 0
		getLogger().debug("Counter %s returned: %s" % (self.oid, ret))
		return api.protoModules[protocolVersion].Counter(ret)

class String(MibVariable):
	def __call__(self, protocolVersion):
		ret = ""
		try:
			ret = self._cb()
		except:
			ret = ""
		getLogger().debug("String %s returned: %s" % (self.oid, ret))
		return api.protoModules[protocolVersion].OctetString(ret)



################################################################################
# Global variable registry
################################################################################

mibVariables = []
mibVariablesByOid = {} # indexed by oid

def registerGauge(oid, callback):
	return register(Gauge(stringToOid(oid), callback))

def registerCounter(oid, callback):
	return register(Counter(stringToOid(oid), callback))

def registerString(oid, callback):
	return register(String(stringToOid(oid), callback))

def stringToOid(oid):
	"""
	Convers a string oid to a tuple of ints
	(the internal oid representation for pysnmp)
	"""
	if not oid.startswith('.'):
		# non-absolute OID: prefix with the testerman base OID
		oid = "%s.%s" % (TESTERMAN_BASE_OID, oid)
	
	return tuple([ int(x) for x in oid.split('.') if x ])

def oidToString(oid):
	return "." + ".".join([ str(x) for x in oid ])

def register(binding):
	"""
	Registers a new variable
	"""
	global mibVariables
	global mibVariablesByOid
	if not binding.oid in mibVariablesByOid:
		mibVariables.append(binding)
		mibVariablesByOid[binding.oid] = binding
	else:
		getLogger().error("Cannot register OID %s: already registered" % binding.oid)
	

################################################################################
# Main SNMP server wrapper class
################################################################################

class SnmpServer(threading.Thread):
	def __init__(self, address):
		threading.Thread.__init__(self)
		self._address = address
		self._transportDispatcher = AsynsockDispatcher()
		self._transportDispatcher.registerRecvCbFun(self.onSnmpMessage)

	def run(self):
		self._transportDispatcher.registerTransport(udp.domainName, udp.UdpSocketTransport().openServerMode(self._address))
		getLogger().info("Now listening on %s:%s" % self._address)
		self._transportDispatcher.jobStarted(1)
		try:
			self._transportDispatcher.runDispatcher(timeout = 1)
		except Exception, e:
			getLogger().error(u"Error while handling an SNMP message: %s" % unicode(e))
	
	def stop(self):
		self._transportDispatcher.jobFinished(1)
		self._transportDispatcher.closeDispatcher()
		self.join()

	# Main handler, called when receiving an SNMP request
	def onSnmpMessage(self, transportDispatcher, transportDomain, transportAddress, wholeMsg):
		while wholeMsg:
			msgVer = api.decodeMessageVersion(wholeMsg)
			if api.protoModules.has_key(msgVer):
				pMod = api.protoModules[msgVer]
			else:
				getLogger().error('Unsupported SNMP version %s' % msgVer)
				return
			reqMsg, wholeMsg = decoder.decode(wholeMsg, asn1Spec=pMod.Message(), )
			rspMsg = pMod.apiMessage.getResponse(reqMsg)
			rspPDU = pMod.apiMessage.getPDU(rspMsg)		
			reqPDU = pMod.apiMessage.getPDU(reqMsg)
			varBinds = []
			errorIndex = -1

			# GET request
			if reqPDU.isSameTypeWith(pMod.GetRequestPDU()):
				getLogger().info("SNMP GET received...")
				for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
					getLogger().debug("Trying to GET %s... " % oidToString(oid))
					if mibVariablesByOid.has_key(oid):
						varBinds.append((oid, mibVariablesByOid[oid](msgVer)))
					else:
						# No such instance
						pMod.apiPDU.setNoSuchInstanceError(rspPDU, errorIndex)
						varBinds = pMod.apiPDU.getVarBinds(reqPDU)
						break

			# GET-NEXT request
			elif reqPDU.isSameTypeWith(pMod.GetNextRequestPDU()):
				getLogger().info("SNMP GET-NEXT received...")
				# Produce response var-binds
				errorIndex = -1
				for oid, val in pMod.apiPDU.getVarBinds(reqPDU):
					getLogger().debug("Trying to GET-NEXT %s... " % oidToString(oid))
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
				getLogger().error("Unsupported SNMP request received...")
				# Report unsupported request type
				pMod.apiPDU.setErrorStatus(rspPDU, -1) # we should use something different from -1

			pMod.apiPDU.setVarBinds(rspPDU, varBinds)
			transportDispatcher.sendMessage(encoder.encode(rspMsg), transportDomain, transportAddress)
		return wholeMsg

TheSnmpServer = None

# SnmpServer singleton initialization

def initialize(address):
	global TheSnmpServer
	if address is None:
		address = (ConfigManager.get("snmp.ip", ""), int(ConfigManager.get("snmp.port", "1161")))
	TheSnmpServer = SnmpServer(address)
	TheSnmpServer.start()

def finalize():
	getLogger().info("Stopping...")
	TheSnmpServer.stop()
	getLogger().info("Stopped.")


##
# Some local testing
##

if __name__ == '__main__':
	logging.basicConfig(level = logging.DEBUG, format = '%(asctime)s.%(msecs)03d %(thread)d %(levelname)-8s %(name)-20s %(message)s', datefmt = '%Y%m%d %H:%M:%S')
	registerGauge(TESTERMAN_BASE_OID + ".1.0", lambda: 314)
	registerCounter(TESTERMAN_BASE_OID + ".2.0", lambda: int(time.time()))
	registerString(TESTERMAN_BASE_OID + ".3.0", lambda: "this is a random version.")
	initialize(('', 1161))
	try:
		while 1:
			time.sleep(1)
	except KeyboardInterrupt:
		finalize()
	

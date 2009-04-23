# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2008-2009 Sebastien Lefevre and other contributors
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
# RTP (and soon RTCP) probe
# - starts/stops sending RTP packets,
# - detects new (or stopped) incoming RTP streams.
#
# This probe is *not* based on a Testerman RTP codec, for performance reasons.
#
# Based on Anthony Baxter's LGPL'd RTP/RTCP packet encoder/decoder,
# used in Shtoom project.
#
##

import ProbeImplementationManager
import DefaultPayloads
# Modified version to support any codec
# (the standard Python wave module fails if the payload type is unknown to it)
import wave

import cStringIO as StringIO
import select
import socket
import threading
import time

# Shtoom RTP codec
import rtp
import rtp.packets
import rtp.rtcp


class LoopablePayload:
	"""
	Encapsulates a (string) payload as a cycling buffer,
	provides a getNextPacket() fonction to get
	the next packetSize repeated payload.
	
	Uses reset() to reset the stream if needed.
	
	Can be called indefinitly.
	
	"""
	def __init__(self, payload, packetSize):
		self._offset = 0
		self._packetSize = packetSize

		# The internal payload contains at least packetSize,
		# so that we don't have to manage N loops before
		# completing a packet
		self._payload = (packetSize / len(payload) + 1) * payload
		self._len = len(self._payload)
	
	def getNextPacket(self):
		# payload is at least packetSize.
		# we start at current offset, loop if needed.
		
		# the internal payload has been cycled to garantee
		# that we'll need to loop at most once to complete
		# our target packet size
		start = self._offset
		end = self._offset + self._packetSize
		if end > self._len: 
			end = end % self._len
			data = self._payload[start:] + self._payload[:end]
			self._offset = end
		else:
			data = self._payload[start:end]
			self._offset = end
		return data
		
	def reset(self):
		self._offset = 0

def getWavData(payload):
	"""
	Extracts the data frames from a WAV file.
	"""
	s = StringIO.StringIO(payload)
	w = wave.open(s)
	ret = w.readframes(w.getnframes())
	w.close()
	s.close()
	return ret

def loadPayload(payload, format):
	"""
	Extracts the actual payload from a higher-level
	format (wav, raw, ...)
	"""
	if not payload:
		return None
	elif format == 'raw':
		return payload
	elif format == 'wav':
		return getWavData(payload)
	else:
		raise Exception('Cannot load payload: unsupported payload format (%s)' % format)

def getPacketSizeAndSampleRate(payloadType, frameSize):
	"""
	Returns a (packet size, sample rate) couple according to
	the payload type and frame size.

	They cannot be guessed in all cases, but should be enough
	for most use cases.
	"""
	if payloadType == 0: # G711u / PCMU
		return (8*frameSize, 8000)
	elif payloadType == 8: # G711a / PCMA
		return (8*frameSize, 8000)
	elif payloadType == 18: # G729
		return (40, 8000) # 40 bytes per packet ?
	else: # Default value: assume linear, 8bit encoding, 8000 samples per packet...
		return (8*frameSize, 8000)			


class RtpProbe(ProbeImplementationManager.ProbeImplementation):
	"""
	= Identification and Properties =

	Probe Type ID: `rtp`

	Properties:
	|| '''Name''' || '''Type''' || '''Default value''' || '''Description''' ||
	|| `listening_ip` || string || `'0.0.0.0'` || Default listening IP address, when starting listening without providing one explicitly || 
	|| `listening_port` || integer || `0` || Default listening UDP port, when starting listening without providing one expliclity. `0` means a system-assigned port. ||
	|| `local_ip` || string || (empty) || Default source IP address when sending packets, if not provided explicitly when starting sending. An empty value means a system-assigned IP address. ||
	|| `local_port` || integer ||  `0` || Default UDP source port when sending packets, if not provided explicitly when starting sending. An empty value means a system-assigned port. ||
	|| `stream_timeout` || float || `0.5` || The maximum interruption interval allowed, in second, before considering an incoming stream has been stopped ||
	|| `ssrc` || integer || `1000` || The default SSRC to use in sent RTP packets, if not provided explicitly when starting sending a stream ||
	|| `payload_type` || integer || `8` || The default payload type to use in sent RTP packets, if not provided explicitly when starting sending a stream ||
	|| `frame_size` || integer || `20` || The default frame size to use when sending RTP packets, if not provided explicitly when starting sending a stream ||
	|| `packet_size` || integer || `160` || The default packet size to use when sending RTP packets, if not provided explicitly when starting sending a stream ||
	|| `sample_rate` || integer || `8000` || The default sample rate to use in sent RTP packets, if not provided explicitly when starting sending a stream ||
	
	The default payload type/frame size/packet size/sample rate values are chosen
	to enable a default stream in G.711 a-law (PCMA) / 20.
	
	= Overview =
	
	Through this probe, you can control sending and receiving RTP (Real Time Protocol)
	streams.[[BR]]
	It can be used as a probe companion of a UDP transport probe to simulate a SIP
	endpoint, or with a RTSP probe to act as a , and of course any other cases where
	controlling sending and receiving of RTP streams is required, without requiring to
	inspect each RTP packets individually.
	
	This probe is based on "signals" that change its state. You can:
	 * start sending a new RTP stream to a remote destination, setting the payload characteristics that will be used until the stream is stopped,
	 * stop sending a started stream
	 * start listening for, i.e. waiting for a possible incoming stream
	 * stop listening
	And you may receive the following "notifications" if the probe was in listening state:
	 * `StartedReceivingEvent`, indicating the payload properties (source ip/port, ssrc, payload type), when a new stream is detected or has been updated,
	 * `StoppedReceivingEvent`, when a stream being received was interrupted (or updated its properties

	Additionally, you may inject at any time while sending RTP
	a recorded payload using the `PlayCommand`. Currently the probe only supports:
	 * WAV file format:	the contained payload must be encoded with the correct codec (payload type). The probe won't check it.
	 * raw format: the payload is encoded using the correct codec, no header, no container.

	The probe sticks to packetize the payload according
	to the current frame size parameter. No transcoding mechanism is provided. 
	
	By default, when starting sending a RTP stream, a default sound is played according
	to the payload type:
	
	|| '''Payload type''' || '''Default sound''' ||
	|| 0 (PCMU/G711 u-law) || a tone ||
	|| 8 (PCMA/G711 a-law) || another tone ||
	|| Other codecs || Some very scratchy sound ||
	
	Anyway, the idea is that, by default, the probe makes some sound or noise.[[BR]]
	If you prefer start sending a silent sound, you should set the argument `defaultPayload` of
	`startSendingRtp` to what fits your need according to the codec. For reference:
	
	|| '''Payload type''' || '''Payload to use for a silence''' ||
	|| 0 (PCMU/G711 u-law) || `'\\xff'` ||
	|| 8 (PCMA/G711 a-law) || `'\\x00'` ||
	|| Other codecs || ... ||
	
	You may, of course, inject another payload as a default sound.
	
	Notes:
	 * A probe can send/receive at most one stream in a way (i.e. can send, receive, or send+receive).
	 * No RTCP support for now
	 * No RFC2833 support for now (excepted by playing a wav file with RFC2833 payload, but this is not integrated enough to be usable)

	 
	== Availability ==

	All platforms. Tested on Linux (kernel 2.6), Solaris 8, Solaris 10.

	== Dependencies ==

	None.

	== See Also ==


	= TTCN-3 Types Equivalence =
	
	The test system interface port bound to such a probe complies with the `RtpPortType` port type as specified below:
	{{{
	type record StartSendingCommand
	{
		integer payloadType optional, // default: payload_type (8)
		integer frameSize optional, // default: frame_size (20 (ms))
		integer ssrc optional, // default: ssrc (1000)
		integer packetSize optional, // default: packet_size (160 bytes, corresponding to 20ms in G711a/u)
		integer sampleRate optional, // default: sample_rate (8000 (Hz))
		
		// Local port may be controlled dynamically - useful when negotiating ports via SDP, etc
		integer fromPort optional, // default: local_port
		charstring fromIp optional, // default: local_ip

		// Default payload to play (infinite loop)
		octetstring defaultPayload optional, // default: see above, according to the codec
		charstring defaultPayloadFormat optional, // choice in wav, raw ; default: wav
	}
	
	type record StopSendingCommand
	{
	}
	
	type record StartListeningCommand
	{
		// Should we control the listening ip/port dynamically ? ...
		integer onPort optional, // default: listening_port
		charstring onIp optional, // default: listening_ip
		integer timeout optional, // timeout to detect interrupted incoming stream, in s
	}
	
	type record StopListeningCommand
	{
	}
	
	type record StartedReceivingEvent
	{
		integer fromPort,
		charstring fromIp,
		integer payloadType,
		integer ssrc,
	}
	
	type record StoppedReceivingEvent
	{
		integer fromPort,
		charstring fromIp,
		enum { interrupted, updated } reason,
	}
	
	type record PlayCommand
	{
		octetstring payload,
		integer loopCount optional, // default: 1
		charstring format optional, // choice in wav, raw ; default: wav
	}
	
	type union Command
	{
		StartSendingCommand startSendingRtp,
		StopSendingCommand stopSendingRtp,
		StartListeningCommand startListeningRtp,
		StopListeningCommand stopListeningRtp,
		PlayCommand play
	}
	
	type union Notification
	{
		StartedReceivingNotification startedReceivingRtp,
		StoppedReceivingNotification stoppedReceivingRtp
	}
	
	type port message RtpPortType
	{
		in Command,
		out Notification
	}
	}}}	
	"""
	def __init__(self):
		ProbeImplementationManager.ProbeImplementation.__init__(self)
		self._mutex = threading.RLock()
		self._stopEvent = threading.Event()
		self._listeningThread = None
		self._sendingThread = None
		
		# A pool of sockets in used, indexed by the local (ip, port)
		self._sockets = {}
		
		# A StringIO that contains the data to packetize and inject onto the network.
		self._dataToStream = None
		self._dataToStreamLoopCount = 0
		
		# Some default properties
		self.setDefaultProperty('local_port', 0)
		self.setDefaultProperty('local_ip', '')
		self.setDefaultProperty('payload_type', 8)
		self.setDefaultProperty('frame_size', 20)
		self.setDefaultProperty('sample_rate', 8000)
		self.setDefaultProperty('packet_size', 160)
		self.setDefaultProperty('listening_port', 0) # ? useful ? 
		self.setDefaultProperty('listening_ip', '')
		self.setDefaultProperty('ssrc', 1000)
		self.setDefaultProperty('stream_timeout', 0.5) # 500ms
		
	def _lock(self):
		self._mutex.acquire()
	
	def _unlock(self):
		self._mutex.release()
	
	def _isSending(self):
		self._lock()
		thread = self._sendingThread
		self._unlock()
		if thread: return True
		return False
	
	def _isListening(self):
		self._lock()
		thread = self._listeningThread
		self._unlock()
		if thread: return True
		return False

	def onTriMap(self):
		self._reset()
	
	def onTriUnmap(self):
		self._reset()
	
	def onTriSAReset(self):
		self._reset()
	
	def onTriExecuteTestCase(self):
		self._reset()
	
	def onTriSend(self, message, sutAddress):
		# Message format verification
		if not (isinstance(message, tuple) or isinstance(message, list)) and not len(message) == 2:
			raise Exception("Invalid message format")
		cmd, args = message

		# SUT Address format verification, if provided
		toIp, toPort = None, None
		if sutAddress:
			try:
				# Split a ip:port to a (ip, port)
				t = sutAddress.split(':')
				toIp, toPort = (t[0], int(t[1]))
			except:
				raise Exception("Invalid SUT Address when sending a message")
		
		
		if cmd == 'startSendingRtp':
			self._checkArgs(args, [ ('toIp', toIp), ('toPort', toPort), 
				('fromIp', self['local_ip']),
				('fromPort', self['local_port']), ('payloadType', self['payload_type']),
				('frameSize', self['frame_size']), ('ssrc', self['ssrc']),
				('defaultPayloadFormat', 'wav'), ('defaultPayload', '') ])
			
			toIp = args['toIp']
			toPort = args['toPort']
			fromIp = args['fromIp']
			fromPort = args['fromPort']
			payloadType = args['payloadType']
			frameSize = args['frameSize']
			ssrc = args['ssrc']
			
			# Try to guess/compute the packetsize/samplerate if not provided
			packetSize, sampleRate = getPacketSizeAndSampleRate(payloadType, frameSize)
			# The user may override these values
			if args.has_key('packetSize'):
				packetSize = args['packetSize']
			if args.has_key('sampleRate'):
				sampleRate = args['sampleRate']
			
			defaultPayload = loadPayload(args['defaultPayload'], args['defaultPayloadFormat'])
			if not defaultPayload:
				# Fallback to a hardcoded default, depending on the payload type
				defaultPayload = DefaultPayloads.getDefaultPayload(payloadType)
			
			# OK, all parameters have been retrieved.
			self.startSendingRtp((toIp, toPort), (fromIp, fromPort), payloadType, frameSize, packetSize, sampleRate, ssrc, defaultPayload)
		
		elif cmd == 'startListeningRtp':
			self._checkArgs(args, [ ('onPort', self['listening_port']), ('onIp', self['listening_ip']),
				('timeout', self['stream_timeout'])])
			
			onPort = args['onPort']
			onIp = args['onIp']
			timeout = args['timeout']
			
			self.startListeningRtp((onIp, onPort), timeout)
			
		elif cmd == 'stopSendingRtp':
			self.stopSendingRtp()

		elif cmd == 'stopListeningRtp':
			self.stopListeningRtp()
	
		elif cmd == 'play':
			self._checkArgs(args, [ ('payload', None), ('loopCount', 1), ('format', 'wav') ])
			payload = args['payload']
			loopCount = args['loopCount']
			type_ = args['type']

			data = loadPayload(payload, type_)
			self.playPayload(data, loopCount)

	def _reset(self):
		self.stopSendingRtp()
		self.stopListeningRtp()		

	def _getLocalSocket(self, addr):
		"""
		Returns a new or reused socket that binds on local address addr.
		Also adds a reference on it if the socket is reused.
		
		@type  addr: tuple (ip, port)
		@param addr: the local address of the socket to get
		
		@rtype: socket.Socket object
		@returns: a socket ready to use
		"""
		(ip, port) = addr
		if not ip:
			addr = ('0.0.0.0', port) # So that addr can match what a sock.getsockname() returns
		self._lock()
		sock = None
		
		try:
			if port == 0:
				# Let the system find a new port to listen onto: no collision risks.
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				sock.bind(addr)
				sock.setblocking(0)
				# Register the new socket (sock, refcount)
				self._sockets[sock.getsockname()] = (sock, 1)
			elif self._sockets.has_key(addr):
				# Reusable socket -> increment the associated refCount
				sock, refCount = self._sockets[addr]
				refCount += 1
				self._sockets[addr] = (sock, refCount)
			else:
				# No reusable socket. Creates a new one.
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				sock.bind(addr)
				sock.setblocking(0)
				# Register the new socket (sock, refcount)
				self._sockets[sock.getsockname()] = (sock, 1)
		except Exception, e:
			self._unlock()
			self.getLogger().error('Unable to get a local socket for %s' % str(addr))
			raise e
		
		self._unlock()
		return sock
			
	def _conditionallyCloseSocket(self, sock):
		"""
		Keeps open a shared socket, or closes it if not used anymore.
		Updates the ref count to it when needed.
		"""
		self._lock()
		try:
			addr = sock.getsockname()
			self.getLogger().debug("Checking if we should close shared socket %s" % str(addr))
			if self._sockets.has_key(addr):
				# OK, found. Decrement the refCount.
				s, refCount = self._sockets[addr]
				assert(s is sock)
				refCount -= 1
				if refCount <= 0:
					# OK, let's close it
					self.getLogger().debug("Closing shared socket %s" % str(addr))
					del self._sockets[addr]
					sock.close()
				else:
					# OK, just update the shared entry, not closing the socket.
					self._sockets[addr] = (s, refCount)
			else:
				self.getLogger().warning("Shared socket %s not found" % str(addr))
		except Exception, e:
			self.getLogger().warning("Unable to close socket conditionally: %s" % str(e))
		self._unlock()

	def startSendingRtp(self, toAddr, fromAddr, payloadType, frameSize, packetSize, sampleRate, ssrc, defaultPayload):
		self.getLogger().info("Starting sending RTP from %s to %s, pt %s, frame %s, size %s, sample rate %s, ssrc %s..." % (fromAddr, toAddr, payloadType, frameSize, packetSize, sampleRate, ssrc))
		# Stop our stream if needed
		self.stopSendingRtp()
		self._lock()
		self._defaultPayload = LoopablePayload(defaultPayload, packetSize)
		try:
			sock = self._getLocalSocket(fromAddr)
			self._sendingThread = SendingThread(self, sock, toAddr, payloadType, frameSize, packetSize, sampleRate, ssrc)
			self._sendingThread.start()
		except Exception, e:
			self.getLogger().error("Unable to start sending RTP: %s" % str(e))
		self._unlock()

	def startListeningRtp(self, fromAddr, timeout):
		self.getLogger().info("Starting listening RTP on %s, stream timeout %4.4fs..." % (fromAddr, timeout))
		# Stop listening if needed
		self.stopListeningRtp()
		self._lock()
		try:
			sock = self._getLocalSocket(fromAddr)
			self._listeningThread = ListeningThread(self, sock, timeout)
			self._listeningThread.start()
		except Exception, e:
			self.getLogger().error("Unable to start listening RTP: %s" % str(e))
		self._unlock()

	def playPayload(self, data, loopCount):
		"""
		Plays a payload within an outgoing stream, loopCount times.
		"""
		# If not currently playing RTP, ignore the request.
		if not self._isSending():
			return # nothing to do.
		
		self.getLogger().info("Playing new data %s times, data len is %s" % (loopCount, len(data)))

		# Now inject the data within the outgoing stream
		self._resetDataToStream()
		self._setDataToStream(data, loopCount)
	
	def getNextPacket(self, packetSize):
		"""
		Returns the payload of the next RTP packet,
		which is packetSize in length.
		
		Gets the payload either from a default resource stream
		depending on the payload type,
		or use the current resource/data to stream if available.
		
		Also prepares the source data for the next iteration.
		"""
		self._lock()
		if self._dataToStream:
			# File/payload to play, provided by the user
			try:
				data = self._dataToStream.read(packetSize)
				if len(data) < packetSize:
					self._dataToStreamLoopCount -= 1
					if self._dataToStreamLoopCount <= 0:
						self.getLogger().info("Data stream played. Now back to the default payload.")
						# TODO: send a notification to tell the userland the source has been played
						self._resetDataToStream()
					else:
						# Reset the stream for next loop
						self.getLogger().info("Resetting stream, remaining count %d" % self._dataToStreamLoopCount)
						self._dataToStream.seek(0)
					# We should "padd" our data with something to reach packetSize
					data += (packetSize - len(data)) * '\x00'
				self._unlock()
			except Exception, e:
				self._unlock()
				self.getLogger().warning("Unable to read next packet from source data to stream: %s" % str(e))	
				data = self._defaultPayload.getNextPacket()
		else:
			self._unlock()
			# No user provided stream to play - using default values
			data = self._defaultPayload.getNextPacket()
		
		return data

	def _setDataToStream(self, data, count):
		"""
		Sets some source data to stream asap.
		"""
		self._lock()
		try:
			self._dataToStream = StringIO.StringIO(data)
			self._dataToStreamLoopCount = count
		except Exception, e:
			self.getLogger().warning("Exception while setting data to stream: %s" % str(e))
		self._unlock()

	def _resetDataToStream(self):
		"""
		Reset the data to stream.
		"""
		self._lock()
		try:
			if self._dataToStream:
				self._dataToStream.close()
			self._dataToStream = None
			self._dataToStreamLoopCount = 0
		except Exception, e:
			self.getLogger().warning("Exception while resetting data to stream: %s" % str(e))
		self._unlock()
	
	def stopSendingRtp(self):
		self._lock()
		thread = self._sendingThread
		self._sendingThread = None
		self._unlock()
		if thread:
			thread.stop()

	def stopListeningRtp(self):
		self._lock()
		thread = self._listeningThread
		self._listeningThread = None
		self._unlock()
		if thread:
			thread.stop()


TWO_TO_THE_48TH = 2L<<48
TWO_TO_THE_32ND = 2L<<32

class SendingThread(threading.Thread):
	def __init__(self, probe, *args):
		"""
		Paramerers:
		fromSocket, toAddr,
		payloadType,
		frameSize,
		packetSize,
		sampleRase,
		ssrc
		"""
		threading.Thread.__init__(self)
		self._probe = probe
		self._args = args
		self._stopEvent = threading.Event()
	
	def stop(self):
		self._probe.getLogger().info("Stopping sending thread...")
		self._stopEvent.set()
		self.join()
		self._probe.getLogger().info("Sending thread stopped.")
	
	def run(self):
		"""
		RTP sending loop.
		"""
		fromSocket, toAddr, payloadType, frameSize, packetSize, sampleRate, ssrc = self._args
		
		# Some fixed values computation
		# interval between 2 packets, in s (float)
		interval = frameSize / 1000.0
		# We always (re)start our stream with a seq number = 0, and a timestamp ts to 0 too
		# (According to RFC1889, should be a unique ID instead)
		seq = 0
		ts = 0
		samplesPerPacket = frameSize * sampleRate / 1000
		# NB: for RFC2833, samplesPerPacket 160 should be used.
		self._probe.getLogger().info("Now sending RTP, %4.4fs between packets, %s samples per packet" % (interval, samplesPerPacket))

		while not self._stopEvent.isSet():
			try:
				# Let's build a RTP packet
				# The payload is a packetsize-bytes extract from the current played resource.
				data = self._probe.getNextPacket(packetSize)
				packet = rtp.packets.RTPPacket(ssrc, seq, ts, data, payloadType)

				packetBytes = packet.netbytes()

				# Log outgoing payloads only on first packet, with a packet as an example.
				if not seq:
					self._probe.logSentPayload("Sending RTP...", packetBytes)
				
				# the sequence number is linearly incremented by one.
				# Cycled on 2^48, at least according to Shtoom implementation.
				seq += 1
				if seq > TWO_TO_THE_48TH:
					seq -= TWO_TO_THE_48TH
				# The timestamp actually counts the samples.
				ts += samplesPerPacket
				if ts > TWO_TO_THE_32ND:
					ts -= TWO_TO_THE_32ND

				try:
					fromSocket.sendto(packetBytes, 0, toAddr)
				except Exception, e:
					self._probe.getLogger().warning("Exception while sending a RTP packet: %s" % str(e))
			except Exception, e:
				self._probe.getLogger().warning("Exception while sending RTP: %s " % str(e))
			# Wait our interval (should be an asynchronous tick, normally...)
			time.sleep(interval)

		self._probe._conditionallyCloseSocket(fromSocket)
		self._probe._resetDataToStream()


class ListeningThread(threading.Thread):
	def __init__(self, probe, *args):
		threading.Thread.__init__(self)
		self._probe = probe
		self._args = args
		self._stopEvent = threading.Event()
	
	def stop(self):
		self._probe.getLogger().info("Stopping listening thread...")
		self._stopEvent.set()
		self.join()
		self._probe.getLogger().info("Listening thread stopped.")
	
	def run(self):
		"""
		Starts listening RTP.
		"""
		fromSocket, timeout = self._args

		lastPt = None
		lastSourceIp = None
		lastSourcePort = None
		lastTime = None # Last time(stamp) we received a packet
		lastSsrc = None
		while not self._stopEvent.isSet():
			try:
				# Stream interrupted on timeout ?
				if (lastTime) and ((time.time() - lastTime) > timeout):
					self._probe.triEnqueueMsg(('stoppedReceivingRtp', { 'reason': 'interrupted' }))
					lastTime = None

				r, w, e = select.select([fromSocket], [], [], 0.01)
				if not fromSocket in r:
					continue
				
				# Something to read. Get it, decode it.
				(data, src) = fromSocket.recvfrom(10000)
				try:
					packet = rtp.packets.parse_rtppacket(data)
				except:
					self._probe.getLogger().info("Invalid RTP packet received")
					continue

				pt = packet.header.pt
				ssrc = packet.header.ssrc
				if not lastTime: # i.e. this is our first packet for the stream
					# Log incoming payloads only on first packet, with a packet as an example.
					self._probe.logReceivedPayload("Receiving RTP...", data)
					self._probe.triEnqueueMsg(('startedReceivingRtp', {'payloadType': pt, 'ssrc': ssrc, 'fromIp': src[0],
						'fromPort': src[1]}), "%s:%s" % src)
					lastTime = time.time()
				else:
					# Stream continued. Check for possible changes in properties
					# TODO: use a bitmap of updated properties
					if (pt, src[0], src[1], ssrc) != (lastPt, lastSourceIp, lastSourcePort, lastSsrc):
						# PT or emitter updated: raise a stop then a start event.
						self._probe.triEnqueueMsg(('stoppedReceivingRtp', {'reason': 'updated'}), "%s:%s" % src)
						self._probe.logReceivedPayload("Receiving RTP...", data)
						self._probe.triEnqueueMsg(('startedReceivingRtp', {'payloadType': pt, 'ssrc': ssrc, 'fromIp': lastSourceIp,
							'fromPort': lastSourcePort}), "%s:%s" % src)

				# Update stream properties with the current values
				lastPt = pt
				lastSourceIp, lastSourcePort = src
				lastSsrc = ssrc
				lastTime = time.time()
			
			except Exception, e:
				self._probe.getLogger().error("Exception while listening RTP: %s" % str(e))

		self._probe._conditionallyCloseSocket(fromSocket)

	
ProbeImplementationManager.registerProbeImplementationClass('rtp', RtpProbe)

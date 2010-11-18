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
# An extension of the standard Testerman Client,
# interfacing additional management functions.
#
##


import TestermanClient
import xmlrpclib

class Client(TestermanClient.Client):
	
	##
	# Specific Server Management functions
	##
	
	def purgeJobQueue(self, older_than):
		"""
		Purges jobs in the queue that:
		- are completed (any status)
		- and whose completion time is strictly older than the provided older_than timestamp (UTC)
	
		@type  older_than: float (timestamp)
		@param older_than: the epoch timestamp of the older job to keep
		
		@throws Exception in case of an error
		
		@rtype: int
		@returns: the number of purged jobs
		"""
		try:
			return self.__proxy.purgeJobQueue(older_than)
		except xmlrpclib.Fault, e:
			self.getLogger().error("Fault while purging old jobs: " + str(e))
			raise Exception(e.faultString)
		

	def persistJobQueue(self):
		try:
			return self.__proxy.persistJobQueue()
		except xmlrpclib.Fault, e:
			self.getLogger().error("Fault while persisting jobs: " + str(e))
			raise Exception(e.faultString)
	

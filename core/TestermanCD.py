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
# Codec manager - view from the TE
##

import CodecManager
import TestermanTCI

CodecManager.instance().setLogCallback(lambda x: TestermanTCI.logInternal("CD: %s" % x))

def instance():
	return CodecManager.instance()

def alias(name, codec, **kwargs):
	return instance().alias(name, codec, **kwargs)

def registerCodecClass(name, class_):
	return instance().registerCodecClass(name, class_)

def encode(name, template):
	return instance().encode(name, template)

def decode(name, data):
	return instance().decode(name, data)


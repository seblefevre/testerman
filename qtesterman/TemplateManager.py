# -*- coding: utf-8 -*-
##
# This file is part of Testerman, a test automation system.
# Copyright (c) 2009 QTesterman contributors
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
# Templates instance creator for editors
#
##

from PyQt4.Qt import *

from Base import *

import xml.dom.minidom
import xml.dom


# These functions (xmlToPythonStruct and xmlNodeToPythonStruct) are copied from server (as no client/server sharing mecanism exists)

def xmlToPythonStruct(xmlString):
	try:
		dom = xml.dom.minidom.parseString(xmlString) 
		return xmlNodeToPythonStruct(dom.documentElement)
	except Exception, e:
		print("Error: " + unicode(e).encode('utf-8'))
	
def xmlNodeToPythonStruct(node):
	if node.nodeType == node.ELEMENT_NODE:
		structList = { 'name' : node.nodeName }

		if node.hasAttributes(): 
			attributesList = {}
			for (attributeName, attributeValue) in node.attributes.items():
				attributesList[attributeName] = attributeValue
			structList['attributes'] = attributesList
			
		if node.hasChildNodes():
			childrenList = []
			for c in node.childNodes:
				childrenList.append(xmlNodeToPythonStruct(c))
			structList['children'] = childrenList
		
		return ("element", structList)

	elif node.nodeType == node.TEXT_NODE:
		return ("text", node.nodeValue)
	elif node.nodeType == node.CDATA_SECTION_NODE:
		try:
			dom = xml.dom.minidom.parseString(node.nodeValue) 

			return ("xmlcdata", xmlNodeToPythonStruct(dom.documentElement))
		
		except Exception, e:
			return ("cdata", node.nodeValue)
	else:
		return ("unsupported", node.nodeValue)

class WTemplateInstanceCreationDialog(QDialog):
	"""
	Form generated using template parameters
	"""
	def __init__(self, variables, templateName, templateDescription, parent = None):
		QDialog.__init__(self, parent)
		self.variables = variables
		self.title = templateName
		self.templateDescription = templateDescription
		self.__createWidgets()

	def __createWidgets(self):
		self.setWindowTitle("Template writer - %s" % self.title)
		layout = QVBoxLayout()
		if self.templateDescription != "":
			layout.addWidget(QLabel(self.templateDescription))

		variablesLayout = QGridLayout()
		self.lineEdits = {}
		i = 0
		for variable in self.variables:
			variablesLayout.addWidget(QLabel(variable.name + (' * ' * int(variable.mandatory)) + ':'), i, 0)
			self.lineEdits[variable.name] = QLineEdit(variable.default)
			self.lineEdits[variable.name].setToolTip(variable.description)
			variablesLayout.addWidget(self.lineEdits[variable.name], i, 1)
			i += 1
		layout.addLayout(variablesLayout)

		# Buttons
		self.okButton = QPushButton("Ok")
		self.connect(self.okButton, SIGNAL("clicked()"), self.accept)
		self.cancelButton = QPushButton("Cancel")
		self.connect(self.cancelButton, SIGNAL("clicked()"), self.reject)
		buttonLayout = QHBoxLayout()
		buttonLayout.addStretch()
		buttonLayout.addWidget(self.okButton)
		buttonLayout.addWidget(self.cancelButton)
		layout.addLayout(buttonLayout)
		self.setLayout(layout)
	
	def accept(self):
		notFilledMandatories = []
		for variable in self.variables:
			if variable.mandatory and self.lineEdits[variable.name].text() == "":
				notFilledMandatories.append(variable.name)
		if len(notFilledMandatories) == 0:
			QDialog.accept(self)
		else:
			QMessageBox.information(self, getClientName(), "Please fill these field(s) : %s" % (", ".join(notFilledMandatories)))

	def getVariablesValues(self):
		ret = {}
		for variable in self.variables:
			ret[variable.name] = unicode(self.lineEdits[variable.name].text())
		return ret

class TemplateWriterParam:
	"""
	A template param
	"""
	def __init__(self, name, description = None, default = None, mandatory = 0):
		self.name = name
		self.description = description
		self.default = default
		self.mandatory = mandatory

class TemplateWriter(QObject):
	"""
	Manage a template, create its parameters window and generates resulting code
	"""
	def __init__(self, name, description = None, shortcut = None, xmlFile = "", params = [], content= [], parent = None):
		QObject.__init__(self, parent)
		self.name = name
		self.description = description
		self.shortcut = shortcut
		self.params = params
		self.content = content
		self.xmlFile = xmlFile

	def generate(self, values):
		"""
		Generate code from template using parameters from parameters window (if necessary)
		"""
		result = ""
		for part in self.content:
			if part[0] == "text":
				result = result + part[1]
			else:
				result = result + values[part[1]]
		return result

	def activate(self):
		"""
		Show the parameters window if necessary, and generate code
		"""
		values = {}
		if len(self.params) > 0:
			dialog = WTemplateInstanceCreationDialog(self.params, self.name, self.description, self.parent())
			if dialog.exec_() == dialog.Accepted:
				values = dialog.getVariablesValues()
			else:
				return None
		#log(self.generate(values))
		return self.generate(values)

	def paramExists(self, paramName):
		"""
		Get template name using its shortcut
		"""
		for param in self.params:
			if param.name == paramName:
				return True
		return False

class TemplateManager(QObject):
	"""
	Creates templateWriters from one or many xml files
	"""
	def __init__(self, xmlFiles, parent = None):
		QObject.__init__(self, parent)
		self.templates = []
		for xmlFile in xmlFiles:
			self.xmlContent = None
			self.xmlFile = xmlFile
			try:
				fp = open(xmlFile, "r")
				filecontent = "".join(fp.readlines())
				fp.close()
				self.xmlContent = xmlToPythonStruct(filecontent)
			except Exception, e:
				log("DEBUG: default template file problem (%s) : %s" % (xmlFile, str(e)))
			self._createTemplateList()

	def _createTemplateList(self):
		if self.xmlContent is None:
			log("DEBUG: XML content is empty... Can't create template")
			return None
		else:
			try:
				if self.xmlContent[0] == "element" and self.xmlContent[1]["name"] == "templates":
					for template in self.xmlContent[1]["children"]: # parse templates
						if template[0] == "element" and template[1]["name"] == "template":
							currentTemplate = template[1]["attributes"]
							newTemplate = TemplateWriter(currentTemplate["name"], currentTemplate.get("description", ""), currentTemplate.get("shortcut", ""), self.xmlFile, [], [])
							for content in template[1]["children"]: # parse template's params
								if content[0] == "element":
									if content[1]["name"] == "param":
										currentContent = content[1]["attributes"]
										if not newTemplate.paramExists(currentContent["name"]):
											newTemplate.params.append(TemplateWriterParam(currentContent["name"], currentContent.get("description", ""), currentContent.get("default", ""), bool(int(currentContent.get("mandatory", "0")))))
										newTemplate.content.append(("param", currentContent["name"]))
									else:
										log("DEBUG: unknown element name parsing template file (not added): %s" % template[1]["name"])
								else:
									newTemplate.content.append(("text", content[1]))
							self.templates.append(newTemplate)
				return True
			except Exception, e:
				log("DEBUG: xml file structure seems to be invalid : %s" % str(e))
				return None

	def byName(self, name):
		"""
		Get template name using its name
		"""
		for template in self.templates:
			if template.name == name:
				return template
		return None

	def byShortcut(self, shortcut):
		"""
		Get template name using its shortcut
		"""
		for template in self.templates:
			if template.shortcut == shortcut:
				return template
		return None

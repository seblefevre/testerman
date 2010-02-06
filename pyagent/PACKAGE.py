##
# Package builder helper.
# Used by testerman-admin to package and publish the current source tree
# 
##

import Version

version = Version.VERSION

component_name = "pyagent"

included_files = [
"../core/CodecManager.py",
"../core/ProbeImplementationManager.py",
"../plugins",
"*.py",
"../common/*.py",
"CHANGELOG",
]

excluded_files = [
".CVS",
".svn",
"*.pyc",
"*.asn",
]




def getVersion():
	return version

def getComponentName():
	return component_name

def getIncludedFiles():
	return included_files

def getExcludedFiles():
	return excluded_files

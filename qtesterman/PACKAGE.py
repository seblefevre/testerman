##
# Package builder helper.
# Used by testerman-admin to package and publish the current source tree
# 
##

import Version

version = Version.CLIENT_VERSION

component_name = "qtesterman"

included_files = [
"*",
"../common/*.py",
]

excluded_files = [
".CVS",
".svn",
"*.pyc",
]




def getVersion():
	return version

def getComponentName():
	return component_name

def getIncludedFiles():
	return included_files

def getExcludedFiles():
	return excluded_files

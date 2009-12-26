#!/bin/sh
################################################################
# Component deployment helper: qtesterman
################################################################
#
# Sample usages:
#
# Build and deploy qtesterman from the source 
# as a testing version to the docroot ~/testerman:
#
#   deploy-qtesterman.sh ~/testerman 
#
# Same thing, but as a stable version: 
#
#   deploy-qtesterman.sh ~/testerman stable
#
# Build and deploy the same component, but advertise it
# as being version 2.0.0 (this can be used to force updates):
#
# deploy-qtesterman.sh ~/testerman stable 2.0.0
#

component="qtesterman"

if [ $# -lt 1 ] ; then
	echo "Usage: $0 <docroot> [branch [version]]"
	exit 1
fi

# The usual software
PYTHON=/usr/bin/python
TAR=/bin/tar
CP=/bin/cp
MKDIR=/bin/mkdir
RM=/bin/rm
CHMOD=/bin/chmod
MV=/bin/mv
DIRNAME=/usr/bin/dirname
CWD=`pwd`

# Computed variables
DIR=`/usr/bin/dirname $0`
COMPONENT_ADMIN=${DIR}/component-admin.py
TMP_DIR=/tmp/.$$
TMP_ARCHIVE=${TMP_DIR}/.${component}.tgz
# The Testerman source tree root
sourcerootdir="${DIR}/.."

# User variables
# Version
docroot=$1
branch=$2
version=$3

if [ "x${branch}" = "x" ]; then
	branch="testing"
fi

if [ "x${version}" = "x" ]; then
	version=`cat ${sourcerootdir}/qtesterman/Base.py | grep ^CLIENT_VERSION | cut -d\" -f 2`
fi

if [ "x${version}" = "x" ]; then
	echo "Error: cannot autodetect component version."
	exit 1
fi

echo "Deploying $component as version $version, branch $branch..."

##
# Component archive packaging
##
echo "Packaging $component..."
$MKDIR -p $TMP_DIR/$component || exit 1

$CP -frL ${sourcerootdir}/qtesterman/* $TMP_DIR/$component/
$CP -fL ${sourcerootdir}/common/*.py $TMP_DIR/$component/
# Make sure everything is writable (for autoupdates)
$CHMOD u+w -R $TMP_DIR/*
cd $TMP_DIR && $TAR cvzf $TMP_ARCHIVE --exclude "*.asn" --exclude "*.pyc" --exclude ".svn" ${component} > /dev/null

##
# Deployment
##
cd $CWD
$PYTHON $COMPONENT_ADMIN deploy -c ${component} -v ${version} -b ${branch} -a $TMP_ARCHIVE -r ${docroot}

##
# Cleanup
##
$RM -rf $TMP_DIR

#!/bin/sh
################################################################
# Component publishing helper: qtesterman
################################################################
#
# (compatibility script - simply wraps testerman-admin)
#
# Sample usages:
#
# Build and deploy pyagent from the source 
# as a testing version to the docroot ~/testerman:
#
#   qtesterman-pyagent.sh ~/testerman 
#
# Same thing, but as a stable version: 
#
#   qtesterman-pyagent.sh ~/testerman stable
#
# Build and deploy the same component, but advertise it
# as being version 2.0.0 (this can be used to force updates):
#
#   qtesterman-pyagent.sh ~/testerman stable 2.0.0
#


component="qtesterman"

if [ $# -lt 1 ] ; then
	echo "Usage: $0 <docroot> [branch [version]]"
	exit 1
fi

# Computed variables
DIR=`/usr/bin/dirname $0`
TESTERMAN_ADMIN=${DIR}/../admin/testerman-admin.py
# The Testerman source tree root
TESTERMAN_SRCROOT="${DIR}/.."

# User variables
# Version
docroot=$1
branch=$2
version=$3

cmd="source-publish component ${component}"

if [ "x${branch}" != "x" ]; then
	cmd="${cmd} branch ${branch}"
fi

if [ "x${version}" != "x" ]; then
	cmd="${cmd} version ${version}"
fi


${TESTERMAN_ADMIN} -r ${docroot} -t ${TESTERMAN_SRCROOT} -c testerman/components ${cmd}

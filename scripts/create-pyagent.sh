#!/bin/sh
# Package a pyagent to a tar file.
#
#

if [ $# -lt 2 ] ; then
	echo "Usage: $0 <testerman source tree root> <outputfilename>"
	exit 1
fi

# The Testerman source tree root
sourcerootdir=$1
# Output filename (without the file extension)
target=$2

commonfiles=common/*
plugins=plugins/*
pyagent=pyagent/*

TMPDIR=/tmp/.pyagent

TAR=/bin/tar
CP=/bin/cp
MKDIR=/bin/mkdir
RM=/bin/rm
CHMOD=/bin/chmod
MV=/bin/mv

echo "Packaging pyagent to $target..."

$MKDIR -p $TMPDIR/pyagent || exit 1

$CP ${sourcerootdir}/core/CodecManager.py $TMPDIR/pyagent/
$CP ${sourcerootdir}/core/ProbeImplementationManager.py $TMPDIR/pyagent/
$CP -r ${sourcerootdir}/plugins $TMPDIR/pyagent/plugins
$CP ${sourcerootdir}/pyagent/* $TMPDIR/pyagent/
$CP ${sourcerootdir}/common/*.py $TMPDIR/pyagent/
# Make sure everything is writable (for autoupdates)
$CHMOD u+w -R $TMPDIR/*

cd $TMPDIR && $TAR cvf ${TMPDIR}/.pyagent.tar --exclude "*.asn" --exclude "*.pyc" --exclude ".svn" pyagent

$MV ${TMPDIR}/.pyagent.tar ${target}.tar
$RM -rf $TMPDIR

echo "pyagent is now available as $target.tar"

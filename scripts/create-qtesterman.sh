#!/bin/sh
# Package a qtesterman to a tar file.
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
qtesterman=qtesterman/*

TMPDIR=/tmp/.qtesterman

TAR=/bin/tar
CP=/bin/cp
MKDIR=/bin/mkdir
RM=/bin/rm
CHMOD=/bin/chmod
MV=/bin/mv

echo "Packaging qtesterman to $target..."

$MKDIR -p $TMPDIR/qtesterman || exit 1

$CP -rL  ${sourcerootdir}/qtesterman/* $TMPDIR/qtesterman/
$CP -L ${sourcerootdir}/common/*.py $TMPDIR/pyagent/
# Make sure everything is writable (for autoupdates)
$CHMOD u+w -R $TMPDIR/*

cd $TMPDIR && $TAR cvf ${TMPDIR}/.qtesterman.tar --exclude "*.pyc" --exclude ".svn" --exclude "qtesterman/resources/*" qtesterman

$MV ${TMPDIR}/.qtesterman.tar ${target}.tar
$RM -rf $TMPDIR

echo "qtesterman is now available as $target.tar"

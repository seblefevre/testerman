#!/bin/bash

SRC_DIR=./src
TMP_DIR=build
VERSION=`grep -o '<em:version>[^<]*' $SRC_DIR/install.rdf | grep -o '[0-9].*'`
FILE_NAME="testerman-formatter-${VERSION}.xpi"

# remove any left-over files from previous build
rm -f $FILE_NAME > /dev/null

mkdir -p $TMP_DIR
cp -r $SRC_DIR/* $TMP_DIR
cd $TMP_DIR
echo "Generating $FILE_NAME ..."
zip -r ../$FILE_NAME *

cd - > /dev/null
rm -rf $TMP_DIR

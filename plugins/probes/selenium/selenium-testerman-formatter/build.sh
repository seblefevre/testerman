#!/bin/bash
 
APP_NAME=testerman-formatter	# xpi name
APP_VERSION=1.1 		# plugin version
 
SRC_DIR=$APP_NAME
TMP_DIR=build
 
# remove any left-over files from previous build
rm -f $APP_NAME.xpi
 
mkdir -p $TMP_DIR/chrome/content/formats
 
cp -v -r $SRC_DIR/chrome/content $TMP_DIR/chrome
cp -v $SRC_DIR/install.rdf $TMP_DIR
cp -v $SRC_DIR/chrome.manifest $TMP_DIR
 
# generate the plugin
cd $TMP_DIR
echo "Generating $APP_NAME.xpi..."
zip -r ../$APP_NAME-$APP_VERSION.xpi *

cd - > /dev/null
rm -rf $TMP_DIR

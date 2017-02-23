#!/bin/bash

#############################################
# Builds Ulauncher Preferences UI witn nodejs
#############################################

set -ex

cd `dirname $0`
cd ../data/preferences

npm install
./node_modules/.bin/bower install -F --allow-root
./gulp build

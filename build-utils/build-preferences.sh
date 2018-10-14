#!/usr/bin/env bash

#############################################
# Builds Ulauncher Preferences UI with nodejs
#############################################

set -ex

cd `dirname $0`
cd ../data/preferences

yarn install
yarn lint
yarn unit
yarn build

#!/usr/bin/env bash

#############################################
# Builds Ulauncher Preferences UI with nodejs
#############################################
build-preferences () {
    set -ex

    cd data/preferences

    yarn install
    yarn lint
    yarn unit
    yarn build
}

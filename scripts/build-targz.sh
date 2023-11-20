#!/usr/bin/env bash

##############################################################
# Builds tar.gz file with (un)install script and Ulauncher src
##############################################################
build-targz () {
    version=$(./ul version)

    echo "#########################################"
    echo "# Building ulauncher v$version sdist #"
    echo "#########################################"

    ./setup.py build_prefs --force
    rm -rf ulauncher.egg-info # https://stackoverflow.com/a/59686298/633921
    python3 -m build --sdist
    echo "Build sdist to ./dist"
}

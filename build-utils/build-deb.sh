#!/bin/bash

######################
# Builds Ulauncher.deb
######################

# Run with --bin to create .deb file
# [!] Requires GPGKEY environment variable

set -ex

buildUtils=`dirname $0`

bash "$buildUtils/build-preferences.sh"

name="ulauncher"
tmpdir="/tmp"
tmpsrc="$tmpdir/$name"

rm -rf $tmpdir || true
mkdir -p $tmpsrc || true

rsync -aq --progress \
    AUTHORS \
    bin \
    data \
    debian \
    LICENSE \
    README.md \
    setup.cfg \
    setup.py \
    ulauncher \
    ulauncher.desktop.in \
    $tmpsrc \
    --exclude-from=.gitignore

rm -rf $tmpsrc/data/preferences/*
cp -r data/preferences/index.html data/preferences/build $tmpsrc/data/preferences

cd $tmpsrc

if [ "$1" = "--bin" ]; then
    dpkg-buildpackage -tc -us -sa -k$GPGKEY
else
    dpkg-buildpackage -tc -S -sa -k$GPGKEY
fi

#!/bin/bash

######################
# Builds Ulauncher.deb
######################

# Args:
# $1 version
# $2 [optional] '--deb'   to create .deb file
#
# [!] Requires GPGKEY environment variable

if [ -z "$1" ]; then
    echo "First argument should be version"
    exit 1
fi

echo "##################################"
echo "# Building ulauncher_$1_all.deb"
echo "##################################"

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

sed -i "s/%VERSION%/$1/g" $tmpsrc/setup.py
sed -i "s/%VERSION%/$1/g" $tmpsrc/debian/changelog

cd $tmpsrc

if [ "$2" = "--deb" ]; then
    dpkg-buildpackage -tc -us -sa -k$GPGKEY
else
    dpkg-buildpackage -tc -S -sa -k$GPGKEY
fi

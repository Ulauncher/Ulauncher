#!/bin/bash

##############################################################
# Builds tar.gz file with (un)install script and Ulauncher src
##############################################################

# Args:
# $1 - version

echo "###################################"
echo "# Building ulauncher-$1.tar.gz"
echo "###################################"

set -ex

buildUtils=`dirname $0`

bash "$buildUtils/build-preferences.sh"

name="ulauncher"
tmpdir="/tmp/$name"

rm -rf $tmpdir || true
mkdir -p $tmpdir || true
rsync -aq --progress \
    AUTHORS \
    bin \
    data \
    LICENSE \
    README.md \
    setup.cfg \
    setup.py \
    install.sh \
    uninstall.sh \
    ulauncher \
    ulauncher.desktop.dev \
    ulauncher.desktop.in \
    $tmpdir \
    --exclude-from=.gitignore

rm -rf $tmpdir/data/preferences/*
cp -r data/preferences/index.html data/preferences/build $tmpdir/data/preferences

# set version to a tag name ($1)
sed -i "s/__version__ =.*/__version__ = '$1'/g" $tmpdir/ulauncher/config.py

filename=$name
if [ ! -z "$1" ]; then
    filename="$name_$1"
fi

cd /tmp
tar czf $filename.tar.gz $name
rm -rf $tmpdir

echo
echo "/tmp/$filename.tar.gz is built"
echo

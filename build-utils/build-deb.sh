#!/usr/bin/env bash

######################
# Builds Ulauncher.deb
######################

# Args:
# $1 version
# $2 --deb | --upload
#
# Env vars:
# GPGKEY required for upload
# PPA required for upload
# RELEASE release name required for upload

if [ -z "$1" ]; then
    echo "First argument should be version"
    exit 1
fi

echo "######################"
echo "# Building DEB package"
echo "######################"

set -ex

buildUtils=`dirname $0`
buildUtils=`realpath $buildUtils`

# bash "$buildUtils/build-preferences.sh"

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
cp -r data/preferences/dist $tmpsrc/data/preferences

sed -i "s/%VERSION%/$1/g" $tmpsrc/setup.py

cd $tmpsrc

if [ "$2" = "--deb" ]; then
    sed -i "s/%VERSION%/$1/g" $tmpsrc/debian/changelog
    dpkg-buildpackage -tc -us -sa -k$GPGKEY
    echo "$tmpdir/${name}_${1}_all.deb is created"
elif [ "$2" = "--upload" ]; then
    if [ -z "$RELEASE" ]; then
        echo "ERROR: RELEASE env var is not supplied"
        exit 1
    fi
    if [ -z "$GPGKEY" ]; then
        echo "ERROR: GPGKEY env var is not supplied"
        exit 1
    fi
    if [ -z "$PPA" ]; then
        echo "ERROR: PPA env var is not supplied"
        exit 1
    fi

    # replace version and release name
    sed -i "s/trusty/$RELEASE/g" $tmpsrc/debian/changelog
    sed -i "s/%VERSION%/${1}-0ubuntu1ppa1~${RELEASE}/g" $tmpsrc/debian/changelog

    # import GPG keys
    if gpg --list-keys | grep -q $GPGKEY; then
        echo "GPG key is already imported"
    else
        echo "Importing GPG key"
        gpg --import $buildUtils/launchpad-public.key
        gpg --import $buildUtils/launchpad-secret.key
    fi

    # build and upload
    dpkg-buildpackage -tc -S -sa -k$GPGKEY
    dput ppa:$PPA /tmp/*.changes
else
    echo
    echo "ERROR: Invalid arguments supplied"
    exit 1
fi

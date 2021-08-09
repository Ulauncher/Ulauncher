#!/usr/bin/env bash

##############################################################
# Builds tar.gz file with (un)install script and Ulauncher src
##############################################################
build-targz () {
    # Args:
    # $1 - version

    echo "###################################"
    echo "# Building ulauncher-$1.tar.gz"
    echo "###################################"

    set -ex

    ./ul build-preferences --skip-if-built

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
        ulauncher \
        ulauncher.desktop.in \
        ulauncher.service \
        $tmpdir \
        --exclude-from=.gitignore

    rm -rf $tmpdir/data/preferences/*
    cp -r data/preferences/dist $tmpdir/data/preferences

    # set version to a tag name ($1)
    sed -i "s/__version__ =.*/__version__ = '$1'/g" $tmpdir/ulauncher/config.py
    sed -i "s/%VERSION%/$1/g" $tmpdir/setup.py

    filename=$name
    if [ ! -z "$1" ]; then
        filename="${name}_$1"
    fi

    cd /tmp
    tar czf $filename.tar.gz $name
    rm -rf $tmpdir

    set +x

    echo
    echo "/tmp/$filename.tar.gz is built"
    echo
}

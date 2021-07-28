#!/usr/bin/env bash

######################
# Builds Ulauncher.rpm
######################
build-rpm () {

    # Args:
    # required: $1 version
    # required: $2 distro name (feodra, centos7). It should match with a suffix in setup.cfg
    # optional: $3 file suffix

    echo "##################################"
    echo "# Building ulauncher-$1.noarch.rpm"
    echo "##################################"

    if [ -z "$1" ]; then
        echo "First argument should be version"
        exit 1
    fi

    if [ -z "$2" ]; then
        echo "Second argument should a distro name"
        exit 1
    fi

    if [ ! -f data/preferences/index.html ]; then
        echo "Preferences are not built"
        exit 1
    fi

    set -ex

    version=$1
    distro_name=$2
    file_suffix=${3:-$distro_name}
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
        $tmpdir \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $tmpdir/data/preferences

    # set version to a tag name
    sed -i "s/%VERSION%/$version/g" $tmpdir/setup.py

    cd $tmpdir

    sed -i "s/\[bdist_rpm_$distro_name\]/[bdist_rpm]/g" setup.cfg
    python3 setup.py bdist_rpm
    find . -name "*noarch.rpm" -print0 | xargs -0 -I file cp file /tmp/ulauncher_$1_$file_suffix.rpm
}

#!/usr/bin/env bash

######################
# Builds Ulauncher.rpm
######################
build-rpm () {
    # Args:
    # required: $1 distro name (feodra, centos7). It should match with a suffix in setup.cfg
    # optional: $2 file suffix

    version=$(./setup.py --version)
    distro_name=$1
    file_suffix=${2:-$distro_name}
    name="ulauncher"
    tmpdir="/tmp/$name"

    echo "##################################"
    echo "# Building ulauncher-$version.noarch.rpm"
    echo "##################################"

    if [ -z "$1" ]; then
        echo "First argument should a distro name"
        exit 1
    fi

    if [ ! -f data/preferences/index.html ]; then
        echo "Preferences are not built"
        exit 1
    fi

    set -ex


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
        io.ulauncher.Ulauncher.desktop \
        $tmpdir \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $tmpdir/data/preferences

    cd $tmpdir

    sed -i "s/\[bdist_rpm_$distro_name\]/[bdist_rpm]/g" setup.cfg
    python3 setup.py bdist_rpm
    find . -name "*noarch.rpm" -print0 | xargs -0 -I file cp file /tmp/ulauncher_$version_$file_suffix.rpm
}

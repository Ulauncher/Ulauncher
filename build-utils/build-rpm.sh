#!/usr/bin/env bash

######################
# Builds Ulauncher.rpm
######################

# Args:
# $1 version

echo "##################################"
echo "# Building ulauncher-$1.noarch.rpm"
echo "##################################"

if [ -z "$1" ]; then
    echo "First argument should be version"
    exit 1
fi

if [ ! -f data/preferences/dist/index.html ]; then
    echo "Preferences are not built"
    exit 1
fi

set -ex

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

rm -rf $tmpdir/data/preferences/*
cp -r data/preferences/dist $tmpdir/data/preferences

# set version to a tag name ($1)
sed -i "s/%VERSION%/$1/g" $tmpdir/setup.py

cd $tmpdir

# build for Fedora
python setup.py bdist_rpm
find . -name "*noarch.rpm" -print0 | xargs -0 -I file cp file /tmp/ulauncher_$1_fedora.rpm

# build for OpenSUSE
sed -i "s/\[bdist_rpm\]/[bdist_rpm_fedora]/g" setup.cfg
sed -i "s/\[bdist_rpm_suse\]/[bdist_rpm]/g" setup.cfg
python setup.py bdist_rpm
find . -name "*noarch.rpm" -print0 | xargs -0 -I file cp file /tmp/ulauncher_$1_suse.rpm

# build for CentOS 7
sed -i "s/\[bdist_rpm\]/[bdist_rpm_suse]/g" setup.cfg
sed -i "s/\[bdist_rpm_centos7\]/[bdist_rpm]/g" setup.cfg
python setup.py bdist_rpm
find . -name "*noarch.rpm" -print0 | xargs -0 -I file cp file /tmp/ulauncher_$1_centos7.rpm

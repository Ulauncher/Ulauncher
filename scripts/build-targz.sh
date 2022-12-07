#!/usr/bin/env bash

##############################################################
# Builds tar.gz file with (un)install script and Ulauncher src
##############################################################
build-targz () {
    version=$(./setup.py --version)
    name="ulauncher"
    tmpdir="/tmp/$name"

    echo "###################################"
    echo "# Building ulauncher-$version.tar.gz"
    echo "###################################"

    set -ex
    ./setup.py build_prefs --force

    rm -rf $tmpdir || true
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
        ulauncher.service \
        $tmpdir \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $tmpdir/data/preferences

    filename=$name
    if [ ! -z "$version" ]; then
        filename="${name}_$version"
    fi

    cd /tmp
    tar czf $filename.tar.gz $name
    rm -rf $tmpdir

    set +x

    echo
    echo "/tmp/$filename.tar.gz is built"
    echo
}

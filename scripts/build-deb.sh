#!/usr/bin/env bash

######################
# Builds Ulauncher.deb
######################
build-deb () {
    # Args:
    #   $1 version
    #   $2 --deb | --upload
    #
    # Env vars:
    #   PPA required for upload
    #   RELEASE release name required for upload
    #   GPGKEY [optional] for upload

    set -e

    GPGKEY=${GPGKEY:-6BD735B0}
    dest_dir=$(dirname `pwd`)
    version=$(fix-version-format "$1")

    if [ -z "$version" ]; then
        error "First argument should be a version"
        exit 1
    fi

    h2 "Building DEB package for Ulauncher $version..."

    underline "Checking that current version is not in debian/changelog"
    if grep -q "$version" debian/changelog; then
        error "debian/changelog already has a record about this version"
        exit 1
    fi

    # back up debian/changelog and setup.py
    if [[ -f /tmp/changelog ]]; then
        cp /tmp/changelog debian/changelog
        cp /tmp/setup.py setup.py
    else
        cp debian/changelog /tmp
        cp setup.py /tmp/setup.py
    fi

    sed -i "s/%VERSION%/$version/g" setup.py

    if [ "$2" = "--deb" ]; then
        sed -i "s/%VERSION%/$version/g" debian/changelog
        dpkg-buildpackage -tc -us -sa -k$GPGKEY
        success "ulauncher_${version}_all.deb saved to $dest_dir"
    elif [ "$2" = "--upload" ]; then
        if [ -z "$RELEASE" ]; then
            error "RELEASE env var is not supplied"
            exit 1
        fi
        if [ -z "$PPA" ]; then
            error "PPA env var is not supplied"
            exit 1
        fi

        # replace version and release name
        sed -i "s/%RELEASE%/$RELEASE/g" debian/changelog
        sed -i "s/%VERSION%/${version}-0ubuntu1ppa1~${RELEASE}/g" debian/changelog

        underline "Importing GPG keys"
        if gpg --list-keys | grep -q $GPGKEY; then
            info "GPG key is already imported"
        else
            gpg --import scripts/launchpad-public.key
            gpg --import scripts/launchpad-secret.key
            success "GPG key has been imported"
        fi

        underline "Starting dpkg-buildpackage"
        dpkg-buildpackage -tc -S -sa -k$GPGKEY

        underline "Uploading to launchpad"
        dput ppa:$PPA $dest_dir/*.changes
    else
        error "Second argument must be either --deb or --upload"
        exit 1
    fi

    # restore changelog
    if [[ -f /tmp/changelog ]]; then
        cp /tmp/changelog debian/changelog
        cp /tmp/setup.py setup.py
    fi
}

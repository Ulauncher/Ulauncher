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
    version=$1
    # Debian prerelease separator is "~" instead of "-" (semver prerelease separator)
    deb_version=$(echo "$version" | tr "-" "~")

    if [ -z "$version" ]; then
        error "First argument should be a version"
        exit 1
    fi

    h2 "Building DEB package for Ulauncher $version..."

    info "Checking that current version is not in debian/changelog"
    if grep -q "$deb_version" debian/changelog; then
        error "debian/changelog already has a record about this version"
        exit 1
    fi

    src_dir=$(pwd)
    name="ulauncher"
    tmpdir="/tmp"
    tmpsrc="$tmpdir/$name"

    info "Building Preferences UI"
    ./ul build-preferences --skip-if-built

    info "Copying src to a temp dir"
    rm -rf $tmpdir/* || true
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
        ulauncher.service \
        $tmpsrc \
        --exclude-from=.gitignore
    rm -rf $tmpsrc/data/preferences/*
    cp -r data/preferences/dist $tmpsrc/data/preferences

    cd $tmpsrc
    sed -i "s/%VERSION%/$version/g" setup.py

    if [ "$2" = "--deb" ]; then
        sed -i "s/%VERSION%/$deb_version/g" debian/changelog
        sed -i "s/%RELEASE%/xenial/g" debian/changelog
        info "Building deb package"
        dpkg-buildpackage -tc -us -sa -k$GPGKEY
        success "ulauncher_${version}_all.deb saved to $tmpdir"
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
        sed -i "s/%VERSION%/${deb_version}-0ubuntu1ppa1~${RELEASE}/g" debian/changelog
        sed -i "s/%RELEASE%/$RELEASE/g" debian/changelog

        info "Importing GPG keys"
        if gpg --list-keys | grep -q $GPGKEY; then
            info "GPG key is already imported"
        else
            gpg --import $src_dir/scripts/launchpad-public.key
            gpg --import $src_dir/scripts/launchpad-secret.key
            success "GPG key has been imported"
        fi

        info "Starting dpkg-buildpackage"
        dpkg-buildpackage -tc -S -sa -k$GPGKEY

        info "Uploading to launchpad"
        dput ppa:$PPA $tmpdir/*.changes
    else
        error "Second argument must be either --deb or --upload"
        exit 1
    fi
}

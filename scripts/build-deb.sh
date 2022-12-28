#!/usr/bin/env bash

######################
# Builds Ulauncher.deb
######################
build-deb () {
    # Args:
    #   $1 --deb | --upload
    #
    # Env vars:
    #   PPA required for upload
    #   RELEASE release name required for upload
    #   GPGKEY [optional] for upload

    set -e

    GPGKEY=${GPGKEY:-6BD735B0}
    version=$(./setup.py --version)
    # Debian prerelease separator is "~" instead of "-" (semver prerelease separator)
    deb_version=$(echo "$version" | tr "-" "~")

    h2 "Building DEB package for Ulauncher $version..."

    info "Checking that current version is not in debian/changelog"
    if grep -q "$deb_version" debian/changelog; then
        error "debian/changelog already has a record about this version"
        exit 1
    fi

    src_dir=$(pwd)
    tmpdir="/tmp/ulauncher"

    info "Building Preferences UI"
    ./setup.py build_prefs --force

    info "Copying src to a temp dir"
    rm -rf $tmpdir/* || true
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
        io.ulauncher.Ulauncher.desktop \
        ulauncher.service \
        $tmpdir \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $tmpdir/data/preferences

    cd $tmpdir

    if [ "$1" = "--deb" ]; then
        sed -i "s/%VERSION%/$deb_version/g" debian/changelog
        sed -i "s/%RELEASE%/bionic/g" debian/changelog
        info "Building deb package"
        dpkg-buildpackage -tc -us -sa -k$GPGKEY
        success "ulauncher_${version}_all.deb saved to /tmp"
    elif [ "$1" = "--upload" ]; then
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
        sed -i "s/%VERSION%/$deb_version/g" debian/changelog
        sed -i "s/%RELEASE%/bionic/g" debian/changelog
        info "Building deb package"
        dpkg-buildpackage -tc --no-sign
        success "ulauncher_${version}_all.deb saved to /tmp"
    fi
}

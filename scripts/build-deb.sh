#!/usr/bin/env bash

######################
# Builds Ulauncher.deb
######################
build-deb () {
    # Args:
    #   $1 --signed | --upload
    #
    # Env vars:
    #   PPA required for upload
    #   RELEASE release name required for upload
    #   GPGKEY [optional] for upload

    set -e

    GPGKEY=${GPGKEY:-B96482D36BD735B0}
    version=$(./ul version)
    # Debian prerelease separator is "~" instead of "-" (semver prerelease separator)
    deb_version=$(echo "$version" | tr "-" "~")

    h2 "Building DEB package for Ulauncher $version..."

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
        io.ulauncher.Ulauncher.service \
        ulauncher.service \
        $tmpdir \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $tmpdir/data/preferences

    cd $tmpdir

    if [ "$1" = "--upload" ]; then
        if [ -z "$RELEASE" ]; then
            error "RELEASE env var is not supplied"
            exit 1
        fi
        if [ -z "$PPA" ]; then
            error "PPA env var is not supplied"
            exit 1
        fi

        info "Importing GPG keys"
        if gpg --list-keys | grep -q $GPGKEY; then
            info "GPG key is already imported"
        else
            gpg --import $src_dir/scripts/launchpad-public.key
            gpg --import $src_dir/scripts/launchpad-secret.key
            success "GPG key has been imported"
        fi

        info "Starting dpkg-buildpackage"
        rm debian/changelog || true
        dch --create --no-multimaint --package ulauncher --newversion=${deb_version}-0ubuntu1ppa1~$RELEASE --empty --distribution $RELEASE
        dpkg-buildpackage -tc -S -sa -k$GPGKEY

        info "Uploading to launchpad"
        dput -f ppa:$PPA ../*.changes
        rm /tmp/ulauncher_* || true
    else
        rm debian/changelog || true
        dch --create --no-multimaint --package ulauncher --newversion=$deb_version --empty --distribution focal
        if [ "$1" = "--signed" ]; then
            info "Building signed deb package"
            dpkg-buildpackage -tc -us -sa -k$GPGKEY
        else
            info "Building unsigned deb package"
            dpkg-buildpackage -tc --no-sign
        fi
        success "ulauncher_${deb_version}_all.deb saved to /tmp"
    fi
}

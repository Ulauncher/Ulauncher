#!/usr/bin/env bash

prep-deb () {
    VERSION=$(./ul version)
    # Debian prerelease separator is "~" instead of "-" (semver prerelease separator)
    DEB_VERSION=$(echo "$VERSION" | tr "-" "~")
    TMPDIR="/tmp/ulauncher"

    echo "Building DEB package for Ulauncher $VERSION..."

    echo "Building Preferences UI"
    ./setup.py build_prefs --force

    echo "Copying src to a temp dir"
    rm -rf "${TMPDIR:?}/"* || true
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
        $TMPDIR \
        --exclude-from=.gitignore

    # This is only needed because data/preferences is in .gitignore
    cp -r data/preferences $TMPDIR/data/preferences

    cd $TMPDIR || exit
}

# Env vars:
#   GPGKEY [optional] for signing
build-deb () {
    prep-deb
    dch --create --no-multimaint --package ulauncher --newversion="$DEB_VERSION" --empty --distribution focal
    if [ -z "$GPGKEY" ]; then
        echo "Building signed deb package"
        dpkg-buildpackage -tc -us -sa "-k$GPGKEY"
    else
        echo "Building unsigned deb package"
        dpkg-buildpackage -tc --no-sign
    fi
    rm debian/changelog || true
    success "ulauncher_${DEB_VERSION}_all.deb saved to /tmp"
}

# Env vars:
#   GPGKEY for signing
#   PPA required for upload
#   RELEASE release name required for upload
release-deb () {
    if [ -z "$PPA" ]; then
        error "PPA env var is not supplied"
        exit 1
    fi
    
    prep-deb

    for RELEASE in "$@"; do
        info "Making release for $RELEASE"
        dch --create --no-multimaint --package ulauncher --newversion="${DEB_VERSION}-0ubuntu1ppa1~$RELEASE" --empty --distribution "$RELEASE"
        dpkg-buildpackage -tc -S -sa "-k$GPGKEY"

        info "Uploading to launchpad"
        dput -f "ppa:$PPA" ../*.changes
        rm debian/changelog || true
        rm /tmp/ulauncher_* || true
    done
}

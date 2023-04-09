#!/usr/bin/env bash

#############################
# Build tar.gz in a container
#############################
build-release() {
    # Args:
    # $1 version

    export VERSION=$1
    if [ -z "$VERSION" ]; then
        echo "First argument should be version"
        exit 1
    fi

    # Ensure the types and unit tests are ok, but don't bother with linting
    ./ul test-mypy
    ./ul test-pytest

    info "Releasing Ulauncher $VERSION"

    set -e

    create_deb
}

upload-release() {
    # Args:
    # $1 version

    export VERSION=$1
    if [ -z "$VERSION" ]; then
        echo "First argument should be version"
        exit 1
    fi

    info "Uploading Ulauncher $VERSION"

    set -e

    # Upload if tag doesn't contain "test"
    if [[ $(echo "$VERSION" | tr '[:upper:]' '[:lower:]') != *test* ]]; then
        launchpad_upload
    fi
}

create_deb() {
    DEB_VERSION=$(echo "$VERSION" | tr "-" "~")
    use_cached_modules="ln -s /var/node_modules preferences-src" # take node modules from cache
    build_deb="./ul build-deb --deb"
    build_targz="./ul build-targz"
    copy_targz="cp /tmp/ulauncher_$VERSION.tar.gz ."
    copy_deb="cp /tmp/ulauncher_${DEB_VERSION}_all.deb ulauncher_${VERSION}_all.deb"

    h1 "Creating .deb"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "$use_cached_modules && $build_deb && $build_targz && $copy_targz && $copy_deb"
    set +x
}

launchpad_upload() {
    # check if release name contains prerelease-separator "-" to decide which PPA to use
    if [[ "$VERSION" == *-* ]]; then
        PPA="agornostal/ulauncher-dev"
    else
        PPA="agornostal/ulauncher"
    fi

    kinetic="PPA=$PPA RELEASE=kinetic ./ul build-deb $VERSION --upload"
    jammy="PPA=$PPA RELEASE=jammy ./ul build-deb $VERSION --upload"
    impish="PPA=$PPA RELEASE=impish ./ul build-deb $VERSION --upload"
    focal="PPA=$PPA RELEASE=focal ./ul build-deb $VERSION --upload"
    bionic="PPA=$PPA RELEASE=bionic ./ul build-deb $VERSION --upload"

    # extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
    # then uploads each release
    h1 "Launchpad upload"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "tar -xvf scripts/launchpad.ssh.tar -C / && $kinetic && $jammy && $impish && $focal && $bionic"
    set +x
}

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
        aur_update
    fi
}

create_deb() {
    DEB_VERSION=$(echo "$VERSION" | tr "-" "~")
    step1="ln -s /var/node_modules preferences-src" # take node modules from cache
    # Both step 2 and 3 should be moved out imo, but we need to make sure they run correctly somewhere before continuing 
    step2="pip3 install --upgrade pip && PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install -r requirements.txt"
    step3="./ul test"
    step4="./ul build-deb --deb"
    step5="./ul build-targz"
    step6="cp /tmp/ulauncher_$VERSION.tar.gz ."
    step7="cp /tmp/ulauncher_${DEB_VERSION}_all.deb ulauncher_${VERSION}_all.deb"

    h1 "Creating .deb"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4 && $step5 && $step6 && $step7"
    set +x
}

aur_update() {
    # Note that this script does not need to run with Docker in any specific
    # environment/distro, but it was written that way and it works,
    # so it still does use Docker and https://hub.docker.com/r/ulauncher/arch
    h1 "Push new PKGBUILD to AUR stable channel"
    workdir=/home/notroot/ulauncher
    chmod 600 scripts/aur_key
    sudo chown 1000:1000 scripts/aur_key

    docker run \
        --rm \
        -u notroot \
        -w $workdir \
        -v $(pwd):$workdir \
        ulauncher/arch:5.0 \
        bash -c "./ul aur-update $VERSION"
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

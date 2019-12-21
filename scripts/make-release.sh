#!/usr/bin/env bash

#############################
# Build tar.gz in a container
#############################
make-release() {
    # Args:
    # $1 version

    export VERSION=$(fix-version-format "$1")
    if [ -z "$VERSION" ]; then
        echo "First argument should be version"
        exit 1
    fi

    info "Releasing Ulauncher $VERSION"

    set -e

    create_deb
    create_rpms
    launchpad_upload
    aur_update
}

create_deb() {
    step1="ln -s /var/node_modules data/preferences" # take node modules from cache
    step2="ln -s /var/bower_components data/preferences"
    step3="./ul test"
    step4="./ul build-deb $VERSION --deb"
    step5="./ul build-targz $VERSION"

    h1 "Creating .deb"
    set -x
    docker run \
        -v $(pwd):/root/ulauncher \
        --name ulauncher-deb \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4 && $step5"
    set +x
    docker cp ulauncher-deb:/tmp/ulauncher_$VERSION.tar.gz .
    docker cp ulauncher-deb:/tmp/ulauncher_${VERSION}_all.deb .
    docker rm ulauncher-deb
}

create_rpms() {
    h1 "Creating .rpm"

    set -ex
    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora.rpm .
    docker rm ulauncher-rpm
    set +x
}

aur_update() {
    h1 "Push new PKGBUILD to AUR stable channel"
    workdir=/home/notroot/ulauncher
    chmod 600 scripts/aur_key
    sudo chown 1000:1000 scripts/aur_key

    docker run \
        --rm \
        -u notroot \
        -w $workdir \
        -v $(pwd):$workdir \
        $ARCH_BUILD_IMAGE \
        bash -c "UPDATE_STABLE=1 ./ul aur-update $VERSION"
}

launchpad_upload() {
    # check if release name contains beta or dev to decide which PPA to use
    if echo "$VERSION" | grep -q beta; then
        PPA="agornostal/ulauncher-dev"
    else
        PPA="agornostal/ulauncher"
    fi
    xenial="PPA=$PPA RELEASE=xenial ./ul build-deb $VERSION --upload"
    bionic="PPA=$PPA RELEASE=bionic ./ul build-deb $VERSION --upload"
    disco="PPA=$PPA RELEASE=disco ./ul build-deb $VERSION --upload"
    eoan="PPA=$PPA RELEASE=eoan ./ul build-deb $VERSION --upload"

    # extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
    # then uploads each realease
    h1 "Launchpad upload"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "tar -xvf scripts/launchpad.ssh.tar -C / && $xenial && $bionic && $disco && $eoan"
    set +x
}

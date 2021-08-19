#!/usr/bin/env bash

#############################
# Build tar.gz in a container
#############################
make-release() {
    # Args:
    # $1 version

    export VERSION=$1
    if [ -z "$VERSION" ]; then
        echo "First argument should be version"
        exit 1
    fi

    info "Releasing Ulauncher $VERSION"

    set -e

    create_deb

    # RPMs deactivated for now
    # create_rpms

    # Upload if tag doesn't contain "test"
    if [[ $(echo "$VERSION" | tr '[:upper:]' '[:lower:]') != *test* ]]; then
        launchpad_upload
        aur_update
    fi
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
    # RPMs are tricky because different distros have different Python3 versions
    # We know that
    #   Fedora 32 has Python 3.8
    #   Fedora 33 has Python 3.9
    # This means that we should use separate docker images to build different RPM packages

    h1 "Creating .rpm"

    set -ex
    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora.rpm .
    docker rm ulauncher-rpm

    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_33_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora fedora33"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora33.rpm .
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
        bash -c "./ul aur-update $VERSION"
}

launchpad_upload() {
    # check if release name contains prerelease-separator "-" to decide which PPA to use
    if [[ "$VERSION" == *-* ]]; then
        PPA="agornostal/ulauncher-dev"
    else
        PPA="agornostal/ulauncher"
    fi
    xenial="PPA=$PPA RELEASE=xenial ./ul build-deb $VERSION --upload"
    hirsute="PPA=$PPA RELEASE=hirsute ./ul build-deb $VERSION --upload"
    focal="PPA=$PPA RELEASE=focal ./ul build-deb $VERSION --upload"
    groovy="PPA=$PPA RELEASE=groovy ./ul build-deb $VERSION --upload"

    # extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
    # then uploads each release
    h1 "Launchpad upload"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "tar -xvf scripts/launchpad.ssh.tar -C / && $xenial && $hirsute && $focal && $groovy"
    set +x
}

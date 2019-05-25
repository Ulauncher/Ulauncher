#!/usr/bin/env bash

#############################
# Build tar.gz in a container
#############################
make-release() {
    # Args:
    # $1 version

    VERSION=$(fix-version-format "$1")
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
    docker cp ulauncher-deb:/root/ulauncher_$VERSION.tar.gz .
    docker cp ulauncher-deb:/root/ulauncher_${VERSION}_all.deb .
    docker rm ulauncher-deb
}

create_rpms() {
    # RPMs are tricky because different distros have different Python3 versions
    # We know that
    #   Fedora 28 has Python 3.6
    #   Fedora 29 and 30 has Python 3.7
    # This means that we should use separate docker images to build different RPM packages

    h1 "Creating .rpm"

    set -ex
    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_28_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora fedora28"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora28.rpm .
    docker rm ulauncher-rpm

    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_29_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora fedora29"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora29.rpm .
    docker rm ulauncher-rpm
    set +x
}

aur_update() {
    h1 "Push new PKGBUILD to AUR stable channel"
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $ARCH_BUILD_IMAGE \
        bash -c "UPDATE_STABLE=1 ./ul aur-update $VERSION"
}

launchpad_upload() {
    # check if release name contains beta or dev to decide which PPA to use
    if curl --silent https://api.github.com/repos/ulauncher/ulauncher/releases | egrep -qi "$VERSION\W+(Beta|Dev)"; then
        PPA="agornostal/ulauncher-dev"
    else
        PPA="agornostal/ulauncher"
    fi
    xenial="PPA=$PPA RELEASE=xenial ./ul build-deb $VERSION --upload"
    bionic="PPA=$PPA RELEASE=bionic ./ul build-deb $VERSION --upload"
    cosmic="PPA=$PPA RELEASE=cosmic ./ul build-deb $VERSION --upload"
    disco=" PPA=$PPA RELEASE=disco  ./ul build-deb $VERSION --upload"

    # extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
    # then uploads each realease
    h1 "Launchpad upload"
    set -x
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "tar -xvf scripts/launchpad.ssh.tar -C / && $xenial && $bionic && $cosmic && $disco"
    set +x
}

#!/usr/bin/env bash

#############################
# Build tar.gz in a container
#############################
make-release() {
    # Args:
    # $1 version

    VERSION=$1
    if [ -z "$VERSION" ]; then
        echo "First argument should be version"
        exit 1
    fi

    echo "###########################"
    echo "# Building ulauncher-$VERSION"
    echo "###########################"

    set -ex

    # create_deb
    create_rpms
    # launchpad_upload
    # aur_update
}

create_deb() {
    step1="ln -s /var/node_modules data/preferences" # take node modules from cache
    step2="ln -s /var/bower_components data/preferences"
    step3="./ul test"
    step4="./ul build-deb $VERSION --deb"
    step5="./ul build-targz $VERSION"

    docker run \
        -v $(pwd):/root/ulauncher \
        --name ulauncher-deb \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4 && $step5"
    docker cp ulauncher-deb:/tmp/ulauncher_$VERSION.tar.gz .
    docker cp ulauncher-deb:/tmp/ulauncher_${VERSION}_all.deb .
    docker rm ulauncher-deb
}

create_rpms() {
    # RPMs are tricky because different distros have different Python3 versions
    # We know that
    #   Fedora 28 has Python 3.6
    #   Fedora 29 and 30 has Python 3.7
    #   Centos7 has Python 3.6
    # This means that we should use separate docker images to build different RPM packages
    # However we can build RPM for Fedora 28 and Centos7 using the same image

    set -ex

    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_28_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora fedora28 && ./ul build-rpm $VERSION centos7"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora28.rpm .
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_centos7.rpm .
    docker rm ulauncher-rpm

    docker run -v $(pwd):/root/ulauncher --name ulauncher-rpm $FEDORA_29_BUILD_IMAGE \
        bash -c "./ul build-rpm $VERSION fedora fedora29"
    docker cp ulauncher-rpm:/tmp/ulauncher_${VERSION}_fedora29.rpm .
    docker rm ulauncher-rpm
}

aur_update() {
    # Push new PKGBUILD to AUR stable channel
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
    GPGKEY="6BD735B0"
    xenial="PPA=$PPA GPGKEY=$GPGKEY RELEASE=xenial ./ul build-deb $VERSION --upload"
    bionic="PPA=$PPA GPGKEY=$GPGKEY RELEASE=bionic ./ul build-deb $VERSION --upload"
    cosmic="PPA=$PPA GPGKEY=$GPGKEY RELEASE=cosmic ./ul build-deb $VERSION --upload"
    disco="PPA=$PPA GPGKEY=$GPGKEY RELEASE=disco ./ul build-deb $VERSION --upload"

    # extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
    # then uploads each realease
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "tar -xvf scripts/launchpad.ssh.tar -C / && $xenial && $bionic && $cosmic && $disco"
}

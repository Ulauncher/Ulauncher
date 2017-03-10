#!/bin/bash

#############################
# Build tar.gz in a container
#############################

# Args:
# $1 version

if [ -z "$1" ]; then
    echo "First argument should be version"
    exit 1
fi

echo "###########################"
echo "# Building ulauncher-$1"
echo "###########################"

set -ex

cd `dirname $0`
source functions.sh
cd ..

buildUtils=`dirname $0`

main() {
    create_deb
    create_rpms
    launchpad_upload
    aur_update
}

create_deb() {
    step1="ln -s /var/node_modules data/preferences" # take node modules from cache
    step2="ln -s /var/bower_components data/preferences"
    step3="./test tests"
    step4="./build-utils/build-deb.sh $1 --deb"
    step5="./build-utils/build-targz.sh $1"

    docker run \
        -v $(pwd):/root/ulauncher \
        --name ulauncher-deb \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4 && $step5"
    docker cp ulauncher-deb:/tmp/ulauncher_$1.tar.gz .
    docker cp ulauncher-deb:/tmp/ulauncher_$1_all.deb .
    docker rm ulauncher-deb
}

create_rpms() {
    # RPM build should go second, so preferences are build into JS/HTML files
    docker run \
        -v $(pwd):/root/ulauncher \
        --name ulauncher-rpm \
        $RPM_BUILD_IMAGE \
        bash -c "./build-utils/build-rpm.sh $1"

    docker cp ulauncher-rpm:/tmp/ulauncher_$1_fedora.rpm .
    docker cp ulauncher-rpm:/tmp/ulauncher_$1_suse.rpm .
    docker rm ulauncher-rpm
}

aur_update() {
    # Push new PKGBUILD to AUR stable channel
    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $ARCH_BUILD_IMAGE \
        bash -c "UPDATE_STABLE=1 ./build-utils/aur-update.py $1"
}

launchpad_upload() {
    # check if release name contains beta or dev to decide which PPA to use
    if curl --silent https://api.github.com/repos/ulauncher/ulauncher/releases | egrep -i "$1\W+(Beta|Dev)"; then
        PPA="agornostal/ulauncher-dev"
    else
        PPA="agornostal/ulauncher"
    fi
    GPGKEY="6BD735B0"
    trusty="PPA=$PPA GPGKEY=$GPGKEY RELEASE=trusty ./build-utils/build-deb.sh $1 --upload"
    xenial="PPA=$PPA GPGKEY=$GPGKEY RELEASE=xenial ./build-utils/build-deb.sh $1 --upload"
    yakkety="PPA=$PPA GPGKEY=$GPGKEY RELEASE=yakkety ./build-utils/build-deb.sh $1 --upload"
    zesty="PPA=$PPA GPGKEY=$GPGKEY RELEASE=zesty ./build-utils/build-deb.sh $1 --upload"

    docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "$trusty && $xenial && $yakkety && $zesty"
}

main

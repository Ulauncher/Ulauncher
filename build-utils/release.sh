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

# RPM build should go second, so preferences are build into JS/HTML files
docker run \
    -v $(pwd):/root/ulauncher \
    --name ulauncher-rpm \
    $RPM_BUILD_IMAGE \
    bash -c "./build-utils/build-rpm.sh $1"

docker cp ulauncher-deb:/tmp/ulauncher_$1.tar.gz .
docker cp ulauncher-deb:/tmp/ulauncher_$1_all.deb .
docker cp ulauncher-rpm:/tmp/ulauncher_$1_fedora.rpm .

docker rm ulauncher-deb ulauncher-rpm

# Push new PKGBUILD to AUR
docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $ARCH_BUILD_IMAGE \
    bash -c "./build-utils/aur-update.py $1"

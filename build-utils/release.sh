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
    --name ulauncher \
    $BUILD_IMAGE \
    bash -c "$step1 && $step2 && $step3 && $step4 && $step5"

docker cp ulauncher:/tmp/ulauncher_$1.tar.gz .
docker cp ulauncher:/tmp/ulauncher_$1_all.deb .
docker rm ulauncher

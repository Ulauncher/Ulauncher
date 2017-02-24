#!/bin/bash

#############################
# Build tar.gz in a container
#############################

# Args:
# $1 - version

echo "########################"
echo "# Building ulauncher-$1"
echo "########################"

set -ex

cd `dirname $0`
source functions.sh
cd ..

buildUtils=`dirname $0`

name="ulauncher"
if [ ! -z "$1" ]; then
    name="$name-$1"
fi
tarfile="/tmp/$name.tar.gz"


step1="ln -s /var/node_modules data/preferences" # take node modules from cache
step2="ln -s /var/bower_components data/preferences"
step3="./test tests"
step4="./build-utils/build-targz.sh $1"

docker run \
    -v $(pwd):/root/ulauncher \
    --name ulauncher \
    $BUILD_IMAGE \
    bash -c "$step1 && $step2 && $step3 && $step4"

docker cp ulauncher:$tarfile .
docker rm ulauncher

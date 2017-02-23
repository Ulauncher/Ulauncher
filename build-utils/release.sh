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
tmpdir="/tmp/"
if [ ! -z "$1" ]; then
    tarfile="$tmpdir-$1"
fi
tarfile="$tmpdir/$name.tar.gz"

docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    --name ulauncher \
    $BUILD_IMAGE \
    bash -c "./test tests && ./build-utils/build-targz.sh"

docker cp ulauncher:$tarfile .

export BUILD_ARTIFACT_TARGZ=$tarfile
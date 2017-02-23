#!/bin/bash

#####################################
# Runs pytests and builds preferences
#####################################

cd `dirname $0`
cd ..

set -ex

docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $BUILD_IMAGE \
    bash -c "./test tests && ./build-utils/build-preferences.sh"

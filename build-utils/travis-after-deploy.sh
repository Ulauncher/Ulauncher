#!/bin/bash

set -ex

# Push new PKGBUILD to AUR stable channel
docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $ARCH_BUILD_IMAGE \
    bash -c "UPDATE_STABLE=1 ./build-utils/aur-update.py $1"

# Push new PKGBUILD to AUR dev channel
docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $ARCH_BUILD_IMAGE \
    bash -c "UPDATE_STABLE=0 ./build-utils/aur-update.py $1"

#!/bin/bash

# Push new PKGBUILD to AUR
docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $ARCH_BUILD_IMAGE \
    bash -c "ALLOW_UNSTABLE=$ALLOW_UNSTABLE ./build-utils/aur-update.py $1"

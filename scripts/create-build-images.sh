#!/usr/bin/env bash

################################################
# Creates Docker images for building and testing
################################################
create-build-images () {
    set -ex

    docker build -t $BUILD_IMAGE .
    docker push $BUILD_IMAGE

    cd scripts/dockerfiles

    docker build -f Dockerfile.arch -t $ARCH_BUILD_IMAGE .
    docker push $ARCH_BUILD_IMAGE

    docker build -f Dockerfile.fedora-28 -t $FEDORA_28_BUILD_IMAGE .
    docker push $FEDORA_28_BUILD_IMAGE

    docker build -f Dockerfile.fedora-29 -t $FEDORA_29_BUILD_IMAGE .
    docker push $FEDORA_29_BUILD_IMAGE

    docker build -f Dockerfile.suse-42.3 -t $SUSE_423_BUILD_IMAGE .
    docker push $SUSE_423_BUILD_IMAGE
}

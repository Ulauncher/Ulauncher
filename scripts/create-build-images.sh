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

    docker build -f Dockerfile.fedora-31 -t $FEDORA_BUILD_IMAGE .
    docker push $FEDORA_BUILD_IMAGE
}

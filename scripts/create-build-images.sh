#!/usr/bin/env bash

################################################
# Creates Docker images for building and testing
################################################
create-build-images () {
    set -ex

    docker build -t $BUILD_IMAGE .
    docker push $BUILD_IMAGE
}

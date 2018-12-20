#!/usr/bin/env bash

################################################
# Creates Docker images for building and testing
################################################
create-build-images () {
    set -ex

    docker build -f Dockerfile.build -t $BUILD_IMAGE .
    docker push $BUILD_IMAGE

    docker build -f Dockerfile.build-rpm -t $RPM_BUILD_IMAGE .
    docker push $RPM_BUILD_IMAGE

    docker build -f Dockerfile.build-arch -t $ARCH_BUILD_IMAGE .
    docker push $ARCH_BUILD_IMAGE
}

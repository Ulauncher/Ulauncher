#!/bin/bash

#############################################
# Creates Docker image for building stuff
#############################################

set -ex

cd `dirname $0`
cd ..

TAG=2.0

docker build -f Dockerfile.build -t ulauncher/build-image:$TAG .
docker push ulauncher/build-image:$TAG

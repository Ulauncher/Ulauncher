#!/bin/bash

#############################################
# Creates Docker image for building stuff
#############################################

set -ex

cd `dirname $0`
source functions.sh
cd ..

docker build -f Dockerfile.build -t $BUILD_IMAGE .
docker push $BUILD_IMAGE

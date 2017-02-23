#!/bin/bash

##########################################################
# Runs Docker container to run build scripts from this dir
##########################################################

cd `dirname $0`
source functions.sh
cd ..

docker run \
    --rm \
    -it \
    -v $(pwd):/root/ulauncher \
    -v $HOME/.bash_history:/root/.bash_history \
    $BUILD_IMAGE \
    bash

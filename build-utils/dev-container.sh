#!/bin/bash

#########################################################
# Runs Docker container to run exec scripts from this dir
#########################################################

cd `dirname $0`
cd ..

TAG=2.0

docker run \
    --rm \
    -it \
    -v $(pwd):/root/ulauncher \
    -v $HOME/.bash_history:/root/.bash_history \
    ulauncher/build-image:$TAG \
    bash

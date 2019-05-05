#!/usr/bin/env bash

##########################################################
# Runs Docker container to run build scripts from this dir
##########################################################
dev-container () {
    # port 3002 is used for developing Preferences UI

    exec docker run \
        --rm \
        -it \
        -v $(pwd):/root/ulauncher \
        -v $HOME/.bash_history:/root/.bash_history \
        -p 3002:3002 \
        --name ulauncher \
        $BUILD_IMAGE \
        bash
}

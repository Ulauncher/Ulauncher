#!/usr/bin/env bash

##########################################################
# Runs Docker container to run build scripts from this dir
##########################################################
dev-container () {
    # port 3002 is used for developing Preferences UI
  case "$1" in
    fedora) image=$FEDORA_BUILD_IMAGE ;;
    arch) image=$ARCH_BUILD_IMAGE ;;
    *) image=$BUILD_IMAGE ;;
  esac

  exec docker run \
    --rm \
    -it \
    -v $(pwd):/root/ulauncher \
    -v $HOME/.bash_history:/root/.bash_history \
    -p 3002:3002 \
    --name ulauncher \
    $image \
    bash
}

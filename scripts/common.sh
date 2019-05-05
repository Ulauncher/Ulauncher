#!/usr/bin/env bash

# define fonts
bold=$(tput bold)
dim=$(tput dim)
normal=$(tput sgr0)
cyan=$'\e[94m'
yellow=$'\e[33m'
red=$'\e[1;31m'

BUILD_IMAGE=ulauncher/build-image:5.0
FEDORA_28_BUILD_IMAGE=ulauncher/fedora:5.0-28
FEDORA_29_BUILD_IMAGE=ulauncher/fedora:5.0-29
SUSE_423_BUILD_IMAGE=ulauncher/opensuse:5.0-42.3
ARCH_BUILD_IMAGE=ulauncher/arch:5.0

warn-if-not-in-docker () {
    if [ ! -f /.dockerenv ]; then
        echo
        echo "${yellow}WARNING: It's recommended to run tests in a docker container to be sure they will also pass in CI${normal}"
        echo
    fi
}

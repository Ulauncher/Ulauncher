#!/usr/bin/env bash

# define fonts
bold=$(tput bold)
dim=$(tput dim)
normal=$(tput sgr0)
cyan=$'\e[94m'
yellow=$'\e[33m'
red=$'\e[1;31m'

BUILD_IMAGE=ulauncher/build-image:5.0
RPM_BUILD_IMAGE=ulauncher/rpm-build-image:5.0
ARCH_BUILD_IMAGE=ulauncher/arch-build-image:5.0

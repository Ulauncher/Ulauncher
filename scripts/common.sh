#!/usr/bin/env bash

# define fonts
dim=$(tput dim)
normal=$(tput sgr0)
reset=$(tput sgr0)
cyan=$'\e[94m'
yellow=$'\e[33m'
bold=$(tput bold)
underline=$(tput sgr 0 1)
red=$(tput setaf 1)
green=$(tput setaf 76)
white=$(tput setaf 7)
tan=$(tput setaf 202)
blue=$(tput setaf 25)

BUILD_IMAGE=ulauncher/build-image:5.0
FEDORA_28_BUILD_IMAGE=ulauncher/fedora:5.0-28
FEDORA_29_BUILD_IMAGE=ulauncher/fedora:5.0-29
ARCH_BUILD_IMAGE=ulauncher/arch:5.0

underline() {
    printf "${underline}${bold}%s${reset}\n" "$@"
}
h1() {
    printf "\n${underline}${bold}${blue}%s${reset}\n" "$@"
}
h2() {
    printf "\n${underline}${bold}${white}%s${reset}\n" "$@"
}
debug() {
    printf "${white}%s${reset}\n" "$@"
}
info() {
    printf "${white}➜ %s${reset}\n" "$@"
}
success() {
    printf "${green}✔ %s${reset}\n" "$@"
}
error() {
    printf "${red}✖ %s${reset}\n" "$@"
}
warn() {
    printf "${tan}➜ %s${reset}\n" "$@"
}
bold() {
    printf "${bold}%s${reset}\n" "$@"
}
note() {
    printf "\n${underline}${bold}${blue}Note:${reset} ${blue}%s${reset}\n" "$@"
}

warn-if-not-in-docker () {
    if [ ! -f /.dockerenv ]; then
        echo
        echo "${yellow}WARNING: It's recommended to run tests in a docker container to be sure they will also pass in CI${normal}"
        echo
    fi
}

fix-version-format () {
    # By Debian convension we must use tilde before "beta", but git tag cannot contain that character
    # So when tag for beta release is created, I have to write 1.2.3-beta4, which then should be converted
    # to 1.2.3~beta4
    echo "$1" | sed 's/-beta/~beta/'
}
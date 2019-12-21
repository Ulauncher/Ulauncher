#!/usr/bin/env bash

# define fonts
normal=$'\e[0m'
reset=$normal
bold=$'\e[1m'
dim=$'\e[2m'
underline=$'\e[4m'
red=$'\e[31m'
green=$'\e[32m'
yellow=$'\e[33m'
blue=$'\e[34m'
tan=$'\e[91m'
cyan=$'\e[96m'
white=$'\e[97m'

BUILD_IMAGE=ulauncher/build-image:5.0
FEDORA_BUILD_IMAGE=ulauncher/fedora:5.0-31
ARCH_BUILD_IMAGE=ulauncher/arch:5.0

underline() {
    printf "${underline}${bold}%s${reset}\n" "$@"
}
h1() {
    printf "\n${underline}${bold}${cyan}%s${reset}\n" "$@"
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
    printf "${tan}✖ %s${reset}\n" "$@"
}
warn() {
    printf "${yellow}➜ %s${reset}\n" "$@"
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
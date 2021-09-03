#!/usr/bin/env bash

#############################################
# Builds Ulauncher Preferences UI with nodejs
#############################################
build-preferences () {
    set -e
    if [[ "$1" == '--skip-if-built' ]] && [[ -d data/preferences/dist ]]; then
        success "Preferences are already built. Skipping."
        return
    fi

    cd data/preferences

    set -x
    yarn install
    yarn lint
    yarn build
}

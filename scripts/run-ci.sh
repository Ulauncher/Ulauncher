#!/usr/bin/env bash

run-ci () {
    set -e

    step1="ln -s /var/node_modules preferences-src" # take node modules from cache
    step2="cd docs && sphinx-apidoc -d 5 -o source ../ulauncher && make html && cd .."
    step3="./ul test"
    step4="./setup.py build_prefs --force"

    exec docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4"
}

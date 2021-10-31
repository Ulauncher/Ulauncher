#!/usr/bin/env bash

run-ci () {
    set -e

    step1="ln -s /var/node_modules preferences-src" # take node modules from cache
    step2="pip install Levenshtein"
    step3="cd docs && sphinx-apidoc -d 5 -o source ../ulauncher && make html && cd .."
    step4="./ul test"
    step5="./setup.py build_prefs --verify 1"

    exec docker run \
        --rm \
        -v $(pwd):/root/ulauncher \
        $BUILD_IMAGE \
        bash -c "$step1 && $step2 && $step3 && $step4 && $step5"
}

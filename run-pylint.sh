#!/usr/bin/env bash

abs-to-rel-path() {
    sed 's|/.*tests|tests|g' | sed 's|/.*ulauncher|ulauncher|g'
}

echo
echo "[ Running pylint ]"

set -e

if [[ -z "$@" ]]; then
    pylint --output-format=colorized tests ulauncher
else
    args=$(echo $@ | abs-to-rel-path) # make a relative path
    eval "pylint --output-format=colorized $args"
fi

#!/usr/bin/env bash

echo
echo "[ Running pylint ]"

set -e

if [[ -z "$@" ]]; then
    pylint --output-format=colorized tests ulauncher
else
    eval "pylint --output-format=colorized $@"
fi

#!/usr/bin/env bash

echo
echo "[ Running tests ]"

# Some tests will fail in Docker unless virtual frame buffer is running
if [ -f /.dockerenv ]; then
    export DISPLAY=:1
    ps cax | grep Xvfb > /dev/null
    if [ $? -eq 0 ]; then
        echo "Xvfb is already running"
    else
        echo "Start Xvfb on display $DISPLAY"
        Xvfb :1 -screen 0 1024x768x16 &
    fi
fi

export PYTHONPATH=`pwd`

abs-to-rel-path() {
    sed 's|/.*tests|tests|g' | sed 's|/.*ulauncher|ulauncher|g'
}

set -e

if [[ -z "$@" ]]; then
    py.test --pep8 tests
else
    args=$(echo $@ | abs-to-rel-path) # make a relative path
    eval "py.test --pep8 $args"
fi

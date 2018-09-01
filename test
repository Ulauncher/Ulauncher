#!/bin/bash

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

args=$(echo $@ | sed 's|/.*tests|tests|g') # make a relative path

eval "PYTHONPATH=`pwd` pytest --pep8 $args"

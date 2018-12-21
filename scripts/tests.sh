#!/usr/bin/env bash

test-mypy () {
    echo '[ test: mypy ]'
    set -e
    mypy .
}

test-pylint () {
    echo '[ test: pylint ]'
    set -e
    pylint --output-format=colorized tests ulauncher $@
}

test-pytest () {
    echo '[ test: pytest ]'
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

    set -e
    py.test --pep8 $@ tests
}


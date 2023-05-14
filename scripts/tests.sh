#!/usr/bin/env bash

test-black () {
    echo '[ test: black ]'
    set -e
    black --diff --check .
}

test-mypy () {
    echo '[ test: mypy ]'
    set -e
    mypy .
}

test-pylint () {
    echo '[ test: pylint ]'
    set -e
    pylint --output-format=colorized ulauncher
}

test-flake8 () {
    echo '[ test: flake8 ]'
    set -e
    flake8 $@
}

test-pytest () {
    set +e
    echo '[ test: pytest ]'
    if ! [ -x "$(command -v xvfb-run)" ]
    then
        pytest tests
    else
        # Use xvfb-run (virtual X server environment)
        # Use very high fake display number to avoid using a real display
        DISPLAY=:99 xvfb-run pytest tests
    fi
    set -e
}


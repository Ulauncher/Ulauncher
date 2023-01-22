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
    # Always use xvfb-run (on display 99) if present
    if ! [ -x "$(command -v xvfb-run)" ]
    then
        DISPLAY=:99 xvfb-run pytest -s tests
    else
        pytest -s tests
    fi
    set -e
}


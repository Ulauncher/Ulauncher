#!/usr/bin/env bash

test-black () {
    echo '[ test: black ]'
    set -e
    black --diff --check .
}

test-mypy () {
    echo '[ test: mypy ]'
    set -e
    mypy ulauncher
}

test-ruff () {
    echo '[ test: ruff ]'
    set -e
    ruff check .
}

test-typos () {
    echo '[ test: typos ]'
    set -e
    typos .
}

test-pytest () {
    set -e
    echo '[ test: pytest ]'
    if ! command -v xvfb-run >/dev/null
    then
        pytest tests
    else
        # Use xvfb-run (virtual X server environment)
        # Use very high fake display number to avoid using a real display
        DISPLAY=:99 xvfb-run pytest tests
    fi
}


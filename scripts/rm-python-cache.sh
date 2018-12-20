#!/usr/bin/env bash

rm-python-cache () {
    set -e
    find . \( -type f -name "*.pyc" -o -type f -name "*.pyo" \) -exec rm {} \;
    find . -type d -name "__pycache__" -prune -exec rm -rf {} \;
}

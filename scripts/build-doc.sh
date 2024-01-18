#!/usr/bin/env bash

build-doc () {
    set -ex

    cd docs

    sphinx-apidoc -d 5 -o source ../ulauncher
    sphinx-build -M html . _build
}

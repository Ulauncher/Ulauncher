#!/usr/bin/env bash

set -ex

cd `dirname $0`/../docs

sphinx-apidoc -d 5 -o source ../ulauncher
make html

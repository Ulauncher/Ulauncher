#!/bin/bash

cd `dirname $0`/..

watchmedo shell-command \
          --patterns="*.py" \
          --recursive \
          --command='./build-utils/builddoc.sh' \
          ulauncher

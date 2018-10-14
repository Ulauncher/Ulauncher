#!/usr/bin/env bash

cd `dirname $0`/..

watchmedo shell-command \
          --patterns="*.py;*.rst" \
          --recursive \
          --command='./build-utils/build-doc.sh' \
          $@

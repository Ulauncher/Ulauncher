#!/usr/bin/env bash

watch-doc () {
    exec watchmedo shell-command \
        --patterns="*.py;*.rst" \
        --recursive \
        --command='./ul build-doc' \
        $@
}

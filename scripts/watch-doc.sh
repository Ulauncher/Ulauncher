#!/usr/bin/env bash

watch-doc () {
    warn-if-not-in-docker
    exec watchmedo shell-command \
        --patterns="*.py;*.rst" \
        --recursive \
        --command='./ul build-doc' \
        $@
}

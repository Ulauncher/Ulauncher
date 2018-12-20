#!/usr/bin/env bash

edit-ui () {
    export GLADE_CATALOG_SEARCH_PATH=./data/ui
    exec glade $1
}

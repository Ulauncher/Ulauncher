#!/usr/bin/env bash

send-signal () {
    signal=${1:-HUP}
    kill -${signal} $(ps aux | grep '[u]launcher' | head -n1 | awk '{print $2}')

    # Uncomment to debug themes
    # while inotifywait -re close_write data/themes/; do ./ul send-signal; done
}


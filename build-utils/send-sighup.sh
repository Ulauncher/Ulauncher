#!/usr/bin/env bash

kill -HUP $(ps aux | grep '[u]launcher' | awk '{print $2}')

# while inotifywait -re close_write data/themes/; do ./bin/send-sighup.sh; done

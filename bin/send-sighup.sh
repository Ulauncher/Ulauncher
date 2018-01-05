#!/bin/bash

kill -HUP $(ps aux | grep '[u]launcher' | awk '{print $2}')

# while inotifywait -re close_write data/styles/; do ./bin/send-sighup.sh; done

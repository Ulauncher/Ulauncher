#!/bin/bash

# Encrypt AUR key:
# travis encrypt-file build-utils/aur_key build-utils/aur_key.enc --add

docker run -it --rm -v $(pwd):/home/travis/ulauncher mgruener/travis-cli

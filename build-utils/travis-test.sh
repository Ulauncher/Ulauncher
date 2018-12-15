#!/usr/bin/env bash

#####################################
# Runs pytests and builds preferences
#####################################

cd `dirname $0`
source env.sh
cd ..

set -ex

step1="ln -s /var/node_modules data/preferences" # take node modules from cache
step2="cd docs && sphinx-apidoc -d 5 -o source ../ulauncher && make html && cd .."
step3="./test tests"
step4="./build-utils/build-preferences.sh"

docker run \
    --rm \
    -v $(pwd):/root/ulauncher \
    $BUILD_IMAGE \
    bash -c "$step1 && $step2 && $step3 && $step4"

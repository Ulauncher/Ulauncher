#!/bin/bash

cd `dirname $0`
source functions.sh
cd ..

docker run \
    --rm \
    -it \
    --cap-add SYS_ADMIN \
    --cap-add MKNOD \
    --security-opt apparmor:unconfined \
    --device=/dev/fuse \
    -v $(pwd)/build-utils:/root/ulauncher/build-utils \
    -v $HOME/.bash_history:/root/.bash_history \
    $APPIMAGE_BUILD_IMAGE \
    bash

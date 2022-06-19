#!/usr/bin/env bash

# Use podman (recommended) if it exists, else docker
# Any files created with docker is then owned by root, not the host user
RUNNER=$(command -v podman || command -v docker)

##########################################################
# Runs Docker container to run build scripts from this dir
##########################################################
dev-container () {
  if [ -z "$RUNNER" ]; then
      echo "You need podman or docker to run the container"
      exit 1
  fi
  # If SELinux is enabled, the volumes mounted into the container
  # need to have the right labels. This is accomplished by appending
  # ":z" to the volume option.
  if command -v selinuxenabled && selinuxenabled
  then
      vol_suffix=":z"
  else
      vol_suffix=""
  fi

  # port 3002 is used for developing Preferences UI
  exec $RUNNER run \
    --rm \
    -it \
    -v $(pwd):/root/ulauncher${vol_suffix} \
    -v $HOME/.bash_history:/root/.bash_history${vol_suffix} \
    -p 3002:3002 \
    --name ulauncher \
    docker.io/$BUILD_IMAGE \
    bash
}

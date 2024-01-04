#!/usr/bin/env bash

# Use podman if it exists, else docker
RUNNER=$(command -v podman || command -v docker)
SHELL_CMD=bash

# Workaround for Docker to avoid generated files getting owned by root (not needed for podman)
if [[ "$RUNNER" == $(command -v docker) ]]; then 
    SHELL_CMD="sudo -H -u ulauncher bash"
    if [[ $(id -u) != 1000 ]]; then 
        SHELL_CMD="usermod -u $(id -u) ulauncher; $SHELL_CMD"
    fi;
    if [[ $(id -g) != 1000 ]]; then 
        SHELL_CMD="groupmod -g $(id -g) ulauncher; $SHELL_CMD"
    fi;
fi;

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
    -v "$(pwd):/ulauncher${vol_suffix}" \
    -v "$HOME/.bash_history:/home/ulauncher/.bash_history${vol_suffix}" \
    -p 3002:3002 \
    --name ulauncher \
    "docker.io/$BUILD_IMAGE" \
    sh -c "$SHELL_CMD"
}

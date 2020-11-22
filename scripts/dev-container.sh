#!/usr/bin/env bash

##########################################################
# Runs Docker container to run build scripts from this dir
##########################################################
dev-container () {
    # port 3002 is used for developing Preferences UI
  case "$1" in
    fedora) image=$FEDORA_BUILD_IMAGE ;;
    fedora33) image=$FEDORA_33_BUILD_IMAGE ;;
    arch) image=$ARCH_BUILD_IMAGE ;;
    *) image=$BUILD_IMAGE ;;
  esac

  # If SELinux is enabled, the volumes mounted into the container
  # need to have the right labels. This is accomplished by appending
  # ":z" to the volume option.
  if command -v selinuxenabled && selinuxenabled
  then
      vol_suffix=":z"
  else
      vol_suffix=""
  fi

  exec docker run \
    --rm \
    -it \
    -v $(pwd):/root/ulauncher${vol_suffix} \
    -v $HOME/.bash_history:/root/.bash_history${vol_suffix} \
    -p 3002:3002 \
    --name ulauncher \
    $image \
    bash
}

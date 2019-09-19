#!/usr/bin/env bash

cleanup-dev-env () {
  # remove icons
  rm \
    -v \
    "${HOME}/.local/share/icons/hicolor/48x48/apps/ulauncher.svg" \
    "${HOME}/.local/share/icons/hicolor/48x48/apps/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/hicolor/scalable/apps/ulauncher.svg" \
    "${HOME}/.local/share/icons/hicolor/scalable/apps/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/gnome/scalable/apps/ulauncher.svg" \
    "${HOME}/.local/share/icons/gnome/scalable/apps/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/breeze/apps/48/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/ubuntu-mono-dark/scalable/apps/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/ubuntu-mono-light/scalable/apps/ulauncher-indicator.svg" \
    "${HOME}/.local/share/icons/elementary/scalable/apps/ulauncher-indicator.svg"

  # remove application folder
  rm \
    -rv \
    "${HOME}/.local/share/ulauncher"

  # remove launcher
  rm \
  -v \
  "${HOME}/.local/share/applications/ulauncher.desktop"


  # remove ulaucher webkit cache
  rm \
  -rv \
  "${HOME}/.cache/ulauncher"

  # remove ulaucher dbs
  rm \
  -rv \
  "${HOME}/.local/share/ulauncher/"*.db

  # remove ulaucher log
  rm \
  -rv \
  "${HOME}/.local/share/ulauncher/last.log"
}

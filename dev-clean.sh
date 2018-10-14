#!/usr/bin/env bash

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
  "${HOME}/.local/share/icons/elementary/scalable/apps/ulauncher-indicator.svg";

# remove application folder
rm \
  -rv \
  "${HOME}/.local/share/ulauncher";

# remove launcher
rm \
 -v \
 "${HOME}/.local/share/applications/ulauncher.desktop";

#!/bin/bash

######################
# Uninstalls Ulauncher
######################

set -x

rm -rf ~/.local/share/applications/ulauncher.desktop
rm -rf ~/.local/share/ulauncher

echo
echo "##############################"
echo "# Ulauncher has been removed #"
echo "##############################"
echo
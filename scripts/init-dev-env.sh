#!/usr/bin/env bash

init-dev-env () {
    set -e

    echo "installing media files to ~/.local to be able to load icons by name"
    python3 setup.py install_data --install-dir="$HOME/.local" || exit 1

    echo "adding .desktop file"
    mkdir -p ~/.local/share/applications/
    desktop=~/.local/share/applications/ulauncher.desktop
    cp ulauncher.desktop.dev $desktop
    sed -i "s,__ulauncher_bin__,`pwd`/bin,g" $desktop
    sed -i "s,__ulauncher_exec__,`pwd`/bin/ulauncher,g" $desktop

    echo "${cyan}All done!${normal}"
}

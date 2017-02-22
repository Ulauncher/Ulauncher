#!/bin/bash

#####################################################
# Installs Ulauncher and its dependencies on users OS
#####################################################

set -ex

if [ -e /usr/bin/apt-get ] ; then
    sudo apt-get update
    sudo apt-get install -y \
            gobject-introspection \
            libkeybinder-3.0-0 \
            gir1.2-gtk-3.0 \
            gir1.2-keybinder-3.0 \
            gir1.2-webkit2-3.0 \
            gir1.2-glib-2.0 \
            gir1.2-gdkpixbuf-2.0 \
            gir1.2-appindicator3-0.1 \
            python-gi \
            python-gobject \
            python-distutils-extra \
            python-pysqlite2 \
            python-xdg \
            python-dbus libgtk-3-0 \
            python-pyinotify \
            python-levenshtein
else
    echo
    echo "###########################################"
    echo "# Only Debian-based distros are supported #"
    echo "###########################################"
    echo
    echo "Please create a pull request with installation steps for RPM-based distros"
    echo "https://github.com/Ulauncher/Ulauncher/blob/dev/install.sh"
    echo
    exit 1
fi

echo "Installing media files to ~/.local to be able to load icons by name"
python setup.py install_data --install-dir="$HOME/.local" || exit 1

echo "adding .desktop file"
mkdir -p ~/.local/share/applications/
desktop=~/.local/share/applications/ulauncher.desktop
cp ulauncher.desktop.dev $desktop
sed -i "s,__ulauncher_bin__,`pwd`/bin,g" $desktop
sed -i "s,__ulauncher_exec__,`pwd`/bin/ulauncher,g" $desktop

set +x

echo
echo "#########################"
echo "# Installation complete #"
echo "#########################"
echo
echo "    You can now run"
echo "    ./bin/ulauncher"
echo
#!/bin/bash

echo "installing media files to ~/.local to be able to load icons by name"
python setup.py install_data --install-dir="$HOME/.local" || exit 1

pushd "data/preferences"
if ! hash git 2>/dev/null || ! grep -q `git rev-parse HEAD` ".build-checksum"; then
    echo "building preferences UI if it's not built"
    npm i && ./node_modules/bower/bin/bower install --config.interactive=false && ./gulp build || exit 1
fi
popd

echo "adding .desktop file"
mkdir -p ~/.local/share/applications/
desktop=~/.local/share/applications/ulauncher.desktop
cp ulauncher.desktop.dev $desktop
sed -i "s,__ulauncher_bin__,`pwd`/bin,g" $desktop
sed -i "s,__ulauncher_exec__,`pwd`/bin/ulauncher,g" $desktop

./bin/ulauncher -v --dev $@

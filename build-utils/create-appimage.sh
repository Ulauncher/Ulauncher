#!/bin/bash

set -ex

cd `dirname $0`
cd ..
ROOT_DIR=$(pwd)

APP=utest
LOWERAPP=${APP,,}
VERSION=2.1.0
ARCH=x86-64

APP_DIR="$ROOT_DIR/$APP.AppDir"
PYTHON_INSTALL_DIR="$ROOT_DIR/python2.7-installed"
rm -rf $APP_DIR
mkdir -p $APP_DIR
. ../functions.sh
rm -rf ../out

main() {
    install_python
    install_pip
    install_deps
    install_pip_deps
    # patch_usr
    install_app
    install_apprun
    desktop_integration
    copy_deps_magic

    cd $ROOT_DIR
    generate_appimage

    copy_to_mounted_volume
}

install_python() {
    cd $ROOT_DIR
    if [ ! -d "$PYTHON_INSTALL_DIR/usr" ]; then
        mkdir -p $PYTHON_INSTALL_DIR/usr
        tar -xzf $ROOT_DIR/../Python-2.7.13.tgz -C .
        cd Python-2.7.13
        ./configure \
            --enable-ipv6 \
            --enable-unicode=ucs4 \
            --prefix=$PYTHON_INSTALL_DIR/usr #the prefix is important for this whole thing to work
        make && make install
    fi

    mkdir -p $APP_DIR/usr
    cp -r $PYTHON_INSTALL_DIR/usr/* $APP_DIR/usr

    # --enable-optimizations \
    # --with-dbmliborder=bdb:gdbm \
    # --with-system-expat \
    # --with-computed-gotos \
    # --with-system-ffi \
    # --with-fpectl \
}

install_pip() {
    cd $APP_DIR
    ./usr/bin/python $ROOT_DIR/../get-pip.py
}

install_pip_deps() {
    # Python headers are required to compile some Levenshtein
    cd $ROOT_DIR
    mkdir -p $APP_DIR/usr/include/python2.7
    cp -r Python-2.7.13/Include/* $APP_DIR/usr/include/python2.7

    cd $APP_DIR
    ./usr/bin/pip install setuptools
    ./usr/bin/pip install \
        pyinotify \
        pysqlite \
        python-Levenshtein

    site_packages=$APP_DIR/usr/lib/python2.7/site-packages
    mkdir -p $site_packages
    # move to usr/lib
    mv $APP_DIR/usr/local/lib/python2.7/dist-packages/* $site_packages
}

install_deps() {
    cd $ROOT_DIR
    mkdir -p deps
    cd deps
    # The following ones cannot be installed using pip
    apt-get -y download \
        python-gobject \
        python-dbus \
        python-distutils-extra \
        python-gi \
        python-xdg \
        libpython2.7-stdlib \
        libwebkit2gtk-4.0-37 \
        gobject-introspection \
        libkeybinder-3.0-0 \
        libgtk-3-0 \
        libwebp5 \
        gir1.2-gtk-3.0 \
        gir1.2-keybinder-3.0 \
        gir1.2-webkit2-4.0 \
        gir1.2-glib-2.0 \
        gir1.2-gdkpixbuf-2.0 \
        gir1.2-appindicator3-0.1 || true

    cd $APP_DIR
    find $ROOT_DIR/deps/ -name "*deb" -exec dpkg -x {} . \;

    site_packages=$APP_DIR/usr/lib/python2.7/site-packages
    mkdir -p $site_packages
    mv $APP_DIR/usr/lib/python2.7/dist-packages/* $site_packages

    # remove '.x86_64-linux-gnu' from .so file names
    find $site_packages -name "*x86_64-linux-gnu.so" -exec rename 's/\.x86_64-linux-gnu//' {} \;
}

install_app() {
    cd $ROOT_DIR/ulauncher
    # `clean` arg is necessary to avoid crashes when DistUtilsExtra tries to figure out deps
    APPIMAGE=1 $APP_DIR/usr/bin/python setup.py install --prefix=$APP_DIR/usr clean
    mv $APP_DIR/usr/bin/ulauncher $APP_DIR/usr/bin/$LOWERAPP
    # Fix hasbang. It get's set to an absolute path at some point
    sed -i "s,\#\!.*,\#\!/usr/bin/env python,g" $APP_DIR/usr/bin/$LOWERAPP

#     cd $APP_DIR
#     mkdir -p usr/bin/
#     cat > usr/bin/$LOWERAPP <<\EOF
# #!/usr/bin/env python
# from pprint import pprint
# from Levenshtein import ratio
# import sys
# pprint(sys.path)
# print 'executable', sys.executable

# import gi
# gi.require_version('Gtk', '3.0')
# from gi.repository import Gtk, Gio, Gdk, GLib, GObject, GdkX11, WebKit2, Keybinder, AppIndicator3, GdkPixbuf, Notify
# win = Gtk.Window()
# win.connect("delete-event", Gtk.main_quit)
# win.show_all()
# Gtk.main()
# EOF
#     chmod a+x usr/bin/$LOWERAPP
}

install_apprun() {
    cd $APP_DIR
    get_apprun
}

desktop_integration() {
    cd $APP_DIR
    cat > $LOWERAPP.desktop <<EOF
[Desktop Entry]
Name=$APP
Exec=$LOWERAPP
Icon=$LOWERAPP
Type=Application
Comment=A hello world app written in GTK3 and Python
Categories=GNOME;GTK;
Terminal=false
EOF

    # Make the AppImage ask to "install" itself into the menu
    get_desktopintegration $LOWERAPP
    wget https://raw.githubusercontent.com/Ulauncher/Ulauncher/dev/data/media/executable-icon.png -O $LOWERAPP.png
}

copy_deps_magic() {
    cd $APP_DIR
    set +x
    copy_deps ; copy_deps ; copy_deps
    delete_blacklisted
    move_lib
    set -x
}

copy_to_mounted_volume() {
    cp $ROOT_DIR/../out/utest-2.1.0-x86-64.AppImage build-utils/
}


main

FROM ubuntu:18.04

MAINTAINER ulauncher.app@gmail.com

WORKDIR /root/ulauncher

RUN apt-get update && \
    apt install -y \
        git \
        vim \
        wget \
        xvfb \
        dput \
        debhelper \
        rsync \
        gobject-introspection \
        libgtk-3-0 \
        libkeybinder-3.0-0 \
        gir1.2-gtk-3.0 \
        gir1.2-keybinder-3.0 \
        gir1.2-webkit2-4.0 \
        gir1.2-glib-2.0 \
        gir1.2-gdkpixbuf-2.0 \
        gir1.2-ayatanaappindicator3-0.1 \
        gir1.2-notify-0.7 \
        python3-all \
        python3-gi \
        python3-distutils-extra \
        python3-xdg \
        python3-dbus \
        python3-pyinotify \
        python3-levenshtein \
        python3-websocket \
        python3-paramiko \
        python3-pip && \
    pip3 install --upgrade pip pybuild setuptools && \
    wget -O /tmp/node-setup.sh https://deb.nodesource.com/setup_10.x && \
    bash /tmp/node-setup.sh && \
    apt install -y nodejs && \
    apt autoremove -y && \
    apt clean && \
    npm install -g yarn

COPY [ "requirements.txt", "preferences-src/package.json", "./" ]
COPY [ "docs/requirements.txt", "./docs/" ]

# update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

# Caching node_modules to make builds faster
RUN pip3 install -r requirements.txt && \
    pip3 install -r docs/requirements.txt && \
    yarn && \
    mv node_modules /var

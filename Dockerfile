FROM ubuntu:22.04
# Run this to build this image:
# source scripts/common.sh && docker build -t $BUILD_IMAGE .

LABEL maintainer="ulauncher.app@gmail.com"

ENV EMAIL=ulauncher.app@gmail.com

# NOTE: Keep lines separate. One "RUN" per dependency/change
# https://stackoverflow.com/a/47451019/633921

WORKDIR /root/ulauncher

RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt install -y tzdata
RUN DEBIAN_FRONTEND=noninteractive apt install -y keyboard-configuration

# Build and build and test dependencies
RUN apt install -y git
RUN apt install -y vim
RUN apt install -y wget
RUN apt install -y rsync
RUN apt install -y xvfb
# deb package build dependencies and helpers
RUN apt install -y debhelper dh-python devscripts git-buildpackage
# ubuntu launchpad upload dependencies
RUN apt install -y dput python3-paramiko
RUN apt install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN wget -qO- https://deb.nodesource.com/setup_18.x | bash -
RUN apt install -y nodejs
RUN npm install -g yarn

# App dependencies
RUN apt install -y gobject-introspection
RUN apt install -y python3-all
RUN apt install -y python3-levenshtein
RUN apt install -y python3-gi
RUN apt install -y python3-gi-cairo
RUN apt install -y gir1.2-glib-2.0
RUN apt install -y gir1.2-gtk-3.0
RUN apt install -y gir1.2-webkit2-4.0

# Not actually used, just makes testing of the package easier
RUN apt update
RUN apt install -y software-properties-common
RUN add-apt-repository ppa:agornostal/ulauncher -y

# Clean up
RUN apt update
RUN apt autoremove -y
RUN apt clean

COPY [ "requirements.txt", "preferences-src/package.json", "./" ]
COPY [ "docs/requirements.txt", "./docs/" ]

# Update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

RUN PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install -r requirements.txt
RUN pip3 install -r docs/requirements.txt
# Caching node_modules to make builds faster
RUN yarn
RUN mv node_modules /var

RUN usermod -c "Ulauncher" root
RUN git config --global --add safe.directory /root/ulauncher

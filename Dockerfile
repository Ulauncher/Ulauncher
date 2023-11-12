FROM ubuntu:22.04
# Run this to build this image:
# source scripts/common.sh && docker build -t $BUILD_IMAGE .

LABEL maintainer="ulauncher.app@gmail.com"

ENV EMAIL=ulauncher.app@gmail.com

# NOTE: Keep lines separate. One "RUN" per dependency/change
# https://stackoverflow.com/a/47451019/633921

WORKDIR /root/ulauncher

RUN apt update --fix-missing
RUN DEBIAN_FRONTEND=noninteractive apt install -y tzdata
RUN DEBIAN_FRONTEND=noninteractive apt install -y keyboard-configuration

# CLI dependencies for building and testing
RUN apt install -y software-properties-common
RUN apt install -y git
RUN apt install -y vim
RUN apt install -y wget
RUN apt install -y rsync
RUN apt install -y xvfb

# deb package build dependencies and helpers
RUN apt install -y debhelper
RUN apt install -y dh-python
RUN apt install -y devscripts
RUN apt install -y git-buildpackage

# ubuntu launchpad upload dependencies
RUN apt install -y dput
RUN apt install -y python3-paramiko

# App dependencies
RUN apt install -y gobject-introspection
RUN apt install -y python3-all
RUN apt install -y python3-levenshtein
RUN apt install -y python3-gi
RUN apt install -y python3-gi-cairo
RUN apt install -y gir1.2-glib-2.0
RUN apt install -y gir1.2-gtk-3.0
RUN apt install -y gir1.2-webkit2-4.0

# pip, setuptools
RUN apt install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools

# yarn for building the Preferences web app
RUN apt install -y yarnpkg

# Clean up
RUN apt update
RUN apt autoremove -y
RUN apt clean

RUN usermod -c "Ulauncher" root
RUN git config --global --add safe.directory /root/ulauncher

COPY [ "requirements.txt", "./" ]
COPY [ "docs/requirements.txt", "./docs/" ]
COPY [ "preferences-src/package.json", "preferences-src/yarn.lock", "./" ]

# Update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

RUN PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install -r requirements.txt
RUN pip3 install -r docs/requirements.txt
# Cache node_modules to make builds faster
RUN yarnpkg
RUN mv node_modules /var

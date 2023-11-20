FROM ubuntu:20.04
# Run this to build this image:
# source scripts/common.sh && docker build -t $BUILD_IMAGE .

LABEL maintainer="ulauncher.app@gmail.com"

ENV EMAIL=ulauncher.app@gmail.com

# NOTE: Keep lines separate. One "RUN" per dependency/change
# https://stackoverflow.com/a/47451019/633921

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
RUN apt install -y python3.8-venv

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

# Nodejs/yarn (ubuntu 20.04 has too old nodejs version, but in 22.04 you just need to install yarnpkg)
RUN wget -qO- https://deb.nodesource.com/setup_18.x | bash -
RUN apt install -y nodejs
RUN npm install -g yarn

# Clean up
RUN apt update
RUN apt autoremove -y
RUN apt clean

COPY [ "requirements.txt", "preferences-src/package.json", "preferences-src/yarn.lock", "./" ]
COPY [ "docs/requirements.txt", "./docs/" ]

# Update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

RUN apt install -y python3-pip
RUN PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install -r requirements.txt
RUN pip3 install -r docs/requirements.txt
# Cache node_modules to make builds faster
RUN yarnpkg
RUN mv node_modules /var

# create user to avoid build output to be owned by root
RUN useradd ulauncher --create-home --shell /bin/bash
RUN usermod -c "Ulauncher" ulauncher
# Need sudo to run dpkg-buildpackage for some reason, so adding passwordless sudo for ulauncher user
RUN echo "ulauncher ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER ulauncher
WORKDIR /home/ulauncher/Ulauncher

RUN git config --global --add safe.directory /home/ulauncher/Ulauncher

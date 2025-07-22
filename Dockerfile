FROM ubuntu:20.04
# Update pygobject-stubs version in the makefile after upgrading ubuntu version
# Run `make docker` to build this image

LABEL maintainer="ulauncher.app@gmail.com"

# NOTE: Keep lines separate. One "RUN" per dependency/change
# https://stackoverflow.com/a/47451019/633921

ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt update --fix-missing
RUN apt install -y tzdata
RUN apt install -y keyboard-configuration

# CLI dependencies for building and testing
RUN apt install -y software-properties-common
RUN apt install -y git
RUN apt install -y vim
RUN apt install -y curl
RUN apt install -y wget
RUN apt install -y xvfb
RUN apt install -y help2man
RUN apt install -y python3-venv

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
RUN apt install -y python3-gi
RUN apt install -y python3-gi-cairo
RUN apt install -y gir1.2-glib-2.0
RUN apt install -y gir1.2-gtk-3.0
RUN apt install -y gir1.2-webkit2-4.0

# Workaround only needed for 20.04 and older: https://github.com/pypa/setuptools/issues/2956
# Replace with python3-setuptools after upgrading to 22.04
RUN apt install -y python3
RUN apt install -y python3-dev
RUN apt install -y build-essential
RUN apt install -y fdupes
WORKDIR /root
RUN git clone -b alvistack/v60.0.4 https://github.com/alvistack/pypa-setuptools.git
WORKDIR /root/pypa-setuptools
RUN find *.spec debian/rules -type f | xargs sed -i 's/export SETUPTOOLS_USE_DISTUTILS=stdlib && //g'
RUN curl -skL https://raw.githubusercontent.com/pypa/distutils/69f8573354/_distutils_system_mod.py > /usr/lib/python3/dist-packages/_distutils_system_mod.py
RUN git clean -xdf
RUN tar zcvf ../python-setuptools_60.0.4.orig.tar.gz --exclude=.git .
RUN debuild -uc -us
WORKDIR /root

# Nodejs/yarn (ubuntu 20.04 has too old nodejs version, but in 22.04 you just need to install yarnpkg)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash
RUN apt install -y nodejs
RUN npm install -g yarn

# Clean up
RUN apt update
RUN apt autoremove -y
RUN apt clean

COPY [ "requirements.txt", "preferences-src/package.json", "preferences-src/yarn.lock", "./" ]

# Update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

RUN apt install -y python3-pip
RUN pip3 install -r requirements.txt
RUN PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install pygobject-stubs --no-cache-dir
# Cache node_modules to make builds faster
RUN yarnpkg
RUN mv node_modules /var

# Create container dir for the repo root dir to mount to
# This is needed because dpkg-buildpackage is stupid and outputs are hard coded to be the parent dir
RUN mkdir src
RUN chmod 777 src

# Create an unprivileged user to run as when testing and building locally (so generated files will not be owned by root on the host)
RUN useradd ulauncher --shell /bin/bash --home-dir /home/ulauncher --create-home --uid 1000 --user-group --comment Ulauncher

WORKDIR /src/ulauncher

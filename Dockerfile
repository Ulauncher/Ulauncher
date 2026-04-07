FROM ubuntu:20.04
# Run `make docker` to build this image

LABEL maintainer="ulauncher.app@gmail.com"

# NOTE: Keep lines separate. One "RUN" per dependency/change
# https://stackoverflow.com/a/47451019/633921

ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV NO_VENV=1

RUN apt-get update --fix-missing
RUN apt-get install -y tzdata
RUN apt-get install -y keyboard-configuration

# CLI dependencies for building and testing
RUN apt-get install -y software-properties-common
RUN apt-get install -y git
RUN apt-get install -y vim
RUN apt-get install -y curl
RUN apt-get install -y wget
RUN apt-get install -y xvfb
RUN apt-get install -y help2man
RUN apt-get install -y python3-venv

# deb package build dependencies and helpers
RUN apt-get install -y debhelper
RUN apt-get install -y dh-python
RUN apt-get install -y devscripts
RUN apt-get install -y git-buildpackage

# ubuntu launchpad upload dependencies
RUN apt-get install -y dput
RUN apt-get install -y python3-paramiko

# App dependencies
RUN apt-get install -y gobject-introspection
RUN apt-get install -y python3-all
RUN apt-get install -y python3-gi
RUN apt-get install -y python3-gi-cairo
RUN apt-get install -y gir1.2-glib-2.0
RUN apt-get install -y gir1.2-gtk-3.0

# Workaround only needed for 20.04 and older: https://github.com/pypa/setuptools/issues/2956
# Replace with python3-setuptools after upgrading to 22.04
RUN apt-get install -y python3
RUN apt-get install -y python3-dev
RUN apt-get install -y build-essential
RUN apt-get install -y fdupes
WORKDIR /root
RUN git clone -b alvistack/v60.0.4 https://github.com/alvistack/pypa-setuptools.git
WORKDIR /root/pypa-setuptools
RUN find *.spec debian/rules -type f | xargs sed -i 's/export SETUPTOOLS_USE_DISTUTILS=stdlib && //g'
RUN curl -skL https://raw.githubusercontent.com/pypa/distutils/69f8573354/_distutils_system_mod.py > /usr/lib/python3/dist-packages/_distutils_system_mod.py
RUN git clean -xdf
RUN tar zcvf ../python-setuptools_60.0.4.orig.tar.gz --exclude=.git .
RUN debuild -uc -us
WORKDIR /root

# Clean up
RUN apt-get update
RUN apt-get autoremove -y
RUN apt-get clean

COPY [ "requirements.txt", "./" ]

# Update /etc/dput.cf to use sftp for upload to ppa.launchpad.net
COPY [ "scripts/dput.cf", "/etc" ]

RUN apt-get install -y python3-pip
RUN PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 pip3 install -r requirements.txt

# Create container dir for the repo root dir to mount to
# This is needed because dpkg-buildpackage is stupid and outputs are hard coded to be the parent dir
RUN mkdir src
RUN chmod 777 src

# Create an unprivileged user to run as when testing and building locally (so generated files will not be owned by root on the host)
RUN useradd ulauncher --shell /bin/bash --home-dir /home/ulauncher --create-home --uid 1000 --user-group --comment Ulauncher

WORKDIR /src/ulauncher

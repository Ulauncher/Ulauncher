FROM archlinux/base

MAINTAINER ulauncher.app@gmail.com

WORKDIR /root/ulauncher

RUN pacman --noconfirm -Syu && \
    pacman --noconfirm -S \
        python \
        git \
        grep \
        openssh

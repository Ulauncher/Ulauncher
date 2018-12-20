#!/usr/bin/env bash

# extracts ~/.shh for uploading package to ppa.launchpad.net via sftp
extract-launchpad-ssh () {
    tar -xvf scripts/launchpad.ssh.tar -C /
}

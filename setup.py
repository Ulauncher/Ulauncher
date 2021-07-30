#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import os
import sys

from itertools import takewhile, dropwhile

try:
    import DistUtilsExtra.auto
except ImportError:
    print('To build ulauncher you need "python3-distutils-extra"', file=sys.stderr)
    sys.exit(1)

assert DistUtilsExtra.auto.__version__ >= '2.18', \
    'needs DistUtilsExtra.auto >= 2.18'


def update_config(libdir, values={}):

    filename = os.path.join(libdir, 'ulauncher/config.py')
    oldvalues = {}
    try:
        fin = open(filename, 'r')
        fout = open(filename + '.new', 'w')

        for line in fin:
            fields = line.split(' = ')  # Separate variable from value
            if fields[0] in values:
                oldvalues[fields[0]] = fields[1].strip()
                line = "%s = %s\n" % (fields[0], values[fields[0]])
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError):
        print("ERROR: Can't find %s" % filename)
        sys.exit(1)

    return oldvalues


def move_desktop_file(root, target_data, prefix):
    # The desktop file is rightly installed into install_data.  But it should
    # always really be installed into prefix, because while we can install
    # normal data files anywhere we want, the desktop file needs to exist in
    # the main system to be found.  Only actually useful for /opt installs.

    old_desktop_path = os.path.normpath(root + target_data + '/share/applications')
    old_desktop_file = old_desktop_path + '/ulauncher.desktop'
    desktop_path = os.path.normpath(root + prefix + '/share/applications')
    desktop_file = desktop_path + '/ulauncher.desktop'

    if not os.path.exists(old_desktop_file):
        print("ERROR: Can't find", old_desktop_file)
        sys.exit(1)
    elif target_data != prefix + '/':
        # This is an /opt install, so rename desktop file to use extras-
        desktop_file = desktop_path + '/extras-ulauncher.desktop'
        try:
            os.makedirs(desktop_path)
            os.rename(old_desktop_file, desktop_file)
            os.rmdir(old_desktop_path)
        except OSError as e:
            print("ERROR: Can't rename", old_desktop_file, ":", e)
            sys.exit(1)

    return desktop_file


def update_desktop_file(filename, target_pkgdata, target_scripts):

    def is_env(p):
        return p == 'env' or '=' in p

    try:
        fin = open(filename, 'r')
        fout = open(filename + '.new', 'w')

        for line in fin:
            if 'Exec=' in line:
                cmd = line.split("=", 1)[1]

                # persist env vars
                env_vars = ''
                if cmd.startswith('env '):
                    env_vars = ' '.join(list(takewhile(is_env, cmd.split()))) \
                               + ' '
                    cmd = ' '.join(list(dropwhile(is_env, cmd.split())))

                cmd = cmd.split(None, 1)
                line = "Exec=%s%s%s" % (env_vars, target_scripts, 'ulauncher')
                if len(cmd) > 1:
                    line += " %s" % cmd[1].strip()  # Add script arguments back
                line += "\n"
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError):
        print("ERROR: Can't find %s" % filename)
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        DistUtilsExtra.auto.install_auto.run(self)

        target_data = '/' + os.path.relpath(self.install_data, self.root) + '/'
        target_pkgdata = target_data + 'share/ulauncher/'
        target_scripts = '/' + os.path.relpath(self.install_scripts,
                                               self.root) + '/'

        values = {'__ulauncher_data_directory__': "'%s'" % (target_pkgdata),
                  '__version__': "'%s'" % self.distribution.get_version()}
        update_config(self.install_lib, values)

        desktop_file = move_desktop_file(self.root, target_data, self.prefix)
        update_desktop_file(desktop_file, target_pkgdata, target_scripts)


class DataFileList(list):

    def append(self, item):
        # don't add node_modules to data_files that DistUtilsExtra tries to
        # add automatically
        filename = item[1][0]
        if 'node_modules' in filename \
           or 'bower_components' in filename or '.tmp' in filename:
            return
        else:
            return super().append(item)


def exclude_files(patterns=[]):
    """
    Suppress completely useless warning about files DistUtilsExta.aut does
    recognize because require developer to scroll past them to get to useful
    output.

    Example of the useless warnings:

    WARNING: the following files are not recognized by DistUtilsExtra.auto:
    Dockerfile.build
    Dockerfile.build-arch
    Dockerfile.build-rpm
    PKGBUILD.template
    scripts/aur-update.py
    """

    # it's maddening the DistUtilsExtra does not offer a way to exclude globs
    # from it's scans and just using "print" to print the warning instead of
    # using warning module which has a mechanism for suppressions
    # it forces us to take the approach of monkeypatching their src_find
    # function.
    original_src_find = DistUtilsExtra.auto.src_find

    def src_find_with_excludes(attrs):
        src = original_src_find(attrs)

        for pattern in patterns:
            DistUtilsExtra.auto.src_markglob(src, pattern)

        return src

    DistUtilsExtra.auto.src_find = src_find_with_excludes

    return original_src_find


def main():

    # exclude files/folder patterns from being considered by distutils-extra
    # this returns the original DistUtilsExtra.auto.src_find function
    # so we can patch bit back in later
    original_find_src = exclude_files([
        "*.sh",
        "ul",
        "Dockerfile.build*",
        "PKGBUILD.template",
        "scripts/*",
        "docs/*",
        "glade",
        "test",
        "ulauncher.desktop.dev",
        "requirements.txt",
    ])

    DistUtilsExtra.auto.setup(
        name='ulauncher',
        version='%VERSION%',
        license='GPL-3',
        author='Aleksandr Gornostal',
        author_email='ulauncher.app@gmail.com',
        description='Application launcher for Linux',
        url='https://ulauncher.io',
        data_files=DataFileList([
            ('share/icons/hicolor/48x48/apps', [
                'data/media/icons/hicolor/ulauncher.svg'
            ]),
            ('share/icons/hicolor/48x48/apps', [
                'data/media/icons/hicolor/ulauncher-indicator.svg'
            ]),
            ('share/icons/hicolor/scalable/apps', [
                'data/media/icons/hicolor/ulauncher.svg'
            ]),
            ('share/icons/hicolor/scalable/apps', [
                'data/media/icons/hicolor/ulauncher-indicator.svg'
            ]),
            # for fedora + GNOME
            ('share/icons/gnome/scalable/apps', [
                'data/media/icons/hicolor/ulauncher.svg'
            ]),
            ('share/icons/gnome/scalable/apps', [
                'data/media/icons/hicolor/ulauncher-indicator.svg'
            ]),
            # for ubuntu
            ('share/icons/breeze/apps/48', [
                'data/media/icons/ubuntu-mono-light/ulauncher-indicator.svg'
            ]),
            ('share/icons/ubuntu-mono-dark/scalable/apps', [
                'data/media/icons/hicolor/ulauncher-indicator.svg'
            ]),
            ('share/icons/ubuntu-mono-light/scalable/apps', [
                'data/media/icons/ubuntu-mono-light/ulauncher-indicator.svg'
            ]),
            ('share/icons/elementary/scalable/apps', [
                'data/media/icons/elementary/ulauncher-indicator.svg'
            ]),
        ]),
        cmdclass={'install': InstallAndUpdateDataDirectory}
    )

    # unpatch distutils-extra src_find
    DistUtilsExtra.auto.src_find = original_find_src


if __name__ == '__main__':
    main()

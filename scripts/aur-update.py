#!/usr/bin/env python3

# Run in ArchLinux container

import os
import sys
import shlex
from tempfile import mkdtemp
from subprocess import call

print("##################################")
print("# Updating AUR with a new PKGBUILD")
print("##################################")

try:
    version = sys.argv[1]
except IndexError:
    print("ERROR: First argument should be version")
    sys.exit(1)

aur_repo = "ssh://aur@aur.archlinux.org/ulauncher.git"

project_path = os.path.abspath(os.sep.join((os.path.dirname(os.path.realpath(__file__)), '..')))


def main():
    if '-' in version:
        print("Pre-release detected. Skipping AUR repository update")
        sys.exit(0)
    source = get_targz_link()
    push_update(source)


def get_targz_link():
    return f'https://github.com/Ulauncher/Ulauncher/releases/download/{version}/ulauncher_{version}.tar.gz'


def set_pkg_key(key, val, file):
    run_shell(f'sed -i -e \'/{key}\\s*=/ s#\\(=\\s*\\).*#\\1{val}#\' {file}')


def push_update(source):
    ssh_key = os.sep.join((project_path, 'scripts', 'aur_key'))
    git_ssh_command = 'ssh -oStrictHostKeyChecking=no -i %s' % ssh_key
    ssh_enabled_env = dict(os.environ, GIT_SSH_COMMAND=git_ssh_command)

    temp_dir = mkdtemp()
    print("Temp dir: %s" % temp_dir)
    print("Cloning AUR repo: %s" % aur_repo)
    run_shell(f'git clone {aur_repo} {temp_dir}', env=ssh_enabled_env)
    os.chdir(temp_dir)
    run_shell('git config user.email ulauncher.app@gmail.com')
    run_shell('git config user.name Aleksandr Gornostal')
    print("Overwriting PKGBUILD and .SRCINFO")
    set_pkg_key('pkgver', version, 'PKGBUILD')
    set_pkg_key('pkgver', version, '.SRCINFO')
    set_pkg_key('source', f'("{source}")', 'PKGBUILD')
    set_pkg_key('source', source, '.SRCINFO')
    print("Making a git commit")
    run_shell(f'git commit PKGBUILD .SRCINFO -m "Version update {version}"')
    print("Pushing changes to master branch")
    run_shell('git push origin master', env=ssh_enabled_env)


def run_shell(command, **kw):
    code = call(shlex.split(command), **kw)
    if code:
        print(f'ERROR: command {command} exited with code {code}')
        sys.exit(1)


main()

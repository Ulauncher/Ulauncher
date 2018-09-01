#!/usr/bin/env python

# Run in ArchLinux container

import os
import sys
import re
from urllib.request import urlopen
import json
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

try:
    update_stable = os.environ['UPDATE_STABLE'] in ('1', 'true')
except KeyError:
    print("ERROR: UPDATE_STABLE is not defined")
    sys.exit(1)
print('UPDATE_STABLE=%s' % update_stable)

try:
    allow_prerelease = os.environ['ALLOW_PRERELEASE'] in ('1', 'true')
except KeyError:
    print("Optional ALLOW_PRERELEASE is not set. Default to False")
    allow_prerelease = False
print('ALLOW_PRERELEASE=%s' % allow_prerelease)


if update_stable:
    aur_repo = "ssh://aur@aur.archlinux.org/ulauncher.git"
else:
    aur_repo = "ssh://aur@aur.archlinux.org/ulauncher-git.git"

project_path = os.path.abspath(os.sep.join((os.path.dirname(os.path.realpath(__file__)), '..')))


def main():
    release = fetch_release()
    is_stable = ' ' not in release['name']  # because "x.y.z (Beta)"
    if (not release['prerelease'] or allow_prerelease) and ((update_stable and is_stable) or not update_stable):
        targz = get_targz_link()
        pkgbuild = pkgbuild_from_template(targz)
        push_update(pkgbuild)
    else:
        print("Don't update AUR")
        sys.exit(0)


def fetch_release():
    print("Fetching releases from Github...")
    response = urlopen('https://api.github.com/repos/ulauncher/ulauncher/releases')
    releases = json.load(response)
    try:
        return (r for r in releases if r['tag_name'] == version).next()
    except StopIteration:
        print("ERROR: Satisfiable release version %s not found" % version)
        sys.exit(1)


def get_targz_link():
    return 'https://github.com/Ulauncher/Ulauncher/releases/download/%s/ulauncher_%s.tar.gz' % (version, version)


def pkgbuild_from_template(targz):
    template_file = '%s/PKGBUILD.template' % project_path
    with open(template_file) as f:
        content = f.read()
        content = re.sub(r'%VERSION%', version, content, flags=re.M)
        content = re.sub(r'%SOURCE%', targz, content, flags=re.M)
        if not update_stable:
            content = re.sub(r'pkgname=ulauncher', 'pkgname=ulauncher-git', content, flags=re.M)
        return content


def push_update(pkgbuild):
    ssh_key = os.sep.join((project_path, 'build-utils', 'aur_key'))
    run_shell(('chmod', '600', ssh_key))
    git_ssh_command = 'ssh -oStrictHostKeyChecking=no -i %s' % ssh_key
    ssh_enabled_env = dict(os.environ, GIT_SSH_COMMAND=git_ssh_command)

    temp_dir = mkdtemp()
    print("Temp dir: %s" % temp_dir)
    run_shell(('git', 'clone', aur_repo, temp_dir), env=ssh_enabled_env)
    os.chdir(temp_dir)
    run_shell(('git', 'config', 'user.email', 'ulauncher.app@gmail.com'))
    run_shell(('git', 'config', 'user.name', 'Aleksandr Gornostal'))
    with open('PKGBUILD', 'w') as f:
        f.write(pkgbuild)
    run_shell(('mksrcinfo'))
    run_shell(('git', 'add', 'PKGBUILD', '.SRCINFO'))
    run_shell(('git', 'commit', '-m', 'Version update %s' % version))
    run_shell(('git', 'push', 'origin', 'master'), env=ssh_enabled_env)


def run_shell(command, **kw):
    code = call(command, **kw)
    if code:
        print("ERROR: command %s exited with code %s" % (command, code))
        sys.exit(1)


main()

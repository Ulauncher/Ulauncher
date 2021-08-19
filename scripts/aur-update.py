#!/usr/bin/env python3

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

aur_repo = "ssh://aur@aur.archlinux.org/ulauncher.git"

project_path = os.path.abspath(os.sep.join((os.path.dirname(os.path.realpath(__file__)), '..')))


def main():
    if '-' in version:
        print("Unstable release detected. Won't update AUR")
        sys.exit(0)
    targz = get_targz_link()
    pkgbuild = pkgbuild_from_template(targz)
    push_update(pkgbuild)


def fetch_release():
    url = f'https://ext-api.ulauncher.io/misc/ulauncher-releases/{version}'
    print("Fetching release info from '%s'..." % url)
    return json.loads(urlopen(url).read().decode('utf-8'))


def get_targz_link():
    return f'https://github.com/Ulauncher/Ulauncher/releases/download/{version}/ulauncher_{version}.tar.gz'


def pkgbuild_from_template(targz):
    template_file = '%s/PKGBUILD.template' % project_path
    with open(template_file) as f:
        content = f.read()
        content = re.sub(r'%VERSION%', version, content, flags=re.M)
        content = re.sub(r'%SOURCE%', targz, content, flags=re.M)
        return content


def push_update(pkgbuild):
    ssh_key = os.sep.join((project_path, 'scripts', 'aur_key'))
    git_ssh_command = 'ssh -oStrictHostKeyChecking=no -i %s' % ssh_key
    ssh_enabled_env = dict(os.environ, GIT_SSH_COMMAND=git_ssh_command)

    temp_dir = mkdtemp()
    print("Temp dir: %s" % temp_dir)
    print("Cloning AUR repo: %s" % aur_repo)
    run_shell(('git', 'clone', aur_repo, temp_dir), env=ssh_enabled_env)
    os.chdir(temp_dir)
    run_shell(('git', 'config', 'user.email', 'ulauncher.app@gmail.com'))
    run_shell(('git', 'config', 'user.name', 'Aleksandr Gornostal'))
    print("Writing PKGBUILD")
    with open('PKGBUILD', 'w') as f:
        f.write(pkgbuild)
    print("Writing .SRCINFO")
    with open('.SRCINFO', 'w') as f:
        run_shell(('makepkg', '--printsrcinfo'), stdout=f)
    print("Making a git commit")
    run_shell(('git', 'add', 'PKGBUILD', '.SRCINFO'))
    run_shell(('git', 'commit', '-m', 'Version update %s' % version))
    print("Pushing changes to master branch")
    run_shell(('git', 'push', 'origin', 'master'), env=ssh_enabled_env)


def run_shell(command, **kw):
    code = call(command, **kw)
    if code:
        print("ERROR: command %s exited with code %s" % (command, code))
        sys.exit(1)


main()

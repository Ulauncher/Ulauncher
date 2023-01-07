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
AUR_ARRAY_PROPS = ["source", "sha256sums"]  # Not actually complete, just added the props we use
project_path = os.path.abspath(os.sep.join((os.path.dirname(os.path.realpath(__file__)), "..")))


def run_shell(command, **kw):
    code = call(shlex.split(command), **kw)
    if code:
        print(f"ERROR: command {command} exited with code {code}")
        sys.exit(1)


def get_targz_link():
    return f"https://github.com/Ulauncher/Ulauncher/releases/download/{version}/ulauncher_{version}.tar.gz"


def _set_pkg_key_(key, val, file):
    run_shell(f"sed -i -e '/{key}\\s*=/ s#\\(=\\s*\\).*#\\1{val}#' {file}")


# Note that this doesn't work to set arrays unless they're single values
def set_pkg_key(key, val):
    _set_pkg_key_(key, val if key not in AUR_ARRAY_PROPS else f'("{val}")', "PKGBUILD")
    _set_pkg_key_(key, val, ".SRCINFO")


def push_update(source):
    ssh_key = os.sep.join((project_path, "scripts", "aur_key"))
    git_ssh_command = f"ssh -oStrictHostKeyChecking=no -i {ssh_key}"
    ssh_enabled_env = dict(os.environ, GIT_SSH_COMMAND=git_ssh_command)
    temp_dir = mkdtemp()
    print(f"Temp dir: {temp_dir}")
    print(f"Cloning AUR repo: {aur_repo}")
    run_shell(f"git clone {aur_repo} {temp_dir}", env=ssh_enabled_env)
    os.chdir(temp_dir)
    print("Overwriting PKGBUILD and .SRCINFO")
    set_pkg_key("pkgver", version)
    set_pkg_key("pkgrel", "1")
    set_pkg_key("source", source)
    run_shell("git config user.email ulauncher.app@gmail.com")
    run_shell("git config user.name 'Aleksandr Gornostal'")
    run_shell("git add PKGBUILD .SRCINFO")
    if os.system("git diff --cached --quiet"):
        print("Making a git commit")
        run_shell(f"git commit -m 'Version update {version}'")
        print(f"Pushing {version} release to {aur_repo}")
        run_shell("git push origin master", env=ssh_enabled_env)
    else:
        print("No changes to commit (you probably already updated this version)")


def main():
    if "-" in version:
        print("Pre-release detected. Skipping AUR repository update")
        sys.exit(0)
    source = get_targz_link()
    push_update(source)


main()

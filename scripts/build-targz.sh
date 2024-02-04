#!/usr/bin/env bash

##############################################################
# Builds tar.gz file with (un)install script and Ulauncher src
##############################################################
build-targz () {
    VERSION=$(./ul version)
    ./setup.py build_prefs
    # copy gitignore to .tarignore, remove data/preferences and add others to ignore instead
    cat .gitignore | grep -v data/preferences | cat <(echo -en "preferences-src\nscripts\ntests\ndebian\ndocs\n.github\nconftest.py\nDockerfile\nCO*.md\n.*ignore\nmakefile\nnix\n.editorconfig\nrequirements.txt\n*.nix\nflake.lock\n") -  > .tarignore
    # create archive with .tarignore
    tar --transform "s|^\.|ulauncher-${VERSION}|" --exclude-vcs --exclude-ignore-recursive=.tarignore -hzcf "dist/ulauncher-${VERSION}.tar.gz" .
	rm .tarignore
	echo -e "Built source dist tarball to ./dist/ulauncher-${VERSION}.tar.gz"
}

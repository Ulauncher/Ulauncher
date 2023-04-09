#!/usr/bin/env bash

help () {
  echo "Usage:

  ${bold}./ul init-dev-env
    ${dim}Installs Ulauncher data (icons, static files for preferences, etc.) to '~/.local/share/ulauncher/'${normal}

  ${bold}./ul cleanup-dev-env
    ${dim}Removes files installed by './ul init-dev-env'. Also removes cache files, but not configs${normal}

  ${bold}./ul run
    ${dim}Alias for './bin/ulauncher -v --dev'
    Run './ul init-dev-env' first. Otherwise the app won't work${normal}

  ${bold}./ul dev-container [IMAGE_NAME]
    ${dim}Takes you into a Docker container from which you can run tests and build binary packages
    This is added for convenience so developers won't be required to install all the build and test dependencies locally

    IMAGE_NAME is an optional argument.
    If not set, an image based on ubuntu image will be used.
    Other possible options: ${normal}${bold}fedora, fedora33, arch${normal}

  ${bold}./ul rm-python-cache
    ${dim}Removes .pyc, .pyo, __pycache__${normal}

  ${bold}./ul test-mypy
    ${dim}Runs type cheker using mypy${normal}

  ${bold}./ul test-pylint
    ${dim}Runs pylint${normal}

  ${bold}./ul test-pytest
    ${dim}Runs pytest${normal}

  ${bold}./ul test
    ${dim}Runs all test-* commands${normal}

  ${bold}./ul send-signal [SIGNAL]
    ${dim}Sends a signal to Ulauncher. SIGHUP by default
    May be useful for debugging themes: Ulauncher handles SIGHUP by re-applying theme files${normal}

  ${bold}./ul edit-ui
    ${dim}Starts glade${normal}


The commands below are useful for maintainers:

  ${bold}./ul build-deb <VERSION> <--deb or --upload>
    ${dim}Builds a deb package or uploads new Ulauncher version to PPA in Launchpad${normal}

  ${bold}./ul build-rpm <VERSION> <DISTRO_NAME> [FILE_SUFFIX]
    ${dim}Builds an rpm package
    DISTRO_NAME is a required second argument and can take one of this values: feodra, suse, centos
    FILE_SUFFIX is an optional argument. By default, file suffix is DISTRO_NAME${normal}

  ${bold}./ul build-targz <VERSION>
    ${dim}Builds a targz archive with the source code${normal}

  ${bold}./ul build-preferences
    ${dim}Builds JS/HTML/CSS files for Preferences UI${normal}

  ${bold}./ul build-release
    ${dim}[CI only] script to build the tag/release and upload the package files to it, and distro repositories ${normal}

  ${bold}./ul build-doc
    ${dim}Builds API docs for extensions using sphinx${normal}

  ${bold}./ul watch-doc
    ${dim}Runs './ul build-doc' when *.py and *.rst files change${normal}"

}

#!/usr/bin/env bash

help () {
  echo "Usage:

  ${bold}./ul run
    ${dim}Alias for './bin/ulauncher -v --dev'${normal}

  ${bold}./ul dev-container
    ${dim}Takes you into an Ubuntu Docker container from which you can run tests and build binary packages
    This is added for convenience so developers won't be required to install all the build and test dependencies locally

  ${bold}./ul test-black
    ${dim}Runs black format checker${normal}

  ${bold}./ul test-mypy
    ${dim}Runs type checker using mypy${normal}

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

  ${bold}./ul build-deb
    ${dim}Builds a deb package or uploads new Ulauncher version to PPA in Launchpad${normal}

  ${bold}./ul build-targz
    ${dim}Builds a targz archive with the source code${normal}

  ${bold}./ul build-doc
    ${dim}Builds API docs for extensions using sphinx${normal}

  ${bold}./ul watch-doc
    ${dim}Runs './ul build-doc' when *.py and *.rst files change${normal}"

}

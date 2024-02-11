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

The commands below are useful for maintainers:

  ${bold}./ul sdist
    ${dim}Builds a tar.gz archive with the source code${normal}

  ${bold}./ul build-deb
    ${dim}Builds a deb package or uploads new Ulauncher version to PPA in Launchpad${normal}

  ${bold}./ul build-doc
    ${dim}Builds API docs for extensions using sphinx${normal}"

}

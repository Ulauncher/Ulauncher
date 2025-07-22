.ONESHELL:
SHELL := bash
INTERACTIVE := $(shell [ -t 0 ] && echo 1)
DOCKER_IMAGE := ulauncher/build-image:6.3
DOCKER_BIN = $(shell eval 'command -v podman || command -v docker')
YARN_BIN = $(shell eval 'command -v yarn || command -v yarnpkg')
ROOT_DIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
VERSION = $(shell eval 'python3 -c "import ulauncher; print(ulauncher.version)"')
DPKG_ARGS := "--post-clean --build=all --no-sign"
DEB_VERSION = $(subst -,~,$(VERSION))
DEB_DISTRO = $(shell eval lsb_release -sc)
DEB_PACKAGER_NAME := "" # Will default to the user full name if empty
DEB_PACKAGER_EMAIL := ulauncher.app@gmail.com

# cli font vars
BOLD := \\e[1m
GREEN := \\e[32m
RED := \\e[31m
RESET := \\e[0m

# Bash scripting in Makefile guide:
# 1. Either set `.ONESHELL:` (applies for all recipes) or write a single line
#    (by escaping with backslash at the end of the line)
# 2. Start every line with @ or it will print the line.
#    (with `.ONESHELL:` or if you're escaping that applies ONLY to the first line)
# 3. Use ${VAR} to use makefile variables and $$VAR for runtime/bash variables
# 4. Instead of $(cmd) for subshells you need to run $(shell eval "cmd")
# 5. You can't pass arguments. ie: `make run build` will run `make run`, then `make build`
#    What you should do instead is to set override the vars `make run VAR=build`

#=General Commands

.PHONY: help version run docker python-venv

help: # Shows this list of available actions (targets)
	@# Only includes targets with comments, but not if they have Commands with two ## chars
	sed -nr \
		-e 's|^#=(.*)|\n\1:|p' \
		-e 's|^([a-zA-Z-]*):([^#]*?\s# (.*))| \1\x1b[35m - \3\x1b[0m|p' \
		$(lastword $(MAKEFILE_LIST)) \
		| expand -t20

version: # Print the Ulauncher version
	@echo ${VERSION}

python-venv: # Creates a python virtual environment and installs dependencies
	@echo -e "$(GREEN)[+] Setting up Python virtual environment...$(RESET)"
	python3 -m venv --system-site-packages .venv
	@echo -e "$(GREEN)[+] Installing dependencies from requirements.txt...$(RESET)"
	.venv/bin/python -m pip install --ignore-installed --upgrade -r requirements.txt
	@echo -e "$(GREEN)[+] Installing pygobject-stubs with Gtk3 compatibility...$(RESET)"

	# Update to the latest (v2.13.0) after migration to python>=9 in Dockerfile
	.venv/bin/python -m pip install pygobject-stubs==2.12.0 --no-cache-dir --config-settings=config=Gtk3,Gdk3,Soup2

	@echo -e "\n$(GREEN)[✓] Virtual environment has been set up and is ready to use.$(RESET)"
	@echo -e "\nTo activate it, run:"
	@echo -e "  $(GREEN)source .venv/bin/activate$(RESET)      # Bash/Zsh"
	@echo -e "  $(GREEN)source .venv/bin/activate.fish$(RESET) # Fish"
	@echo -e "\nDo the activation each time you open the terminal."
	@echo "Now you can run make commands in this environment."

run: prefs # Run ulauncher from source
	# If systemd unit running, stop it, else try killall. We want to make sure to be the main/daemon instance of Ulauncher
	@if [ -n $(shell eval "command -v systemctl") ] && [ "inactive" != $(shell eval "systemctl --user is-active ulauncher") ]; then
		systemctl --user stop ulauncher
	else
		killall -eq ulauncher || true
	fi
	./bin/ulauncher --dev

run-container: # Start a bash session in the Ulauncher Docker build container (Ubuntu)
	@set -euo pipefail
	SHELL_CMD=bash
	VOL_SUFFIX=""
	if [ -z "${DOCKER_BIN}" ]; then
		echo -e "${BOLD}You need podman or docker to run this command${RESET}"
		exit 1
	fi
	if [[ "${DOCKER_BIN}" == $(shell eval "command -v docker") ]]; then
		SHELL_CMD="sudo -H -u ulauncher bash"
		if [[ $$UID != 1000 ]]; then
			SHELL_CMD="usermod -u $$UID ulauncher; $$SHELL_CMD"
		fi
		if [[ $(shell eval "id -g") != 1000 ]]; then
			SHELL_CMD="groupmod -g $(shell eval "id -g") ulauncher; $$SHELL_CMD"
		fi
	fi
	# If SELinux is enabled, append ":z" to get the right label
	if command -v selinuxenabled && selinuxenabled; then
		VOL_SUFFIX=":z"
	fi
	# port 3002 is used for developing Preferences UI
	exec ${DOCKER_BIN} run \
		--rm \
		-it \
		-v "${PWD}:/src/ulauncher$$VOL_SUFFIX" \
		-v "$$HOME/.bash_history:/home/ulauncher/.bash_history$$VOL_SUFFIX" \
		-p 3002:3002 \
		--name ulauncher \
		"docker.io/${DOCKER_IMAGE}" \
		sh -c "$$SHELL_CMD";

#=Lint/test Commands

.PHONY: check mypy ruff typos pytest test format

check: typos ruff mypy # Run all linters

test: check pytest # Run all linters and test

mypy: # Lint with mypy (type checker)
	mypy ulauncher

ruff: # Lint with ruff
	ruff check . && ruff format --check .

typos: # Lint with typos (typo checker)
	typos .

pytest: # Run unit tests
	@set -euo pipefail
	if [ -z $(shell eval "command -v xvfb-run") ]; then
		pytest -p no:cacheprovider tests
	else
		echo -e "xvfb-run detected. Running pytest in a virtual X server environment."
		xvfb-run --auto-servernum -- pytest -p no:cacheprovider tests
	fi

format: # Auto format the code
	ruff check . --fix
	ruff format .

#=Build Commands

.PHONY: prefs docker docs sdist manpage deb nix-run nix-build-dev nix-build

docs: # Build the API docs
	@set -euo pipefail
	cd docs
	sphinx-build -M html . ./_build
	if [ -n "${INTERACTIVE}" ]; then
		python3 -m http.server -d _build/html
	fi

docker: # Build the docker image (only needed if you make changes to it)
	docker build -t "${DOCKER_IMAGE}" .

prefs: # Build the preferences web app
	@set -euo pipefail
	if [ ! -d "preferences-src" ]; then
		echo -e "${BOLD}${RED}preferences-src does not exist.${RESET}"
		exit 1
	fi

	if [ -z "$(FORCE)" ] && [ -d data/preferences ] && [ -z $(shell eval "find preferences-src -newer data/preferences -print -quit") ] ; then
		echo -e "${BOLD}Preferences build SKIPPED${RESET} - No changes since last build"
		exit 0
	fi
	cd preferences-src
	${YARN_BIN}
	${YARN_BIN} build

sdist: manpage prefs # Build a source tarball
	@set -euo pipefail
	# See https://github.com/Ulauncher/Ulauncher/pull/1337 for why we're not using setuptools
	# copy gitignore to .tarignore, remove data/preferences and add others to ignore instead
	cat .gitignore | grep -v data/preferences | grep -v ulauncher.1.gz | cat <(echo -en "preferences-src\nscripts\ntests\ndebian\ndocs\n.github\nconftest.py\nDockerfile\nCO*.md\n.*ignore\nmakefile\nnix\n.editorconfig\nrequirements.txt\n*.nix\nflake.lock\n") - > .tarignore
	mkdir -p dist
	# create archive with .tarignore
	tar --transform 's|^\.|ulauncher|' --exclude-vcs --exclude-ignore-recursive=.tarignore -zcf dist/ulauncher-${VERSION}.tar.gz .
	rm .tarignore
	echo -e "Built source dist tarball to ${BOLD}${GREEN}./dist/ulauncher-${VERSION}.tar.gz${RESET}"

deb: sdist # Build a deb package. Optionally override DEB_DISTRO arguments. Ex: $`make deb DEB_DISTRO=focal`
	@set -euo pipefail
	export NAME=${DEB_PACKAGER_NAME}
	export EMAIL=${DEB_PACKAGER_EMAIL}
	if [ -z $(shell eval "command -v dpkg-buildpackage") ]; then
		echo -e "${BOLD}${RED}You need dpkg-buildpackage to build the .deb${RESET}"
		exit 1
	fi
	rm -rf dist/ulauncher_deb || true
	tar --strip-components=1 -xvf dist/ulauncher-${VERSION}.tar.gz --one-top-level=dist/ulauncher_deb
	cp -r debian dist/ulauncher_deb/
	cd dist/ulauncher_deb || exit
	rm -f debian/changelog
	dch --create --no-multimaint --package ulauncher --newversion="${DEB_VERSION}" --empty --distribution ${DEB_DISTRO}
	echo ${DPKG_ARGS} | xargs dpkg-buildpackage
	cd -
	rm -rf dist/ulauncher_deb
	echo -e "Package saved to ${BOLD}${GREEN}./dist/ulauncher_${DEB_VERSION}_all.deb${RESET}"

nix-run: # Build and run Ulauncher Nix package
	exec nix run --show-trace --print-build-logs '.#default' -- $(ARGS)

nix-build-dev: # Build Ulauncher Nix package for development
	exec nix build --out-link nix/dev --show-trace --print-build-logs $(ARGS) '.#development'

nix-build: # Build Ulauncher Nix package
	exec nix build --out-link nix/result --show-trace --print-build-logs $(ARGS) '.#default'

manpage: # Generate manpage
	@if [ -z $(shell eval "command -v help2man") ]; then
		echo -e "${BOLD}${RED}You need help2man to (re)generate the manpage${RESET}"
		exit 1
	fi
	help2man --section=1 --name="Feature rich application Launcher for Linux" --no-info ./bin/ulauncher > ulauncher.1
	echo -e "Generated manpage to ${BOLD}${GREEN}./ulauncher.1${RESET}"
	if [ -n "${INTERACTIVE}" ]; then
		man -l ulauncher.1
	fi

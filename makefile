.ONESHELL:
SHELL := bash
DOCKER_BIN = $(shell eval 'command -v docker || command -v podman')
ROOT_DIR = $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

# cli font vars
BOLD := \\e[1m
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
#    What you should do instead is to override the vars `make run VAR=build`

#=General Commands

.PHONY: help run init-dev-env cleanup-dev-env run-container send-signal edit-ui rm-python-cache

# Shows this list of available actions (targets)
help:
	@sed -nr \
		-e 's|^#=(.*)|\n\1:|p' \
		-e '/^# (.*)/ { N; s|^# (.*)\n([a-zA-Z0-9_-]*):.*| \2\x1b[35m - \1\x1b[0m|p }' \
		$(lastword $(MAKEFILE_LIST)) \
		| expand -t20

# Run Ulauncher from source, with verbose logging. Pass extra arguments with ARGS.
run:
	@exec ./bin/ulauncher -v --dev $(ARGS)

# Install the data files and a .desktop file to ~/.local, so icons load by name
init-dev-env:
	@exec ./ul init-dev-env

# Remove what init-dev-env installed, and the caches and dbs (but not the config)
cleanup-dev-env:
	@exec ./ul cleanup-dev-env

# Start a bash session in the Docker build container, so you can build packages without the deps
run-container:
	@exec ./ul dev-container $(IMAGE)

# Signal the running Ulauncher process, HUP by default, which makes it reload the theme
send-signal:
	@# the brackets keep the pattern from matching the grep itself, and sed takes the pid column
	exec kill -$(or $(SIGNAL),HUP) $$(ps aux | grep '[u]launcher' | head -n1 | sed -E 's/^[^ ]+ +([0-9]+).*/\1/')

# Open Glade with the Ulauncher widget catalog. Ex: `make edit-ui FILE=data/ui/UlauncherWindow.ui`
edit-ui:
	@export GLADE_CATALOG_SEARCH_PATH=./data/ui
	exec glade $(FILE)

# Remove all .pyc and .pyo files and __pycache__ directories
rm-python-cache:
	@find . \( -name '*.pyc' -o -name '*.pyo' \) -type f -delete
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

#=Lint/test Commands

.PHONY: lint check check-container check-all flake8 mypy pylint pytest

# Run all linters
lint: flake8 mypy pylint

# Run all linters and unit tests
check: lint pytest

# Run all linters and unit tests inside the Docker build container
check-container:
	@source ./scripts/common.sh
	# SELinux needs the ":z" label on mounted volumes
	if command -v selinuxenabled >/dev/null && selinuxenabled; then vol_suffix=":z"; else vol_suffix=""; fi
	exec $(DOCKER_BIN) run --rm -v "$(ROOT_DIR):/root/ulauncher$$vol_suffix" $$BUILD_IMAGE make check

# Run all checks locally and in the Docker build container
check-all: check
	@$(MAKE) --no-print-directory check-container

# Lint with flake8
flake8:
	@echo -e "$(BOLD)[+] flake8$(RESET)"
	flake8 .

# Type check with mypy
mypy:
	@echo -e "$(BOLD)[+] mypy$(RESET)"
	mypy .

# Lint with pylint (slow)
pylint:
	@echo -e "$(BOLD)[+] pylint$(RESET)"
	pylint --output-format=colorized ulauncher

# Run unit tests. Pass extra arguments with ARGS.
pytest:
	@echo -e "$(BOLD)[+] pytest$(RESET)"
	export PYTHONPATH=$(ROOT_DIR)
	# tests that need a display are skipped without one, so give the container a virtual one
	if [ -f /.dockerenv ] || [ -f /run/.containerenv ]; then
	  export DISPLAY=:1
	  exec xvfb-run pytest $(ARGS) tests
	fi
	exec pytest $(ARGS) tests

#=Build Commands

.PHONY: docker prefs docs watch-docs sdist deb rpm build-release upload-release require-version

# Build the Docker build image, which is only needed if you change the Dockerfile
docker:
	@source ./scripts/common.sh
	exec $(DOCKER_BIN) build -t "$$BUILD_IMAGE" .

# Build the preferences web app. Set SKIP_IF_BUILT=1 to keep an existing build.
prefs:
	@exec ./ul build-preferences $(if $(SKIP_IF_BUILT),--skip-if-built)

# Build the extension API docs with sphinx
docs:
	@exec ./ul build-doc

# Rebuild the docs whenever a .py or .rst file changes
watch-docs:
	@exec ./ul watch-doc

# Build a source tarball. Ex: `make sdist VERSION=5.15.16`
sdist: require-version
	@exec ./ul build-targz $(VERSION)

# Build a deb package. Ex: `make deb VERSION=5.15.16`
deb: require-version
	@exec ./ul build-deb $(VERSION) --deb

# Build an rpm package. Ex: `make rpm VERSION=5.15.16 DISTRO=fedora`. Also takes SUFFIX.
rpm: require-version
	@exec ./ul build-rpm $(VERSION) $(or $(DISTRO),fedora) $(SUFFIX)

# Build every release artifact in containers. Ex: `make build-release VERSION=5.15.16`
build-release: require-version
	@exec ./ul build-release $(VERSION)

# Attach the built artifacts to the release and upload them. Ex: `make upload-release VERSION=5.15.16`
upload-release: require-version
	@exec ./ul upload-release $(VERSION)

require-version:
	@if [ -z "$(VERSION)" ]; then
	  echo -e "$(BOLD)$(RED)[!] Set the version, ex: make $(MAKECMDGOALS) VERSION=5.15.16$(RESET)"
	  exit 1
	fi

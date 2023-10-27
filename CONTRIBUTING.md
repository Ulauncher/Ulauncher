## Communication

Please read our General communication guidelines [here](CODE_OF_CONDUCT.md#General_communication_guidelines).

## Code contributions

Thank you for you interest in contributing to Ulauncher! We very much appreciate it.

Issues with the [contributor-friendly](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) label are more straight forward to implement. Other issues may require in-depth knowledge of the Ulauncher architecture. Before you put the work in, you may want to ask about it in [Code Contributions](https://github.com/Ulauncher/Ulauncher/discussions/categories/code-contributions), to ensure that it's a feature or improvement we want.

Although there are no releases for it yet as of writing this, all the active development is happening for Ulauncher [v6](https://github.com/Ulauncher/Ulauncher/milestone/7). So use the v6 (default) branch as the base branch and target for new pull requests, and check that your contributions haven't already been fixed there.

### Setup Development Environment

For the v6 branch you need the the following to setup the local build environment:

* Git
* [Yarn](https://classic.yarnpkg.com/en/docs/install)
* python3-setuptools (if you have pip, you have it already)
* Application runtime dependencies (if you already installed Ulauncher you should have most of these, but **wnck is new for v6**)
* Optionally install [pygobject-stubs](https://github.com/pygobject/pygobject-stubs). Note that pygobject-stubs can only be installed for Gtk3 OR Gtk4. The only way to switch is to reinstall. Ulauncher uses Gtk3, but Gtk4 is the default. Rather than requiring users to install it for Gtk3 we are currently ignoring the mypy errors for all the incompatible places.

#### Distro specific instructions

<details>
  <summary>Ubuntu/Debian</summary>

  Install the development dependecies:

  ```sh
  sudo apt update && sudo apt install git yarnpkg python3-setuptools debhelper dh-python
  ```

  Install the Python testing packages (read about the `PIP_BREAK_SYSTEM_PACKAGES` flag [here](https://peps.python.org/pep-0668/)):

  ```sh
  PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 PIP_BREAK_SYSTEM_PACKAGES=1 pip3 install -r requirements.txt
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well (requires universe repo):

  ```sh
  sudo add-apt-repository universe
  sudo apt install python3-{all,gi,levenshtein} gobject-introspection \
    gir1.2-{glib-2.0,gtk-3.0,webkit2-4.0,wnck-3.0}
  ```

</details>

<details>
  <summary>Arch</summary>

  First, install your system updates:

  ```sh
  sudo pacman -Syu
  ```

  Install the development and testing dependecies:

  ```sh
  sudo pacman -Syu --needed git yarn mypy ruff python-{black,pytest,pytest-mock,setuptools}
  ```

  To get types from pygobject, you need [pygobject-stubs](https://github.com/pygobject/pygobject-stubs) for GTK3. There is a AUR package for this, but it's only for GTK4, so the pip install is recommended (read about the `PIP_BREAK_SYSTEM_PACKAGES` flag [here](https://peps.python.org/pep-0668/)):

  ```sh
  PYGOBJECT_STUB_CONFIG=Gtk3,Gdk3,Soup2 PIP_BREAK_SYSTEM_PACKAGES=1 pip install --no-cache-dir pygobject-stubs
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well:

  ```sh
  sudo pacman -Syu --needed gtk3 webkit2gtk-4.1 libwnck3 python-{cairo,gobject,levenshtein}
  ```

</details>

#### Running the app from the local repository

1. `git clone` the repository locally
1. If you have Ulauncher running, make sure you stop it. For systemd this will do it: `systemctl --user stop ulauncher`
1. Open a terminal window and cd into the ulauncher repository root directory.
1. Run `./bin/ulauncher -v` to start the app (`-v` turns on verbose logging), so you can test it.
1. When you are done testing or want to restart, press ctrl+c to stop the Ulauncher process.

### How to contribute

Use the Ulauncher working branch (v6), and verify that the issue or feature hasn't already been resolved there.

1. Follow the steps above to set up and test locally, but fork the Ulauncher repo and git clone from that fork instead (or change/add the remote to your fork).
1. When you are ready to contribute code, create a new branch for your PR.
1. Commit and push your changes. When possible, try to make your changes so that each commit changes just one thing, and please use [Conventional Commits](https://www.conventionalcommits.org/) for your commit messages.
1. Create a pull request (provide the relevant information suggested by the template). Use the v6 branch as the base branch and target.

Check out our [Developer resources](https://github.com/Ulauncher/Ulauncher/discussions/879) for links for GTK/GOjbject documentation and similar.

There are some more helpful developer and maintainer commands provided by the `ul` wrapper. `./ul` lists all of them, but most of them are only useful to the maintainers and/or requires docker/podman.

If you have any questions, feel free to ask in a our [Code Contributions](https://github.com/Ulauncher/Ulauncher/discussions/categories/code-contributions) Discussions.

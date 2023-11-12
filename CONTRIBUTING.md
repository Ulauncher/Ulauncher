## Communication

Please read our General communication guidelines [here](CODE_OF_CONDUCT.md#General_communication_guidelines).

## Code contributions

Thank you for you interest in contributing to Ulauncher! We much appreciate it.

Issues with the [contributor-friendly](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) label are more straight forward to implement. Other issues may require in-depth knowledge of the Ulauncher architecture. Before you put the work in, you may want to ask about it in [Code Contributions](https://github.com/Ulauncher/Ulauncher/discussions/categories/code-contributions), to ensure that it's a feature or improvement we want.

There are no more releases are planned for Ulauncher v5 unless we discover critical bugs and fix these. All the active development is happening for Ulauncher [v6](https://github.com/Ulauncher/Ulauncher/milestone/7). So use the [v6 branch](https://github.com/Ulauncher/Ulauncher/tree/v6) as the base branch and target for new pull requests, and check that your contributions haven't already been fixed there.

### Setup Development Environment

For the v6 branch you need the the following to setup the local build environment:

* Git
* [Yarn](https://classic.yarnpkg.com/en/docs/install)
* python3-setuptools (if you have pip, you have it already)
* Application runtime dependencies (if you already installed Ulauncher you should have these)

#### Distro specific instructions

<details>
  <summary>Ubuntu/Debian</summary>

  Install the development dependencies:

  ```sh
  sudo apt-get update && sudo apt-get install git yarnpkg python3-setuptools
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well:

  ```sh
  sudo apt-get install \
    gobject-introspection libgtk-3-0 libkeybinder-3.0-0 wmctrl \
    gir1.2-{glib-2.0,gtk-3.0,gdkpixbuf-2.0,notify-0.7,webkit2-4.0,keybinder-3.0,ayatanaappindicator3-0.1} \
    python3-{all,gi,dbus,levenshtein}
  ```

</details>

<details>
  <summary>Arch</summary>

  First, install your system updates:

  ```sh
  sudo pacman -Syu
  ```

  Install the development dependencies:

  ```sh
  sudo pacman -Syu --needed git yarn python-setuptools
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well:

  ```sh
  sudo pacman -Syu --needed \
    gobject-introspection-runtime gtk3 gdk-pixbuf2 libnotify libkeybinder3 libappindicator-gtk3 \
    webkit2gtk wmctrl python-{gobject,cairo,dbus,levenshtein}
  ```
</details>

### How to build, run and contribute

Please note that no more releases are planned for Ulauncher v5 unless they are critical bug fixes. All the active development is happening for Ulauncher [v6](https://github.com/Ulauncher/Ulauncher/milestone/7). So use the v6 branch as the base branch and target for new Pull requests, and check that your contributions haven't already been fixed.

1. Fork the repo, check out the v6 branch and clone your fork locally.
1. Create a new branch for your PR
1. Make your changes to the code
1. If you have Ulauncher running, make sure you stop it. For systemd this will do it: `systemctl --user stop ulauncher.service`
1. `./bin/ulauncher -v` runs the app from the git root directory (`-v` turns on verbose logging), so you can test it.
1. Create a pull request (provide the relevant information suggested by the template)

Check out our [Developer resources](https://github.com/Ulauncher/Ulauncher/discussions/879) for links for GTK/GOjbject documentation and similar.

There are more some helpful developer and maintainer commands provided by the `ul` wrapper. `./ul` lists all of them, but most of them are only useful to the maintainers and/or requires docker/podman.

If you have any questions, feel free to ask in a our [Code Contributions](https://github.com/Ulauncher/Ulauncher/discussions/categories/code-contributions) Discussions.

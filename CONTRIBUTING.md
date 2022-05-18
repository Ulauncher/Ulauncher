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

#### Distro specific instructions

<details>
  <summary>Ubuntu/Debian</summary>

  Install the development dependecies:

  ```sh
  sudo apt-get update && sudo apt-get install git yarnpkg python3-setuptools
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well:

  ```sh
  sudo apt-get install python3-{all,gi,levenshtein} gobject-introspection \
    gir1.2-{glib-2.0,gtk-3.0,notify-0.7,webkit2-4.0,wnck-3.0,keybinder-3.0,ayatanaappindicator3-0.1}    
  ```

</details>

<details>
  <summary>Arch</summary>

  First, install your system updates:

  ```sh
  sudo pacman -Syu
  ```

  Install the development dependecies:

  ```sh
  sudo pacman -Syu --needed git yarn python-setuptools
  ```

  If you don't have Ulauncher installed already, install the runtime dependencies as well:

  ```sh
  sudo pacman -Syu --needed \
    gtk3 webkit2gtk libappindicator-gtk3 libnotify libkeybinder3 libwnck3 python-{gobject,levenshtein}
  ```
</details>

### How to build, run and contribute

Use the v6 branch as the base branch and target for new Pull requests, and check that your contributions haven't already been fixed.

1. Fork the repo here and clone your fork locally.
1. Create a new branch for your PR
1. Make your changes to the code
1. If you have Ulauncher running, make sure you stop it. For systemd this will do it: `systemctl --user stop ulauncher`
1. `./bin/ulauncher -v` runs the app from the git directory (`-v` turns on verbose logging), so you can test it.
1. Commit and push your changes. When possible, try to make your changes so that each commit changes just one thing.
1. Create a pull request (provide the relevant information suggested by the template)

Check out our [Developer resources](https://github.com/Ulauncher/Ulauncher/discussions/879) for links for GTK/GOjbject documentation and similar.

There are some more helpful developer and maintainer commands provided by the `ul` wrapper. `./ul` lists all of them, but most of them are only useful to the maintainers and/or requires docker/podman.

If you have any questions, feel free to ask in a our [Code Contributions](https://github.com/Ulauncher/Ulauncher/discussions/categories/code-contributions) Discussions.

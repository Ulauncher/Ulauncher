[![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=dev)](https://travis-ci.org/Ulauncher/Ulauncher)


[Application Launcher for Linux 🐧](https://ulauncher.io)
================================

Ulauncher is a fast application launcher for Linux. It's is written in Python, using GTK+, and features: App Search (fuzzy matching), Calculator, [Extensions](https://ext.ulauncher.io/), Shortcuts, File browser mode and [Custom Color Themes](https://docs.ulauncher.io/en/latest/themes/themes.html)

| App Search | File Browser | Color Themes |
---|---|---
|![screenshot](https://i.imgur.com/8FpJLGG.png?1)|![screenshot](https://i.imgur.com/wJvXSmP.png?1)|![screenshot](https://i.imgur.com/2a4GCW7.png?1)|

For more info or download links see [ulauncher.io](https://ulauncher.io)


### Run Ulauncher on startup

If your distribution uses [Systemd](https://www.freedesktop.org/wiki/Software/systemd/) and the packages includes [ulauncher.service](ulauncher.service), then you can run `ulauncher` on startup by running:

```
systemctl --user enable --now ulauncher
```

If not, then you can open Ulauncher and enable "Launch at Login" in the preferences.


### Known Issues and workarounds

* If your DE doesn't use compositing, run ulauncher with `--no-window-shadow` to remove a black box around a window
* [inotify watch limit reached](https://github.com/Ulauncher/Ulauncher/issues/51)
* [Can't map the keys to ALT+SPACE](https://github.com/Ulauncher/Ulauncher/issues/100)
* [Hotkey doesn't work in Wayland when is triggered from certain apps](https://github.com/Ulauncher/Ulauncher/issues/183)
* [Border appears around ulauncher window in Sway DE](https://github.com/Ulauncher/Ulauncher/issues/230#issuecomment-570736422)
* [Pass custom environment variable to Ulauncher](https://github.com/Ulauncher/Ulauncher/issues/780#issuecomment-912982174)


### Code Contribution


| Project | Contributor-friendly Issues |
---|---
| Ulauncher App | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/contributor-friendly.svg?color=3cf014&label=All%20contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Python.svg?color=5319e7&label=Python&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Python) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/VueJS.svg?color=a553cc&label=VueJS&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/VueJS) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Linux.svg?color=0e035e&label=Linux&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Linux)|
| [Frontend for extensions website](https://github.com/Ulauncher/ext.ulauncher.io) <br> Uses ReactJS | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext.ulauncher.io/labels/contributor-friendly)|
| [API for extensions website](https://github.com/Ulauncher/ext-api.ulauncher.io) <br> Uses Python and bottle library | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext-api.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext-api.ulauncher.io/labels/contributor-friendly)|

Contributions are appreciated, but before you put a the work in please ensure that it's a feature or improvement we want by creating an [issue](https://github.com/Ulauncher/Ulauncher/issues) for it if there isn't one already. Be aware that we might still not accept the PR depending on the implementation. Issues with the [contributor-friendly](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) label are more straight forward to implement without in depth knowledge of the Ulauncher architecture.

### Setup Development Environment

You need the the following:

* [Docker](https://docs.docker.com/engine/installation/)
* python3-distutils-extra (may just be named python-distutils-extra in some distros)
* Application runtime dependencies (if you already installed Ulauncher you should have these)

#### Distro specific instructions

<details>
  <summary>Ubuntu/Debian</summary>

  Install the dependencies (note that Docker recommends to use their installation instructions instead to get the latest version)

  ```
  sudo apt-get update && sudo apt-get install \
    docker.io gobject-introspection libgtk-3-0 libkeybinder-3.0-0 \
    gir1.2-{gtk-3.0,keybinder-3.0,webkit2-4.0,glib-2.0,gdkpixbuf-2.0,notify-0.7,ayatanaappindicator3-0.1} \
    python3-{all,gi,distutils-extra,xdg,dbus,pyinotify,levenshtein,websocket}
  ```
  
  Enable docker and set permissions
  
  ```
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER
  ```

</details>

### How to build, run and contribute
1. Fork the repo and clone your fork locally.
1. Create a new branch for your PR
1. Run `$ ./ul dev-container` to take you into a Docker container from which you can run build and test scripts. Use `sudo -E ./ul dev-container` if your user is not in the `docker` group.
1. Build the preferences UI from inside the docker container: `root@container: # ./ul build-preferences`
1. Make your changes to the code
1. Run the app `$ ./ul run`
1. Write unit tests and check if all tests pass using `root@container: # ./ul test` command (preferably from inside the container)
1. Create a pull request (provide the relevant information suggested by the template)

For GTK-related issues you may want to check out [Useful Resources for a Python GTK Developer](https://github.com/Ulauncher/Ulauncher/wiki/Resources-for-a-Python-GTK-Developer).

If you have any questions, feel free to ask in a Github issue.

`./ul` lists more commands (note that many of them are only useful to the maintainers).


### License

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

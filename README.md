Master: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=master)](https://travis-ci.org/Ulauncher/Ulauncher)
Dev: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=dev)](https://travis-ci.org/Ulauncher/Ulauncher)


[Application Launcher for Linux 🐧](https://ulauncher.io)
================================

Ulauncher is a fast application launcher for Linux. It's is written in Python, using GTK+.

| App Search | File Browser | Custom Themes |
---|---|---
|![screenshot](http://i.imgur.com/8FpJLGG.png?1)|![screenshot](http://i.imgur.com/wJvXSmP.png?1)|![screenshot](http://i.imgur.com/2a4GCW7.png?1)|

Download it at [ulauncher.io](http://ulauncher.io)


[Create Your Ulauncher Extensions](http://docs.ulauncher.io/)
==============================================================

As of Ulauncher v3, you can create your own Ulauncher extensions
Check out [docs.ulauncher.io](http://docs.ulauncher.io/) to find out how.


[Create Your Ulauncher Color themes](http://docs.ulauncher.io/en/latest/themes/themes.html)
==============================================================

As of Ulauncher v4, you can create your own color themes
Check out [docs.ulauncher.io](http://docs.ulauncher.io/en/latest/themes/themes.html) to find out how.


Known Issues
============

* Ubuntu 14.04 is not supported since v4.0
* [[Solved] inotify watch limit reached](https://github.com/Ulauncher/Ulauncher/issues/51)
* [[Workaround exists] Can't map the keys to ALT+SPACE](https://github.com/Ulauncher/Ulauncher/issues/100)
* [[Workaround exists] Hotkey doesn't work in Wayland when is triggered from certain apps](https://github.com/Ulauncher/Ulauncher/issues/183)


Code Contribution
=================

Any code contributions are welcomed as long as they are discussed in [Github Issues](https://github.com/Ulauncher/ext.ulauncher.io/issues) with maintainers.
Be aware that if you decide to change something and submit a PR on your own, it may not be accepted.

Checkout [Code Contribution Guidelines](https://github.com/Ulauncher/Ulauncher/wiki/Code-Contribution) for more info.

### Setup Development Environment

You must have the following things installed:

* [Docker](https://docs.docker.com/engine/installation/)
* python3-distutils-extra
* Application runtime dependencies.
  (You don't have to manually install these if you have already installed Ulauncher)

  ```
  sudo apt-get install \
    libkeybinder-3.0-0 \
    libgtk-3-0 \
    gir1.2-gtk-3.0 \
    gir1.2-keybinder-3.0 \
    gir1.2-webkit2-4.0 \
    gir1.2-glib-2.0 \
    gir1.2-notify-0.7 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-appindicator3-0.1 \
    python3-dbus \
    python3-levenshtein \
    python3-pyinotify \
    python3-websocket \
    python3-xdg
  ```

### Build and Run
1. `$ ./ul init-dev-env` installs Ulauncher data to `~/.local/share/ulauncher/`
1. `$ ./ul dev-container` will take you into a Docker container from which you can run build and test scripts. Use `sudo -E ./ul dev-container` if your user is not in the `docker` group.
1. `root@container: # ./ul build-preferences` build preferences UI in JS/HTML
1. `root@container: # ./test` runs linter, type checker, and unit tests
1. `$ ./ul run` runs the app

Check out output of `./ul` to find more useful commands.


License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

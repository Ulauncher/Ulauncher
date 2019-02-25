Master: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=master)](https://travis-ci.org/Ulauncher/Ulauncher)
Dev: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=dev)](https://travis-ci.org/Ulauncher/Ulauncher)


[Application Launcher for Linux 🐧](http://ulauncher.io)
================================

Ulauncher is a fast application launcher for Linux. It's is written in Python, using GTK+.

| App Search | File Browser | Custom Themes |
---|---|---
|![screenshot](http://i.imgur.com/8FpJLGG.png?1)|![screenshot](http://i.imgur.com/wJvXSmP.png?1)|![screenshot](http://i.imgur.com/2a4GCW7.png?1)|


[Create Your Ulauncher Extensions](http://docs.ulauncher.io/)
==============================================================

As of Ulauncher v3, you can create your own Ulauncher extensions  
Check out [docs.ulauncher.io](http://docs.ulauncher.io/) to find out how.


[Create Your Ulauncher Color Themes](http://docs.ulauncher.io/en/latest/themes/themes.html)
==============================================================

As of Ulauncher v4, you can create your own color themes.

Check out [docs.ulauncher.io](http://docs.ulauncher.io/en/latest/themes/themes.html) to find out how,
or go to [here](https://gist.github.com/gornostal/02a232e6e560da7946c053555ced6cce) to see themes contributed by other users.


Known Issues
============

* Ubuntu 14.04 is not supported since v4.0
* [[Solved] inotify watch limit reached](https://github.com/Ulauncher/Ulauncher/issues/51)
* [[Workaround exists] Can't map the keys to ALT+SPACE](https://github.com/Ulauncher/Ulauncher/issues/100)
* [[Workaround exists] Hotkey doesn't work in Wayland when is triggered from certain apps](https://github.com/Ulauncher/Ulauncher/issues/183)


Install for Development
=======================

If you just want to use the app, see download instructions at [ulauncher.io](http://ulauncher.io)

### Dev Requirements

* [Docker](https://docs.docker.com/engine/installation/)
* [python-distutils-extra](https://launchpad.net/python-distutils-extra)
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
    python-dbus \
    python-levenshtein \
    python-pyinotify \
    python-pysqlite2 \
    python-websocket \
    python-xdg \
    python-distutils-extra
  ```

### Build and Run
1. `$ ./build-utils/dev-container.sh` will take you into a Docker container from which you can run build and test scripts
2. `root@container: # ./build-utils/build-preferences.sh` build preferences UI in JS/HTML
3. `root@container: # ./test tests` runs Python tests
4. `$ ./dev-run.sh` installs Ulauncher data to `~/.local/share/ulauncher/` and then runs the app

If you have any questions, join chat in [Gitter](https://gitter.im/Ulauncher/General)

***
### Want to contribute? [See How!](https://github.com/Ulauncher/Ulauncher/wiki/Code-Contribution)
***

License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

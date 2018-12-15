Master: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=master)](https://travis-ci.org/Ulauncher/Ulauncher)
Dev: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=dev)](https://travis-ci.org/Ulauncher/Ulauncher)


[Application Launcher for Linux 🐧](https://ulauncher.io)
================================

Ulauncher s a fast application launcher for Linux written in Python and uses GTK+ as a GUI toolkit.

| App Search | File Browser | Custom Themes |
---|---|---
|![screenshot](http://i.imgur.com/8FpJLGG.png?1)|![screenshot](http://i.imgur.com/wJvXSmP.png?1)|![screenshot](http://i.imgur.com/2a4GCW7.png?1)|


[Create Your Ulauncher Extensions](http://docs.ulauncher.io/)
==============================================================

Since Ulauncher v3 you can create your own Ulauncher extensions  
Check out [docs.ulauncher.io](http://docs.ulauncher.io/) to find out how.


[Create Your Ulauncher Color themes](http://docs.ulauncher.io/en/latest/themes/themes.html)
==============================================================

Since Ulauncher v4 you can create your own color Themes  
Check out [docs.ulauncher.io](http://docs.ulauncher.io/en/latest/themes/themes.html) to find out how.


Known Issues
============

* Ubuntu 14.04 is not supported since v4.0
* [[Solved] inotify watch limit reached](https://github.com/Ulauncher/Ulauncher/issues/51)
* [[Workaround exists] Can't map the keys to ALT+SPACE](https://github.com/Ulauncher/Ulauncher/issues/100)
* [[Workaround exists] Hotkey doesn't work in Wayland when is triggered from certain apps](https://github.com/Ulauncher/Ulauncher/issues/183)


Install for Development
=======================

If you just want to use the app see download instructions at [ulauncher.io](https://ulauncher.io)

### Dev Requirements

* [Docker](https://docs.docker.com/engine/installation/)
* python3-distutils-extra
* Application runtime dependencies.  
  (You don't have to manually install those if you had already installed Ulauncher)  
  
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
1. `$ ./build-utils/dev-container.sh` will take you into a Docker container from which you can run build and test scripts
2. `root@container: # ./build-utils/build-preferences.sh` build preferences UI in JS/HTML
3. `root@container: # ./test tests` runs Python tests
4. `$ ./dev-run.sh` installs Ulauncher data to `~/.local/share/ulauncher/` and then runs the app

If you have any questions, join chat in [Gitter](https://gitter.im/Ulauncher/General)

***
### Want to contribute? [See How!](https://github.com/Ulauncher/Ulauncher/wiki)
***

License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

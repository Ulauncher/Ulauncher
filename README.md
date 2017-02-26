Master: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=master)](https://travis-ci.org/Ulauncher/Ulauncher)
Dev: [![Build Status](https://travis-ci.org/Ulauncher/Ulauncher.svg?branch=dev)](https://travis-ci.org/Ulauncher/Ulauncher)

[Ulauncher](http://ulauncher.io)
========

**[Ulauncher](http://ulauncher.io)** Application launcher for Linux.  
It's written in Python and uses GTK as a GUI toolkit.

<img width="290" aligh="left" src="http://i.imgur.com/3owfsfV.png?1">
<img width="290" aligh="left" src="http://i.imgur.com/W1rryU5.png?1">
<img width="290" aligh="left" src="http://i.imgur.com/Axhqjp0.png?1">

Install for Development
===========

If you just want to use the app see download instructions at ulauncher.io

### Dev Requirements

* [Docker](https://docs.docker.com/engine/installation/)
* [python-distutils-extra](https://launchpad.net/python-distutils-extra)
* Application runtime dependencies. Listed in `install.sh`.  
  You don't have to manually install those if you had already installed Ulauncher

### Build and Run
1. `./build-utils/dev-container.sh` will take you into a Docker container from which you can run build scripts
2. `./build-utils/build-preferences.sh` build preferences UI in JS/HTML
3. `./test tests` runs Python tests
4. `./dev-run.sh` installs Ulauncher data to `~/.local/share/ulauncher/` and then runs the app

If you have any questions, join chat in [Gitter](https://gitter.im/Ulauncher/General)

Known Issues
============

* [inotify watch limit reached](https://github.com/Ulauncher/Ulauncher/issues/51)

***
### Want to contribute? [See How!](https://github.com/Ulauncher/Ulauncher/wiki)

### Reed [How to Report A New Bug](https://github.com/Ulauncher/Ulauncher/wiki/How-to-Report-A-New-Bug)
***

License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

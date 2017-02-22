Dev: [![Build Status](https://semaphoreci.com/api/v1/projects/9b1a4089-bf7e-4e02-833b-7cecc3c942ea/420163/shields_badge.svg)](https://semaphoreci.com/ulauncher/ulauncher)
Master: [![Build Status](https://semaphoreci.com/api/v1/projects/9b1a4089-bf7e-4e02-833b-7cecc3c942ea/581066/shields_badge.svg)](https://semaphoreci.com/ulauncher/ulauncher)

TODO: add links to .tar.gz
TODO: update text

[Ulauncher](http://ulauncher.io)
========

**[Ulauncher](http://ulauncher.io)** is a desktop application for Linux that allows users to launch installed applications and open file directories using a fast and convenient UI.

It's written in Python and uses GTK as a GUI toolkit.

***
:warning: **Currently it is tested and distributed only for *Debian-based* distors.**  
To run Ulauncher on rpm-based OS, clone the repo and install needed dependencies manually (see `./build-utils/install-deps.sh` file).  
*[Help us create RPM distribution!](https://github.com/Ulauncher/Ulauncher/issues/27)*
***

<img height="220" aligh="left" src="http://i.imgur.com/YAiF0ue.png">
<img height="200" aligh="left" src="http://i.imgur.com/VN9LaTT.png">

Install & Run
===========

### From PPA

```
sudo add-apt-repository ppa:agornostal/ulauncher
sudo apt-get update
sudo apt-get install ulauncher
ulauncher
```

### From Sources

*Useful for developers or those who want to use latest source code*

```
git clone https://github.com/Ulauncher/Ulauncher.git
cd Ulauncher
./build-utils/install-deps.sh
./run
```

`./run` will copy icon files to `~/.local/share/icons/` and `.desktop` file to `~/.local/share/applications/`. Then it will run the app.

After you run `./run` once, you can find and start ulauncher from your OS launcher (like Ubuntu Dash, etc.)

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

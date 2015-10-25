Dev: [![Build Status](https://semaphoreci.com/api/v1/projects/9b1a4089-bf7e-4e02-833b-7cecc3c942ea/420163/shields_badge.svg)](https://semaphoreci.com/ulauncher/ulauncher)
Mater: [![Build Status](https://semaphoreci.com/api/v1/projects/9b1a4089-bf7e-4e02-833b-7cecc3c942ea/581066/shields_badge.svg)](https://semaphoreci.com/ulauncher/ulauncher)

Ulauncher
========

**Ulauncher** is a desktop application for Linux that allows users to launch installed applications 
and open file directories using a fast and convenient UI.

It's written in Python and uses GTK as a GUI toolkit.

Install
======

### From PPA

```
sudo add-apt-repository ppa:agornostal/ulauncher
sudo apt-get update
sudo apt-get install ulauncher
```

### From Sources

*Useful for developers or those who want to use latest source code*

```
git clone https://github.com/Ulauncher/Ulauncher.git
cd Ulauncher
./install_deps
./run
```

`./run` will copy icon files to `~/.local/share/icons/` and `.desktop` file to `~/.local/share/applications/`. Then it will run the app.

After you run `./run` once, you can find and start ulauncher from your OS launcher (like Ubuntu Dash, etc.)

Run Unit Tests
=========

`./test [file_path]`


Conventions
===========

* *Config directory* (`~/.config/ulauncher/apps`) should contain only human-readable config files or other assets
* *Cache directory* (`~/.cache/ulauncher/apps`) should contain auto-generated files (logs, user query DB, etc.)


License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

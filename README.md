[![Build Status](https://semaphoreci.com/api/v1/projects/75187cd4-f9eb-4135-b9fb-63e74f48d2dd/420152/shields_badge.svg)](https://semaphoreci.com/agornostal/ulauncher)

Install Dependencies
====================

1. `sudo apt-get install python-xdg gir1.2-gtk-3.0 python-dbus python-levenshtein libgtk-3-0 gir1.2-keybinder-3.0 libkeybinder-3.0-0 gir1.2-glib-2.0 gir1.2-gdkpixbuf-2.0 gir1.2-appindicator3-0.1 python-inotify python-pip`
2. `sudo pip install -r requirements.txt`

Ulauncher
=========

`./run`

Run tests
=========

`./test [file_path]`


Conventions
===========

* *Config directory* (`~/.config/ulauncher/apps`) should contain only human-readable config files or other assets
* *Cache directory* (`~/.cache/ulauncher/apps`) should contain auto-generated files (logs, user query DB, etc.)


License
=======

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

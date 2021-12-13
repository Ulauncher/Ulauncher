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

* If you get a black box or border a border around the Ulauncher window, it's likely because your compositor or desktop environment doesn't support shadows. Try turning them off from the settings. For Sway in particular you may need to follow [these instructions](https://github.com/Ulauncher/Ulauncher/issues/230#issuecomment-570736422)
* [Can't map the keys to ALT+SPACE](https://github.com/Ulauncher/Ulauncher/issues/100)
* [Hotkey doesn't work in Wayland when is triggered from certain apps](https://github.com/Ulauncher/Ulauncher/issues/183)
* [Pass custom environment variable to Ulauncher](https://github.com/Ulauncher/Ulauncher/issues/780#issuecomment-912982174)


### Code Contributions

Please see our [Code Contributions](CONTRIBUTING.md) documentation.


| Project | Contributor-friendly Issues |
---|---
| Ulauncher App | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/contributor-friendly.svg?color=3cf014&label=All%20contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Python.svg?color=5319e7&label=Python&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Python) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/VueJS.svg?color=a553cc&label=VueJS&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/VueJS) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Linux.svg?color=0e035e&label=Linux&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Linux)|
| [Frontend for extensions website](https://github.com/Ulauncher/ext.ulauncher.io) <br> Uses ReactJS | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext.ulauncher.io/labels/contributor-friendly)|
| [API for extensions website](https://github.com/Ulauncher/ext-api.ulauncher.io) <br> Uses Python and bottle library | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext-api.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext-api.ulauncher.io/labels/contributor-friendly)|

### License

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

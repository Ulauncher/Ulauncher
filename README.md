[![Made in Ukraine](https://img.shields.io/badge/made_in-ukraine-ffd700.svg?labelColor=0057b7)](https://stand-with-ukraine.pp.ua)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Test Status](https://github.com/Ulauncher/Ulauncher/actions/workflows/tests.yml/badge.svg?branch=v6)

#### ⚠️ This is the branch for the unreleased [v6](https://github.com/Ulauncher/Ulauncher/issues/869) release. If you want the v5 branch version, go [here](https://github.com/Ulauncher/Ulauncher/tree/v5).
We are currently working on Ulauncher v6, which is a huge rewrite. Until then we're only supporting the existing functionality in v5. No new features or improvements.

We are not yet ready to make releases or pre-releases for Ulauncher 6, as the API is not yet set and further major changes may come.

[Application Launcher for Linux 🐧](https://ulauncher.io)
================================

Ulauncher is a fast application launcher for Linux. It's written in Python using GTK+, and features: App Search (fuzzy matching), Calculator, [Extensions](https://ext.ulauncher.io/), Shortcuts, File browser mode and [Custom Color Themes](https://docs.ulauncher.io/en/latest/themes/themes.html)

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


### Troubleshooting

Please read our discussion page [Troubleshooting - Quirks and workaround](https://github.com/Ulauncher/Ulauncher/discussions/991) if you run into issues, and also check our outher discussions and issues if you still need help after this.

### Code Contributions

Please see our [Code Contributions](CONTRIBUTING.md) documentation.


| Project | Contributor-friendly Issues |
---|---
| Ulauncher App | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/contributor-friendly.svg?color=3cf014&label=All%20contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/contributor-friendly) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Python.svg?color=5319e7&label=Python&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Python) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/VueJS.svg?color=a553cc&label=VueJS&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/VueJS) <br> [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/Ulauncher/Linux.svg?color=0e035e&label=Linux&style=for-the-badge)](https://github.com/Ulauncher/Ulauncher/labels/Linux)|
| [Frontend for extensions website](https://github.com/Ulauncher/ext.ulauncher.io) <br> Uses ReactJS | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext.ulauncher.io/labels/contributor-friendly)|
| [API for extensions website](https://github.com/Ulauncher/ext-api.ulauncher.io) <br> Uses Python and bottle library | [![GitHub issues by-label](https://img.shields.io/github/issues/Ulauncher/ext-api.ulauncher.io/contributor-friendly.svg?color=3cf014&label=contributor-friendly&style=for-the-badge)](https://github.com/Ulauncher/ext-api.ulauncher.io/labels/contributor-friendly)|

### License

See the [LICENSE](LICENSE) file for license rights and limitations (GNU GPL v3.0).

Color Themes
================================

Ulauncher comes with built-in color themes you can choose between. In addition to that you can install community contributed themes or create you own.

New simplified CSS theme format
-------------------------------
Ulauncher themes were originally implemented as a directory with a manifest json file with theme metadata to complement the css file,
but as of Ulauncher version 6.0.0, we support and recommend just using plain CSS files.

We still support the legacy theme format. You install either kind by putting the themes in your user theme directory.

Migrating old themes
--------------------

#. If your theme manifest.json defines a `css_file_gtk_3.20` property, this is the theme css file. Otherwise `css_file` is the theme css file.
#. Start by flattening imports. For example if the theme contains `@import url("theme.css");`, then replace this by the actual content of "theme.css".
#. Copy the color defined in manifest.json `matched_text_hl_colors.when_not_selected` to your css file as `.item-highlight`. Ex: `.item-highlight { color: #ff7b57 }`.
#. If your color for `matched_text_hl_colors.when_selected` differs from `when_not_selected`, then also add that to your css file as `.selected.item-box .item-highlight { color: #ffcbbd }`.
#. If manifest.json defines `extend_theme` and it's not null, then locate that theme and copy the css selectors and properties from it to the top of your theme. Then go through and filter out the duplicated selectors, that your css file already had before (this is likely most of them).
#. Copy/move the css file directly to the user theme directory. If you want to keep it compatible with your old theme name, it should have the `name` property from manifest.json as it's file name and `.css` as the extension.

Installing Community Themes
---------------------------

If you find a `community contributed theme <https://gist.github.com/gornostal/02a232e6e560da7946c053555ced6cce>`_ you like, this is how you install it:

#. Ensure that you have the user theme directory ``mkdir -p ~/.config/ulauncher/user-themes``
#. Move to the user theme directory ``cd ~/.config/ulauncher/user-themes``
#. Clone the theme ``git clone git@github.com:<user_name>/<theme_name>.git`` (replace with the actual user name and theme name)
#. Open Ulauncher Preferences and select the theme

Creating Custom Color Themes
----------------------------

You can only change colors in themes. Changing element sizes is not possible due to restrictions in the GTK+ API.

#. Take a look at how the `built-in themes <https://github.com/Ulauncher/Ulauncher/tree/HEAD/data/themes>`_ are written
#. Ensure that you have the user theme directory ``mkdir -p ~/.config/ulauncher/user-themes``
#. Copy an existing theme to this directory and give it a unique name.
#. Open Ulauncher Preferences and select your theme
#. Edit colors in CSS files
#. Press ``Ctrl+Space`` (or your hotkey) to check the result
#. Repeat 6 - 8 until you get a desired result

You might find these two pages on GTK+ CSS useful:

* https://developer.gnome.org/gtk3/stable/chap-css-overview.html
* https://developer.gnome.org/gtk3/stable/chap-css-properties.html

Color Themes
================================

Ulauncher comes with built-in color themes you can choose between. In addition to that you can install community contributed themes or create you own.

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

#. Take a look at how the `built-in themes <https://github.com/Ulauncher/Ulauncher/tree/dev/data/themes>`_ are written
#. Ensure that you have the user theme directory ``mkdir -p ~/.config/ulauncher/user-themes``
#. Copy an existing theme directory to this directory.
#. Rename the copied directory and change the name and display_name in ``manifest.json``
#. Open Ulauncher Preferences and select your theme
#. Edit colors in CSS files
#. Tell Ulauncher to re-read theme files by running ``kill -HUP <PID>``
#. Press ``Ctrl+Space`` (or your hotkey) to check the result
#. Repeat 6 - 8 until you get a desired result

You might find these two pages on GTK+ CSS useful:

* https://developer.gnome.org/gtk3/stable/chap-css-overview.html
* https://developer.gnome.org/gtk3/stable/chap-css-properties.html


manifest.json
-------------

Use the following template::

  {
    "manifest_version": "1",
    "name": "adwaita",
    "display_name": "Adwaita",
    "extend_theme": "light",
    "css_file": "theme.css",
    "matched_text_hl_colors": {
      "when_selected": "#99ccff",
      "when_not_selected": "#99ccff"
    }
  }

* ``manifest_version`` - version of ``manifest.json`` file. Current version is "1"
* ``name`` - used to uniquely identify theme
* ``display_name`` - is displayed in a list of theme options in preferences
* ``extend_theme`` - can be ``null`` or a name of an existing theme you'd like to extend
* ``css_file`` - name of your css file
* ``matched_text_hl_colors`` - Colors of characters in name or description of an item that
  match with your query. Must contain ``when_selected`` and ``when_not_selected`` colors.

.. NOTE:: All fields except ``extend_theme`` are required and cannot be empty.

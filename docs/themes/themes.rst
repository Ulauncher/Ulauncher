How to Create Custom Color Theme
================================

You can create your own custom themes by overriding existing ones.

You can only change colors in themes. Changing element sizes won't be possible due to quirky GTK+ API.

Steps
-----

#. Take a look at how `built-in themes <https://github.com/Ulauncher/Ulauncher/tree/dev/data/themes>`_ are written
#. Create a new theme dir in ``~/.config/ulauncher/user-themes/<your_theme_name>``
#. Copy files from existing theme in there
#. Change name and display_name in ``manifest.json``
#. Open Ulauncher Preferences and select your theme
#. Edit colors in CSS files
#. Tell Ulauncher to re-read theme files by running ``kill -HUP <PID>``
#. Press ``Ctrl+Space`` (or your hotkey) to check the result
#. Repeat 6 - 8 until you get a desired result

You might find these two wiki entries on GTK+ CSS useful:

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
    "css_file_gtk_3.20+": "theme-gtk-3.20.css",
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
* ``css_file_gtk_3.20+`` - name css file for GTK+ v3.20 or higher
* ``matched_text_hl_colors`` - Colors of characters in name or description of an item that
  match with your query. Must contain ``when_selected`` and ``when_not_selected`` colors.

.. NOTE:: All fields except ``extend_theme`` are required and cannot be empty.

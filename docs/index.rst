.. Ulauncher documentation master file, created by
   sphinx-quickstart on Sat Apr 22 13:15:04 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

`Ulauncher <http://ulauncher.io>`_ |version| documentation
==========================================================

Currently only docs about extensions are available here.
Everything else is on
`Github Wiki <https://github.com/Ulauncher/Ulauncher/wiki/>`_.


Launch-Targets
==============

Additionally to launching Applications, Ulauncher can launch the following targets:

Desktop-Entries
---------------

Ulauncher indexes desktop-entries in ``~/.local/share/applications`` the same as applications.
Using desktop-entries, launchers that require no query (no space or arguments other than the name/keyword) can be created easily.


Shortcuts
---------

Shortcuts configure Web-URLs using a Query-String or Script, to be opened in the default browser.


Extensions
----------

Extensions are custom scripts, that extend Ulauncher with arbitrary features, such as displaying options generated from the extension in Ulauncher, and evaluating (launching) these options via Ulauncher or the extension.


Custom Color Themes
===================

.. toctree::
   :caption: Custom Color Themes
   :hidden:

   themes/themes

:doc:`themes/themes`
    Create your own color themes


Extension Development Guide
===========================

.. toctree::
   :caption: Extension Development Guide
   :hidden:

   extensions/intro
   extensions/tutorial
   extensions/events
   extensions/actions
   extensions/libs
   extensions/examples
   extensions/debugging

:doc:`extensions/intro`
    Understand what Ulauncher extensions are and how they work.

:doc:`extensions/tutorial`
    Create your first extension in under 5 minutes.

:doc:`extensions/events`
    Events that your extensions can subscribe to and handle.

:doc:`extensions/actions`
    Actions that your extensions perform in response to events.

:doc:`extensions/libs`
    List of libraries that you can use in your extensions.

:doc:`extensions/examples`
    Learn from other Ulauncher extensions.

:doc:`extensions/debugging`
    Debugging tips.


Indexes and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

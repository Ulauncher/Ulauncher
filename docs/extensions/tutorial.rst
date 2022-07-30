Extension Development Tutorial
==============================

Creating a Project
------------------

Ulauncher runs all extensions from ``~/.local/share/ulauncher/extensions/``.

Create a new directory there (name it as you wish) with the following structure::

  .
  ├── images
  │   └── icon.png
  ├── manifest.json
  └── main.py

* :file:`manifest.json` contains all necessary metadata
* :file:`main.py` is an entry point for your extension
* :file:`images/` contains at least an icon of you extension


Check out :doc:`debugging` to learn how to test and debug your extension.

manifest.json
-------------

Create :file:`manifest.json` using the following template::

  {
    "api_version": "3",
    "authors": "John Doe",
    "name": "Demo extension",
    "icon": "images/icon.png",
    "instructions": "You need to install <code>examplecommand</code> to run this extension",
    "preferences": {
      "main_keyword": {
        "type": "keyword",
        "name": "Demo",
        "description": "Demo extension",
        "default_value": "dm"
      }
    }
  }

* ``api_version`` - the version(s) of the Ulauncher Extension API (not the main app version) that the extension requires. See above for more information.
* ``authors`` - the name(s) or user name(s) of the extension authors and maintainers
* ``name`` can be anything you like but not an empty string
* ``icon`` - relative path to an extension icon, or the name of a `themed icon <https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html#names>`_, for example "edit-paste".
* ``preferences`` - Preferences available for users to override (see below for details).
* ``instructions`` - Optional installation instructions that is shown in the extension preferences view.
* ``query_debounce`` - Default: ``0.05``. Delay (in seconds) to avoid running queries while the user is typing. Raise to higher values like ``1`` for slow I/O operations like network requests.
  They are rendered in Ulauncher preferences in the same order they are listed in manifest.


.. NOTE:: All fields except ``instructions`` and ``query_debounce`` are required and cannot be empty.


Preferences
^^^^^^^^^^^

.. NOTE:: The key for the preferences should be a unique identifier that never changes. It's what Ulauncher uses to associate your preferences with user preferences. It was previously named ``id``.

``type`` (required)
  Can be "keyword", "checkbox", "number", "input", "text", or "select"

  * keyword - define keyword that user has to type in in order to use your extension
  * checkbox - rendered as a checkbox
  * number - rendered as a single line number input
  * input - rendered as a single line text input
  * text - rendered as a multiple line text input
  * select - rendered as list of options to choose from

  .. NOTE:: At least one preference with type "keyword" must be defined.

``name`` (required)
  Name of your preference. If type is "keyword" name will show up as a name of item in a list of results

``default_value`` (required)
  Default value

``description``
  Optional description

``icon``
  Optional per-keyword icon (path or themed icon). If not specificed it will use the extension icon

``min`` and ``max``
  Optional for type "number". Must be a non-decimal number

``options``
  Required for type "select". Must be a list of strings or objects like: ``{"value": "...", "text": "..."}``

main.py
-------

Copy the following code to ``main.py``::

  from ulauncher.api import Extension, ExtensionResult
  from ulauncher.api.shared.action.HideWindowAction import HideWindowAction


  class DemoExtension(Extension):

      def on_query_change(self, query):
          for i in range(5):
              yield ExtensionResult(
                  name='Item %s' % i,
                  description='Item description %s' % i,
                  on_enter=HideWindowAction()
              )

  if __name__ == '__main__':
      DemoExtension().run()

.. TIP:: If you don't want to use ``yield``, you can also return a list of ExtensionResults.


Now exit Ulauncher and run ``ulauncher -v`` from command line to see the verbose output.


.. figure:: https://i.imgur.com/GlEfHjA.png
  :align: center


When you type in "dm " (keyword that you defined) you'll get a list of items.
This is all your extension can do now -- show a list of 5 items.


Basic API Concepts
------------------

.. figure:: https://imgur.com/Wzb6KUz.png
  :align: center

  Message flow


**1. Define extension class and the `on_query_change` listener**

  Create a subclass of :class:`~ulauncher.api.Extension`.
  ::

    class DemoExtension(Extension):

        def on_query_change(self, query):
            # `query` will be an instance of :class:`Query`

            ...

  `on_query_change` is new in the V3 API. Previously this was handled by manually binding the events.

**2. Render results**

  Return a list of :class:`~ulauncher.api.ExtensionResult` in order to render results.

  You can also use :class:`~ulauncher.api.ExtensionSmallResult` if you want
  to render more items. You won't have item description with this type.
  ::

    class DemoExtension(Extension):
        def on_query_change(self, query):
            for i in range(5):
                yield ExtensionResult(
                    name='Item %s' % i,
                    description='Item description %s' % i,
                    on_enter=HideWindowAction()
                )


  :code:`on_enter` is an action that will be ran when item is entered/clicked.


**3. Run extension**

  ::

    if __name__ == '__main__':
        DemoExtension().run()


Custom Action on Item Enter
---------------------------

**1. Pass custom data with ExtensionCustomAction**

  Instantiate :class:`~ulauncher.api.ExtensionResult`
  with ``on_enter`` that is instance of :class:`~ulauncher.api.shared.action.ExtensionCustomAction.ExtensionCustomAction`

  ::

    data = {'new_name': 'Item %s was clicked' % i}
    ExtensionResult(
        name='Item %s' % i,
        description='Item description %s' % i,
        on_enter=ExtensionCustomAction(data, keep_app_open=True)
    )

  ``data`` is any custom data that you want to pass to your callback function.

  .. NOTE:: It can be of any type as long as it's serializable with :meth:`pickle.dumps`


**2. Define a new listener**

  ::

    class DemoExtension(Extension):

        def on_query_change(self, query):
            ...

        def on_item_enter(self, data):
            # data is whatever you passed as the first argument to ExtensionCustomAction
            # do any additional actions here...

            # you may want to return another list of results
            yield ExtensionResult(
                name=data['new_name'],
                on_enter=HideWindowAction()
            )



.. figure:: https://i.imgur.com/3x7SXgi.png
  :align: center

  Now this will be rendered when you click on any item



.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

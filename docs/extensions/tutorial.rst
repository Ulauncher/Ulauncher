Development Tutorial
====================

Creating a Project
------------------

Ulauncher runs all extensions from ``~/.local/share/ulauncher/extensions/``.

Create a new directory there (name it as you wish) with the following structure::

  .
  ├── images
  │   └── icon.png
  ├── versions.json
  ├── manifest.json
  └── main.py

* :file:`versions.json` contains mapping of Ulauncher Extension API to branch name of the extension
* :file:`manifest.json` contains all necessary metadata
* :file:`main.py` is an entry point for your extension
* :file:`images/` contains at least an icon of you extension


Check out :doc:`debugging` to learn how to test and debug your extension.


versions.json
-------------

The file contains a list with supported versions of Ulauncher API. ``commit`` field may be either a commit id, branch name, or git tag where the code for that required version is located

``versions.json`` must be checked in to the **root** dir of **master** branch.

``required_api_version`` specifies the minimum supported API version or a lower and upper version. You can find the current version number on the About page of Ulauncher preferences or the log output if you run `ulauncher -v` from a terminal.

Some examples of how to target a range of versions:
* ``2`` matches any versions that starts with ``2.``. It is the same as ``2.x`` and ``2.0``
* ``2.1`` matches Ulauncher's API version 2.1 or higher, but lower than 3.0
* ``2.1 - 5`` will match version 2.1 and higher up to version 5.9999... but not version 6.x. Make sure you specify the separator exactly like this `` - ``, as it is intentionally "picky" to be backward compatible.

Ulauncher will update the major version number (before the dot) when we have to introduce changes that can't be made backward compatible. The minor version number (after the dot) will update when we add new features.

Previously Ulauncher used semver for the API version. We simplified this by dropping the "patch" version and a third party dependency. But we made sure that the previous documented way of specifying the version still works for new extensions and vice versa.


Let's take this example::

  [
    {"required_api_version": "2.1", "commit": "release-for-api-v2"},
    {"required_api_version": "3", "commit": "release-for-api-v3"},
    {"required_api_version": "3.3 - 5", "commit": "master"}
  ]

``release-for-api-v1`` is a branch name (or may be a git tag in this case too). You can choose branch/tag names whatever you like.

With this example Ulauncher will install the extension from the branch ``release-for-api-v2`` if if the API version is 2.1 or 2.9999
If instead the API version is ``3.5``, this satisfies both the second and third criterias. Then Ulauncher will use the version specified last.

.. TODO: add a screenshot

**What problem does versions.json solve?**

We want to minimize the amount of code and infrastructure components that are needed to have a flexible extension ecosystem. For that reason we want to rely on Github as much as possible as a storage of extensions. We also want to allow extension developers to release extensions for previous versions of Ulauncher (for bug fixes for example). That's why ``versions.json`` will be used to track all releases of a certain extension.

**How does Ulauncher use this file?**

| First, Ulauncher will download ``versions.json`` from the master branch of the extension repo.
| Then it will find a required API version that matches current API version.
| After that it will download extension code using a branch/tag/commit name.

manifest.json
-------------

Create :file:`manifest.json` using the following template::

  {
    "required_api_version": "2",
    "name": "Demo extension",
    "description": "Extension Description",
    "developer_name": "John Doe",
    "icon": "images/icon.png",
    "instructions": "You need to install <code>examplecommand</code> to run this extension",
    "options": {
      "query_debounce": 0.1
    },
    "preferences": [
      {
        "id": "demo_kw",
        "type": "keyword",
        "name": "Demo",
        "description": "Demo extension",
        "default_value": "dm"
      }
    ]
  }

* ``required_api_version`` - the version(s) of the Ulauncher Extension API (not the main app version) that the extension requires. See above for more information.
* ``name``, ``description``, ``developer_name`` can be anything you like but not an empty string
* ``icon`` - relative path to an extension icon, or the name of a `themed icon <https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html#names>`_, for example "edit-paste".
* ``options`` - dictionary of optional parameters. See available options below
* ``instructions`` - optional installation instructions to be shown in the extension preferences.
* ``preferences`` - list of preferences available for users to override.
  They are rendered in Ulauncher preferences in the same order they are listed in manifest.


.. NOTE:: All fields except ``options`` and ``instructions`` are required and cannot be empty.


Available Options
^^^^^^^^^^^^^^^^^

``query_debounce``
  Default ``0.05``. Delay in seconds between event is created and sent to your extension.

  If a new event is created during that period, previous one is skipped.
  Debounce helps to prevent redundant events caused by user typing too fast or maybe some other reasons
  when you may not want to process events each time they are triggered.

  If your extension is super responsive (i.e, doesn't wait for I/O operations like network requests, file read/writes,
  and doesn't load CPU, you may want to set a lower value like ``0.05`` or ``0.1``.
  Otherwise it's recommended to set value to ``1`` or higher.


Preference Object Fields
^^^^^^^^^^^^^^^^^^^^^^^^
The values of the preferences are forwarded to the ``on_event`` method of the ``KeywordQueryEventListener`` class as an attribute of extension. For example the value of the keyword with ``id = 'id'`` and ``value = 'val'`` is obtained with the line ``value = extension.preferences['id']`` which  assigns the string ``'val'`` to value. An example of the use of preferences can be found in the `ulauncher demo extension <https://github.com/Ulauncher/ulauncher-demo-ext>`_


``id`` (required)
  Key that is used to retrieve value for a certain preference

``type`` (required)
  Can be "keyword", "input", "text", or "select"

  * keyword - define keyword that user has to type in in order to use your extension
  * input - rendered as ``<input>``
  * text - rendered as ``<textarea>``
  * select - rendered as ``<select>`` with a list of options

  .. NOTE:: At least one preference with type "keyword" must be defined.

``name`` (required)
  Name of your preference. If type is "keyword" name will show up as a name of item in a list of results

``default_value``
  Default value

``description``
  Optional description

``icon``
  Optional per-keyword icon (path or themed icon). If not specificed it will use the extension icon

``options``
  Required for type "select". Must be a list of strings or objects like: ``{"value": "...", "text": "..."}``

.. NOTE:: All fields except ``description`` are required and cannot be empty.


main.py
-------

Copy the following code to ``main.py``::

  from ulauncher.api import Extension, ExtensionResult
  from ulauncher.api.shared.action.HideWindowAction import HideWindowAction


  class DemoExtension(Extension):

      def on_query_change(self, event):
          items = []
          for i in range(5):
              items.append(ExtensionResult(
                  icon='images/icon.png',
                  name='Item %s' % i,
                  description='Item description %s' % i,
                  on_enter=HideWindowAction()
              ))

          return items

  if __name__ == '__main__':
      DemoExtension().run()

Now restart Ulauncher.

.. TIP:: Run ``ulauncher -v`` from command line to see verbose output.

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

        def on_query_change(self, event):
            # `event` will be an instance of :class:`KeywordQueryEvent`

            ...

  `on_query_change` is new in the V3 API. Previously this was handled by manually binding the events.

**2. Render results**

  Return a list of :class:`~ulauncher.api.ExtensionResult` in order to render results.

  You can also use :class:`~ulauncher.api.ExtensionSmallResult` if you want
  to render more items. You won't have item description with this type.
  ::

    class DemoExtension(Extension):
        def on_query_change(self, event):
            items = []
            for i in range(5):
                items.append(ExtensionResult(
                    icon='images/icon.png',
                    name='Item %s' % i,
                    description='Item description %s' % i,
                    on_enter=HideWindowAction()
                ))

            return items


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
        icon='images/icon.png',
        name='Item %s' % i,
        description='Item description %s' % i,
        on_enter=ExtensionCustomAction(data, keep_app_open=True)
    )

  ``data`` is any custom data that you want to pass to your callback function.

  .. NOTE:: It can be of any type as long as it's serializable with :meth:`pickle.dumps`


**2. Define a new listener**

  ::

    class DemoExtension(Extension):

        def on_query_change(self, event):
            ...

        def on_item_enter(self, event):
            # event is instance of ItemEnterEvent

            data = event.get_data()
            # do additional actions here...

            # you may want to return another list of results
            return [ExtensionResult(
                icon='images/icon.png',
                name=data['new_name'],
                on_enter=HideWindowAction()
            )]



.. figure:: https://i.imgur.com/3x7SXgi.png
  :align: center

  Now this will be rendered when you click on any item



.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

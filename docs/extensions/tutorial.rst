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
``versions.json`` lists the supported versions of Ulauncher API. It should be in to the **root** directory of the default branch.

Note that before Ulauncher 5.15.0 the default branch had to be named **master**, so for compatibility reasons it's highly advised to use this name still.

* ``commit`` should specify the commit hash, branch name, or git tag referencing the version.
* ``required_api_version`` should contain a version string, ex "2".

Example::

  [
    {"required_api_version": "2", "commit": "master"},
    {"required_api_version": "3", "commit": "future_v3_api"}
  ]

You can find the current version on the About page of Ulauncher preferences.

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

* ``required_api_version`` - a version of Ulauncher Extension API that the extension requires, for example "2". You can find the current version number on the About page of Ulauncher preferences.
* ``name``, ``description``, ``developer_name`` can be anything you like but not an empty string
* ``icon`` - relative path to an extension icon
* ``options`` - dictionary of optional parameters. See available options below
* ``preferences`` - list of preferences available for users to override.
  They are rendered in Ulauncher preferences in the same order they are listed in manifest.


.. NOTE:: All fields except ``options`` are required and cannot be empty.


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

``options``
  Required for type "select". Must be a list of strings or objects like: ``{"value": "...", "text": "..."}``

.. NOTE:: All fields except ``description`` are required and cannot be empty.








main.py
-------

Copy the following code to ``main.py``::

  from ulauncher.api.client.Extension import Extension
  from ulauncher.api.client.EventListener import EventListener
  from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
  from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
  from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
  from ulauncher.api.shared.action.HideWindowAction import HideWindowAction


  class DemoExtension(Extension):

      def __init__(self):
          super().__init__()
          self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


  class KeywordQueryEventListener(EventListener):

      def on_event(self, event, extension):
          items = []
          for i in range(5):
              items.append(ExtensionResultItem(icon='images/icon.png',
                                               name='Item %s' % i,
                                               description='Item description %s' % i,
                                               on_enter=HideWindowAction()))

          return RenderResultListAction(items)

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


**1. Define extension class and subscribe to an event**

  Create a subclass of :class:`~ulauncher.api.client.Extension.Extension` and subscribe to events in :meth:`__init__`.
  ::

    class DemoExtension(Extension):

        def __init__(self):
            super().__init__()
            self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


  :code:`self.subscribe(event_class, event_listener)`


  In our case we subscribed to one event -- :class:`KeywordQueryEvent`.
  This means whenever user types in a query that starts with a keyword from manifest file,
  :meth:`KeywordQueryEventListener.on_event` will be invoked.

**2. Define a new event listener**

  Create a subclass of :class:`~ulauncher.api.client.EventListener.EventListener` and implement :func:`on_event`
  ::

    class KeywordQueryEventListener(EventListener):

        def on_event(self, event, extension):
            # in this case `event` will be an instance of KeywordQueryEvent

            ...

  :meth:`~ulauncher.api.client.EventListener.EventListener.on_event` may return an action (see :doc:`actions`).


**3. Render results**

  Return :class:`~ulauncher.api.shared.action.RenderResultListAction.RenderResultListAction` in order to render results.
  :class:`~ulauncher.api.shared.item.ExtensionResultItem.ExtensionResultItem` describes a single result item.

  You can also use :class:`~ulauncher.api.shared.item.ExtensionSmallResultItem.ExtensionSmallResultItem` if you want
  to render more items. You won't have item description with this type.
  ::

    class KeywordQueryEventListener(EventListener):

        def on_event(self, event, extension):
            items = []
            for i in range(5):
                items.append(ExtensionResultItem(icon='images/icon.png',
                                                 name='Item %s' % i,
                                                 description='Item description %s' % i,
                                                 on_enter=HideWindowAction()))

            return RenderResultListAction(items)


  :code:`on_enter` is an action that will be ran when item is entered/clicked.


**4. Run extension**

  ::

    if __name__ == '__main__':
        DemoExtension().run()









Custom Action on Item Enter
---------------------------

**1. Pass custom data with ExtensionCustomAction**

  Instantiate :class:`~ulauncher.api.shared.item.ExtensionResultItem.ExtensionResultItem`
  with ``on_enter`` that is instance of :class:`~ulauncher.api.shared.action.ExtensionCustomAction.ExtensionCustomAction`

  ::

    data = {'new_name': 'Item %s was clicked' % i}
    ExtensionResultItem(icon='images/icon.png',
                        name='Item %s' % i,
                        description='Item description %s' % i,
                        on_enter=ExtensionCustomAction(data, keep_app_open=True))

  ``data`` is any custom data that you want to pass to your callback function.

  .. NOTE:: It can be of any type as long as it's serializable with :meth:`pickle.dumps`


**2. Define a new listener**

  ::

    from ulauncher.api.client.EventListener import EventListener

    class ItemEnterEventListener(EventListener):

        def on_event(self, event, extension):
            # event is instance of ItemEnterEvent

            data = event.get_data()
            # do additional actions here...

            # you may want to return another list of results
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                               name=data['new_name'],
                                                               on_enter=HideWindowAction())])

**3. Subscribe to ItemEnterEvent**

  You want your new listener to be subscribed to :class:`ItemEnterEvent` like this::

    from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent

    class DemoExtension(Extension):

        def __init__(self):
            super().__init__()
            self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
            self.subscribe(ItemEnterEvent, ItemEnterEventListener())  # <-- add this line



.. figure:: https://i.imgur.com/3x7SXgi.png
  :align: center

  Now this will be rendered when you click on any item



.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

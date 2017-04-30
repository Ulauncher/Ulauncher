Development Tutorial
====================

Creating a Project
------------------

Ulauncher runs all extensions from ``~/.cache/ulauncher_cache/extensions/``.

Create a new directory there (name it as you wish) with the following structure::

  .
  ├── images
  │   └── icon.png
  ├── manifest.json
  └── main.py

* :file:`manifest.json` contains all necessary metadata
* :file:`main.py` is an entry point for your extension
* :file:`images/` contains at least an icon of you extension


manifest.json
-------------

Create :file:`manifest.json` using the following template::

  {
    "manifest_version": "1",
    "api_version": "1",
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

* ``manifest_version`` - version of ``manifest.json`` file. Currently only version "1" is supported
* ``api_version`` - version of Ulauncher API. Currently only version "1" is supported.
* ``name``, ``description``, ``developer_name`` can be anything you like but not an empty string
* ``icon`` - relative path to an extension icon
* ``options`` - dictionary of optional parameters. See available options bellow
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

``id``
  Key that is used to retrieve value for a certain preference

``type``
  Can be "keyword", "input", or "text"

  * keyword - define keyword that user has to type in in order to use your extension
  * input - rendered as ``<input>``
  * text - rendered as ``<textarea>``

  .. NOTE:: At least one preference with type "keyword" must be defined.

``name``
  Name of your preference. If type is "keyword" name will show up as a name of item in a list of results

``default_value``
  Default value

``description``
  Optional description

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
          super(DemoExtension, self).__init__()
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

.. figure:: http://i.imgur.com/GlEfHjA.png
  :align: center


When you type in "dm " (keyword that you defined) you'll get a list of items.
This is all your extension can do now -- show a list of 5 items.






Basic API Concepts
------------------

**1. Define extension class and subscribe to an event**

  Create a subclass of :class:`~ulauncher.api.client.Extension.Extension` and subscribe to events in :meth:`__init__`.
  ::

    class DemoExtension(Extension):

        def __init__(self):
            super(DemoExtension, self).__init__()
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
            super(DemoExtension, self).__init__()
            self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
            self.subscribe(ItemEnterEvent, ItemEnterEventListener())  # <-- add this line



.. figure:: http://i.imgur.com/3x7SXgi.png
  :align: center

  Now this will be rendered when you click on any item
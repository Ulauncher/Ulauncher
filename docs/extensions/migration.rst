Extension Migration
===================

Migrate from API v1 to v2
-------------------------

API version 2 was introduced along with Ulauncher v5 after migrating from Python 2 to 3.

.. TODO: add description of new features introduced in API 2

*Required actions:*

1. Remove ``manifest_version`` from ``manifest.json``. It's no longer needed
2. In the manifest file rename ``api_version`` to ``required_api_version``
3. Set its value to ``2``.
4. ``required_api_version`` is the supported version(s) of the Ulauncher extension API (not the Ulauncher app version). See the `tutorial <tutorial.html#versions-json>`__ for full details.
5. Migrate your extension to Python 3 manually or by using `2to3 tool <https://docs.python.org/2/library/2to3.html>`_
6. Create a file called ``versions.json`` in the **root** directory of **master** branch using the following content as a template:

  ::

    [
      { "required_api_version": "1", "commit": "<branch name with the pre-migration code>" },
      { "required_api_version": "2", "commit": "<branch name with python3 code>" }
    ]

  For more details about ``version.json``, see `tutorial <tutorial.html#versions-json>`__.

  For example, you may choose ``python2`` as a branch name where you keep the old code, which is going to be used by the old Ulauncher app, and ``master`` as a branch name where you keep the latest version. In this case the file contents should look like this:

  ::

    [
      { "required_api_version": "1", "commit": "python2" },
      { "required_api_version": "2", "commit": "master" }
    ]

----

.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

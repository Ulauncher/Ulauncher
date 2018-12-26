Migration
=========

Migrate from API v1 to v2.0.0
-----------------------------

API version 2 is introduced along with Ulauncher v5 after switching from Python 2 to 3.

.. TODO: add description of new features introduced in API 2

*Required actions:*

1. Remove ``manifest_version`` from ``manifest.json``. It's no longer needed
2. Also rename ``api_version`` to ``required_api_version``
3. ``required_api_version`` should follow `NPM Semver <https://docs.npmjs.com/misc/semver>`_ format. In most of the cases you would want to specify string like ``^1.2.3`` if ``1.2.3`` is the current version of extension API.
4. Migrate your extension to Python 3 manually or by using `2to3 tool <https://docs.python.org/2/library/2to3.html>`_ for example.

----

.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

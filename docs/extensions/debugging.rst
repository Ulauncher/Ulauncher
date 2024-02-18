Testing & Logging
===================

To test an extension, copy it to ~/.local/share/ulauncher/extensions/your-extension

Then restart Ulauncher with the following command::

  ulauncher --no-extensions --dev -v

When you need to restart your extension hit ``Ctrl+C`` and run the last command again.


Set up Logger
--------------

Here's all you need to do to enable logging for your extension::

  import logging

  # create an instance of logger at a module level
  logger = logging.getLogger(__name__)

  # then use these methods in your classes or functions:
  logger.error('...')
  logger.warn('...')
  logger.info('...')
  logger.debug('...')




.. NOTE::
  Please take `a short survey <https://goo.gl/forms/wcIRCTjQXnO0M8Lw2>`_ to help us build greater API and documentation

Debugging & Logging
===================

WIP
------------------------

We have removed the Extension debugging functionality from Ulauncher v6.
We plan to do internal changes and then bring back a more convenient method to debug extensions without copying/installing them to the Ulauncher extension directory, then update this space.


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

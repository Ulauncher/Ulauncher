Debugging & Logging
===================

#. Install your extension using the path to your local git repo rather than the public URL.
#. Commit your changes in the local repo.
#. Update the extension in Ulauncher's preferences to pull in the changes from your local repo.
#. To get verbose log output, stop Ulauncher and start it in a terminal ``ulauncher -v``.
#. Once you are done with your changes, stop Ulaunchar and start it normally again
#. Push your changes to your public remote (GitHub, GitLab or other) if you want to make them available to others.


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

Debugging & Logging
===================

Run Extension Separately
------------------------

You don't have to restart Ulauncher every time a change is made to your extension.
For your convenience there is a flag ``--no-extension`` that prevents extensions from starting automatically.

First, start Ulauncher with the following command::

  ulauncher --no-extensions --dev -v

Then find in the logs command to run your extension. It should look like this::

  VERBOSE=1 ULAUNCHER_WS_API=ws://127.0.0.1:5050/ulauncher-demo PYTHONPATH=/home/username/projects/ulauncher /usr/bin/python /home/username/.local/share/ulauncher/extensions/ulauncher-demo/main.py

Now when you need to restart your extension hit ``Ctrl+C`` and run the last command again.


Debugging With `ipdb <https://github.com/gotcha/ipdb>`_
-------------------------------------------------------

Here is the easiest way to set a breakpoint and execute code line by line:

1. Install ipdb

  ::

    sudo pip install ipdb

2. In your code add this line wherever you need to break

  ::

    import ipdb; ipdb.set_trace()

3. Restart extension



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

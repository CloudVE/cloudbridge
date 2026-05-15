Common Setup Issues
===================

macOS Issues
------------

* If you are getting an error message like so: ``Authentication with cloud provider failed: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:749)``
  then this indicates that you are probably using a Python distribution on
  macOS whose installer ships its own OpenSSL and does not use the system
  trusted certificate keychain.

  The python.org installer includes a script that installs a bundle of root
  certificates from ``certifi``.  Run the ``Install Certificates.command``
  script bundled with your Python install, for example:

  .. code-block:: bash

    /Applications/Python\ 3.13/Install\ Certificates.command

  For more information see `this StackOverflow
  answer <https://stackoverflow.com/a/42583411/1419499>`_.

Common Setup Issues
===================

macOS Issues
------------

* If you are getting an error message like so: ``Authentication with cloud provider failed: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:749)``
  then this indicates that you are probably using a newer version of Python on
  macOS. Starting with Python 3.6, the Python installer includes its own version
  of OpenSSL and it no longer uses the system trusted certificate keychains.

  Python 3.6 includes a script that can install a bundle of root certificates
  from ``certifi``.  To install this bundle execute the following:

  .. code-block:: bash

    cd /Applications/Python\ 3.6/
    sudo ./Install\ Certificates.command

  For more information see `this StackOverflow
  answer <https://stackoverflow.com/a/42583411/1419499>`_ and the `Python 3.6
  Release Notes <https://www.python.org/downloads/release/python-360/>`_.

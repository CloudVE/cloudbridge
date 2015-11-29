Installation
============

**Prerequisites**: CloudBridge runs on Python 2.7 and higher. Python 3 is recommended.

Latest release
--------------
The latest release of cloudbridge can be installed from PyPI::

    pip install cloudbridge

Manual installation
-------------------
The development version of the library can be installed from the
`Github repo <https://github.com/gvlproject/cloudbridge>`_::

    $ git clone https://github.com/gvlproject/cloudbridge.git
    $ cd cloudbridge
    $ python setup.py install

Developer installation
----------------------
To install additional libraries required by CloudBridge contributors, such as
`tox <https://tox.readthedocs.org/en/latest/>`_, run the following command::

    pip install cloudbridge[dev]

----------

To check what version of the library you have installed, do the following::

    import cloudbridge
    cloudbridge.get_version()

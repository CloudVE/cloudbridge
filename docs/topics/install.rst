Installation
============

**Prerequisites**: CloudBridge runs on Python 2.7 and higher. Python 3 is recommended.

We highly recommend installing CloudBridge in a
`virtualenv <http://virtualenv.readthedocs.org/>`_. Creating a new virtualenv
is simple:

.. code-block:: shell

    pip install virtualenv
    virtualenv .venv
    source .venv/bin/activate

Latest release
--------------
The latest release of cloudbridge can be installed from PyPI::

    pip install cloudbridge

Latest unreleased dev version
-----------------------------
The development version of the library can be installed from the
`Github repo <https://github.com/gvlproject/cloudbridge>`_::

    $ git clone https://github.com/gvlproject/cloudbridge.git
    $ cd cloudbridge
    $ python setup.py install

Developer installation
----------------------
To install additional libraries required by CloudBridge contributors, such as
`tox <https://tox.readthedocs.org/en/latest/>`_, clone the source code
repository and run the following command from the repository root directory::

    pip install -U -e .[dev]

----------

To check what version of the library you have installed, do the following::

    import cloudbridge
    cloudbridge.get_version()

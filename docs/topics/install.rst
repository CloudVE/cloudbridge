Installation
============

**Prerequisites**: CloudBridge runs on Python 2.7 and higher. Python 3 is
recommended.

We highly recommend installing CloudBridge in a
`virtualenv <http://virtualenv.readthedocs.org/>`_. Creating a new virtualenv
is simple:

.. code-block:: shell

    pip install virtualenv
    virtualenv .venv
    source .venv/bin/activate

Latest stable release
---------------------
The latest release of CloudBridge can be installed from PyPI::

    pip install cloudbridge

Latest unreleased dev version
-----------------------------
The development version of the library can be installed directly from the
`GitHub repo <https://github.com/CloudVE/cloudbridge>`_::

    $ pip install --upgrade git+https://github.com/CloudVE/cloudbridge.git

Single Provider Installation
-----------------------------
If you only require to integrate with one to two providers, you can install
the particular providers only as the following.

    $ pip install cloudbridge[aws,gcp]

The available options are aws, azure, gcp and openstack.

Developer installation
----------------------
To install additional libraries required by CloudBridge contributors, such as
`tox <https://tox.readthedocs.org/en/latest/>`_, clone the source code
repository and run the following command from the repository root directory::

    $ git clone https://github.com/CloudVE/cloudbridge.git
    $ cd cloudbridge
    $ pip install --upgrade --editable .[dev]

Checking installation
---------------------
To check what version of the library you have installed, do the following::

    import cloudbridge
    cloudbridge.get_version()

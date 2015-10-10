cloudbridge
===========

cloudbridge provides a layer of abstraction over different cloud providers.
It's a straightfoward implementation of the `bridge pattern`_.

.. image:: https://codeclimate.com/github/gvlproject/cloudbridge/badges/gpa.svg
   :target: https://codeclimate.com/github/gvlproject/cloudbridge
   :alt: Code Climate

.. image:: https://landscape.io/github/gvlproject/cloudbridge/master/landscape.svg?style=flat
   :target: https://landscape.io/github/gvlproject/cloudbridge/master
   :alt: Landscape Code Health

.. image:: https://coveralls.io/repos/gvlproject/cloudbridge/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/gvlproject/cloudbridge?branch=master
   :alt: Code Coverage

.. image:: https://travis-ci.org/gvlproject/cloudbridge.svg?branch=master
   :target: https://travis-ci.org/gvlproject/cloudbridge
   :alt: Travis Build Status

.. image:: https://img.shields.io/pypi/status/cloudbridge.svg
   :target: https://pypi.python.org/pypi/cloudbridge/
   :alt: latest version available on PyPI

Usage example
~~~~~~~~~~~~~

The simplest possible example for doing something useful with cloudbridge would
look like the following.

.. code-block:: python

	from cloudbridge.providers.factory import CloudProviderFactory, ProviderList

	provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})
	print(provider.security.key_pairs.list())

In the example above, the AWS_ACCESS_KEY and AWS_SECRET_KEY environment variables
must be set to your cloud credentials.


Documentation
~~~~~~~~~~~~~
Complete documentation can be found at <https://cloudbridge.readthedocs.org>.


Running tests
~~~~~~~~~~~~~
To run the test suite locally, install `tox`_ with :code:`pip install tox`
and run ``tox`` command. This will run all the tests for
all the environments defined in file ``tox.ini``. In order to properly run the
tests, you should have all the environment variables listed in
``tox.ini`` file (under ``passenv``) exported.

If you’d like to run the tests on a specific environment only, use a command
like this: ``tox -e py27`` (or ``python setup.py test`` directly). If you'd
like to run the tests for a specific cloud only, you should export env var
``CB_TEST_PROVIDER`` and specify the desired provider name (e.g., ``aws`` or
``openstack``) and then run the ``tox`` command.

Note that running the tests will create various cloud resources, for which you
may incur costs.


.. _`bridge pattern`: https://en.wikipedia.org/wiki/Bridge_pattern
.. _`tox`: https://tox.readthedocs.org/en/latest/

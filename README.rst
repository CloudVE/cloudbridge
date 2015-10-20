cloudbridge
===========

cloudbridge provides a layer of abstraction over different cloud providers.
It's a straightfoward implementation of the `bridge pattern`_. It is currently
under development and is in a Pre-Alpha state.

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
must be set to your AWS credentials.


Documentation
~~~~~~~~~~~~~
Documentation can be found at https://cloudbridge.readthedocs.org.

Contributing
~~~~~~~~~~~~
Community contributions for any part of the project are welcome. If you have
a completely new idea or would like to bounce your idea before moving forward
with the implementation, feel free to create an issue to start a discussion.

Contributions should come in the form or a pull request. We strive for 100%
test coverage so code will only be accepted if it comes with appropriate tests
and it does not break existing functionality. Further, the code needs to be
well documented and all methods have docstrings.

Conceptually, the library is laid out such that there is a factory used to
create a reference to a cloud provider. Each provider offers a set of services
and resources. Services typically perform actions while resources offer
information (and can act on itself, when appropriate). The structure of each
object is defined via an abstract interface (see
``cloudbridge/providers/interfaces``) and any object should implement the
defined interface.

Running tests
~~~~~~~~~~~~~
To run the test suite locally, install `tox`_ with :code:`pip install tox`
and run ``tox`` command. This will run all the tests for
all the environments defined in file ``tox.ini``. In order to properly run the
tests, you should have all the environment variables listed in
``tox.ini`` file (under ``passenv``) exported.

If you’d like to run the tests on a specific environment only, use a command
like such: ``tox -e py27`` (or ``python setup.py test`` directly). If you'd
like to run the tests for a specific cloud only, you should export env var
``CB_TEST_PROVIDER`` and specify the desired provider name (e.g., ``aws`` or
``openstack``) and then run the ``tox`` command.

Note that running the tests may create various cloud resources, for which you
may incur costs. For the AWS cloud, there is also a mock provider that will
simulate AWS resources. It is used by default when running the test suite. To
disable it, set the following environment variable:
``export CB_USE_MOCK_DRIVERS=No``.


.. _`bridge pattern`: https://en.wikipedia.org/wiki/Bridge_pattern
.. _`tox`: https://tox.readthedocs.org/en/latest/

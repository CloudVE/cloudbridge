Running tests
=============
In the spirit of the library's :doc:`design_goals`, the aim is to have thorough
tests for the entire library. This page explains the testing philosophy and
shows how to run the tests locally.

Testing philosophy
------------------
Our testing goals are to:

 1. Write one set of tests that all provider implementations must pass.

 2. Make that set of tests a 'conformance' test suite, which validates that each
    implementation correctly implements the CloudBridge specification.

 3. Make the test suite comprehensive enough that a provider which passes all
    the tests can be used safely by an application with no additional testing.
    In other words, the CloudBridge specification and accompanying test suite
    must be comprehensive enough that no provider specific workarounds, code or
    testing is required.

 4. For development, mock providers may be used to speed up the feedback cycle,
    but providers must also pass the full suite of tests when run against actual
    cloud infrastructure to ensure that we are not testing against an idealised
    or imagined environment.

 5. Aim for 100% code coverage.


Running tests
-------------
To run the test suite locally:
 1. Install `tox`_ with :code:`pip install tox`
 2. Export all environment variables listed in ``tox.ini`` (under ``passenv``)
 3. Run ``tox`` command

This will run all the tests for all the environments defined in file
``tox.ini``.


Specific environment and infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you’d like to run the tests on a specific environment only, say Python 2.7,
against a specific infrastructure, say aws, use a command like this:
``tox -e py27-aws``. The available provider names are listed in the
`ProviderList`_ class (e.g., ``aws`` or ``openstack``).

Specific test cases
~~~~~~~~~~~~~~~~~~~~
You can run a specific test case, as follows:
``tox -- tests/test_image_service.py:CloudImageServiceTestCase.test_create_and_list_imag``

It can also be restricted to a particular environment as follows:
``tox -e "py27-aws" -- tests/test_cloud_factory.py:CloudFactoryTestCase``

See nosetest documentation for other parameters that can be passed in.

Using unittest directly
~~~~~~~~~~~~~~~~~~~~~~~
You can also run the tests against your active virtual environment directly
with ``python setup.py test``. You will need to set the ``CB_TEST_PROVIDER``
environment variable prior to running the tests, or they will default to
``CB_TEST_PROVIDER=aws``.

You can also run a specific test case, as follows:
``python setup.py test -s tests.test_cloud_factory.CloudFactoryTestCase``

Using a mock provider
~~~~~~~~~~~~~~~~~~~~~

Note that running the tests may create various cloud resources, for which you
may incur costs. For the AWS cloud, there is also a mock provider (`moto`_) that
will simulate AWS resources. You can use ``CB_TEST_PROVIDER=mock`` to run tests
against the mock provider only, which will provide faster feedback times.

Alternatively you can run the mock tests through tox.
``tox -e "py27-mock"``

.. _design goals: https://github.com/CloudVE/cloudbridge/
   blob/main/README.rst
.. _tox: https://tox.readthedocs.org/en/latest/
.. _ProviderList: https://github.com/CloudVE/cloudbridge/blob/main/
   cloudbridge/cloud/factory.py#L15
.. _moto: https://github.com/spulec/moto

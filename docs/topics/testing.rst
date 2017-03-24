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


Specific environment
~~~~~~~~~~~~~~~~~~~~
If you’d like to run the tests on a specific environment only, say Python 2.7,
use a command like this: ``tox -e py27``. Alternatively, to use your default
python, you can also run the test command directly ``python setup.py test``.

Select infrastructure
~~~~~~~~~~~~~~~~~~~~~
You can also run the tests on a specific cloud only. To do so, export an
environment variable ``CB_TEST_PROVIDER`` and specify the desired provider
name. The available provider names are listed in the `ProviderList`_ class
(e.g., ``aws`` or ``openstack``). Then, run the ``tox`` command.

Using a mock provider
~~~~~~~~~~~~~~~~~~~~~

Note that running the tests may create various cloud resources, for which you
may incur costs. For the AWS cloud, there is also a mock provider (`moto`_) that
will simulate AWS resources. It is used by default when running the test suite.
You can toggle the use of mock providers by setting an environment variable:
``CB_USE_MOCK_PROVIDERS`` to ``Yes`` or ``No``.


.. _design goals: https://github.com/gvlproject/cloudbridge/
   blob/master/README.rst
.. _tox: https://tox.readthedocs.org/en/latest/
.. _ProviderList: https://github.com/gvlproject/cloudbridge/blob/master/
   cloudbridge/cloud/factory.py#L15
.. _moto: https://github.com/spulec/moto

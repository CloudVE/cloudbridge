Provider Development Walkthrough
================================
This guide will walk you through the basic process of developing a new provider
for CloudBridge.


1. We start off by creating a new folder for the provider within the
``cloudbridge/cloud/providers`` folder. In this case: ``gcp``. Further, install
the native cloud provider Python library, here
``pip install google-api-python-client==1.4.2`` and a couple of its requirements
``oauth2client==1.5.2`` and ``pycrypto==2.6.1``.

2. Add a ``provider.py`` file. This file will contain the main implementation
of the cloud provider and will be the entry point that CloudBridge uses for all
provider related services. You will need to subclass ``BaseCloudProvider`` and
add a class variable named ``PROVIDER_ID``.

.. code-block:: python

    from cloudbridge.cloud.base import BaseCloudProvider


    class GCPCloudProvider(BaseCloudProvider):

        PROVIDER_ID = 'gcp'

        def __init__(self, config):
            super(GCPCloudProvider, self).__init__(config)



3. Add an ``__init__.py`` to the ``cloudbridge/cloud/providers/gcp`` folder
and export the provider.

.. code-block:: python

    from .provider import GCPCloudProvider  # noqa

.. tip ::

   You can view the code so far here: `commit 1`_

4. Next, we need to register the provider with the factory.
This only requires that you register the provider's ID in the ``ProviderList``.
Add GCP to the ``ProviderList`` class in ``cloudbridge/cloud/factory.py``.


5. Run the test suite. We will get the tests passing on py27 first.

.. code-block:: bash

    export CB_TEST_PROVIDER=gcp
    tox -e py27

You should see the tests fail with the following message:

.. code-block:: bash

    "TypeError: Can't instantiate abstract class GCPCloudProvider with abstract
    methods storage, compute, security, network."

6. Therefore, our next step is to implement these methods. We can start off by
implementing these methods in ``provider.py`` and raising a
``NotImplementedError``.

.. code-block:: python

    @property
    def compute(self):
        raise NotImplementedError(
            "GCPCloudProvider does not implement this service")

    @property
    def network(self):
        raise NotImplementedError(
            "GCPCloudProvider does not implement this service")

    @property
    def security(self):
        raise NotImplementedError(
            "GCPCloudProvider does not implement this service")

    @property
    def storage(self):
        raise NotImplementedError(
            "GCPCloudProvider does not implement this service")


Running the tests now will complain as much. We will next implement each
Service in turn.


7. We will start with the compute service. Add a ``services.py`` file.

.. code-block:: python

    from cloudbridge.cloud.base.services import BaseSecurityService


    class GCPSecurityService(BaseSecurityService):

        def __init__(self, provider):
            super(GCPSecurityService, self).__init__(provider)


8. We can now return this new service from the security property in
``provider.py`` as follows:

.. code-block:: python

    def __init__(self, config):
        super(GCPCloudProvider, self).__init__(config)
        self._security = GCPSecurityService(self)

    @property
    def security(self):
        return self._security

.. tip ::

   You can view the code so far here: `commit 2`_

9. Run the tests, and the following message will cause all security service
tests to fail:

.. code-block:: bash

    "TypeError: Can't instantiate abstract class GCPSecurityService with abstract
    methods key_pairs, security_groups."

The Abstract Base Classes are doing their job and flagging all methods that
need to be implemented.

10. Since the security service simply provides organisational structure, and is
a container for the ``key_pairs`` and ``security_groups`` services, we must
next implement these services.

.. code-block:: python

    from cloudbridge.cloud.base.services import BaseKeyPairService
    from cloudbridge.cloud.base.services import BaseSecurityGroupService
    from cloudbridge.cloud.base.services import BaseSecurityService


    class GCPSecurityService(BaseSecurityService):

        def __init__(self, provider):
            super(GCPSecurityService, self).__init__(provider)

            # Initialize provider services
            self._key_pairs = GCPKeyPairService(provider)
            self._security_groups = GCPSecurityGroupService(provider)

        @property
        def key_pairs(self):
            return self._key_pairs

        @property
        def security_groups(self):
            return self._security_groups


    class GCPKeyPairService(BaseKeyPairService):

        def __init__(self, provider):
            super(GCPKeyPairService, self).__init__(provider)


    class GCPSecurityGroupService(BaseSecurityGroupService):

        def __init__(self, provider):
            super(GCPSecurityGroupService, self).__init__(provider)

.. tip ::

   You can view the code so far here: `commit 3`_


Once again, running the tests will complain of missing methods:

.. code-block:: bash

    "TypeError: Can't instantiate abstract class GCPKeyPairService with abstract
    methods create, find, get, list."

11. Keep implementing the methods till the security service works, and the
tests pass.

.. note ::

    We start off by implementing the list keypairs method. Therefore, to obtain
    the keypair, we need to have a connection to the cloud provider. For this,
    we need to install the Google sdk, and thereafter, to obtain the desired
    connection via the sdk. While the design and structure of that connection
    is up to the implementor, a general design we have followed is to have the
    cloud connection globally available within the provider.

To add the sdk, we edit CloudBridge's main ``setup.py`` and list the
dependencies.

.. code-block:: python

    gcp_reqs = ['google-api-python-client==1.4.2']
    full_reqs = base_reqs + aws_reqs + openstack_reqs + gcp_reqs

We will also register the provider in ``cloudbridge/cloud/factory.py``'s
provider list.

.. code-block:: python

    class ProviderList(object):
        AWS = 'aws'
        OPENSTACK = 'openstack'
        ...
        GCP = 'gcp'

.. tip ::

   You can view the code so far here: `commit 4`_


12. Thereafter, we create the actual connection through the sdk. In the case of
GCP, we need a Compute API client object. We will make this connection
available as a public property named ``gcp_compute`` in the provider. We will
then lazily initialize this connection.

A full implementation of the KeyPair service can now be made in a provider
specific manner.

.. tip ::

   You can view the code so far here: `commit 5`_



.. _commit 1: https://github.com/CloudVE/cloudbridge/commit/54c67e93a3cd9d51e7d2b1195ebf4e257d165297
.. _commit 2: https://github.com/CloudVE/cloudbridge/commit/82c0244aa4229ae0aecfe40d769eb93b06470dc7
.. _commit 3: https://github.com/CloudVE/cloudbridge/commit/e90a7f6885814a3477cd0b38398d62af64f91093
.. _commit 4: https://github.com/CloudVE/cloudbridge/commit/2d5c14166a538d320e54eed5bc3fa04997828715
.. _commit 5: https://github.com/CloudVE/cloudbridge/commit/98c9cf578b672867ee503027295f9d901411e496

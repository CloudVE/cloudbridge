Setup
-----
To initialize a connection to a cloud and get a provider object, you will
need to provide the cloud's access credentials to Cloudbridge. These may
be provided in one of two ways:

1. Environment variables
2. A dictionary

Providing access credentials through environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following environment variables must be set, depending on the provider in use.

**Amazon**

*Mandatory variables*::

    AWS_ACCESS_KEY
    AWS_SECRET_KEY

**Openstack**

*Mandatory variables*::

    OS_AUTH_URL
    OS_USERNAME
    OS_PASSWORD
    OS_TENANT_NAME
    OS_REGION_NAME

*Optional variables*::

    NOVA_SERVICE_NAME
    OS_COMPUTE_API_VERSION
    OS_VOLUME_API_VERSION

Once the environment variables are set, you can create a connection as follows:

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK, {})


Providing access credentials through a dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can initialize a simple config as follows. The key names are the same
as the environment variables, in lower case. Note that the config dictionary
will override environment values.

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'aws_access_key' : '<your_access_key>',
              'aws_secret_key' : '<your_secret_key>'}
    provider = CloudProviderFactory().create_provider(ProviderList.AWS, config)

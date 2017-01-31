Setup
-----
To initialize a connection to a cloud and get a provider object, you will
need to provide the cloud's access credentials to CloudBridge. These may
be provided in one of two ways:

1. Environment variables
2. A dictionary

Providing access credentials through environment variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The following environment variables must be set, depending on the provider in use.

**Amazon**

===================  ==================
Mandatory variables  Optional Variables
===================  ==================
AWS_ACCESS_KEY
AWS_SECRET_KEY
===================  ==================

**Openstack**

===================  ==================
Mandatory variables  Optional Variables
===================  ==================
OS_AUTH_URL			 NOVA_SERVICE_NAME
OS_USERNAME			 OS_COMPUTE_API_VERSION
OS_PASSWORD			 OS_VOLUME_API_VERSION
OS_PROJECT_NAME
OS_REGION_NAME
===================  ==================


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

Some optional configuration values can only be provided through the config
dictionary. These are listed below for each provider.

**CloudBridge**

====================  ==================
Variable		      Description
====================  ==================
default_result_limit  Number of results that a ``.list()`` method should return.
                      Defaults to 50.
====================  ==================


**Amazon**

====================  ==================
Variable		      Description
====================  ==================
ec2_is_secure         True to use an SSL connection. Default is ``True``.
ec2_region_name       Default region name. Defaults to ``us-east-1``.
ec2_region_endpoint   Endpoint to use. Default is ``ec2.us-east-1.amazonaws.com``.
ec2_port              EC2 connection port. Does not need to be specified unless
                      EC2 service is running on an alternative port.
ec2_conn_path	      Connection path. Defaults to ``/``.
ec2_validate_certs    Whether to use SSL certificate verification. Default is
                      ``False``.
s3_is_secure          True to use an SSL connection. Default is ``True``.
s3_host               Host connection endpoint. Default is ``s3.amazonaws.com``.
s3_port               Host connection port. Does not need to be specified unless
                      S3 service is running on an alternative port.
s3_conn_path          Connection path. Defaults to ``/``.
s3_validate_certs     Whether to use SSL certificate verification. Default is
                      ``False``.
====================  ==================


Other configuration variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In addition to the provider specific configuration variables above, there are
some general configuration environment variables that apply to CloudBridge as
a whole

=====================  ==================
Variable		       Description
=====================  ==================
CB_DEBUG               Setting ``CB_DEBUG=True`` will cause detailed debug
                       output to be printed for each provider (including HTTP
                       traces).
CB_USE_MOCK_PROVIDERS  Setting this to ``True`` will cause the CloudBridge test
                       suite to use mock drivers when available.
CB_TEST_PROVIDER       Set this value to a valid :class:`.ProviderList` value
                       such as ``aws``, to limit tests to that provider only.
=====================  ==================

Setup
-----
To initialize a connection to a cloud and get a provider object, you will
need to provide the cloud's access credentials to CloudBridge. These may
be provided in one of following ways:

1. Environment variables
2. A dictionary
3. Configuration file

Procuring access credentials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For Azure, Create service principle credentials from the following link : 
https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal#check-azure-subscription-permissions


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
OS_PROJECT_NAME      OS_STORAGE_URL
OS_REGION_NAME       OS_AUTH_TOKEN
===================  ==================

**Azure**

Note that managing resources in Azure requires a Resource Group. If a
Resource Group is not provided as part of the configuration, cloudbridge will
attempt to create a Resource Group using the given credentials. This
operation will happen with the client initialization, and requires a
"contributor" or "owner" role.
Similarly, a Storage Account is required when managing some resources, such
as KeyPairs and Buckets. If a Storage Account name is not provided as part
of the configuration, cloudbridge will attempt to create the Storage Account
when initializing the relevant services. This operation similarly requires a
"contributor" or "owner" role.
For more information on roles, see: https://docs.microsoft.com/en-us/azure/role-based-access-control/overview

======================  ==================
Mandatory variables     Optional Variables
======================  ==================
AZURE_SUBSCRIPTION_ID   AZURE_REGION_NAME
AZURE_CLIENT_ID         AZURE_RESOURCE_GROUP
AZURE_SECRET            AZURE_STORAGE_ACCOUNT
AZURE_TENANT            AZURE_VM_DEFAULT_USER_NAME
                        AZURE_PUBLIC_KEY_STORAGE_TABLE_NAME
======================  ==================

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


    ## For Azure
    config = {'azure_subscription_id': '<your_subscription_id>',
              'azure_client_id': '<your_client_id>',
              'azure_secret': '<your_secret>',
              'azure_tenant': '<your_tenant>',
              'azure_resource_group': '<your resource group>'}
    provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)

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
aws_session_token     Session key for your AWS account (if using temporary
                      credentials).
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


Providing access credentials in a file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CloudBridge can also read credentials from a file on your local file system.
The file should be placed in one of two locations: ``/etc/cloudbridge.ini`` or
``~/.cloudbridge``. Each set of credentials should be delineated with the
provider ID (e.g., ``openstack``, ``aws``, ``azure``) with the necessary credentials
being supplied in YAML format. Note that only one set of credentials per
cloud provider type can be supplied (i.e., via this method, it is not possible
to provide credentials for two different OpenStack clouds).

.. code-block:: bash

    [openstack]
    os_username: username
    os_password: password
    os_auth_url: auth url
    os_user_domain_name: user domain name
    os_project_domain_name: project domain name
    os_project_name: project name

    [aws]
    aws_access_key: access key
    aws_secret_key: secret key


Other configuration variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In addition to the provider specific configuration variables above, there are
some general configuration environment variables that apply to CloudBridge as
a whole

======================  ==================
Variable		            Description
======================  ==================
CB_DEBUG                Setting ``CB_DEBUG=True`` will cause detailed debug
                        output to be printed for each provider (including HTTP
                        traces).
CB_USE_MOCK_PROVIDERS   Setting this to ``True`` will cause the CloudBridge test
                        suite to use mock drivers when available.
CB_TEST_PROVIDER        Set this value to a valid :class:`.ProviderList` value
                        such as ``aws``, to limit tests to that provider only.
CB_DEFAULT_SUBNET_NAME  Name to be used for a subnet that will be considered
                        the 'default' by the library. This default will be used
                        only in cases there is no subnet marked as the default by the provider.
CB_DEFAULT_NETWORK_NAME Name to be used for a network that will be considered
                        the 'default' by the library. This default will be used
                        only in cases there is no network marked as the default by the provider.
======================= ==================

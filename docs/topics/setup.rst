Setup
=====
To initialize a connection to a cloud and get a provider object, you will
need to provide the cloud's access credentials to CloudBridge. For more
details on how to create and find these credentials, see the `Procuring Access
Credentials <procuring_credentials.html>`_ page. Note that you can selectively
provide the credentials for any provider you want to use and do not have to
provide credentials for all the providers. CloudBridge will consume the
available credentials in one of following ways:

1. `Providing access credentials through a dictionary`_
2. `Providing access credentials through environment variables`_
3. `Providing access credentials in a CloudBridge config file`_


Providing access credentials through a dictionary
-------------------------------------------------
You can initialize a simple config as follows. The key names are the same
as the environment variables, in lower case. Note that the config dictionary
will override environment values.

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    ## For AWS
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


    ## For GCE
    config = {'gce_service_creds_file': '<service_creds_file_name>.json'}
    # Alternatively, we can supply a dictionary with the credentials values
    # as the following:
    gce_creds = {
        "type": "service_account",
        "project_id": "<project_name>",
        "private_key_id": "<private_key_id>",
        "private_key": "<private_key>",
        "client_email": "<client_email>",
        "client_id": "<client_id>",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-name%40my-project.iam.gserviceaccount.com"
    }
    config = {'gce_service_creds_dict': gce_creds}
    provider = CloudProviderFactory().create_provider(ProviderList.GCE, config)


    ## For OpenStack
    config = {'os_username': '<your username>',
              'os_password': '<your password>',
              'os_auth_url': '<auth url>,
              'os_user_domain_name': '<user_domain_name>',
              'os_project_domain_name': '<project_domain_name>',
              'os_project_name': '<project_name>')
    provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK, config)

Some optional configuration values can only be provided through the config
dictionary. These are listed below for each provider.

CloudBridge
~~~~~~~~~~~

+----------------------+------------------------------------------------------------+
| Variable             | Description                                                |
+======================+============================================================+
| default_result_limit | Number of results that a ``.list()`` method should return. |
|                      | Default is 50.                                             |
+----------------------+------------------------------------------------------------+

AWS
~~~

+---------------------+--------------------------------------------------------------+
| Variable            | Description                                                  |
+=====================+==============================================================+
| aws_session_token   | Session key for your AWS account (if using temporary         |
|                     | credentials).                                                |
+---------------------+--------------------------------------------------------------+
| ec2_conn_path	      | Connection path. Default is ``/``.                           |
+---------------------+--------------------------------------------------------------+
| ec2_is_secure       | True to use an SSL connection. Default is ``True``.          |
+---------------------+--------------------------------------------------------------+
| ec2_port            | EC2 connection port. Does not need to be specified unless    |
|                     | EC2 service is running on an alternative port.               |
+---------------------+--------------------------------------------------------------+
| ec2_region_endpoint | Endpoint to use. Default is ``ec2.us-east-1.amazonaws.com``. |
+---------------------+--------------------------------------------------------------+
| ec2_region_name     | Default region name. Default is ``us-east-1``.               |
+---------------------+--------------------------------------------------------------+
| ec2_validate_certs  | Whether to use SSL certificate verification. Default is      |
|                     | ``False``.                                                   |
+---------------------+--------------------------------------------------------------+
| s3_conn_path        | Connection path. Default is ``/``.                           |
+---------------------+--------------------------------------------------------------+
| s3_is_secure        | True to use an SSL connection. Default is ``True``.          |
+---------------------+--------------------------------------------------------------+
| s3_host             | Host connection endpoint. Default is ``s3.amazonaws.com``.   |
+---------------------+--------------------------------------------------------------+
| s3_port             | Host connection port. Does not need to be specified unless   |
|                     | S3 service is running on an alternative port.                |
+---------------------+--------------------------------------------------------------+
| s3_validate_certs   | Whether to use SSL certificate verification. Default is      |
|                     | ``False``.                                                   |
+---------------------+--------------------------------------------------------------+

Azure
~~~~~

+-------------------------------------+----------------------------------------------------------+
| Variable                            | Description                                              |
+=====================================+==========================================================+
| azure_access_token                  | To sign requests to APIs protected by Azure.             |
+-------------------------------------+----------------------------------------------------------+
| azure_public_key_storage_table_name | Storage table name where the key pairs are stored.       |
|                                     | Default is ``cbcerts``.                                  |
+-------------------------------------+----------------------------------------------------------+
| azure_region_name                   | Default region to use for the current                    |
|                                     | session. Default is ``eastus``.                          |
+-------------------------------------+----------------------------------------------------------+
| azure_resource_group                | Azure resource group to use. Default is ``cloudbridge``. |
+-------------------------------------+----------------------------------------------------------+
| azure_storage_account               | Azure storage account to use. Note that this value must  |
|                                     | be unique across Azure and all data in a given session   |
|                                     | is stored within the supplied storage account. Default   |
|                                     | ``storacc`` + first 6 chars of subscription id + first 6 |
|                                     | chars of the supplied resource group.                    |
+-------------------------------------+----------------------------------------------------------+
| azure_vm_default_username           | System user name for which supplied key pair will be     |
|                                     | placed.                                                  |
+-------------------------------------+----------------------------------------------------------+

GCE
~~~

+-------------------------+----------------------------------------------------------+
| Variable                | Description                                              |
+=========================+==========================================================+
| gce_default_zone        | Default placement zone to use for the current session.   |
|                         | Default is ``us-central1-a``.                            |
+-------------------------+----------------------------------------------------------+
| gce_region_name         | Default region to use for the current session. Default   |
|                         | is ``us-central1``.                                      |
+-------------------------+----------------------------------------------------------+
| gce_vm_default_username | System user name for which supplied key pair will be     |
|                         | placed.                                                  |
+-------------------------+----------------------------------------------------------+


Providing access credentials through environment variables
----------------------------------------------------------
The following environment variables must be set, depending on the provider in
use. For the meaning of the variables and default values, see the descriptions
above.

AWS
~~~

+---------------------+------------+
| Variable            | Required?  |
+=====================+============+
| AWS_ACCESS_KEY      | ✔          |
+---------------------+------------+
| AWS_SECRET_KEY      | ✔          |
+---------------------+------------+

Azure
~~~~~

Note that managing resources in Azure requires a Resource Group. If a
Resource Group is not provided as part of the configuration, CloudBridge will
attempt to create a Resource Group using the given credentials. This
operation will happen with the client initialization, and requires a
"contributor" or "owner" role.

Similarly, a Storage Account is required when managing some resources, such
as key pairs and buckets. If a Storage Account name is not provided as part
of the configuration, CloudBridge will attempt to create the Storage Account
when initializing the relevant services. This operation similarly requires a
"contributor" or "owner" role.

For more information on roles, see
https://docs.microsoft.com/en-us/azure/role-based-access-control/overview.

+-------------------------------------+-----------+
| Variable                            | Required? |
+=====================================+===========+
| AZURE_CLIENT_ID                     | ✔         |
+-------------------------------------+-----------+
| AZURE_SECRET                        | ✔         |
+-------------------------------------+-----------+
| AZURE_SUBSCRIPTION_ID               | ✔         |
+-------------------------------------+-----------+
| AZURE_TENANT                        | ✔         |
+-------------------------------------+-----------+
| AZURE_PUBLIC_KEY_STORAGE_TABLE_NAME |           |
+-------------------------------------+-----------+
| AZURE_REGION_NAME                   |           |
+-------------------------------------+-----------+
| AZURE_RESOURCE_GROUP                |           |
+-------------------------------------+-----------+
| AZURE_STORAGE_ACCOUNT               |           |
+-------------------------------------+-----------+
| AZURE_VM_DEFAULT_USER_NAME          |           |
+-------------------------------------+-----------+

GCE
~~~

+------------------------+-----------+
| Variable               | Required? |
+========================+===========+
| GCE_SERVICE_CREDS_DICT | ✔         |
| or                     |           |
| GCE_SERVICE_CREDS_FILE |           |
+------------------------+-----------+
| GCE_DEFAULT_ZONE       |           |
+------------------------+-----------+
| GCE_PROJECT_NAME       |           |
+------------------------+-----------+
| GCE_REGION_NAME        |           |
+------------------------+-----------+

OpenStack
~~~~~~~~~

+------------------------+-----------+
| Variable               | Required? |
+========================+===========+
| OS_AUTH_URL            | ✔         |
+------------------------+-----------+
| OS_USERNAME            | ✔         |
+------------------------+-----------+
| OS_PASSWORD            | ✔         |
+------------------------+-----------+
| OS_PROJECT_NAME        | ✔         |
+------------------------+-----------+
| OS_REGION_NAME         | ✔         |
+------------------------+-----------+
| NOVA_SERVICE_NAME      |           |
+------------------------+-----------+
| OS_AUTH_TOKEN          |           |
+------------------------+-----------+
| OS_COMPUTE_API_VERSION |           |
+------------------------+-----------+
| OS_VOLUME_API_VERSION  |           |
+------------------------+-----------+
| OS_STORAGE_URL         |           |
+------------------------+-----------+

Once the environment variables are set, you can create a connection as follows,
replacing ``ProviderList.AWS`` with the desired provider (AZURE, GCE, or
OPENSTACK):

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})


Providing access credentials in a CloudBridge config file
---------------------------------------------------------
CloudBridge can also read credentials from a file on your local file system.
The file should be placed in one of two locations: ``/etc/cloudbridge.ini`` or
``~/.cloudbridge``. Each set of credentials should be delineated with the
provider ID (e.g., ``openstack``, ``aws``, ``azure``, ``gce``) with the
necessary credentials being supplied in YAML format. Note that only one set
of credentials per cloud provider type can be supplied (i.e., via this
method, it is not possible to provide credentials for two different
OpenStack clouds).

.. code-block:: bash

    [aws]
    aws_access_key: access key
    aws_secret_key: secret key

    [azure]
    azure_subscription_id: subscription id
    azure_tenant: tenant
    azure_client_id: client id
    azure_secret: secret
    azure_resource_group: resource group

    [gce]
    gce_service_creds_file: absolute path to credentials file

    [openstack]
    os_username: username
    os_password: password
    os_auth_url: auth url
    os_user_domain_name: user domain name
    os_project_domain_name: project domain name
    os_project_name: project name

Once the file is created, you can create a connection as follows, replacing
``ProviderList.AWS`` with the desired provider (AZURE, GCE, or OPENSTACK):

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    provider = CloudProviderFactory().create_provider(ProviderList.AWS, {})


General configuration variables
-------------------------------
In addition to the provider specific configuration variables above, there are
some general configuration environment variables that apply to CloudBridge as
a whole.

+-----------------------------+------------------------------------------------------+
| Variable                    | Description                                          |
+=============================+======================================================+
| CB_DEBUG                    | Setting ``CB_DEBUG=True`` will cause detailed        |
|                             | debug output to be printed for each provider         |
|                             | (including HTTP traces).                             |
+-----------------------------+------------------------------------------------------+
| CB_USE_MOCK_PROVIDERS       | Setting this to ``True`` will cause the CloudBridge  |
|                             | test suite to use mock drivers when available.       |
+-----------------------------+------------------------------------------------------+
| CB_TEST_PROVIDER            | Set this value to a valid :class:`.ProviderList`     |
|                             | value such as ``aws``, to limit tests to that        |
|                             | provider only.                                       |
+-----------------------------+------------------------------------------------------+
| CB_DEFAULT_SUBNET_LABEL     | Name to be used for a subnet that will be            |
|                             | considered the 'default' by the library. This        |
|                             | default will be used only in cases there is no       |
|                             | subnet marked as the default by the provider.        |
+-----------------------------+------------------------------------------------------+
| CB_DEFAULT_NETWORK_LABEL    | Name to be used for a network that will be           |
|                             | considered the 'default' by the library. This        |
|                             | default will be used only in cases there is no       |
|                             | network marked as the default by the provider.       |
+-----------------------------+------------------------------------------------------+
| CB_DEFAULT_IPV4RANGE        | The default IPv4 range when creating networks if     |
|                             | one is not provided. This value is also used in      |
|                             | tests.                                               |
+-----------------------------+------------------------------------------------------+
| CB_DEFAULT_SUBNET_IPV4RANGE | The default subnet IPv4 range used by CloudBridge    |
|                             | if one is not specified by the user. Tests do not    |
|                             | respect this variable.                               |
+-----------------------------+------------------------------------------------------+

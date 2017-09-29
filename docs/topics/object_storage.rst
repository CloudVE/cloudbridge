Working with object storage
==========================
Object storage provides a simple way to store and retrieve large amounts of
unstructured data over HTTP. Object Storage is also referred to as Blob (Binary
Large OBject) Storage by Azure, and Simple Storage Service (S3) by Amazon.

Typically, you would store your objects within a Bucket, as it is known in
AWS and GCE. A Bucket is also called a Container in OpenStack and Azure. In
CloudBridge, we use the term Bucket.

Storing objects in a bucket
---------------------------
To store an object within a bucket, we need to first create a bucket or
retrieve an existing bucket.

.. code-block:: python

    bucket = provider.storage.buckets.create('my-bucket')
    bucket.objects.list()

Next, let's upload some data to this bucket. To efficiently upload a file,
simple use the upload_from_file method.

.. code-block:: python

    obj = bucket.objects.create('my-data.txt')
    obj.upload_from_file('/path/to/myfile.txt')

You can also use the upload() function to upload from an in memory stream.
Note that, an object you create with objects.create() doesn't actually get
persisted until you upload some content.

To locate and download this uploaded file again, you can do the following:

.. code-block:: python

    bucket = provider.storage.buckets.find('my-bucket')[0]
    obj = bucket.objects.find('my-data.txt')[0]
    print("Size: {0}, Modified: {1}".format(obj.size, obj.last_modified))
    with open('/tmp/myfile.txt', 'wb') as f:
        test_obj.save_content(f)
 

Using tokens for authentication
-------------------------------
Some providers may support using temporary credentials with a session token,
in which case you will be able to access a particular bucket by using that
session token.

.. code-block:: python

    provider = CloudProviderFactory().create_provider(
        ProviderList.AWS,
        {'aws_access_key': 'ACCESS_KEY',
         'aws_secret_key': 'SECRET_KEY',
         'aws_session_token': 'MY_SESSION_TOKEN'})
.. code-block:: python

    provider = CloudProviderFactory().create_provider(
        ProviderList.OPENSTACK,
        {'os_storage_url': 'SWIFT_STORAGE_URL',
         'os_auth_token': 'MY_SESSION_TOKEN'})

Once a provider is obtained, you can access the container as usual:

.. code-block:: python

    bucket = provider.object_store.get(container)
    obj = bucket.create_object('my_object.txt')
    obj.upload_from_file(source)

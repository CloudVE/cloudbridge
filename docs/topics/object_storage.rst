Working with object storage
===========================
Object storage provides a simple way to store and retrieve large amounts of
unstructured data over HTTP. Object Storage is also referred to as Blob (Binary
Large OBject) Storage by Azure, and Simple Storage Service (S3) by Amazon.

Typically, you would store your objects within a Bucket, as it is known in
AWS and GCP. A Bucket is also called a Container in OpenStack and Azure. In
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

    bucket = provider.storage.buckets.find(name='my-bucket')[0]
    obj = bucket.objects.find(name='my-data.txt')[0]
    print("Size: {0}, Modified: {1}".format(obj.size, obj.last_modified))
    with open('/tmp/myfile.txt', 'wb') as f:
        obj.save_content(f)

To download to a local path, prefer download_to_file(), which fetches large
objects as parallel ranged reads. save_content() and iter_content() are the
single-stream alternatives, for writing to an arbitrary stream or for handing
the content on somewhere else - proxying it to an HTTP response, say.

.. code-block:: python

    for chunk in obj.iter_content():
        process(chunk)

Content is streamed, never held in memory whole, and chunks are sized by
chunk_size rather than by the content - binary data is never split on
newlines. Only the last chunk may be short.

.. code-block:: python

    for chunk in obj.iter_content(chunk_size=4 * 1024 * 1024):
        process(chunk)

chunk_size defaults to 1 MiB, which suits most callers. It trades per-chunk
overhead against memory and latency: each chunk costs a read from the provider
plus whatever your loop does per chunk, so small values get expensive over a
large object, while a large value is buffered in full before it is yielded and
so costs memory per concurrent stream. To change the default globally, set the
iter_chunk_size provider config value or the CB_ITER_CHUNK_SIZE environment
variable. save_content() takes the same argument.

.. note::
    On GCP the content is fetched as successive ranged requests, because the
    underlying client library has no single-connection streaming read, so
    chunk_size is also the request size there. Prefer a large chunk_size when
    streaming a large object from GCP.


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

    bucket = provider.storage.buckets.get(container)
    obj = bucket.objects.create('my_object.txt')
    obj.upload_from_file(source)


Generating signed URLs
----------------------

Signed URLs are a great way to allow users who do not have credentials for
the cloud provider of your choice, to interact with an object within a
storage bucket.

You can generate signed URLs with ``GET`` permissions to allow a user to
get an object. 

.. code-block:: python
 
    provider = CloudProviderFactory().create_provider(
        ProviderList.AWS,
        {'aws_access_key': 'ACCESS_KEY',
         'aws_secret_key': 'SECRET_KEY',
         'aws_session_token': 'MY_SESSION_TOKEN'}) 

    bucket = provider.storage.buckets.get("my-bucket")
    obj = bucket.objects.get("my-file.txt")

    url = obj.generate_url(expires_in=7200)

You can also generate a signed URL with `PUT` permissions to allow users
to upload files to your storage bucket.

.. code-block:: python
 
    provider = CloudProviderFactory().create_provider(
        ProviderList.AWS,
        {'aws_access_key': 'ACCESS_KEY',
         'aws_secret_key': 'SECRET_KEY',
         'aws_session_token': 'MY_SESSION_TOKEN'}) 

    bucket = provider.storage.buckets.get("my-bucket")
    obj = bucket.objects.create("my-file.txt")
    url = obj.generate_url(expires_in=7200, writable=True)


With your signed URL, you or someone on your team can upload a file like this

.. code-block:: python

    import requests

    content = b"Hello world!"
    # Only Azure requires the x-ms-blob-type header to be present, but there's no harm
    # in sending this in for all providers.
    headers = {'x-ms-blob-type': 'BlockBlob'}
    requests.put(url, data=content)

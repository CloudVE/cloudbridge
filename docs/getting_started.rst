Getting Started
===============
This getting started guide will provide a quick tour of some CloudBridge
features. For more details on individual features, see the
`Using CloudBridge <topics/overview.html>`_ section or the
`API reference <api_docs/ref.html>`_.

Installation
------------
Cloudbridge is available on PyPI so to install the latest available version,
run::

    pip install cloudbridge

Create a provider
-----------------
To start, you will need to create a reference to a provider object. The
provider object identifies the cloud you want to work with and supplies your
credentials. In this code snippet, we will be using AWS. For the details on
other providers, take a look at the `Setup page <topics/setup.html>`_.

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'aws_access_key': 'AKIAJW2XCYO4AF55XFEQ',
              'aws_secret_key': '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'}
    provider = CloudProviderFactory().create_provider(ProviderList.AWS, config)

List some resources
-------------------
Once you have a reference to a provider, explore the cloud platform:

.. code-block:: python

    provider.compute.images.list()
    provider.security.security_groups.list()
    provider.block_store.snapshots.list()
    provider.object_store.list()

This will demonstrate the fact that the library was properly installed and your
provider object is setup correctly but it is not very interesting. Therefore,
let's create a new instance we can ssh into using a key pair.

Create a key pair
-----------------
We'll create a new key pair and save the private portion of the key to a file
on disk as a read-only file.

.. code-block:: python

    kp = provider.security.key_pairs.create('cloudbridge_intro')
    with open('cloudbridge_intro.pem', 'w') as f:
        f.write(kp.material)
    import os
    os.chmod('cloudbridge_intro.pem', 0400)

Create a security group
-----------------------
Next, we need to create a security group and add a rule to allow ssh access.

.. code-block:: python

    sg = provider.security.security_groups.create(
        'cloudbridge_intro', 'A security group used by Cloudbridge')
    sg.add_rule('tcp', 22, 22, '0.0.0.0/0')

Launch an instance
------------------
Before we can launch an instance, we need to decide what image to use so let's
get a base Ubuntu image ``ami-d85e75b0`` and launch an instance.

.. code-block:: python

    img = provider.compute.images.get('ami-d85e75b0')
    inst_type = provider.compute.instance_types.find(name='m1.small')
    inst = provider.compute.instances.create(
        name='Cloudbridge-intro', image=img, instance_type=inst_type,
        keypair=kp, security_groups=[sg])
    # Refresh the state
    inst.refresh()
    inst.state
    # 'running'
    inst.public_ips
    # [u'54.166.125.219']

From the command prompt, you can now ssh into the instance
``ssh -i cloudbridge_intro.pem ubuntu@54.166.125.219``.

Cleanup
-------
To wrap things up, let's clean up all the resources we have created

.. code-block:: python

    inst.terminate()
    sg.delete()
    kp.delete()

And that's it - a full circle in a few lines of code. You can now try
the same with a different provider. All you will need to change is the
cloud-specific data, namely the provider setup and the image ID.

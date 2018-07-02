Getting Started
===============
This getting started guide will provide a quick tour of some CloudBridge
features. For more details on individual features, see the
`Using CloudBridge <topics/overview.html>`_ section or the
`API reference <api_docs/ref.html>`_.

Installation
------------
CloudBridge is available on PyPI so to install the latest available version,
run::

    pip install --upgrade cloudbridge
    
For common issues during setup, check the following section:
`Common Setup Issues <topics/troubleshooting.html>`

Create a provider
-----------------
To start, you will need to create a reference to a provider object. The
provider object identifies the cloud you want to work with and supplies your
credentials. The following two code snippets setup a necessary provider object,
for AWS and OpenStack. For the details on other providers, take a look at the
`Setup page <topics/setup.html>`_. The remainder of the code is the same for
either provider.

AWS:

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'aws_access_key': 'AKIAJW2XCYO4AF55XFEQ',
              'aws_secret_key': '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'}
    provider = CloudProviderFactory().create_provider(ProviderList.AWS, config)
    image_id = 'ami-aa2ea6d0'  # Ubuntu 16.04 (HVM)

OpenStack (with Keystone authentication v2):

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'os_username': 'username',
              'os_password': 'password',
              'os_auth_url': 'authentication URL',
              'os_region_name': 'region name',
              'os_project_name': 'project name'}
    provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK,
                                                      config)
    image_id = 'c1f4b7bc-a563-4feb-b439-a2e071d861aa'  # Ubuntu 14.04 @ NeCTAR

OpenStack (with Keystone authentication v3):

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'os_username': 'username',
              'os_password': 'password',
              'os_auth_url': 'authentication URL',
              'os_project_name': 'project name',
              'os_project_domain_name': 'project domain name',
              'os_user_domain_name': 'domain name'}
    provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK,
                                                      config)
    image_id = 'acb53109-941f-4593-9bf8-4a53cb9e0739'  # Ubuntu 16.04 @ Jetstream

Azure:

.. code-block:: python

    from cloudbridge.cloud.factory import CloudProviderFactory, ProviderList

    config = {'azure_subscription_id': 'REPLACE WITH ACTUAL VALUE',
              'azure_client_id': 'REPLACE WITH ACTUAL VALUE',
              'azure_secret': 'REPLACE WITH ACTUAL VALUE',
              'azure_tenant': ' REPLACE WITH ACTUAL VALUE'}
    provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)
    image_id = 'Canonical/UbuntuServer/16.04.0-LTS/latest'  # Ubuntu 16.04


List some resources
-------------------
Once you have a reference to a provider, explore the cloud platform:

.. code-block:: python

    provider.security.security_groups.list()
    provider.compute.vm_types.list()
    provider.storage.snapshots.list()
    provider.storage.buckets.list()

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
    os.chmod('cloudbridge_intro.pem', 0o400)

Create a network
----------------
A cloudbridge instance should be launched into a private subnet. We'll create
a private network and subnet, and make sure it has internet connectivity, by
attaching an internet gateway to the subnet via a router.

.. code-block:: python

    net = self.provider.networking.networks.create(
        name='my-network', cidr_block='10.0.0.0/16')
    sn = net.create_subnet(name='my-subnet', cidr_block='10.0.0.0/28')
    router = self.provider.networking.routers.create(network=net, name='my-router')
    router.attach_subnet(sn)
    gateway = net.gateways.get_or_create_inet_gateway(name)
    router.attach_gateway(gateway)


Create a VM firewall
--------------------
Next, we need to create a VM firewall (also commonly known as a security group)
and add a rule to allow ssh access. A VM firewall needs to be associated with
a private network.

.. code-block:: python

    net = provider.networking.networks.get('desired network ID')
    fw = provider.security.vm_firewalls.create(
        'cloudbridge-intro', 'A VM firewall used by CloudBridge', net.id)
    fw.rules.create(TrafficDirection.INBOUND, 'tcp', 22, 22, '0.0.0.0/0')

Launch an instance
------------------
We can now launch an instance using the created key pair and security group.
We will launch an instance type that has at least 2 CPUs and 4GB RAM. We will
also add the network interface as a launch argument.

.. code-block:: python

    img = provider.compute.images.get(image_id)
    vm_type = sorted([t for t in provider.compute.vm_types
                      if t.vcpus >= 2 and t.ram >= 4],
                      key=lambda x: x.vcpus*x.ram)[0]
    inst = provider.compute.instances.create(
        name='cloudbridge-intro', image=img, vm_type=vm_type,
        subnet=sn, key_pair=kp, vm_firewalls=[fw])
    # Wait until ready
    inst.wait_till_ready()  # This is a blocking call
    # Show instance state
    inst.state
    # 'running'

.. note ::

   Note that we iterated through provider.compute.vm_types directly
   instead of calling provider.compute.vm_types.list(). This is
   because we need to iterate through all records in this case. The list()
   method may not always return all records, depending on the global limit
   for records, necessitating that additional records be paged in. See
   :doc:`topics/paging_and_iteration`.

Assign a public IP address
--------------------------
To access the instance, let's assign a public IP address to the instance. For
this step, we'll first need to allocate a floating IP address for our account
and then associate it with the instance. Note that floating IPs are associated
with an Internet Gateway so we allocate the IP under the gateway we dealt with
earlier.

.. code-block:: python

    fip = gateway.floating_ips.create()
    inst.add_floating_ip(fip)
    inst.refresh()
    inst.public_ips
    # [u'54.166.125.219']

From the command prompt, you can now ssh into the instance
``ssh -i cloudbridge_intro.pem ubuntu@54.166.125.219``.

Cleanup
-------
To wrap things up, let's clean up all the resources we have created

.. code-block:: python

    inst.delete()
    from cloudbridge.cloud.interfaces import InstanceState
    inst.wait_for([InstanceState.DELETED, InstanceState.UNKNOWN],
                   terminal_states=[InstanceState.ERROR])  # Blocking call
    fip.delete()
    fw.delete()
    kp.delete()
    os.remove('cloudbridge_intro.pem')
    router.detach_gateway(gateway)
    router.detach_subnet(sn)
    gateway.delete()
    router.delete()
    sn.delete()
    net.delete()

And that's it - a full circle in a few lines of code. You can now try
the same with a different provider. All you will need to change is the
cloud-specific data, namely the provider setup and the image ID.

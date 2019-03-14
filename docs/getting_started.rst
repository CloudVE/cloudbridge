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

    from cloudbridge.factory import CloudProviderFactory, ProviderList

    config = {'aws_access_key': 'AKIAJW2XCYO4AF55XFEQ',
              'aws_secret_key': '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'}
    provider = CloudProviderFactory().create_provider(ProviderList.AWS, config)
    image_id = 'ami-aa2ea6d0'  # Ubuntu 16.04 (HVM)

OpenStack (with Keystone authentication v2):

.. code-block:: python

    from cloudbridge.factory import CloudProviderFactory, ProviderList

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

    from cloudbridge.factory import CloudProviderFactory, ProviderList

    config = {'os_username': 'username',
              'os_password': 'password',
              'os_auth_url': 'authentication URL',
              'os_project_name': 'project name',
              'os_project_domain_name': 'project domain name',
              'os_user_domain_name': 'domain name'}
    provider = CloudProviderFactory().create_provider(ProviderList.OPENSTACK,
                                                      config)
    image_id = '470d2fba-d20b-47b0-a89a-ab725cd09f8b'  # Ubuntu 18.04@Jetstream

Azure:

.. code-block:: python

    from cloudbridge.factory import CloudProviderFactory, ProviderList

    config = {'azure_subscription_id': 'REPLACE WITH ACTUAL VALUE',
              'azure_client_id': 'REPLACE WITH ACTUAL VALUE',
              'azure_secret': 'REPLACE WITH ACTUAL VALUE',
              'azure_tenant': ' REPLACE WITH ACTUAL VALUE'}
    provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)
    image_id = 'Canonical:UbuntuServer:16.04.0-LTS:latest'  # Ubuntu 16.04

Google Compute Cloud:

.. code-block:: python

    from cloudbridge.factory import CloudProviderFactory, ProviderList

    config = {'gcp_project_name': 'project name',
              'gcp_service_creds_file': 'service_file.json',
              'gcp_region_name': 'us-east1',  # Use desired value
              'gcp_zone_name': 'us-east1-b'}  # Use desired value
    provider = CloudProviderFactory().create_provider(ProviderList.GCP, config)
    image_id = 'https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/global/images/ubuntu-1804-bionic-v20181222'

List some resources
-------------------
Once you have a reference to a provider, explore the cloud platform:

.. code-block:: python

    provider.security.vm_firewalls.list()
    provider.compute.vm_types.list()
    provider.storage.snapshots.list()
    provider.storage.buckets.list()

This will demonstrate the fact that the library was properly installed and your
provider object is setup correctly. By itself, those commands are not very
interesting so let's create a new instance we can ssh into using a key pair.

Create a key pair
-----------------
We'll create a new key pair and save the private portion of the key to a file
on disk as a read-only file.

.. code-block:: python

    import os
    kp = provider.security.key_pairs.create('cb-keypair')
    with open('cloudbridge_intro.pem', 'wb') as f:
        f.write(kp.material)
    os.chmod('cloudbridge_intro.pem', 0o400)

Create a network
----------------
A cloudbridge instance should be launched into a private subnet. We'll create
a private network and subnet, and make sure it has internet connectivity, by
attaching an internet gateway to the subnet via a router.

.. code-block:: python

    net = provider.networking.networks.create(cidr_block='10.0.0.0/16',
                                              label='cb-network')
    zone = provider.compute.regions.get(provider.region_name).zones[0]
    sn = net.subnets.create(
        cidr_block='10.0.0.0/28', label='cb-subnet', zone=zone)
    router = provider.networking.routers.create(network=net, label='cb-router')
    router.attach_subnet(sn)
    gateway = net.gateways.get_or_create()
    router.attach_gateway(gateway)


Create a VM firewall
--------------------
Next, we need to create a VM firewall (also commonly known as a security group)
and add a rule to allow ssh access. A VM firewall needs to be associated with
a private network.

.. code-block:: python

    from cloudbridge.interfaces.resources import TrafficDirection
    fw = provider.security.vm_firewalls.create(
        label='cb-firewall', description='A VM firewall used by
        CloudBridge', network=net)
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
        image=img, vm_type=vm_type, label='cb-instance',
        subnet=sn, zone=zone, key_pair=kp, vm_firewalls=[fw])
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

    if not inst.public_ips:
        fip = gateway.floating_ips.create()
        inst.add_floating_ip(fip)
        inst.refresh()
    inst.public_ips
    # [u'54.166.125.219']

From the command prompt, you can now ssh into the instance
``ssh -i cloudbridge_intro.pem ubuntu@54.166.125.219``.

Get a resource
--------------
When a resource already exists, a reference to it can be retrieved using either
its ID, name, or label. It is important to note that while IDs and names are
unique, multiple resources of the same type could use the same label, thus the
`find` method always returns a list, while the `get` method returns a single
object. While the methods are similar across resources, they are explicitly
listed in order to help map each resource with the service that handles it.
Note that labeled resources allow to find by label, while unlabeled
resources find by name or their special properties (eg: public_ip for
floating IPs). For more detailed information on the types of resources and
their provider mappings, see :doc:`topics/resource_types_and_mapping`.

.. code-block:: python

    # Key Pair
    kp = provider.security.key_pairs.get('keypair ID')
    kp = provider.security.key_pairs.find(name='cb-keypair')[0]

    # Floating IPs
    fip = gateway.floating_ips.get('FloatingIP ID')
    # Find using public IP address
    fip_list = gateway.floating_ips.find(public_ip='IP address')
    # Find using name (the behavior of the `name` property can be 
    # cloud-dependent). More details can be found `here <topics/resource_types_and_mapping.html>`
    fip_list = gateway.floating_ips.find(name='cb-fip')[0]

    # Network
    net = provider.networking.networks.get('network ID')
    net_list = provider.networking.networks.find(label='my-network')
    net = net_list[0]

    # Subnet
    sn = provider.networking.subnets.get('subnet ID')
    # Unknown network
    sn_list = provider.networking.subnets.find(label='cb-subnet')
    # Known network
    sn_list = provider.networking.subnets.find(network=net.id,
                                               label='cb-subnet')
    sn = sn_list(0)

    # Router
    router = provider.networking.routers.get('router ID')
    router_list = provider.networking.routers.find(label='cb-router')
    router = router_list[0]

    # Gateway
    gateway = net.gateways.get_or_create()

    # Firewall
    fw = provider.security.vm_firewalls.get('firewall ID')
    fw_list = provider.security.vm_firewalls.find(label='cb-firewall')
    fw = fw_list[0]

    # Instance
    inst = provider.compute.instances.get('instance ID')
    inst_list = provider.compute.instances.list(label='cb-instance')
    inst = inst_list[0]


Cleanup
-------
To wrap things up, let's clean up all the resources we have created

.. code-block:: python

    from cloudbridge.interfaces import InstanceState
    inst.delete()
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

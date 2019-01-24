Launching instances
===================
Before being able to run below commands, you will need a ``provider`` object
(see `this page <setup.html>`_).

Common launch data
------------------
Before launching an instance, you need to decide what image to launch
as well as what type of instance. We will create those objects here. The
specified image ID is a base Ubuntu image on AWS so feel free to change it as
desired. For instance type, we're going to let CloudBridge figure out what's
the appropriate name on a given provider for an instance with at least 2 CPUs
and 4 GB RAM.

.. code-block:: python

    img = provider.compute.images.get('ami-759bc50a')  # Ubuntu 16.04 on AWS
    vm_type = sorted([t for t in provider.compute.vm_types
                      if t.vcpus >= 2 and t.ram >= 4],
                      key=lambda x: x.vcpus*x.ram)[0]

In addition, CloudBridge instances must be launched into a private subnet.
While it is possible to create complex network configurations as shown in the
`Private networking`_ section, if you don't particularly care in which subnet
the instance is launched, CloudBridge provides a convenience function to
quickly obtain a default subnet for use. We just need to supply a zone to use.

.. code-block:: python

    zone = provider.compute.regions.get(provider.region_name).zones[0]
    subnet = provider.networking.subnets.get_or_create_default(zone)

When launching an instance, you can also specify several optional arguments
such as the firewall (aka security group), a key pair, or instance user data.
To allow you to connect to the launched instances, we will also supply those
parameters (note that we're making an assumption here these resources exist;
if you don't have those resources under your account, take a look at the
`Getting Started <../getting_started.html>`_ guide).

.. code-block:: python

    kp = provider.security.key_pairs.find(name='cloudbridge-intro')[0]
    fw = provider.security.vm_firewalls.list()[0]

Launch an instance
------------------
Once we have all the desired pieces, we'll use them to launch an instance:

.. code-block:: python

    inst = provider.compute.instances.create(
        label='cloudbridge-vpc', image=img, vm_type=vm_type,
        subnet=subnet, zone=zone, key_pair=kp, vm_firewalls=[fw])

Private networking
~~~~~~~~~~~~~~~~~~
Private networking gives you control over the networking setup for your
instance(s) and is considered the preferred method for launching instances. To
launch an instance with an explicit private network, you can create a custom
network and make sure it has internet connectivity. You can then launch into
that subnet.

.. code-block:: python

    net = self.provider.networking.networks.create(
        label='my-network', cidr_block='10.0.0.0/16')
    sn = net.create_subnet(label='my-subnet', cidr_block='10.0.0.0/28')
    # make sure subnet has internet access
    router = self.provider.networking.routers.create(label='my-router', network=net)
    router.attach_subnet(sn)
    gateway = net.gateways.get_or_create_inet_gateway()
    router.attach_gateway(gateway)

    inst = provider.compute.instances.create(
        label='cloudbridge-vpc', image=img, vm_type=vm_type,
        subnet=sn, zone=zone, key_pair=kp, vm_firewalls=[fw])

For more information on how to create and setup a private network, take a look
at `Networking <./networking.html>`_.

Block device mapping
~~~~~~~~~~~~~~~~~~~~
Optionally, you may want to provide a block device mapping at launch,
specifying volume or ephemeral storage mappings for the instance. While volumes
can also be attached and mapped after instance boot using the volume service,
specifying block device mappings at launch time is especially useful when it is
necessary to resize the root volume.

The code below demonstrates how to resize the root volume. For more information,
refer to :class:`.LaunchConfig`.

.. code-block:: python

    lc = provider.compute.instances.create_launch_config()
    lc.add_volume_device(source=img, size=11, is_root=True)
    inst = provider.compute.instances.create(
        label='cloudbridge-bdm', image=img,  vm_type=vm_type,
        launch_config=lc, key_pair=kp, vm_firewalls=[fw],
        subnet=subnet, zone=zone)

where ``img`` is the :class:`.Image` object to use for the root volume.

After launch
------------
After an instance has launched, you can access its properties:

.. code-block:: python

    # Wait until ready
    inst.wait_till_ready()  # This is a blocking call
    inst.state
    # 'running'

Depending on the provider's networking setup, it may be necessary to explicitly
assign a floating IP address to your instance. This can be done as follows:

.. code-block:: python

    # Create a new floating IP address
    fip = provider.networking.floating_ips.create()
    # Assign the desired IP to the instance
    inst.add_floating_ip(fip)
    inst.refresh()
    inst.public_ips
    # [u'149.165.168.143']

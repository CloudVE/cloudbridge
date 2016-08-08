Launching instances
===================
Depending on the cloud provider, instances can be launched using
software-managed networking (e.g., VPC on AWS, Neutron on OpenStack) or the
classic networking approach. Before being able to run below command, you will
need a ``provider`` object (see `this page <setup.html>`_).

Common launch data
------------------
Before launching an instance, you need to decide on what image to launch
as well as what type of instance. We will create those objects here are use
them in both options below. The specified image ID is a base Ubuntu image on
AWS so feel free to change it as desired.

.. code-block:: python

    img = provider.compute.images.get('ami-d85e75b0')  # Ubuntu 14.04 on AWS
    inst_type = provider.compute.instance_types.find(name='m1.small')[0]

When launching an instance, you can also specify several optional arguments
such as the security group, a key pair, or instance user data. To allow you to
connect to the launched instances, we will also supply those parameters (note
that we're making an assumption here these resources exist; if you don't have
those resources, take a look at the `Getting Started <../getting_started.html>`_
guide).

.. code-block:: python

    kp = provider.security.key_pairs.find(name='cloudbridge_intro')[0]
    sg = provider.security.security_groups.list()[0]

Private networking setup
------------------------
Private networking gives you control over the networking setup for your
instance(s) and is considered the preferred method for launching instances.

Create a new private network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To start, we will create a private network and a corresponding subnet into
which an instance will be launched. When creating the subnet, we need to
set the address pool. For OpenStack, any address pool is acceptable while for
the AWS cloud, the subnet address pool needs to belong to the private network
address space; we can obtain the private network address space via
network object's ``cidr_block`` field (e.g., ``10.0.0.0/16``). Let's crate a
subnet starting from the beginning of the block and allow up to 32 IP addresses
into the subnet (``/27``):

.. code-block:: python

    net = provider.network.create(name="CloudBridge-net")
    net.cidr_block  # '10.0.0.0/16'
    sn = net.create_subnet('10.0.0.1/27', "CloudBridge-subnet")

Note that it may be necessary to also create a route for this new network. If
that's the case, take a look at the
`Getting Started <../getting_started.html>`_ document for an example.

Retrieve an existing private network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you already have existing networks, we can simply reuse an existing one:

.. code-block:: python

    provider.network.list()  # Find a desired network ID
    net = provider.network.get('desired network ID')
    sn = net.subnets()[0]  # Get a handle on a desired subnet

Launch an instance
------------------
Once we have a handle on a private network, we'll define a launch configuration
object to aggregate all the launch configuration options. The launch config
can contain other launch options, such as the block storage mappings (see
below). Finally, we can launch the instance:

.. code-block:: python

    lc = provider.compute.instances.create_launch_config()
    lc.add_network_interface(net.id)
    inst = provider.compute.instances.create(
        name='CloudBridge-VPC', image=img,  instance_type=inst_type,
        launch_config=lc, key_pair=kp, security_groups=[sg])

.. warning::

    CloudBridge version 0.1.0 does not uniformly deal with network abstractions
    for AWS and OpenStack providers. AWS takes a subnet ID for it's launch
    config while OpenStack takes a network ID. As a result, the user needs to
    make this distinction in their code and supply the correct value. For
    example, for AWS, above code needs to look like the following:
    ``lc.add_network_interface(sn.id)``. This has been corrected in newer code.

Launch with default networking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Launching an instance with the default networking model is straightforward,
only needing to specify the basic parameters. This will only work for the case
a default network exists for your account, which is provider-dependent and may
not necessarily exist.

For the case of AWS, an instance will be launched into the VPC where the
specified security group belongs to. If no security group is specified, the
instance will get launched into the *default* VPC, assuming such VPC exists.

.. code-block:: python

    inst = provider.compute.instances.create(
        name='CloudBridge-basic', image=img, instance_type=inst_type,
        key_pair=kp, security_groups=[sg])

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
        name='CloudBridge-BDM', image=img,  instance_type=inst_type,
        launch_config=lc, key_pair=kp, security_groups=[sg])

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

    # List all the IP addresses and find the desired one
    provider.network.floating_ips()
    # Assign the desired IP to the instance
    inst.add_floating_ip('149.165.168.143')
    inst.refresh()
    inst.public_ips
    # [u'149.165.168.143']

Launching instances
===================
Depending on the cloud provider, instances can be launched using
software-managed networking (e.g., VPC on AWS, Neutron on OpenStack) or the
classic networking approach. Before being able to run below command, you will
need a ``provider`` object (see `this page <setup.html>`_).

Common launch data
------------------
Before launching an instane, you need to decide on what image to launch
as well as what type of instance. We will create those objects here are use
them in both options below. The specified image ID is a base Ubuntu image on
AWS so feel free to change it as desired.

.. code-block:: python

    img = provider.compute.images.get('ami-d85e75b0')
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

Launch with classic networking
------------------------------
Launching an instance with the traditional networking model is straighforward,
only needing to specify the basic parameters:

.. code-block:: python

    inst = provider.compute.instances.create(
        name='Cloudbridge-basic', image=img, instance_type=inst_type,
        key_pair=kp, security_groups=[sg])

Launch with private networking
------------------------------
To start, we will create a private network and a corresponding subnet into
which an instance will be launched. When creating the subnet, we need to
set the address pool. For the AWS cloud, the subnet address pool needs to
belong to the private network address space; for OpenStack, any address pool
is acceptable. On AWS, we can obtain the private network address space via
network object's ``cidr_block`` field (e.g., ``10.0.0.0/16``). Let's crate a
subnet starting from the beginning of the block and allow up to 32 IP addresses
into the subnet (``/27``):

.. code-block:: python

    net = provider.network.create(name="Cloudbridge-net")
    net.cidr_block  # '10.0.0.0/16'
    sn = net.create_subnet('10.0.0.1/27', "Cloudbridge-subnet")

Once we hace created a private network, we'll define a launch configuration
object to aggregate all the launch configuration options. The launch config
can contain other launch options, such as the block storage mappings (see
below). Finally, we can launch the instance:

.. code-block:: python

    lc = provider.compute.instances.create_launch_config()
    lc.add_network_interface(sn.id)
    inst = provider.compute.instances.create(
        name='Cloudbridge-VPC', image=img,  instance_type=inst_type,
        launch_config=lc, key_pair=kp, security_groups=[sg])


Block device mapping
--------------------
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
        name='Cloudbridge-BDM', image=img,  instance_type=inst_type,
        launch_config=lc, key_pair=kp, security_groups=[sg])

where img is the :class:`.Image` object to use for the root volume.

After an instance has launched, you can access its properties:

.. code-block:: python

    # Wait until ready
    inst.wait_till_ready()
    inst.state
    # 'running'
    inst.public_ips
    # [u'54.166.125.219']

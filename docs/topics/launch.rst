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
    inst_type = provider.compute.instance_types.find(name='m1.small')

When launching an instance, you can also specify several optional arguments
such as the security group, a key pair, or instance user data. To allow you to
connect to the launched instances, we will also supply those parameters.

.. code-block:: python

    kp = provider.security.key_pairs.find(name='cloudbridge_intro')
    sg = provider.security.security_groups.list()[0]

Launch with classic networking
------------------------------
Launching an instance with the traditional networking model is straighforward,
only needing to specify the basic parameters:

.. code-block:: python

    inst = provider.compute.instances.create(
        name='Cloudbridge-basic', image=img, instance_type=inst_type,
        keypair=kp, security_groups=[sg])

Launch with private networking
------------------------------
Before we can launch an instance into a private newtork, we need to supply a
network into which the instance will get launched. To aggregate multiple such
launch configuration options, we create a launch config object and supply it
when launching an instance. Note that for the time being (Cloudbridge v0.1)
there is no support for exploring the networking resources so it is necessary
to get the network IDs via other means (e.g., native API, web dashboard).

.. code-block:: python

    lc = provider.compute.instances.create_launch_config()
    lc.add_network_interface('subnet-c24aeaff')
    inst = provider.compute.instances.create(
        name='Cloudbridge-VPC', image=img,  instance_type=inst_type,
        launch_config=lc, keypair=kp, security_groups=[sg])

For OpenStack, the process is the same and you only need to specify the
appropriate network interface ID (e.g.,
``lc.add_network_interface('5820c766-75fe-4fc6-96ef-798f67623238')``).

------------

After an instance has launched, you can access it's properties:

.. code-block:: python

    # Refresh the state
    inst.refresh()
    inst.state
    # 'running'
    inst.public_ips
    # [u'54.166.125.219']

Private networking
==================
Private networking gives you control over the networking setup for your
instance(s) and is considered the preferred method for launching instances.
Also, providers these days are increasingly requiring use of private networks.
All CloudBridge deployed VMs must be deployed into a particular subnet.

If you do not explicitly specify a private network to use when launching an
instance, CloudBridge will attempt to use a default one. A 'default' network is
one tagged as such by the native API. If such tag or functionality does not
exist, CloudBridge will look for one with a predefined name (by default, called
'CloudBridgeNet', which can be overridden with environment variable
``CB_DEFAULT_NETWORK_NAME``).

Once a VM is deployed, cloudbridge's networking capabilities must address
several common scenarios.

1. Allowing internet access from a launched VM

   In the simplest scenario, a user may simply want to launch an instance and
   allow the instance to access the internet.


2. Allowing internet access to a launched VM

   Alternatively, the user may want to allow the instance to be contactable
   from the internet. In a more complex scenario, a user may want to deploy
   VMS into several subnets, and deploy a gateway, jump host or bastion host
   to access other VMs which are not directly connected to the internet. In
   the latter scenario, the gateway/jump host/bastion host will need to be
   contactable over the internet.


3. Secure access between subnets for n-tier applications

   In this third scenario, a multi-tier app may be deployed into several
   subnets depending on their tier. For example, consider the following
   scenario:

   - Tier 1/Subnet 1 - Web Server Needs to be externally accessible over the
     internet. However, in this particular scenario, the web server itself does
     not need access to the internet.

   - Tier 2/Subnet 2 - Application Server The Application server must only be
     able to communicate with the database server in Subnet 3, and receive
     communication from the Web Server in Subnet 1. However, we assume a
     special case here where the application server needs to access the
     internet.

   - Tier 3/Subnet 3 - Database Server The database server must only be able to
     receive incoming traffic from Tier 2, but must not be able to make
     outgoing traffic outside of its subnet.

    At present, CloudBridge does not provide support for this scenario,
    primarily because OpenStack's FwaaS (Firewall-as-a-Service) is not widely
    available.

1. Allowing internet access from a launched VM
----------------------------------------------
Creating a private network is a simple, one-line command but appropriately
connecting it so that it has uniform Internet access across all providers
is a multi-step process:
(1) create a network; (2) create a subnet within this network; (3) create a
router; (4) attach the router to the subnet and (5) attach the router to the
internet gateway.

When creating a network, we need to set an address pool. Any subsequent
subnets you create must have a CIDR block that falls within the parent
network's CIDR block. Below, we'll create a subnet starting from the beginning
of the block and allow up to 16 IP addresses within a subnet (``/28``).

.. code-block:: python

    net = provider.networking.networks.create(
        name='my-network', cidr_block='10.0.0.0/16')
    sn = net.create_subnet(name='my-subnet', cidr_block='10.0.0.0/28', zone=zone)
    router = provider.networking.routers.create(network=net, name='my-router')
    router.attach_subnet(sn)
    gateway = net.gateways.get_or_create_inet_gateway(name)
    router.attach_gateway(gateway)


2. Allowing internet access to a launched VM
--------------------------------------------
The additional step that's required here is to assign a floating IP to the VM:

.. code-block:: python

    net = provider.networking.networks.create(
        name='my-network', cidr_block='10.0.0.0/16')
    sn = net.create_subnet(name='my-subnet', cidr_block='10.0.0.0/28', zone=zone)

    vm = provider.compute.instances.create('my-inst', subnet=sn, ...)

    router = provider.networking.routers.create(network=net, name='my-router')
    router.attach_subnet(sn)
    gateway = net.gateways.get_or_create_inet_gateway(net, name)
    router.attach_gateway(gateway)

    fip = provider.networking.floating_ips.create()
    vm.add_floating_ip(fip)


Retrieve an existing private network
------------------------------------
If you already have existing networks, we can query for it:

.. code-block:: python

    provider.networking.networks.list()  # Find a desired network ID
    net = provider.networking.networks.get('desired network ID')

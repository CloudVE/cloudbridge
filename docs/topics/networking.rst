Private networking
==================
Private networking gives you control over the networking setup for your
instance(s) and is considered the preferred method for launching instances.
Also, providers these days are increasingly requiring use of private networks.

If you do not explicitly specify a private network to use when launching an
instance, CloudBridge will attempt to use a default one. A 'default' network is
one tagged as such by the native API. If such tag or functionality does not
exist, CloudBridge will look for one with a predefined name (by default, called
'CloudBridgeNet', which can be overridden with environment variable
``CB_DEFAULT_NETWORK_NAME``).

Create a new private network
----------------------------
Creating a private network is a simple, one-line command but appropriately
connecting it so it has Internet access is a multi-step process:
(1) create a network; (2) create a subnet within the network; (3) create a
router; (4) attach the router to an external network; and (5) add a route to
the router that links with with a subnet. For some providers, any network can
be external (ie, connected to the Internet) while for others it's a specific,
pre-defined one that exists in the an account by default. In order to properly
connect the router, we need to ensure we're using an external network.

When creating the subnet, we need to set an address pool. We can obtain the
private network address space via network object's ``cidr_block`` field (e.g.,
``10.0.0.0/16``). Below, we'll create a subnet starting from the beginning of
the block and allow up to 16 IP addresses into the subnet (``/28``).

.. code-block:: python

    net = provider.network.create('cloudbridge_intro')
    sn = net.create_subnet('10.0.0.0/28', 'cloudbridge-intro')
    router = provider.network.create_router('cloudbridge-intro')
    if not net.external:
        for n in self.provider.network.list():
            if n.external:
                external_net = n
                break
    router.attach_network(external_net.id)
    router.add_route(sn.id)

Retrieve an existing private network
------------------------------------
If you already have existing networks, we can query for those:

.. code-block:: python

    provider.network.list()  # Find a desired network ID
    net = provider.network.get('desired network ID')

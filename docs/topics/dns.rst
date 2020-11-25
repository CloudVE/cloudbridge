DNS Service
===========
The DNS service provides a cloud-independent way to create and edit
dns zones and records.

1. Creating a DNS zone
------------------------
At the top-level, dns records are organized into zones. A zone
is a portion of the dns namespace that's managed by a particular
organization or group.

.. code-block:: python

    host_zone = provider.dns.host_zones.create("cloudve.org.", "admin@cloudve.org")


2. Create a DNS record
----------------------
Once a zone is created, you can create records as required.

.. code-block:: python

    host_zone = provider.dns.host_zones.find(name="cloudve.org.")
    # create an A record
    rec1 = host_zone.records.create("mysubdomain.cloudve.org.", DnsRecordType.A, data='10.1.1.1')
    # create a wildcard record
    rec2 = host_zone.records.create("*.cloudve.org.", DnsRecordType.A, data='10.1.1.2')
    # create an MX record
    MX_DATA = ['10 mx1.hello.com.', '20 mx2.hello.com.']
    test_rec2 = host_zone.records.create("cloudve.org.", DnsRecordType.MX, data=MX_DATA, ttl=300)

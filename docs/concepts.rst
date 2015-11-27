Concepts and Organisation
=========================

Conceptually, CloudBridge consists of the following types of objects.

1. Providers - Represents a connection to a cloud provider, and is
the gateway to using its services.

2. Services - Represents a service provided by a cloud provider,
such as its compute service, block storage service, object storage etc.
Services may in turn be divided into smaller services. Smaller services
tend to have uniform methods, such as create, find and list. For example,
InstanceService.list(), InstanceService.find() etc. which can be used
to access cloud resources. Larger services tend to provide organisational
structure only. For example, the block store service provides access to
the VolumeService and SnapshotService.

3. Resources - resources are objects returned by a service,
and represent a remote resource. For example, InstanceService.list()
will return a list of Instance objects, which can be used to manipulate
an instance. Similarly, VolumeService.create() will return a Volume object.


.. image:: images/object_relationships_overview.svg

The actual source code structure of CloudBridge also mirrors this organisation.

Detailed class relationships
----------------------------

The following diagram shows a typical provider object graph and the relationship
between services.

.. raw:: html

   <object data="_images/object_relationships_detailed.svg" type="image/svg+xml"></object>

Some services are nested. For example, to access the instance service, you can
use `provider.compute.instances`. Similarly, to get a list of all instances,
you can use the following code.

.. code-block:: python

	instances = provider.compute.instances.list()
	print(instances[0].name)
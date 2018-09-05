Concepts and Organisation
=========================

Object types
------------

Conceptually, CloudBridge consists of the following types of objects.

1. Providers - Represents a connection to a cloud provider, and is
the gateway to using its services.

2. Services - Represents a service provided by a cloud provider,
such as its compute service, storage service, networking service etc.
Services may in turn be divided into smaller services. Smaller services
tend to have uniform methods, such as create, find and list. For example,
InstanceService.list(), InstanceService.find() etc. which can be used
to access cloud resources. Larger services tend to provide organisational
structure only. For example, the storage service provides access to
the VolumeService, SnapshotService and BucketService.

3. Resources - resources are objects returned by a service,
and represent a remote resource. For example, InstanceService.list()
will return a list of Instance objects, which can be used to manipulate
an instance. Similarly, VolumeService.create() will return a Volume object.


.. image:: images/object_relationships_overview.svg

The actual source code structure of CloudBridge also mirrors this organisation.

Object identification and naming
---------------------------------

In order to function uniformly across across cloud providers, object identity
and naming must be conceptually consistent. In CloudBridge, there are three
main properties for identifying and naming an object.

1.Id - The `id` corresponds to a unique identifier that can be reliably used to
reference a resource. All CloudBridge resources have an id. Most methods in
CloudBridge services, such as `get`, use the `id` property to identify and
retrieve objects.

2. Name - The `name` property is a more human-readable identifier for
a particular resource, and is often useful to display to the end user instead
of the `id`. While it is often unique, it is not guaranteed to be so, and
therefore, the `id` property must always be used for uniquely identifying
objects. All CloudBridge resources have a `name` property. The `name` property
is often assigned during resource creation, and is often derived from the
`label` property by appending some unique characters to it. Once assigned
however, it is unchangeable.

3. Label - Most resources also support a `label` property, which is a user
changeable value that can be used to describe an object. When creating
resources, cloudbridge often accepts a `label` property as a parameter.
The `name` property is derived from the `label`, by appending some unique
characters to it. However, there are some resources which do not support a
`label` property, such as key pairs and buckets. In the latter case, the
`name` can be specified during resource creation, but cannot be changed
thereafter.


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
"""
Specifications for services available through a provider
"""
from abc import ABCMeta, abstractmethod, abstractproperty

from cloudbridge.cloud.interfaces.resources import PageableObjectMixin


class CloudService(object):

    """
    Base interface for any service supported by a provider. This interface
    has a  provider property that can be used to access the provider associated
    with this service.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def provider(self):
        """
        Returns the provider instance associated with this service.

        :rtype: :class:`.CloudProvider`
        :return: a CloudProvider object
        """
        pass


class ComputeService(CloudService):
    """
    The compute service interface is a collection of services that provides
    access to the underlying compute related services in a provider. For
    example, the compute.instances service can be used to launch a new
    instance, and the compute.images service can be used to list available
    machine images.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def images(self):
        """
        Provides access to all Image related services in this provider.
        (e.g. Glance in OpenStack)

        Example:

        .. code-block:: python

            # print all images
            for image in provider.compute.images:
                print(image.id, image.name)

            # print only first 50 images
            for image in provider.compute.images.list(limit=50):
                print(image.id, image.name)

            # find image by name
            image = provider.compute.images.find(name='Ubuntu 14.04')
            print(image.id, image.name)

        :rtype: :class:`.ImageService`
        :return: an ImageService object
        """
        pass

    @abstractproperty
    def instance_types(self):
        """
        Provides access to all Instance type related services in this provider.

        Example:

        .. code-block:: python

            # list all instance sizes
            for inst_type in provider.compute.instance_types:
                print(inst_type.id, inst_type.name)

            # find a specific size by name
            inst_type = provider.compute.instance_types.find(name='m1.small')
            print(inst_type.vcpus)

        :rtype: :class:`.InstanceTypeService`
        :return: an InstanceTypeService object
        """
        pass

    @abstractproperty
    def instances(self):
        """
        Provides access to all Instance related services in this provider.

        Example:

        .. code-block:: python

            # launch a new instance
            image = provider.compute.images.find(name='Ubuntu 14.04')[0]
            size = provider.compute.instance_types.find(name='m1.small')
            instance = provider.compute.instances.create('Hello', image, size)
            print(instance.id, instance.name)

        :rtype: :class:`.InstanceService`
        :return: an InstanceService object
        """
        pass

    @abstractproperty
    def regions(self):
        """
        Provides access to all Region related services in this provider.

        Example:

        .. code-block:: python

            for region in provider.compute.regions:
                print("Region: ", region.name)
                for zone in region.zones:
                   print("\\tZone: ", zone.name)

        :rtype: :class:`.RegionService`
        :return: a RegionService object
        """
        pass


class InstanceService(PageableObjectMixin, CloudService):
    """
    Provides access to instances in a provider, including creating,
    listing and deleting instances.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __iter__(self):
        """
        Iterate through the  list of instances.

        Example:
        ```
        for instance in provider.compute.instances:
            print(instance.name)
        ```

        :rtype: ``object`` of :class:`.Instance`
        :return:  an Instance object
        """
        pass

    @abstractmethod
    def get(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.

        :rtype: ``object`` of :class:`.Instance`
        :return:  an Instance object
        """
        pass

    @abstractmethod
    def find(self, name):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.Instance`
        :return: an Instance object
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List available instances.

        The returned results can be limited with limit and marker. If not
        specified, the limit defaults to a global default.
        See :func:`~interfaces.resources.PageableObjectMixin.list`
        for more information on how to page through returned results.

        example::

            # List instances
            instlist = provider.compute.instances.list()
            for instance in instlist:
                print("Instance Data: {0}", instance)

        :type  limit: ``int``
        :param limit: The maximum number of objects to return. Note that the
                      maximum is not guaranteed to be honoured, and a lower
                      maximum may be enforced depending on the provider. In
                      such a case, the returned ResultList's is_truncated
                      property can be used to determine whether more records
                      are available.

        :type  marker: ``str``
        :param marker: The marker is an opaque identifier used to assist
                       in paging through very long lists of objects. It is
                       returned on each invocation of the list method.

        :rtype: ``ResultList`` of :class:`.Instance`
        :return: A ResultList object containing a list of Instances
        """
        pass

    @abstractmethod
    def create(self, name, image, instance_type, subnet, zone=None,
               key_pair=None, security_groups=None, user_data=None,
               launch_config=None,
               **kwargs):
        """
        Creates a new virtual machine instance.

        :type  name: ``str``
        :param name: The name of the virtual machine instance

        :type  image: ``MachineImage`` or ``str``
        :param image: The MachineImage object or id to boot the virtual machine
                      with

        :type  instance_type: ``InstanceType`` or ``str``
        :param instance_type: The InstanceType or name, specifying the size of
                              the instance to boot into

        :type  subnet:  ``Subnet`` or ``str``
        :param subnet: The subnet object or a subnet string ID with which the
                       instance should be associated. The subnet is a mandatory
                       parameter, and must be provided when launching an
                       instance.

                       Note: Older clouds (with classic networking), may not
                       have proper subnet support and are not guaranteed to
                       work. Some providers (e.g. OpenStack) support a null
                       value but the behaviour is implementation specific.

        :type  zone: ``Zone`` or ``str``
        :param zone: The Zone or its name, where the instance should be placed.
                     This parameter is provided for legacy compatibility (with
                     classic networks).

                     The subnet's placement zone will take precedence over this
                     parameter, but in its absence, this value will be used.

        :type  key_pair: ``KeyPair`` or ``str``
        :param key_pair: The KeyPair object or its name, to set for the
                         instance.

        :type  security_groups: A ``list`` of ``SecurityGroup`` objects or a
                                list of ``str`` object IDs
        :param security_groups: A list of ``SecurityGroup`` objects or a list
                                of ``SecurityGroup`` IDs, which should be
                                assigned to this instance.

                                The security groups must be associated with the
                                same network as the supplied subnet. Use
                                ``network.security_groups`` to retrieve a list
                                of security groups belonging to a network.

        :type  user_data: ``str``
        :param user_data: An extra userdata object which is compatible with
                          the provider.

        :type  launch_config: ``LaunchConfig`` object
        :param launch_config: A ``LaunchConfig`` object which
               describes advanced launch configuration options for an instance.
               Currently, this includes only block_device_mappings. To
               construct a launch configuration object, call
               provider.compute.instances.create_launch_config()

        :rtype: ``object`` of :class:`.Instance`
        :return:  an instance of Instance class
        """
        pass

    def create_launch_config(self):
        """
        Creates a ``LaunchConfig`` object which can be used
        to set additional options when launching an instance, such as
        block device mappings and network interfaces.

        :rtype: ``object`` of :class:`.LaunchConfig`
        :return:  an instance of a LaunchConfig class
        """
        pass


class VolumeService(PageableObjectMixin, CloudService):
    """
    Base interface for a Volume Service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, volume_id):
        """
        Returns a volume given its id.

        :rtype: ``object`` of :class:`.Volume`
        :return: a Volume object or ``None`` if the volume does not exist.
        """
        pass

    @abstractmethod
    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.

        :rtype: ``object`` of :class:`.Volume`
        :return: a Volume object or ``None`` if not found.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all volumes.

        :rtype: ``list`` of :class:`.Volume`
        :return: a list of Volume objects.
        """
        pass

    @abstractmethod
    def create(self, name, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.

        :type  name: ``str``
        :param name: The name of the volume.

        :type  size: ``int``
        :param size: The size of the volume (in GB).

        :type  zone: ``str`` or :class:`.PlacementZone` object
        :param zone: The availability zone in which the Volume will be created.

        :type  snapshot: ``str`` or :class:`.Snapshot` object
        :param snapshot: An optional reference to a snapshot from which this
                         volume should be created.

        :type  description: ``str``
        :param description: An optional description that may be supported by
                            some providers. Providers that do not support this
                            property will return ``None``.

        :rtype: ``object`` of :class:`.Volume`
        :return: a newly created Volume object.
        """
        pass


class SnapshotService(PageableObjectMixin, CloudService):
    """
    Base interface for a Snapshot Service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, volume_id):
        """
        Returns a snapshot given its id.

        :rtype: ``object`` of :class:`.Snapshot`
        :return: a Snapshot object or ``None`` if the snapshot does not exist.
        """
        pass

    @abstractmethod
    def find(self, name, limit=None, marker=None):
        """
        Searches for a snapshot by a given list of attributes.

        :rtype: list of :class:`.Snapshot`
        :return: a Snapshot object or an empty list if none found.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all snapshots.

        :rtype: ``list`` of :class:`.Snapshot`
        :return: a list of Snapshot objects.
        """
        pass

    @abstractmethod
    def create(self, name, volume, description=None):
        """
        Creates a new snapshot off a volume.

        :type  name: ``str``
        :param name: The name of the snapshot

        :type  volume: ``str`` or ``Volume``
        :param volume: The volume to create a snapshot of.

        :type  description: ``str``
        :param description: An optional description that may be supported by
                            some providers. Providers that do not support this
                            property will return None.

        :rtype: ``object`` of :class:`.Snapshot`
        :return: a newly created Snapshot object.
        """
        pass


class BlockStoreService(CloudService):

    """
    The Block Store Service interface provides access to block device services,
    such as volume and snapshot services in the provider.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def volumes(self):
        """
        Provides access to volumes (i.e., block storage) for this provider.

        Example:

        .. code-block:: python

            # print all volumes
            for vol in provider.block_store.volumes:
                print(vol.id, vol.name)

            # find volume by name
            vol = provider.block_store.volumes.find(name='my_vol')[0]
            print(vol.id, vol.name)

        :rtype: :class:`.VolumeService`
        :return: a VolumeService object
        """
        pass

    @abstractproperty
    def snapshots(self):
        """
        Provides access to volume snapshots for this provider.

        Example:

        .. code-block:: python

            # print all snapshots
            for snap in provider.block_store.snapshots:
                print(snap.id, snap.name)

            # find snapshot by name
            snap = provider.block_store.snapshots.find(name='my_snap')[0]
            print(snap.id, snap.name)

        :rtype: :class:`.SnapshotService`
        :return: an SnapshotService object
        """
        pass


class ImageService(PageableObjectMixin, CloudService):

    """
    Base interface for an Image Service
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, image_id):
        """
        Returns an Image given its id. Returns None if the Image does not
        exist.

        :rtype: ``object`` of :class:`.Image`
        :return:  an Image instance
        """
        pass

    @abstractmethod
    def find(self, name, limit=None, marker=None):
        """
        Searches for an image by a given list of attributes

        :rtype: ``object`` of :class:`.Image`
        :return:  an Image instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all images.

        :rtype: ``list`` of :class:`.Image`
        :return:  list of image objects
        """
        pass


class NetworkService(PageableObjectMixin, CloudService):

    """
    Base interface for a Network Service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, network_id):
        """
        Returns a Network given its ID or ``None`` if not found.

        :type network_id: ``str``
        :param network_id: The ID of the network to retrieve.

        :rtype: ``object`` of :class:`.Network`
        :return: a Network object
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all networks.

        :rtype: ``list`` of :class:`.Network`
        :return: list of Network objects
        """
        pass

    @abstractmethod
    def create(self, name=None):
        """
        Create a new network.

        :type name: ``str``
        :param name: An optional network name. The name will be set if the
                     provider supports it.

        :rtype: ``object`` of :class:`.Network`
        :return:  A Network object
        """
        pass

    @abstractmethod
    def delete(self, network_id):
        """
        Delete an existing Network.

        :type network_id: ``str``
        :param network_id: The ID of the network to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the network does not exist, ``False`` otherwise.
                  Note that this implies that the network may not have been
                  deleted by this method but instead has not existed at all.
        """
        pass

    @abstractproperty
    def subnets(self):
        """
        Provides access to subnets.

        Example:

        .. code-block:: python

            # Print all subnets
            for s in provider.network.subnets:
                print(s.id, s.name)

            # Get subnet by ID
            s = provider.network.subnets.get('subnet-id')
            print(s.id, s.name)

        :rtype: :class:`.SubnetService`
        :return: a SubnetService object
        """
        pass

    @abstractmethod
    def floating_ips(self, network_id=None):
        """
        List floating (i.e., static) IP addresses.

        :type network_id: ``str``
        :param network_id: The ID of the network by which to filter the IPs.

        :rtype: ``list`` of :class:`FloatingIP`
        :return: list of floating IP objects
        """
        pass

    @abstractmethod
    def create_floating_ip(self):
        """
        Allocate a new floating (i.e., static) IP address.

        :type network_id: ``str``
        :param network_id: The ID of the network with which to associate the
                           new IP address.

        :rtype: :class:`FloatingIP`
        :return: floating IP object
        """
        pass

    @abstractmethod
    def routers(self):
        """
        Get a list of available routers.

        :rtype: ``list`` of :class: `Router`
        :return: list of routers
        """
        pass

    @abstractmethod
    def create_router(self, name=None):
        """
        Create a new router/gateway.

        :type name: ``str``
        :param name: An optional router name. The name will be set if the
                     provider supports it.

        :rtype: :class:`Router`
        :return: a newly created router object
        """
        pass


class SubnetService(PageableObjectMixin, CloudService):

    """
    Base interface for a Subnet Service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, subnet_id):
        """
        Returns a Subnet given its ID or ``None`` if not found.

        :type network_id: :class:`.Network` object or ``str``
        :param network_id: The ID of the subnet to retrieve.

        :rtype: ``object`` of :class:`.Subnet`
        return: a Subnet object
        """
        pass

    @abstractmethod
    def list(self, network=None, limit=None, marker=None):
        """
        List all subnets or filter them by the supplied network ID.

        :type network: ``str``
        :param network: Network object or ID with which to filter the subnets.

        :rtype: ``list`` of :class:`.Subnet`
        :return: list of Subnet objects
        """
        pass

    @abstractmethod
    def create(self, network_id, cidr_block, name=None, zone=None):
        """
        Create a new subnet within the supplied network.

        :type network: :class:`.Network` object or ``str``
        :param network: Network object or ID under which to create the subnet.

        :type cidr_block: ``str``
        :param cidr_block: CIDR block within the Network to assign to the
                           subnet.

        :type name: ``str``
        :param name: An optional subnet name. The name will be set if the
                     provider supports it.

        :type zone: ``str``
        :param zone: An optional placement zone for the subnet. Some providers
                     may not support this, in which case the value is ignored.

        :rtype: ``object`` of :class:`.Subnet`
        :return:  A Subnet object
        """
        pass

    @abstractmethod
    def get_or_create_default(self, zone=None):
        """
        Return a default subnet for the account or create one if not found.

        A default network is one marked as such by the provider or matches the
        default name used by this library (e.g., CloudBridgeNet).

        If this method creates a new subnet, it will create one in each zone
        available from the provider.

        :type zone: ``str``
        :param zone: Placement zone where to look for the subnet. If not
                     supplied, a subnet from random zone will be selected.

        :rtype: ``object`` of :class:`.Subnet`
        :return: A Subnet object
        """
        pass

    @abstractmethod
    def delete(self, subnet):
        """
        Delete an existing Subnet.

        :type subnet: :class:`.Subnet` object or ``str``
        :param subnet: Subnet object or ID of the subnet to delete.

        :rtype: ``bool``
        :return:  ``True`` if the subnet does not exist, ``False`` otherwise.
                  Note that this implies that the subnet may not have been
                  deleted by this method but instead has not existed at all.
        """
        pass


class ObjectStoreService(PageableObjectMixin, CloudService):

    """
    The Object Storage Service interface provides access to the underlying
    object store capabilities of this provider. This service is optional and
    the :func:`CloudProvider.has_service()` method should be used to verify its
    availability before using the service.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist. On some providers, such as AWS and OpenStack,
        the bucket id is the same as its name.

        Example:

        .. code-block:: python

            bucket = provider.object_store.get('my_bucket_id')
            print(bucket.id, bucket.name)

        :rtype: :class:`.Bucket`
        :return:  a Bucket instance
        """
        pass

    @abstractmethod
    def find(self, name):
        """
        Searches for a bucket by a given list of attributes.

        Example:

        .. code-block:: python

            buckets = provider.object_store.find(name='my_bucket_name')
            for bucket in buckets:
                print(bucket.id, bucket.name)

        :rtype: :class:`.Bucket`
        :return:  a Bucket instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all buckets.

        Example:

        .. code-block:: python

            buckets = provider.object_store.find(name='my_bucket_name')
            for bucket in buckets:
                print(bucket.id, bucket.name)

        :rtype: :class:`.Bucket`
        :return:  list of bucket objects
        """
        pass

    @abstractmethod
    def create(self, name, location=None):
        """
        Create a new bucket.

        If a bucket with the specified name already exists, return a reference
        to that bucket.

        Example:

        .. code-block:: python

            bucket = provider.object_store.create('my_bucket_name')
            print(bucket.name)


        :type name: str
        :param name: The name of this bucket.

        :type location: ``object`` of :class:`.Region`
        :param location: The region in which to place this bucket.

        :return:  a Bucket object
        :rtype: ``object`` of :class:`.Bucket`
        """
        pass


class SecurityService(CloudService):

    """
    The security service interface can be used to access security related
    functions in the provider, such as firewall control and keypairs.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        Example:

        .. code-block:: python

            # print all keypairs
            for kp in provider.security.keypairs:
                print(kp.id, kp.name)

            # find keypair by name
            kp = provider.security.keypairs.find(name='my_key_pair')[0]
            print(kp.id, kp.name)

        :rtype: :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        pass

    @abstractproperty
    def security_groups(self):
        """
        Provides access to security groups for this provider.

        Example:

        .. code-block:: python

            # print all security groups
            for sg in provider.security.security_groups:
                print(sg.id, sg.name)

            # find security group by name
            sg = provider.security.security_groups.find(name='my_sg')[0]
            print(sg.id, sg.name)

        :rtype: :class:`.SecurityGroupService`
        :return: a SecurityGroupService object
        """
        pass


class KeyPairService(PageableObjectMixin, CloudService):

    """
    Base interface for key pairs.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, key_pair_id):
        """
        Return a KeyPair given its ID or ``None`` if not found.

        On some providers, such as AWS and OpenStack, the KeyPair ID is
        the same as its name.

        Example:

        .. code-block:: python

            key_pair = provider.security.keypairs.get('my_key_pair_id')
            print(key_pair.id, key_pair.name)

        :rtype: :class:`.KeyPair`
        :return:  a KeyPair instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        pass

    @abstractmethod
    def find(self, name, limit=None, marker=None):
        """
        Searches for a key pair by a given list of attributes.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  a KeyPair object
        """
        pass

    @abstractmethod
    def create(self, name):
        """
        Create a new key pair or raise an exception if one already exists.

        :type name: str
        :param name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance or ``None``.
        """
        pass

    @abstractmethod
    def delete(self, key_pair_id):
        """
        Delete an existing SecurityGroup.

        :type key_pair_id: str
        :param key_pair_id: The id of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist, ``False`` otherwise. Note
                  that this implies that the key may not have been deleted by
                  this method but instead has not existed at all.
        """
        pass


class SecurityGroupService(PageableObjectMixin, CloudService):

    """
    Base interface for security groups.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, security_group_id):
        """
        Returns a SecurityGroup given its ID. Returns ``None`` if the
        SecurityGroup does not exist.

        Example:

        .. code-block:: python

            sg = provider.security.security_groups.get('my_sg_id')
            print(sg.id, sg.name)

        :rtype: :class:`.SecurityGroup`
        :return:  a SecurityGroup instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        pass

    @abstractmethod
    def create(self, name, description, network_id):
        """
        Create a new SecurityGroup.

        :type name: str
        :param name: The name of the new security group.

        :type description: str
        :param description: The description of the new security group.

        :type  network_id: ``str``
        :param network_id: Network ID under which to create the security group.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return:  A SecurityGroup instance or ``None`` if one was not created.
        """
        pass

    @abstractmethod
    def find(self, name, limit=None, marker=None):
        """
        Get security groups associated with your account filtered by name.

        :type name: str
        :param name: The name of the security group to retrieve.

        :rtype: list of :class:`SecurityGroup`
        :return: A list of SecurityGroup objects or an empty list if none
                 found.
        """
        pass

    @abstractmethod
    def delete(self, group_id):
        """
        Delete an existing SecurityGroup.

        :type group_id: str
        :param group_id: The security group ID to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the security group does not exist, ``False``
                  otherwise. Note that this implies that the group may not have
                  been deleted by this method but instead has not existed in
                  the first place.
        """
        pass


class InstanceTypesService(PageableObjectMixin, CloudService):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, instance_type_id):
        """
        Returns an InstanceType given its ID. Returns ``None`` if the
        InstanceType does not exist.

        Example:

        .. code-block:: python

            itype = provider.compute.instance_types.get('my_itype_id')
            print(itype.id, itype.name)

        :rtype: :class:`.InstanceType`
        :return:  an InstanceType instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all instance types.

        :rtype: ``list`` of :class:`.InstanceType`
        :return: list of InstanceType objects
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.InstanceType`
        :return: an Instance object
        """
        pass


class RegionService(PageableObjectMixin, CloudService):

    """
    Base interface for a Region service
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def current(self):
        """
        Returns the current region that this provider is connected to.

        If the current region cannot be discovered, return ``None``.

        :rtype: ``object`` of :class:`.Region`
        :return:  a Region instance or ``None``
        """
        pass

    @abstractmethod
    def get(self, region_id):
        """
        Returns a region given its id. Returns None if the region
        does not exist.

        :rtype: ``object`` of :class:`.Region`
        :return:  a Region instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all regions.

        :rtype: ``list`` of :class:`.Region`
        :return:  list of region objects
        """
        pass

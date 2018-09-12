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
                print(image.id, image.name, image.label)

            # print only first 50 images
            for image in provider.compute.images.list(limit=50):
                print(image.id, image.name, image.label)

            # find image by name
            image = provider.compute.images.find(name='Ubuntu 16.04')[0]
            print(image.id, image.name, image.label)

        :rtype: :class:`.ImageService`
        :return: an ImageService object
        """
        pass

    @abstractproperty
    def vm_types(self):
        """
        Provides access to all VM type related services in this provider.

        Example:

        .. code-block:: python

            # list all VM sizes
            for vm_type in provider.compute.vm_types:
                print(vm_type.id, vm_type.name)

            # find a specific size by name
            vm_type = provider.compute.vm_types.find(name='m1.small')[0]
            print(vm_type.vcpus)

        :rtype: :class:`.VMTypeService`
        :return: an VMTypeService object
        """
        pass

    @abstractproperty
    def instances(self):
        """
        Provides access to all Instance related services in this provider.

        Example:

        .. code-block:: python

            # launch a new instance
            image = provider.compute.images.find(name='Ubuntu 16.04')[0]
            size = provider.compute.vm_types.find(name='m1.small')
            instance = provider.compute.instances.create('Hello', image, size)
            print(instance.id, instance.label)

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
    def find(self, **kwargs):
        """
        Searches for an instance by a given list of attributes.

        Supported attributes: name, label

        :type  name: ``str``
        :param name: The name to search for

        :type  label: ``str``
        :param label: The label to search for

        :rtype: List of ``object`` of :class:`.Instance`
        :return: A list of Instance objects matching the supplied attributes.
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
    def create(self, label, image, vm_type, subnet, zone=None,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None,
               **kwargs):
        """
        Creates a new virtual machine instance.

        :type  label: ``str``
        :param label: The label of the virtual machine instance. The instance
                      name will be derived from this label.

        :type  image: ``MachineImage`` or ``str``
        :param image: The MachineImage object or id to boot the virtual machine
                      with

        :type  vm_type: ``VMType`` or ``str``
        :param vm_type: The VMType or name, specifying the size of
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
        :param zone: The Zone or its id, where the instance should be placed.
                     This parameter is provided for legacy compatibility (with
                     classic networks).

                     The subnet's placement zone will take precedence over this
                     parameter, but in its absence, this value will be used.

        :type  key_pair: ``KeyPair`` or ``str``
        :param key_pair: The KeyPair object or its id, to set for the
                         instance.

        :type  vm_firewalls: A ``list`` of ``VMFirewall`` objects or a
                             list of ``str`` object IDs
        :param vm_firewalls: A list of ``VMFirewall`` objects or a list
                             of ``VMFirewall`` IDs, which should be
                             assigned to this instance.

                             The VM firewalls must be associated with the
                             same network as the supplied subnet. Use
                             ``network.vm_firewalls`` to retrieve a list
                             of firewalls belonging to a network.

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
    def find(self, **kwargs):
        """
        Searches for a volume by a given list of attributes.

        Supported attributes: label

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
    def create(self, label, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.

        :type  label: ``str``
        :param label: The label for the volume.

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
    def find(self, **kwargs):
        """
        Searches for a snapshot by a given list of attributes.

        Supported attributes: label

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
    def create(self, label, volume, description=None):
        """
        Creates a new snapshot off a volume.

        :type  label: ``str``
        :param label: The label for the snapshot.

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


class StorageService(CloudService):

    """
    The Storage Service interface provides access to block device services,
    such as volume and snapshot services, as well as object store services,
    such as buckets, in the provider.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def volumes(self):
        """
        Provides access to volumes (i.e., block storage) for this provider.

        Example:

        .. code-block:: python

            # print all volumes
            for vol in provider.storage.volumes:
                print(vol.id, vol.name, vol.label)

            # find volume by label
            vol = provider.storage.volumes.find(label='my_vol')[0]
            print(vol.id, vol.name, vol.label)

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
            for snap in provider.storage.snapshots:
                print(snap.id, snap.name, snap.label)

            # find snapshot by label
            snap = provider.storage.snapshots.find(label='my_snap')[0]
            print(snap.id, snap.name, snap.label)

        :rtype: :class:`.SnapshotService`
        :return: a SnapshotService object
        """
        pass

    @abstractproperty
    def buckets(self):
        """
        Provides access to object storage services in this provider.

        Example:

        .. code-block:: python

            # print all buckets
            for bucket in provider.storage.buckets:
                print(bucket.id, bucket.name)

            # find bucket by name
            bucket = provider.storage.buckets.find(name='my_bucket')[0]
            print(bucket.id, bucket.name)

        :rtype: :class:`.BucketService`
        :return: a BucketService object
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
    def find(self, **kwargs):
        """
        Searches for an image by a given list of attributes

        Supported attributes: name, label

        :rtype: ``object`` of :class:`.Image`
        :return:  an Image instance
        """
        pass

    @abstractmethod
    def list(self, filter_by_owner=True, limit=None, marker=None):
        """
        List all images.

        :type  filter_by_owner: ``bool``
        :param filter_by_owner: If ``True``, return only images owned
                                by the current user. Else, return all
                                public images available from the provider.
                                Note that fetching all images may take a
                                long time.

        :rtype: ``list`` of :class:`.Image`
        :return:  list of image objects
        """
        pass


class NetworkingService(CloudService):
    """
    Base service interface for networking.

    This service offers a collection of networking services that in turn
    provide access to networking resources.
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def networks(self):
        """
        Provides access to all Network related services.

        :rtype: :class:`.NetworkService`
        :return: a Network service object
        """
        pass

    @abstractproperty
    def subnets(self):
        """
        Provides access to all Subnet related services.

        :rtype: :class:`.SubnetService`
        :return: a Subnet service object
        """
        pass

    @abstractproperty
    def routers(self):
        """
        Provides access to all Router related services.

        :rtype: :class:`.RouterService`
        :return: a Router service object
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
    def find(self, **kwargs):
        """
        Searches for a network by a given list of attributes.

        Supported attributes: name, label

        :rtype: List of ``object`` of :class:`.Network`
        :return: A list of Network objects matching the supplied attributes.
        """
        pass

    @abstractmethod
    def create(self, label, cidr_block):
        """
        Create a new network.

        :type label: ``str``
        :param label: A label for the network.

        :type cidr_block: ``str``
        :param cidr_block: The cidr block for this network. Some providers
                           will respect this at the network level, while others
                           will only respect it at subnet level. However, to
                           write portable code, you should make sure that any
                           subnets you create fall within this initially
                           specified range. Note that the block size should be
                           between a /16 netmask (65,536 IP addresses) and /28
                           netmask (16 IP addresses). e.g. 10.0.0.0/16

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
        """
        pass

    @abstractproperty
    def subnets(self):
        """
        Provides access to subnets.

        Example:

        .. code-block:: python

            # Print all subnets
            for s in provider.networking.subnets:
                print(s.id, s.name, s.label)

            # Get subnet by ID
            s = provider.networking.subnets.get('subnet-id')
            print(s.id, s.name, s.label)

        :rtype: :class:`.SubnetService`
        :return: a SubnetService object
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

        :type subnet_id: :class:`.Network` object or ``str``
        :param subnet_id: The ID of the subnet to retrieve.

        :rtype: ``object`` of :class:`.Subnet`
        return: a Subnet object
        """
        pass

    @abstractmethod
    # pylint:disable=arguments-differ
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
    def find(self, **kwargs):
        """
        Searches for a subnet by a given list of attributes.

        Supported attributes: name, label

        :rtype: List of ``object`` of :class:`.Subnet`
        :return: A list of Subnet objects matching the supplied attributes.
        """
        pass

    @abstractmethod
    def create(self, label, network_id, cidr_block, zone):
        """
        Create a new subnet within the supplied network.

        :type label: ``str``
        :param label: The subnet label.

        :type network: :class:`.Network` object or ``str``
        :param network: Network object or ID under which to create the subnet.

        :type cidr_block: ``str``
        :param cidr_block: CIDR block within the Network to assign to the
                           subnet.

        :type zone: ``str``
        :param zone: A placement zone for the subnet. Some providers
                     may not support this, in which case the value is ignored.

        :rtype: ``object`` of :class:`.Subnet`
        :return:  A Subnet object
        """
        pass

    @abstractmethod
    def get_or_create_default(self, zone):
        """
        Return a default subnet for the account or create one if not found.
        This provides a convenience method for obtaining a network if you
        are not particularly concerned with how the network is structured.

        A default network is one marked as such by the provider or matches the
        default label used by this library (e.g., cloudbridge-net).

        :type zone: :class:`.PlacementZone` object ``str``
        :param zone: Placement zone where to look for the subnet.

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
        """
        pass


class RouterService(PageableObjectMixin, CloudService):
    """
    Manage networking router actions and resources.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, router_id):
        """
        Returns a Router object given its ID.

        :type router_id: ``str``
        :param router_id: The ID of the router to retrieve.

        :rtype: ``object``  of :class:`.Router` or ``None``
        :return: a Router object of ``None`` if not found.
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all routers.

        :rtype: ``list`` of :class:`.Router`
        :return: list of Router objects
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for a router by a given list of attributes.

        Supported attributes: label

        :rtype: List of ``object`` of :class:`.Router`
        :return: A list of Router objects matching the supplied attributes.
        """
        pass

    @abstractmethod
    def create(self, label, network):
        """
        Create a new router.

        :type label: ``str``
        :param label: A router label.

        :type network: :class:`.Network` object or ``str``
        :param network: Network object or ID under which to create the router.

        :rtype: ``object`` of :class:`.Router`
        :return:  A Router object
        """
        pass

    @abstractmethod
    def delete(self, router):
        """
        Delete an existing Router.

        :type router: :class:`.Router` object or ``str``
        :param router: Router object or ID of the router to delete.
        """
        pass


class BucketService(PageableObjectMixin, CloudService):

    """
    The Bucket Service interface provides access to the underlying
    object storage capabilities of this provider. This service is optional and
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

            bucket = provider.storage.buckets.get('my_bucket_id')
            print(bucket.id, bucket.name)

        :rtype: :class:`.Bucket`
        :return:  a Bucket instance
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for a bucket by a given list of attributes.

        Supported attributes: name

        Example:

        .. code-block:: python

            buckets = provider.storage.buckets.find(name='my_bucket_name')
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

            buckets = provider.storage.buckets.find(name='my_bucket_name')
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

            bucket = provider.storage.buckets.create('my_bucket_name')
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
    def vm_firewalls(self):
        """
        Provides access to firewalls (security groups) for this provider.

        Example:

        .. code-block:: python

            # print all VM firewalls
            for fw in provider.security.vm_firewalls:
                print(fw.id, fw.name)

            # find firewall by name
            fw = provider.security.vm_firewalls.find(name='my_vm_fw')[0]
            print(fw.id, fw.name)

        :rtype: :class:`.VMFirewallService`
        :return: a VMFirewallService object
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
    def find(self, **kwargs):
        """
        Searches for a key pair by a given list of attributes.

        Supported attributes: name

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  a KeyPair object
        """
        pass

    @abstractmethod
    def create(self, name, public_key_material=None):
        """
        Create a new key pair or raise an exception if one already exists.
        If the public_key_material is provided, the material will be imported
        to create the new keypair. Otherwise, a new public and private key
        pair will be generated.

        :type name: str
        :param name: The name of the key pair to be created.

        :type public_key_material: str
        :param public_key_material: The key-pair material to import in OpenSSH
                                    format.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance or ``None``.
        """
        pass

    @abstractmethod
    def delete(self, key_pair_id):
        """
        Delete an existing VMFirewall.

        :type key_pair_id: str
        :param key_pair_id: The id of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist, ``False`` otherwise. Note
                  that this implies that the key may not have been deleted by
                  this method but instead has not existed at all.
        """
        pass


class VMFirewallService(PageableObjectMixin, CloudService):

    """
    Base interface for VM firewalls.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, vm_firewall_id):
        """
        Returns a VMFirewall given its ID. Returns ``None`` if the
        VMFirewall does not exist.

        Example:

        .. code-block:: python

            fw = provider.security.vm_firewalls.get('my_fw_id')
            print(fw.id, fw.name)

        :rtype: :class:`.VMFirewall`
        :return:  a VMFirewall instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all VM firewalls associated with this account.

        :rtype: ``list`` of :class:`.VMFirewall`
        :return:  list of VMFirewall objects
        """
        pass

    @abstractmethod
    def create(self, label, network_id, description=None):
        """
        Create a new VMFirewall.

        :type label: str
        :param label: The label for the new VM firewall.

        :type  network_id: ``str``
        :param network_id: Network ID under which to create the VM firewall.

        :type description: str
        :param description: The description of the new VM firewall.

        :rtype: ``object`` of :class:`.VMFirewall`
        :return:  A VMFirewall instance or ``None`` if one was not created.
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Get VM firewalls associated with your account filtered by name.

        Supported attributes: name

        :type name: str
        :param name: The name of the VM firewall to retrieve.

        :rtype: list of :class:`VMFirewall`
        :return: A list of VMFirewall objects or an empty list if none
                 found.
        """
        pass

    @abstractmethod
    def delete(self, group_id):
        """
        Delete an existing VMFirewall.

        :type group_id: str
        :param group_id: The VM firewall ID to be deleted.
        """
        pass


class VMTypeService(PageableObjectMixin, CloudService):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, vm_type_id):
        """
        Returns an VMType given its ID. Returns ``None`` if the
        VMType does not exist.

        Example:

        .. code-block:: python

            vm_type = provider.compute.vm_types.get('my_vm_type_id')
            print(vm_type.id, vm_type.name)

        :rtype: :class:`.VMType`
        :return:  an VMType instance
        """
        pass

    @abstractmethod
    def list(self, limit=None, marker=None):
        """
        List all VM types.

        :rtype: ``list`` of :class:`.VMType`
        :return: list of VMType objects
        """
        pass

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for an instance by a given list of attributes.

        Supported attributes: name

        :rtype: ``object`` of :class:`.VMType`
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

    @abstractmethod
    def find(self, **kwargs):
        """
        Searches for a region by a given list of attributes.

        Supported attributes: name

        :rtype: ``object`` of :class:`.Region`
        :return: a Region object
        """
        pass

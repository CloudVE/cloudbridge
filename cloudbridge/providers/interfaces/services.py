"""
Specifications for services available through a provider
"""


class ProviderService(object):

    """
    Base interface for any service supported by a provider
    """

    def provider(self):
        """
        Returns the provider instance associated with this service.

        :rtype: ``object`` of :class:`.CloudProvider`
        :return: a Provider object
        """
        raise NotImplementedError(
            'ComputeService.Provider not implemented by this provider')


class ComputeService(ProviderService):

    """
    Base interface for compute service supported by a provider
    """

    def get_instance(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.

        :rtype: ``object`` of :class:`.Instance`
        :return:  an Instance object
        """
        raise NotImplementedError(
            'get_instance not implemented by this provider')

    def find_instance(self, name):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.Instance`
        :return: an Instance object
        """
        raise NotImplementedError(
            'find_instance not implemented by this provider')

    def list_instances(self):
        """
        List all instances.

        :rtype: ``list`` of :class:`.Instance`
        :return: list of Instance objects
        """
        raise NotImplementedError(
            'list_instances not implemented by this provider')

    def instance_types(self):
        """
        Provides access to all Instance type related services in this provider.

        :rtype: ``object`` of :class:`.InstanceTypeService`
        :return:  an InstanceTypeService object
        """
        raise NotImplementedError(
            'instance_types not implemented by this provider')

    def list_regions(self):
        """
        List all data center regions for this provider.

        :rtype: ``list`` of :class:`.Region`
        :return: list of Region objects
        """
        raise NotImplementedError(
            'list_regions not implemented by this provider')

    def create_instance(self, name, image, instance_type, zone=None,
                        keypair=None, security_groups=None, user_data=None,
                        block_device_mapping=None, network_interfaces=None,
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

        :type  zone: ``Zone`` or ``str``
        :param zone: The Zone or its name, where the instance should be placed.

        :type  keypair: ``KeyPair`` or ``str``
        :param keypair: The KeyPair object or its name, to set for the
        instance.

        :type  security_groups: A ``list`` of ``SecurityGroup`` objects or a
                                list of ``str`` names
        :param security_groups: A list of ``SecurityGroup`` objects or a list
                                of ``SecurityGroup`` names, which should be
                                assigned to this instance.

        :type  user_data: ``str``
        :param user_data: An extra userdata object which is compatible with
                          the provider.

        :type  block_device_mapping: ``BlockDeviceMapping`` object
        :param block_device_mapping: A ``BlockDeviceMapping`` object which
                                     describes additional block device mappings
                                     for this instance.

        :type  network_interfaces: ``NetworkInterfaceList`` object
        :param network_interfaces: A ``NetworkInterfaceList`` object which
                                   describes network interfaces for this
                                   instance.

        :rtype: `object`` of :class:`.Instance`
        :return:  an instance of Instance class
        """
        raise NotImplementedError(
            'create_instance not implemented by this provider')


class VolumeService(ProviderService):

    """
    Base interface for a Volume Service
    """

    def get_volume(self, volume_id):
        """
        Returns a volume given its id. Returns None if the volume
        does not exist.

        :rtype: ``object`` of :class:`.Volume`
        :return: a Volume object
        """
        raise NotImplementedError(
            'get_volume not implemented by this provider')

    def find_volume(self, name):
        """
        Searches for a volume by a given list of attributes.

        :rtype: ``object`` of :class:`.Volume`
        :return: a Volume object or ``None`` if not found
        """
        raise NotImplementedError(
            'find_volume not implemented by this provider')

    def list_volumes(self):
        """
        List all volumes.

        :rtype: ``list`` of :class:`.Volume`
        :return: a list of Volume objects
        """
        raise NotImplementedError(
            'list_volumes not implemented by this provider')

    def create_volume(self, name, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.

        :type  name: ``str``
        :param name: The name of the volume

        :type  size: ``int``
        :param size: The size of the volume (in GB)

        :type  zone: ``str`` or ``PlacementZone``
        :param zone: The availability zone in which the Volume will be created.

        :type  description: ``str``
        :param description: An optional description that may be supported by
        some providers. Providers that do not support this property will return
        None.

        :rtype: ``object`` of :class:`.Volume`
        :return: a newly created Volume object
        """
        raise NotImplementedError(
            'create_volume not implemented by this provider')


class SnapshotService(ProviderService):

    """
    Base interface for a Snapshot Service
    """

    def get_snapshot(self, volume_id):
        """
        Returns a snapshot given its id. Returns None if the snapshot
        does not exist.

        :rtype: ``object`` of :class:`.Snapshot`
        :return: a Snapshot object
        """
        raise NotImplementedError(
            'get_snapshot not implemented by this provider')

    def find_snapshot(self, name):
        """
        Searches for a snapshot by a given list of attributes.

        :rtype: ``object`` of :class:`.Snapshot`
        :return: a Snapshot object or ``None`` if not found
        """
        raise NotImplementedError(
            'find_snapshot not implemented by this provider')

    def list_snapshots(self):
        """
        List all snapshots.

        :rtype: ``list`` of :class:`.Snapshot`
        :return: a list of Snapshot objects
        """
        raise NotImplementedError(
            'list_snapshots not implemented by this provider')

    def create_snapshot(self, name, volume, description=None):
        """
        Creates a new snapshot off a volume.

        :type  name: ``str``
        :param name: The name of the snapshot

        :type  volume: ``str`` or ``Volume``
        :param volume: The volume to create a snapshot of.

        :type  description: ``str``
        :param description: An optional description that may be supported by
        some providers. Providers that do not support this property will return
        None.

        :rtype: ``object`` of :class:`.Snapshot`
        :return: a newly created Snapshot object
        """
        raise NotImplementedError(
            'create_snapshot not implemented by this provider')


class BlockStoreService(ProviderService):

    """
    Base interface for a Block Store Service
    """

    @property
    def volumes(self):
        """
        Provides access to the volumes (i.e., block storage) for this provider.

        :rtype: ``object`` of :class:`.VolumeService`
        :return: a VolumeService object
        """
        raise NotImplementedError(
            'CloudProvider.block_store not implemented by this provider')

    @property
    def snapshots(self):
        """
        Provides access to volume snapshots for this provider.

        :rtype: ``object`` of :class:`.SnapshotService`
        :return: an SnapshotService object
        """
        raise NotImplementedError(
            'CloudProvider.object_store not implemented by this provider')


class ImageService(ProviderService):

    """
    Base interface for an Image Service
    """

    def get_image(self, image_id):
        """
        Returns an Image given its id. Returns None if the Image does not
        exist.

        :rtype: ``object`` of :class:`.Image`
        :return:  an Image instance
        """
        raise NotImplementedError(
            'get_image implemented by this provider')

    def find_image(self, name):
        """
        Searches for an image by a given list of attributes

        :rtype: ``object`` of :class:`.Image`
        :return:  an Image instance
        """
        raise NotImplementedError(
            'find_image not implemented by this provider')

    def list_images(self):
        """
        List all images.

        :rtype: ``list`` of :class:`.Image`
        :return:  list of image objects
        """
        raise NotImplementedError(
            'list_images not implemented by this provider')


class ObjectStoreService(ProviderService):

    """
    Base interface for an Object Storage Service
    """

    def get_container(self, container_id):
        """
        Returns a container given its id. Returns None if the container
        does not exist.

        :rtype: ``object`` of :class:`.Container`
        :return:  a Container instance
        """
        raise NotImplementedError(
            'get_container implemented by this provider')

    def find_container(self, name):
        """
        Searches for a container by a given list of attributes

        :rtype: ``object`` of :class:`.Container`
        :return:  a Container instance
        """
        raise NotImplementedError(
            'find_container not implemented by this provider')

    def list_containers(self):
        """
        List all containers.

        :rtype: ``list`` of :class:`.Container`
        :return:  list of container objects
        """
        raise NotImplementedError(
            'list_containers not implemented by this provider')

    def create_container(self, name, location=None):
        """
        Create a new container.

        :type name: str
        :param name: The name of this container

        :type location: ``object`` of :class:`.Region`
        :param location: The region in which to place this container

        :return:  a Container object
        :rtype: ``object`` of :class:`.Container`
        """
        raise NotImplementedError(
            'create_container not implemented by this provider')


class SecurityService(ProviderService):

    """
    Base interface for a Security Service.
    """

    @property
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        :rtype: ``object`` of :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        return self._key_pairs

    @property
    def security_groups(self):
        """
        Provides access to security groups for this provider.

        :rtype: ``object`` of :class:`.SecurityGroupService`
        :return: a SecurityGroupService object
        """
        return self._security_groups


class KeyPairService(ProviderService):

    """
    Base interface for key pairs.
    """

    def list(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        raise NotImplementedError(
            'list_key_pairs not implemented by this provider')

    def create(self, key_name):
        """
        Create a new keypair.

        :type key_name: str
        :param key_name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance
        """
        raise NotImplementedError(
            'create_key_pair not implemented by this provider')

    def delete(self, key_name):
        """
        Delete an existing SecurityGroup.

        :type key_name: str
        :param key_name: The name of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist, ``False`` otherwise. Note
                  that this implies that the key may not have been deleted by
                  this method but instead has not existed at all.
        """
        raise NotImplementedError(
            'delete not implemented by this provider')


class SecurityGroupService(ProviderService):

    """
    Base interface for security groups.
    """

    def list(self):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        raise NotImplementedError(
            'list not implemented by this provider')

    def create(self, name, description):
        """
        Create a new SecurityGroup.

        :type name: str
        :param name: The name of the new security group.

        :type description: str
        :param description: The description of the new security group.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return:  A SecurityGroup instance or ``None`` if one was not created.
        """
        raise NotImplementedError(
            'create not implemented by this provider')

    def get(self, group_names=None, group_ids=None):
        """
        Get all security groups associated with your account.

        :type group_names: list
        :param group_names: A list of the names of security groups to retrieve.
                           If not provided, all security groups will be
                           returned.

        :type group_ids: list
        :param group_ids: A list of IDs of security groups to retrieve.
                          If not provided, all security groups will be
                          returned.

        :rtype: list of :class:`SecurityGroup`
        :return: A list of SecurityGroup objects or an empty list if none
        found.
        """
        raise NotImplementedError(
            'get not implemented by this provider')

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
        raise NotImplementedError(
            'delete not implemented by this provider')


class InstanceTypesService(object):

    def list(self):
        """
        List all instance types.

        :rtype: ``list`` of :class:`.InstanceType`
        :return: list of InstanceType objects
        """
        raise NotImplementedError(
            'InstanceTypesService.list not implemented by this provider')

    def find_by_name(self, name):
        """
        Searches for an instance by a given list of attributes.

        :rtype: ``object`` of :class:`.InstanceType`
        :return: an Instance object
        """
        raise NotImplementedError(
            'InstanceTypesService.find_instance not implemented by this'
            'provider')

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

    def get_instance(self, id):
        """
        Returns an instance given its id.

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

    def create_instance(self, name, image, instance_type, zone=None, keypair=None, security_groups=None,
                        user_data=None, block_device_mapping=None, network_interfaces=None, **kwargs):
        """
        Creates a new virtual machine instance.

        :type  name: ``str``
        :param name: The name of the virtual machine instance

        :type  image: ``MachineImage`` or ``str``
        :param image: The MachineImage object or id to boot the virtual machine with

        :type  instance_type: ``InstanceType`` or ``str``
        :param instance_type: The InstanceType or name, specifying the size of
                              the instance to boot into

        :type  zone: ``Zone`` or ``str``
        :param zone: The Zone or its name, where the instance should be placed.

        :type  keypair: ``KeyPair`` or ``str``
        :param keypair: The KeyPair object or its name, to set for the instance.

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

    def get_volume(self, id):
        """
        Returns a volume given its id.

        :rtype: ``object`` of :class:`.Volume`
        :return: a Volume object
        """
        raise NotImplementedError(
            'get_volume not implemented by this provider')

    def find_volume(self, name):
        """
        Searches for a volume by a given list of attributes.

        :rtype: ``object`` of :class:`.Instance`
        :return: an Instance object or ``None`` if not found
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

    def list_volume_snapshots(self):
        """
        List all volume snapshots.

        :rtype: ``list`` of :class:`.Snapshot`
        :return: a list of Snapshot objects
        """
        raise NotImplementedError(
            'list_volume_snapshots not implemented by this provider')

    def create_volume(self):
        """
        Creates a new volume.

        :rtype: ``list`` of :class:`.Volume`
        :return: a newly created Volume object
        """
        raise NotImplementedError(
            'create_volume not implemented by this provider')


class ImageService(ProviderService):

    """
    Base interface for an Image Service
    """

    def get_image(self, id):
        """
        Returns an Image given its id

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

    def get_container(self, id):
        """
        Returns a container given its id

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

    def create_container(self):
        """
        Create a new container.
        :return:  a Container object
        :rtype: ``object`` of :class:`.Container`
        """
        raise NotImplementedError(
            'create_container not implemented by this provider')


class SecurityService(ProviderService):

    """
    Base interface for an Image Service
    """

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        raise NotImplementedError(
            'list_key_pairs not implemented by this provider')

    def create_key_pair(self):
        """
        Create a new keypair.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance
        """
        raise NotImplementedError(
            'create_key_pair not implemented by this provider')

    def list_security_groups(self):
        """
        Create a new SecurityGroup.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return:  A SecurityGroup instance
        """
        raise NotImplementedError(
            'list_security_groups not implemented by this provider')

    def create_security_group(self):
        """
        Create a new SecurityGroup.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance
        """
        raise NotImplementedError(
            'create_security_group not implemented by this provider')

    def delete_security_group(self):
        """
        Delete an existing SecurityGroup.

        :rtype: ``bool``
        :return:  True if successful, false otherwise
        """
        raise NotImplementedError(
            'delete_security_group not implemented by this provider')


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
            'InstanceTypesService.find_instance not implemented by this provider')

class CloudProviderServiceType():

    """
    Defines possible service types that
    are offered by providers. Providers can implement the
    has_service method and clients can check for the availability
    of a service with
    if (provider.has_service(CloudProviderServiceTypes.OBJECTSTORE))
        provider.ObjectStore.
    """
    COMPUTE = 'compute'
    IMAGE = 'image'
    SECURITY = 'security'
    VOLUME = 'volume'
    OBJECTSTORE = 'objectstore'


class CloudProvider():

    """
    Base interface for a cloud provider
    """

    def __init__(self, config):
        """
        Create a new provider implementation given a dictionary of configuration
        attributes.

        :type config: an object with required fields
        :param config: This can be a Bunch or any other object whose fields can
                       be accessed using dot notation. See specific provider
                       implementation for the required fields.

        :rtype: ``object`` of :class:`.CloudProvider`
        :return:  a concrete provider instance
        """
        raise NotImplementedError(
            '__init__ not implemented by this provider')

    def has_service(self, service):
        """
        Checks whether this provider supports a given service"

        :type config: an object with required fields
        :param config: This can be a Bunch or any other object whose fields can
                       be accessed using dot notation. See specific provider
                       implementation for the required fields.

        :rtype: ``object`` of :class:`.CloudProvider`
        :return:  a concrete provider instance
        """
        raise NotImplementedError(
            'has_service not implemented by this provider')

    def account(self):
        """
        Provides access to all user account related services in this provider.
        This includes listing available tenancies.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        raise NotImplementedError(
            'CloudProvider.Compute not implemented by this provider')

    def compute(self):
        """
        Provides access to all compute related services in this provider.

        :rtype: ``object`` of :class:`.ComputeService`
        :return:  a ComputeService object
        """
        raise NotImplementedError(
            'CloudProvider.Compute not implemented by this provider')

    def image(self):
        """
        Provides access to all Image related services in this provider.
        (e.g. Glance in Openstack)

        :rtype: ``object`` of :class:`.ImageService`
        :return: an ImageService object
        """
        raise NotImplementedError(
            'CloudProvider.Images not implemented by this provider')

    def security(self):
        """
        Provides access to keypair management and firewall control

        :rtype: ``object`` of :class:`.SecurityService`
        :return: a SecurityService object
        """
        raise NotImplementedError(
            'CloudProvider.Security not implemented by this provider')

    def volume(self):
        """
        Provides access to the volume/elastic block store services in this
        provider.

        :rtype: ``object`` of :class:`.VolumeService`
        :return: a VolumeService object
        """
        raise NotImplementedError(
            'CloudProvider.VolumeService not implemented by this provider')

    def object_store(self):
        """
        Provides access to object storage services in this provider.

        :rtype: ``object`` of :class:`.ObjectStoreService`
        :return: an ObjectStoreService object
        """
        raise NotImplementedError(
            'CloudProvider.ObjectStore not implemented by this provider')


class ProviderService():

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

    def list_instance_types(self):
        """
        List all instance types supported by this provider.

        :rtype: ``list`` of :class:`.InstanceType`
        :return: list of InstanceType objects
        """
        raise NotImplementedError(
            'list_instance_types not implemented by this provider')

    def list_regions(self):
        """
        List all data center regions for this provider.

        :rtype: ``list`` of :class:`.Region`
        :return: list of Region objects
        """
        raise NotImplementedError(
            'list_regions not implemented by this provider')

    def create_instance(self):
        """
        Creates a new virtual machine instance.

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

    def create_image(self):
        """
        Create a new image.
        :return:  an Image object
        :rtype: ``object`` of :class:`.Image`
        """
        raise NotImplementedError(
            'create_image not implemented by this provider')


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
        List all key pairs.

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


class Instance():

    def instance_id(self):
        """
        Get the instance identifier.

        :rtype: str
        :return: ID for this instance as returned by the cloud middleware.
        """
        raise NotImplementedError(
            'instance_id not implemented by this provider')

    def name(self):
        """
        Get the instance name.

        :rtype: str
        :return: Name for this instance as returned by the cloud middleware.
        """
        raise NotImplementedError(
            'name not implemented by this provider')

    def public_ips(self):
        """
        Get all the public IP addresses for this instance.

        :rtype: list
        :return: A list of public IP addresses associated with this instance.
        """
        raise NotImplementedError(
            'public_ips not implemented by this provider')

    def private_ips(self):
        """
        Get all the private IP addresses for this instance.

        :rtype: list
        :return: A list of private IP addresses associated with this instance.
        """
        raise NotImplementedError(
            'private_ips not implemented by this provider')

    def type(self):
        """
        Get the instance type.

        :rtype: str
        :return: API type of this instance (e.g., ``m1.large``)
        """
        raise NotImplementedError(
            'type not implemented by this provider')

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).

        :rtype: bool
        :return: ``True`` if the reboot was succesful; ``False`` otherwise.
        """
        raise NotImplementedError(
            'reboot not implemented by this provider')

    def terminate(self):
        """
        Permanently terminate this instance.

        :rtype: bool
        :return: ``True`` if the termination of the instance was succesfully
                 initiated; ``False`` otherwise.
        """
        raise NotImplementedError(
            'terminate not implemented by this provider')

    def image_id(self):
        """
        Get the image ID for this insance.

        :rtype: str
        :return: Image ID (i.e., AMI) this instance is using.
        """
        raise NotImplementedError(
            'image_id not implemented by this provider')

    def placement(self):
        """
        Get the placement where this instance is running.

        :rtype: str
        :return: Region/zone/placement where this instance is running.
        """
        raise NotImplementedError(
            'placement not implemented by this provider')

    def mac_address(self):
        """
        Get the MAC address for this instance.

        :rtype: str
        :return: MAC address for ths instance.
        """
        raise NotImplementedError(
            'mac_address not implemented by this provider')

    def security_group_ids(self):
        """
        Get the security group IDs associated with this instance.

        :rtype: list
        :return: A list of security group IDs associated with this instance.
        """
        raise NotImplementedError(
            'security_group_ids not implemented by this provider')

    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.

        :rtype: str
        :return: Name of the ssh key pair associated with this instance.
        """
        raise NotImplementedError(
            'key_pair_name not implemented by this provider')


class Volume():

    def attach(self, instance_id, device):
        """
        Attach this volume to an instance.

        :type instance_id: str
        :param instance_id: The ID of the instance to which it will
                            be attached.

        :type device: str
        :param device: The device on the instance through which the
                       volume will be exposed (e.g. /dev/sdh)

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError(
            'attach not implemented by this provider')

    def detach(self, force=False):
        """
        Detach this volume from an instance.

        :type force: bool
        :param force: Forces detachment if the previous detachment
            attempt did not occur cleanly. This option is supported on select
            clouds only. This option can lead to data loss or a corrupted file
            system. Use this option only as a last resort to detach a volume
            from a failed instance. The instance will not have an opportunity
            to flush file system caches nor file system meta data. If you
            use this option, you must perform file system check and
            repair procedures.

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError(
            'detach not implemented by this provider')

    def snapshot(self, description=None):
        """
        Create a snapshot of this Volume.

        :type description: str
        :param description: A description of the snapshot.
                            Limited to 256 characters.

        :rtype: :class:`.Snapshot`
        :return: The created Snapshot object
        """
        raise NotImplementedError(
            'snapshot not implemented by this provider')

    def delete(self):
        """
        Delete this volume.

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError(
            'delete not implemented by this provider')


class Snapshot():

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.

        :type zone: str
        :param zone: The availability zone in which the Volume will be created.

        :type size: int
        :param size: The size of the new volume, in GiB (optional). Defaults to
                     the size of the snapshot.

        :type volume_type: str
        :param volume_type: The type of the volume (optional). Availability and
                            valid values depend on the provider.

        :type iops: int
        :param iops: The provisioned IOPs you want to associate with
                     this volume (optional). Availability depends on the
                     provider.

        :rtype: :class:`.Volume`
        :return: An instance of the created Volume
        """
        raise NotImplementedError(
            'create_volume not implemented by this provider')

    def share(self, user_ids=None):
        """
        Share this Snapshot.

        :type user_ids: list of strings
        :param user_ids: A list of cloud provider compatible user IDs. If no
                         IDs are specified, the snapshot is made public.

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError('share not implemented by this provider')

    def unshare(self, user_ids=None):
        """
        Unshare this Snapshot.

        :type user_ids: list of strings
        :param user_ids: A list of cloud provider compatible user IDs. If no
                         IDs are specified, the snapshot is made private.

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError('unshare not implemented by this provider')

    def delete(self):
        """
        Delete this snapshot.

        :rtype: bool
        :return: True if successful
        """
        raise NotImplementedError('delete not implemented by this provider')


class Region():

    def name(self):
        raise NotImplementedError(
            'name not implemented by this provider')

    def list_zones(self):
        raise NotImplementedError(
            'list_zones not implemented by this provider')


class KeyPair():

    def __init__(self, name, material=None):
        self.name = name
        self.material = material

    def __repr__(self):
        return "CloudBridge KeyPair:{0}".format(self.name)

    # def name(self):
    #     """
    #     Return the name of this key pair.

    #     :rtype: str
    #     :return: A name of this ssh key pair
    #     """
    #     raise NotImplementedError(
    #         'name not implemented by this provider')


class SecurityGroup():

    def name(self):
        """
        Return the name of this security group.

        :rtype: str
        :return: A name of this security group
        """
        raise NotImplementedError(
            'name not implemented by this provider')


class ContainerProvider():

    """
    Represents a container instance, such as Docker or LXC
    """

    def create_container(self):
        raise NotImplementedError(
            'create_container not implemented by this provider')

    def delete_container(self):
        raise NotImplementedError(
            'delete_container not implemented by this provider')


class DeploymentProvider():

    """
    Represents a deployment provider, such as Ansible or Shell script provider
    """

    def deploy(self, target):
        """
        Deploys on given target, where target is an Instance or Container
        """
        raise NotImplementedError(
            'deploy not implemented by this provider')

"""
Services implemented by the OpenStack provider.
"""
from cinderclient.exceptions import NotFound as CinderNotFound
from novaclient.exceptions import NotFound as NovaNotFound

from cloudbridge.providers.interfaces import BlockStoreService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import ImageService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import InstanceTypesService
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import KeyPairService
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import ObjectStoreService
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import SecurityGroupService
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import SnapshotService
from cloudbridge.providers.interfaces import VolumeService

from .resources import OpenStackContainer
from .resources import OpenStackInstance
from .resources import OpenStackInstanceType
from .resources import OpenStackKeyPair
from .resources import OpenStackMachineImage
from .resources import OpenStackRegion
from .resources import OpenStackSecurityGroup
from .resources import OpenStackSnapshot
from .resources import OpenStackVolume


class OpenStackSecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

        # Initialize provider services
        self._key_pairs = OpenStackKeyPairService(provider)
        self._security_groups = OpenStackSecurityGroupService(provider)

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


class OpenStackKeyPairService(KeyPairService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.nova.keypairs.list()
        return [OpenStackKeyPair(self.provider, kp) for kp in key_pairs]

    def create(self, key_name):
        """
        Create a new key pair.

        :type key_name: str
        :param key_name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance or None if one was not be created.
        """
        kp = self.provider.nova.keypairs.create(key_name)
        if kp:
            return OpenStackKeyPair(self.provider, kp)
        return None

    def delete(self, key_name):
        """
        Delete an existing key pair.

        :type key_name: str
        :param key_name: The name of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist, ``False`` otherwise. Note
                  that this implies that the key may not have been deleted by
                  this method but instead has not existed in the first place.
        """
        try:
            kp = self.provider.nova.keypairs.find(name=key_name)
            kp.delete()
            return True
        except NovaNotFound:
            return True


class OpenStackSecurityGroupService(SecurityGroupService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        groups = self.provider.nova.security_groups.list()
        return [OpenStackSecurityGroup(
            self.provider, group) for group in groups]

    def create(self, name, description):
        """
        Create a new security group under the current account.

        :type name: str
        :param name: The name of the new security group.

        :type description: str
        :param description: The description of the new security group.

        :rtype: ``object`` of :class:`.SecurityGroup`
        :return: a SecurityGroup object
        """
        sg = self.provider.nova.security_groups.create(name, description)
        if sg:
            return OpenStackSecurityGroup(self.provider, sg)
        return None

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
        if not group_names:
            group_names = []
        if not group_ids:
            group_ids = []
        security_groups = self.provider.nova.security_groups.list()
        filtered = []
        for sg in security_groups:
            if sg.name in group_names:
                filtered.append(sg)
            if sg.id in group_ids:
                filtered.append(sg)
        # If a filter was specified, use the filtered list; otherwise, get all
        return [OpenStackSecurityGroup(self.provider, sg)
                for sg in (filtered
                           if (group_names or group_ids) else security_groups)]

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
        sg = self.get(group_ids=[group_id])
        if sg:
            sg[0].delete()
        return True


class OpenStackImageService(ImageService):

    def __init__(self, provider):
        self.provider = provider

    def get_image(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            return OpenStackMachineImage(
                self.provider, self.provider.nova.images.get(image_id))
        except NovaNotFound:
            return None

    def find_image(self, name):
        """
        Searches for an image by a given list of attributes
        """
        raise NotImplementedError(
            'find_image not implemented by this provider')

    def list_images(self):
        """
        List all images.
        """
        images = self.provider.nova.images.list()
        return [OpenStackMachineImage(self.provider, image)
                for image in images]


class OpenStackInstanceTypesService(InstanceTypesService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        return [OpenStackInstanceType(f)
                for f in self.provider.nova.flavors.list()]

    def find_by_name(self, name):
        return next(
            (itype for itype in self.list() if itype.name == name), None)


class OpenStackBlockStoreService(BlockStoreService):

    def __init__(self, provider):
        self.provider = provider

        # Initialize provider services
        self._volumes = OpenStackVolumeService(self.provider)
        self._snapshots = OpenStackSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volumes

    @property
    def snapshots(self):
        return self._snapshots


class OpenStackVolumeService(VolumeService):

    def __init__(self, provider):
        self.provider = provider

    def get_volume(self, volume_id):
        """
        Returns a volume given its id.
        """
        try:
            return OpenStackVolume(
                self.provider, self.provider.cinder.volumes.get(volume_id))
        except CinderNotFound:
            return None

    def find_volume(self, name):
        """
        Searches for a volume by a given list of attributes.
        """
        raise NotImplementedError(
            'find_volume not implemented by this provider')

    def list_volumes(self):
        """
        List all volumes.
        """
        return [OpenStackVolume(self.provider, vol)
                for vol in self.provider.cinder.volumes.list()]

    def create_volume(self, name, size, zone, snapshot=None):
        """
        Creates a new volume.
        """
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.snapshot_id if isinstance(
            zone, OpenStackSnapshot) and snapshot else snapshot

        os_vol = self.provider.cinder.volumes.create(
            size, name=name, availability_zone=zone_name,
            snapshot_id=snapshot_id)
        return OpenStackVolume(self.provider, os_vol)


class OpenStackSnapshotService(SnapshotService):

    def __init__(self, provider):
        self.provider = provider

    def get_snapshot(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        try:
            return OpenStackSnapshot(
                self.provider,
                self.provider.cinder.volume_snapshots.get(snapshot_id))
        except CinderNotFound:
            return None

    def find_snapshot(self, name):
        """
        Searches for a volume by a given list of attributes.
        """
        raise NotImplementedError(
            'find_volume not implemented by this provider')

    def list_snapshots(self):
        """
        List all snapshot.
        """
        return [OpenStackSnapshot(self.provider, snap)
                for snap in self.provider.cinder.volume_snapshots.list()]

    def create_snapshot(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_id = volume.volume_id if \
            isinstance(volume, OpenStackVolume) else volume

        os_snap = self.provider.cinder.volume_snapshots.create(
            volume_id, name=name,
            description=description)
        return OpenStackSnapshot(self.provider, os_snap)


class OpenStackObjectStoreService(ObjectStoreService):

    def __init__(self, provider):
        self.provider = provider

    def get_container(self, container_id):
        """
        Returns a container given its id. Returns None if the container
        does not exist.
        """
        _, container_list = self.provider.swift.get_account(
            prefix=container_id)
        if container_list:
            return OpenStackContainer(self.provider, container_list[0])
        else:
            return None

    def find_container(self, name):
        """
        Searches for a container by a given list of attributes
        """
        raise NotImplementedError(
            'find_container not implemented by this provider')

    def list_containers(self):
        """
        List all containers.
        """
        _, container_list = self.provider.swift.get_account()
        return [
            OpenStackContainer(self.provider, c) for c in container_list]

    def create_container(self, name, location=None):
        """
        Create a new container.
        """
        self.provider.swift.put_container(name)
        return self.get_container(name)


class OpenStackComputeService(ComputeService):

    def __init__(self, provider):
        self.provider = provider
        self.instance_types = OpenStackInstanceTypesService(self.provider)

    def create_instance(self, name, image, instance_type, zone=None,
                        keypair=None, security_groups=None, user_data=None,
                        block_device_mapping=None, network_interfaces=None,
                        **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.image_id if isinstance(image, MachineImage) else image
        instance_size = instance_type.name if \
            isinstance(instance_type, InstanceType) else \
            self.instance_types.find_by_name(instance_type).id
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        keypair_name = keypair.name if \
            isinstance(keypair, KeyPair) else keypair
        if security_groups:
            if isinstance(security_groups, list) and \
                    isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None

        os_instance = self.provider.nova.servers.create(
            name,
            image_id,
            instance_size,
            min_count=1,
            max_count=1,
            availability_zone=zone_name,
            key_name=keypair_name,
            security_groups=security_groups_list,
            userdata=user_data)
        return OpenStackInstance(self.provider, os_instance)

    def list_instances(self):
        """
        List all instances.
        """
        instances = self.provider.nova.servers.list()
        return [OpenStackInstance(self.provider, instance)
                for instance in instances]

    def list_regions(self):
        """
        List all data center regions.
        """
        # detailed must be set to ``False`` because the (default) ``True``
        # value requires Admin priviledges
        regions = self.provider.nova.availability_zones.list(detailed=False)
        return [OpenStackRegion(self.provider, region) for region in regions]

    def get_instance(self, instance_id):
        """
        Returns an instance given its id.
        """
        try:
            os_instance = self.provider.nova.servers.get(instance_id)
            return OpenStackInstance(self.provider, os_instance)
        except NovaNotFound:
            return None

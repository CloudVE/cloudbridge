"""
Services implemented by the OpenStack provider.
"""
from cinderclient.exceptions import NotFound as CinderNotFound
from novaclient.exceptions import NotFound as NovaNotFound

from cloudbridge.providers.base import BaseBlockStoreService
from cloudbridge.providers.base import BaseComputeService
from cloudbridge.providers.base import BaseImageService
from cloudbridge.providers.base import BaseInstanceService
from cloudbridge.providers.base import BaseInstanceTypesService
from cloudbridge.providers.base import BaseKeyPairService
from cloudbridge.providers.base import BaseObjectStoreService
from cloudbridge.providers.base import BaseSecurityGroupService
from cloudbridge.providers.base import BaseSecurityService
from cloudbridge.providers.base import BaseSnapshotService
from cloudbridge.providers.base import BaseVolumeService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup

from .resources import OpenStackContainer
from .resources import OpenStackInstance
from .resources import OpenStackInstanceType
from .resources import OpenStackKeyPair
from .resources import OpenStackMachineImage
from .resources import OpenStackRegion
from .resources import OpenStackSecurityGroup
from .resources import OpenStackSnapshot
from .resources import OpenStackVolume


class OpenStackSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(OpenStackSecurityService, self).__init__(provider)

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


class OpenStackKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(OpenStackKeyPairService, self).__init__(provider)

    def list(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self._provider.nova.keypairs.list()
        return [OpenStackKeyPair(self._provider, kp) for kp in key_pairs]

    def create(self, name):
        """
        Create a new key pair.

        :type name: str
        :param name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance or None if one was not be created.
        """
        kp = self._provider.nova.keypairs.create(name)
        if kp:
            return OpenStackKeyPair(self._provider, kp)
        return None

    def delete(self, name):
        """
        Delete an existing key pair.

        :type name: str
        :param name: The name of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist, ``False`` otherwise. Note
                  that this implies that the key may not have been deleted by
                  this method but instead has not existed in the first place.
        """
        try:
            kp = self._provider.nova.keypairs.find(name=name)
            kp.delete()
            return True
        except NovaNotFound:
            return True


class OpenStackSecurityGroupService(BaseSecurityGroupService):

    def __init__(self, provider):
        super(OpenStackSecurityGroupService, self).__init__(provider)

    def list(self):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        groups = self._provider.nova.security_groups.list()
        return [OpenStackSecurityGroup(
            self._provider, group) for group in groups]

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
        sg = self._provider.nova.security_groups.create(name, description)
        if sg:
            return OpenStackSecurityGroup(self._provider, sg)
        return None

    def get(self, group_names=None, group_ids=None):
        """
        Get all security groups associated with your account.

        :type group_names: list
        :param group_names: A list of strings of the names of security groups
                           to retrieve. If not provided, all security groups
                           will be returned.

        :type group_ids: list
        :param group_ids: A list of string IDs of security groups to retrieve.
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
        security_groups = self._provider.nova.security_groups.list()
        filtered = []
        for sg in security_groups:
            if sg.name in group_names:
                filtered.append(sg)
            if sg.id in group_ids:
                filtered.append(sg)
        # If a filter was specified, use the filtered list; otherwise, get all
        return [OpenStackSecurityGroup(self._provider, sg)
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


class OpenStackImageService(BaseImageService):

    def __init__(self, provider):
        super(OpenStackImageService, self).__init__(provider)

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        try:
            return OpenStackMachineImage(
                self._provider, self._provider.nova.images.get(image_id))
        except NovaNotFound:
            return None

    def find(self, name):
        """
        Searches for an image by a given list of attributes
        """
        raise NotImplementedError(
            'find_image not implemented by this provider')

    def list(self):
        """
        List all images.
        """
        images = self._provider.nova.images.list()
        return [OpenStackMachineImage(self._provider, image)
                for image in images]


class OpenStackInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(OpenStackInstanceTypesService, self).__init__(provider)

    def list(self):
        return [OpenStackInstanceType(f)
                for f in self._provider.nova.flavors.list()]

    def find_by_name(self, name):
        return next(
            (itype for itype in self.list() if itype.name == name), None)


class OpenStackBlockStoreService(BaseBlockStoreService):

    def __init__(self, provider):
        super(OpenStackBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = OpenStackVolumeService(self._provider)
        self._snapshot_svc = OpenStackSnapshotService(self._provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class OpenStackVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(OpenStackVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        try:
            return OpenStackVolume(
                self._provider, self._provider.cinder.volumes.get(volume_id))
        except CinderNotFound:
            return None

    def find(self, name):
        """
        Searches for a volume by a given list of attributes.
        """
        raise NotImplementedError(
            'find_volume not implemented by this provider')

    def list(self):
        """
        List all volumes.
        """
        return [OpenStackVolume(self._provider, vol)
                for vol in self._provider.cinder.volumes.list()]

    def create(self, name, size, zone, snapshot=None):
        """
        Creates a new volume.
        """
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.snapshot_id if isinstance(
            zone, OpenStackSnapshot) and snapshot else snapshot

        os_vol = self._provider.cinder.volumes.create(
            size, name=name, availability_zone=zone_name,
            snapshot_id=snapshot_id)
        return OpenStackVolume(self._provider, os_vol)


class OpenStackSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(OpenStackSnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        try:
            return OpenStackSnapshot(
                self._provider,
                self._provider.cinder.volume_snapshots.get(snapshot_id))
        except CinderNotFound:
            return None

    def find(self, name):
        """
        Searches for a volume by a given list of attributes.
        """
        raise NotImplementedError(
            'find_volume not implemented by this provider')

    def list(self):
        """
        List all snapshot.
        """
        return [OpenStackSnapshot(self._provider, snap)
                for snap in self._provider.cinder.volume_snapshots.list()]

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_id = volume.volume_id if \
            isinstance(volume, OpenStackVolume) else volume

        os_snap = self._provider.cinder.volume_snapshots.create(
            volume_id, name=name,
            description=description)
        return OpenStackSnapshot(self._provider, os_snap)


class OpenStackObjectStoreService(BaseObjectStoreService):

    def __init__(self, provider):
        super(OpenStackObjectStoreService, self).__init__(provider)

    def get(self, container_id):
        """
        Returns a container given its id. Returns None if the container
        does not exist.
        """
        _, container_list = self._provider.swift.get_account(
            prefix=container_id)
        if container_list:
            return OpenStackContainer(self._provider, container_list[0])
        else:
            return None

    def find(self, name):
        """
        Searches for a container by a given list of attributes
        """
        raise NotImplementedError(
            'find_container not implemented by this provider')

    def list(self):
        """
        List all containers.
        """
        _, container_list = self._provider.swift.get_account()
        return [
            OpenStackContainer(self._provider, c) for c in container_list]

    def create(self, name, location=None):
        """
        Create a new container.
        """
        self._provider.swift.put_container(name)
        return self.get(name)


class OpenStackComputeService(BaseComputeService):

    def __init__(self, provider):
        super(OpenStackComputeService, self).__init__(provider)
        self._instance_type_svc = OpenStackInstanceTypesService(self._provider)
        self._instance_svc = OpenStackInstanceService(self._provider)

    @property
    def instance_types(self):
        return self._instance_type_svc

    @property
    def instances(self):
        return self._instance_svc

    def list_regions(self):
        """
        List all data center regions.
        """
        # detailed must be set to ``False`` because the (default) ``True``
        # value requires Admin priviledges
        regions = self._provider.nova.availability_zones.list(detailed=False)
        return [OpenStackRegion(self._provider, region) for region in regions]


class OpenStackInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(OpenStackInstanceService, self).__init__(provider)

    def create(self, name, image, instance_type, zone=None,
               keypair=None, security_groups=None, user_data=None,
               block_device_mapping=None, network_interfaces=None,
               **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.image_id if isinstance(image, MachineImage) else image
        instance_size = instance_type.name if \
            isinstance(instance_type, InstanceType) else \
            self.provider.compute.instance_types.find_by_name(instance_type).id
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

        os_instance = self._provider.nova.servers.create(
            name,
            image_id,
            instance_size,
            min_count=1,
            max_count=1,
            availability_zone=zone_name,
            key_name=keypair_name,
            security_groups=security_groups_list,
            userdata=user_data)
        return OpenStackInstance(self._provider, os_instance)

    def find(self, name):
        """
        Searches for an instance by a given list of attributes.
        """
        raise NotImplementedError(
            'find_instance not implemented by this provider')

    def list(self):
        """
        List all instances.
        """
        instances = self._provider.nova.servers.list()
        return [OpenStackInstance(self._provider, instance)
                for instance in instances]

    def get(self, instance_id):
        """
        Returns an instance given its id.
        """
        try:
            os_instance = self._provider.nova.servers.get(instance_id)
            return OpenStackInstance(self._provider, os_instance)
        except NovaNotFound:
            return None

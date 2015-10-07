"""
Services implemented by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import BlockStoreService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import ImageService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import InstanceTypesService
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import SnapshotService
from cloudbridge.providers.interfaces import VolumeService

from .resources import OpenStackInstance
from .resources import OpenStackInstanceType
from .resources import OpenStackMachineImage
from .resources import OpenStackRegion
from .resources import OpenStackSnapshot
from .resources import OpenStackVolume


class OpenStackSecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.nova.keypairs.list()
        return [BaseKeyPair(kp.id) for kp in key_pairs]

    def list_security_groups(self):
        """
        Create a new security group

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        groups = self.provider.nova.security_groups.list()
        return [BaseSecurityGroup(group.name) for group in groups]


class OpenStackImageService(ImageService):

    def __init__(self, provider):
        self.provider = provider

    def get_image(self, image_id):
        """
        Returns an Image given its id
        """
        image = self.provider.nova.images.get(image_id)
        if image:
            return OpenStackMachineImage(self.provider, image)
        else:
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
        vol = self.provider.cinder.volumes.get(volume_id)
        return OpenStackVolume(self.provider, vol) if vol else None

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
        snap = self.provider.cinder.volume_snapshots.get(snapshot_id)
        return OpenStackSnapshot(self.provider, snap) if snap else None

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
        os_instance = self.provider.nova.servers.get(instance_id)
        return OpenStackInstance(self.provider, os_instance)

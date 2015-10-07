"""
Services implemented by this provider
"""

from cloudbridge.providers.base import BaseKeyPair
from cloudbridge.providers.base import BaseSecurityGroup
from cloudbridge.providers.interfaces import BlockStoreService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import ImageService
from cloudbridge.providers.interfaces import InstanceType
from cloudbridge.providers.interfaces import KeyPair
from cloudbridge.providers.interfaces import MachineImage
from cloudbridge.providers.interfaces import PlacementZone
from cloudbridge.providers.interfaces import SecurityGroup
from cloudbridge.providers.interfaces import SecurityService
from cloudbridge.providers.interfaces import SnapshotService
from cloudbridge.providers.interfaces import VolumeService

from .resources import AWSInstance
from .resources import AWSMachineImage
from .resources import AWSSnapshot
from .resources import AWSVolume


class AWSSecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

    def list_key_pairs(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.ec2_conn.get_all_key_pairs()
        return [BaseKeyPair(kp.name) for kp in key_pairs]

    def list_security_groups(self):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        groups = self.provider.ec2_conn.get_all_security_groups()
        return [BaseSecurityGroup(group.id, group.name, group.description)
                for group in groups]


class AWSBlockStoreService(BlockStoreService):

    def __init__(self, provider):
        self.provider = provider

        # Initialize provider services
        self._volumes = AWSVolumeService(self.provider)
        self._snapshots = AWSSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volumes

    @property
    def snapshots(self):
        return self._snapshots


class AWSVolumeService(VolumeService):

    def __init__(self, provider):
        self.provider = provider

    def get_volume(self, volume_id):
        """
        Returns a volume given its id.
        """
        vols = self.provider.ec2_conn.get_all_volumes(volume_ids=[volume_id])
        return AWSVolume(self.provider, vols[0]) if vols else None

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
        return [AWSVolume(self.provider, vol)
                for vol in self.provider.ec2_conn.get_all_volumes()]

    def create_volume(self, name, size, zone, snapshot=None):
        """
        Creates a new volume.
        """
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.snapshot_id if isinstance(
            zone, AWSSnapshot) and snapshot else snapshot

        ec2_vol = self.provider.ec2_conn.create_volume(
            size,
            zone_name,
            snapshot=snapshot_id)
        cb_vol = AWSVolume(self.provider, ec2_vol)
        cb_vol.name = name
        return cb_vol


class AWSSnapshotService(SnapshotService):

    def __init__(self, provider):
        self.provider = provider

    def get_snapshot(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        snaps = self.provider.ec2_conn.get_all_snapshots(
            snapshot_ids=[snapshot_id])
        return AWSSnapshot(self.provider, snaps[0]) if snaps else None

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
        # TODO: get_all_images returns too many images - some kind of filtering
        # abilities are needed. Forced to "self" for now
        return [AWSSnapshot(self.provider, snap)
                for snap in
                self.provider.ec2_conn.get_all_snapshots(owner="self")]

    def create_snapshot(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        volume_id = volume.volume_id if isinstance(
            volume,
            AWSVolume) else volume

        ec2_snap = self.provider.ec2_conn.create_snapshot(
            volume_id,
            description=description)
        cb_snap = AWSSnapshot(self.provider, ec2_snap)
        cb_snap.name = name
        return cb_snap


class AWSImageService(ImageService):

    def __init__(self, provider):
        self.provider = provider

    def get_image(self, image_id):
        """
        Returns an Image given its id
        """
        image = self.provider.ec2_conn.get_image(image_id)
        if image:
            return AWSMachineImage(self.provider, image)
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
        # TODO: get_all_images returns too many images - some kind of filtering
        # abilities are needed. Forced to "self" for now
        images = self.provider.ec2_conn.get_all_images(owners="self")
        return [AWSMachineImage(self.provider, image) for image in images]


class AWSComputeService(ComputeService):

    def __init__(self, provider):
        self.provider = provider

    def create_instance(self, name, image, instance_type, zone=None,
                        keypair=None, security_groups=None, user_data=None,
                        block_device_mapping=None, network_interfaces=None,
                        **kwargs):
        """
        Creates a new virtual machine instance.
        """
        image_id = image.image_id if isinstance(image, MachineImage) else image
        instance_size = instance_type.name if \
            isinstance(instance_type, InstanceType) else instance_type
        zone_name = zone.name if isinstance(zone, PlacementZone) else zone
        keypair_name = keypair.name if isinstance(
            keypair,
            KeyPair) else keypair
        if security_groups:
            if isinstance(security_groups, list) and \
                    isinstance(security_groups[0], SecurityGroup):
                security_groups_list = [sg.name for sg in security_groups]
            else:
                security_groups_list = security_groups
        else:
            security_groups_list = None

        reservation = self.provider.ec2_conn.run_instances(
            image_id=image_id, instance_type=instance_size,
            min_count=1, max_count=1, placement=zone_name,
            key_name=keypair_name, security_groups=security_groups_list,
            user_data=user_data
        )
        if reservation:
            instance = AWSInstance(self.provider, reservation.instances[0])
            instance.name = name
        return instance

"""
Services implemented by the AWS provider.
"""
from boto.exception import EC2ResponseError

from cloudbridge.providers.interfaces import BlockStoreService
from cloudbridge.providers.interfaces import ComputeService
from cloudbridge.providers.interfaces import ImageService
from cloudbridge.providers.interfaces import InstanceType
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

from .resources import AWSContainer
from .resources import AWSInstance
from .resources import AWSKeyPair
from .resources import AWSMachineImage
from .resources import AWSSecurityGroup
from .resources import AWSSnapshot
from .resources import AWSVolume


class AWSSecurityService(SecurityService):

    def __init__(self, provider):
        self.provider = provider

        # Initialize provider services
        self._key_pairs = AWSKeyPairService(provider)
        self._security_groups = AWSSecurityGroupService(provider)

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


class AWSKeyPairService(KeyPairService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        """
        List all key pairs associated with this account.

        :rtype: ``list`` of :class:`.KeyPair`
        :return:  list of KeyPair objects
        """
        key_pairs = self.provider.ec2_conn.get_all_key_pairs()
        return [AWSKeyPair(self.provider, kp) for kp in key_pairs]

    def create(self, key_name):
        """
        Create a new key pair.

        :type key_name: str
        :param key_name: The name of the key pair to be created.

        :rtype: ``object`` of :class:`.KeyPair`
        :return:  A keypair instance or None if one was not be created.
        """
        kp = self.provider.ec2_conn.create_key_pair(key_name)
        if kp:
            return AWSKeyPair(self.provider, kp)
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
        for kp in self.provider.ec2_conn.get_all_key_pairs():
            if kp.name == key_name:
                kp.delete()
                return True
        return True


class AWSSecurityGroupService(SecurityGroupService):

    def __init__(self, provider):
        self.provider = provider

    def list(self):
        """
        List all security groups associated with this account.

        :rtype: ``list`` of :class:`.SecurityGroup`
        :return:  list of SecurityGroup objects
        """
        security_groups = self.provider.ec2_conn.get_all_security_groups()
        return [AWSSecurityGroup(self.provider, sg) for sg in security_groups]

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
        sg = self.provider.ec2_conn.create_security_group(name, description)
        if sg:
            return AWSSecurityGroup(self.provider, sg)
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
        try:
            security_groups = self.provider.ec2_conn.get_all_security_groups(
                groupnames=group_names, group_ids=group_ids)
        except EC2ResponseError:
            security_groups = []
        return [AWSSecurityGroup(self.provider, sg) for sg in security_groups]

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
        try:
            for sg in self.provider.ec2_conn.get_all_security_groups(
                    group_ids=[group_id]):
                try:
                    sg.delete()
                except EC2ResponseError:
                    return False
        except EC2ResponseError:
            pass
        return True


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


class AWSObjectStoreService(ObjectStoreService):

    def __init__(self, provider):
        self.provider = provider

    def get_container(self, container_id):
        """
        Returns a container given its id. Returns None if the container
        does not exist.
        """
        bucket = self.provider.s3_conn.lookup(container_id)
        if bucket:
            return AWSContainer(self.provider, bucket)
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
        buckets = self.provider.s3_conn.get_all_buckets()
        return [AWSContainer(self.provider, bucket) for bucket in buckets]

    def create_container(self, name, location=None):
        """
        Create a new container.
        """
        bucket = self.provider.s3_conn.create_bucket(
            name,
            location=location if location else '')
        return AWSContainer(self.provider, bucket)


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
        try:
            image = self.provider.ec2_conn.get_image(image_id)
            if image:
                return AWSMachineImage(self.provider, image)
        except EC2ResponseError:
            pass

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

    def get_instance(self, instance_id):
        """
        Returns an instance given its id. Returns None
        if the object does not exist.
        """
        reservation = self.provider.ec2_conn.get_all_reservations(
            instance_ids=[instance_id])
        if reservation:
            return AWSInstance(self.provider, reservation[0].instances[0])
        else:
            return None

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
        """
        reservations = self.provider.ec2_conn.get_all_reservations()
        return [AWSInstance(self.provider, inst)
                for res in reservations
                for inst in res.instances]

"""
DataTypes used by this provider
"""
import shutil

from boto.exception import EC2ResponseError
from boto.s3.key import Key
from retrying import retry

from cloudbridge.cloud.base import BaseContainer
from cloudbridge.cloud.base import BaseContainerObject
from cloudbridge.cloud.base import BaseInstance
from cloudbridge.cloud.base import BaseInstanceType
from cloudbridge.cloud.base import BaseKeyPair
from cloudbridge.cloud.base import BaseMachineImage
from cloudbridge.cloud.base import BaseRegion
from cloudbridge.cloud.base import BaseSecurityGroup
from cloudbridge.cloud.base import BaseSecurityGroupRule
from cloudbridge.cloud.base import BaseSnapshot
from cloudbridge.cloud.base import BaseVolume
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import VolumeState


class AWSMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        self._provider = provider
        if isinstance(image, AWSMachineImage):
            self._ec2_image = image._ec2_image
        else:
            self._ec2_image = image

    @property
    def id(self):
        """
        Get the image identifier.

        :rtype: ``str``
        :return: ID for this instance as returned by the cloud middleware.
        """
        return self._ec2_image.id

    @property
    def name(self):
        """
        Get the image name.

        :rtype: ``str``
        :return: Name for this image as returned by the cloud middleware.
        """
        return self._ec2_image.name

    @property
    def description(self):
        """
        Get the image description.

        :rtype: ``str``
        :return: Description for this image as returned by the cloud middleware
        """
        return self._ec2_image.description

    def delete(self):
        """
        Delete this image
        """
        self._ec2_image.deregister(delete_snapshot=True)

    @property
    def state(self):
        return AWSMachineImage.IMAGE_STATE_MAP.get(
            self._ec2_image.state, MachineImageState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        image = self._provider.compute.images.get(self.id)
        if image:
            self._ec2_image = image._ec2_image
        else:
            # image no longer exists
            self._ec2_image.state = "unknown"


class AWSPlacementZone(PlacementZone):

    def __init__(self, provider, zone):
        self._provider = provider
        if isinstance(zone, AWSPlacementZone):
            self._aws_zone = zone._aws_zone
        else:
            self._aws_zone = zone

    @property
    def name(self):
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        return self._aws_zone

    @property
    def region(self):
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._aws_zone.region_name


class AWSInstanceType(BaseInstanceType):

    def __init__(self, provider, instance_dict):
        self._provider = provider
        self._inst_dict = instance_dict

    @property
    def id(self):
        return self._inst_dict['instance_type']

    @property
    def name(self):
        return self._inst_dict['instance_type']

    @property
    def family(self):
        return self._inst_dict.get('family')

    @property
    def vcpus(self):
        return self._inst_dict.get('vCPU')

    @property
    def ram(self):
        return self._inst_dict.get('memory')

    @property
    def size_root_disk(self):
        return 0

    @property
    def size_ephemeral_disks(self):
        storage = self._inst_dict.get('storage')
        if storage:
            return storage.get('size') * storage.get("devices")
        else:
            return 0

    @property
    def num_ephemeral_disks(self):
        storage = self._inst_dict.get('storage')
        if storage:
            return storage.get("devices")
        else:
            return 0

    @property
    def extra_data(self):
        return {key: val for key, val in enumerate(self._inst_dict)
                if key not in ["instance_type", "family", "vCPU", "memory"]}


class AWSInstance(BaseInstance):

    # ref:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    INSTANCE_STATE_MAP = {
        'pending': InstanceState.PENDING,
        'running': InstanceState.RUNNING,
        'shutting-down': InstanceState.CONFIGURING,
        'terminated': InstanceState.TERMINATED,
        'stopping': InstanceState.CONFIGURING,
        'stopped': InstanceState.STOPPED
    }

    def __init__(self, provider, ec2_instance):
        self._provider = provider
        self._ec2_instance = ec2_instance

    @property
    def id(self):
        """
        Get the instance identifier.
        """
        return self._ec2_instance.id

    @property
    def name(self):
        """
        Get the instance name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._ec2_instance.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the instance name.
        """
        self._ec2_instance.add_tag('Name', value)

    @property
    def public_ips(self):
        """
        Get all the public IP addresses for this instance.
        """
        return [self._ec2_instance.ip_address]

    @property
    def private_ips(self):
        """
        Get all the private IP addresses for this instance.
        """
        return [self._ec2_instance.private_ip_address]

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return AWSInstanceType(self._ec2_instance.instance_type)

    def reboot(self):
        """
        Reboot this instance (using the cloud middleware API).
        """
        self._ec2_instance.reboot()

    def terminate(self):
        """
        Permanently terminate this instance.
        """
        self._ec2_instance.terminate()

    @property
    def image_id(self):
        """
        Get the image ID for this insance.
        """
        return self._ec2_instance.image_id

    @property
    def placement_zone(self):
        """
        Get the placement zone where this instance is running.
        """
        return AWSPlacementZone(self._provider, self._ec2_instance.placement)

    @property
    def mac_address(self):
        """
        Get the MAC address for this instance.
        """
        raise NotImplementedError(
            'mac_address not implemented by this provider')

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        # boto instance.groups field returns a ``Group`` object so need to
        # convert that into a ``SecurityGroup`` object before creating a
        # cloudbridge SecurityGroup object
        names = [group.name for group in self._ec2_instance.groups]
        security_groups = self._provider.security.security_groups.get(names)
        return [AWSSecurityGroup(self._provider, group)
                for group in security_groups]

    @property
    def key_pair_name(self):
        """
        Get the name of the key pair associated with this instance.
        """
        return self._ec2_instance.key_name

    def create_image(self, name):
        """
        Create a new image based on this instance.
        """
        image_id = self._ec2_instance.create_image(name)
        # Sometimes, the image takes a while to register, so retry a few times
        # if the image cannot be found
        retry_decorator = retry(retry_on_result=lambda result: result is None,
                                stop_max_attempt_number=3, wait_fixed=1000)
        image = retry_decorator(self._provider.compute.images.get)(image_id)
        return image

    def add_floating_ip(self, ip_address):
        """
        Add an elastic IP address to this instance.
        """
        return self._ec2_instance.use_ip(ip_address)

    def remove_floating_ip(self, ip_address):
        """
        Remove a elastic IP address from this instance.
        """
        raise NotImplementedError(
            'remove_floating_ip not implemented by this provider.')

    @property
    def state(self):
        return AWSInstance.INSTANCE_STATE_MAP.get(
            self._ec2_instance.state, InstanceState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._ec2_instance.update(validate=True)
        except (EC2ResponseError, ValueError):
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._ec2_instance.status = 'unknown'


class AWSVolume(BaseVolume):

    # Ref:
    # http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/
    # ApiReference-cmd-DescribeVolumes.html
    VOLUME_STATE_MAP = {
        'creating': VolumeState.CREATING,
        'available': VolumeState.AVAILABLE,
        'in-use': VolumeState.IN_USE,
        'deleting': VolumeState.CONFIGURING,
        'deleted': VolumeState.DELETED,
        'error': VolumeState.ERROR
    }

    def __init__(self, provider, volume):
        self._provider = provider
        self._volume = volume

    @property
    def id(self):
        return self._volume.id

    @property
    def name(self):
        """
        Get the volume name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._volume.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the volume name.
        """
        self._volume.add_tag('Name', value)

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            AWSInstance) else instance
        self._volume.attach(instance_id, device)

    def detach(self, force=False):
        """
        Detach this volume from an instance.
        """
        self._volume.detach()

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        snap = AWSSnapshot(
            self._provider,
            self._volume.create_snapshot(
                description=description))
        snap.name = name
        return snap

    def delete(self):
        """
        Delete this volume.
        """
        self._volume.delete()

    @property
    def state(self):
        return AWSVolume.VOLUME_STATE_MAP.get(
            self._volume.status, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._volume.update(validate=True)
        except (EC2ResponseError, ValueError):
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.status = 'unknown'


class AWSSnapshot(BaseSnapshot):

    # Ref: http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/
    # ApiReference-cmd-DescribeSnapshots.html
    SNAPSHOT_STATE_MAP = {
        'pending': SnapshotState.PENDING,
        'completed': SnapshotState.AVAILABLE,
        'error': SnapshotState.ERROR
    }

    def __init__(self, provider, snapshot):
        self._provider = provider
        self._snapshot = snapshot

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        """
        Get the snapshot name.

        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return self._snapshot.tags.get('Name')

    @name.setter
    def name(self, value):
        """
        Set the snapshot name.
        """
        self._snapshot.add_tag('Name', value)

    @property
    def state(self):
        return AWSSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.status, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._snapshot.update(validate=True)
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        raise NotImplementedError(
            'create_volume not implemented by this provider')

    def share(self, user_ids=None):
        raise NotImplementedError('share not implemented by this provider')

    def unshare(self, user_ids=None):
        raise NotImplementedError('share not implemented by this provider')


class AWSKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AWSKeyPair, self).__init__(provider, key_pair)

    @property
    def material(self):
        """
        Unencrypted private key.

        :rtype: str
        :return: Unencrypted private key or ``None`` if not available.

        """
        return self._key_pair.material


class AWSSecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, security_group):
        super(AWSSecurityGroup, self).__init__(provider, security_group)

    @property
    def rules(self):
        return [AWSSecurityGroupRule(self._provider, r, self)
                for r in self._security_group.rules]

    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        """
        Create a security group rule.

        You need to pass in either ``src_group`` OR ``ip_protocol``,
        ``from_port``, ``to_port``, and ``cidr_ip``.  In other words, either
        you are authorizing another group or you are authorizing some
        ip-based rule.

        :type ip_protocol: str
        :param ip_protocol: Either ``tcp`` | ``udp`` | ``icmp``

        :type from_port: int
        :param from_port: The beginning port number you are enabling

        :type to_port: int
        :param to_port: The ending port number you are enabling

        :type cidr_ip: str or list of strings
        :param cidr_ip: The CIDR block you are providing access to.

        :type src_group: ``object`` of :class:`.SecurityGroup`
        :param src_group: The Security Group you are granting access to.

        :rtype: bool
        :return: True if successful.
        """
        return self._security_group.authorize(
            ip_protocol=ip_protocol,
            from_port=from_port,
            to_port=to_port,
            cidr_ip=cidr_ip,
            src_group=src_group._security_group if src_group else None)


class AWSSecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, provider, rule, parent):
        super(AWSSecurityGroupRule, self).__init__(provider, rule, parent)

    @property
    def ip_protocol(self):
        return self._rule.ip_protocol

    @property
    def from_port(self):
        return self._rule.from_port

    @property
    def to_port(self):
        return self._rule.to_port

    @property
    def cidr_ip(self):
        if len(self._rule.grants) > 0:
            return self._rule.grants[0].cidr_ip
        return None

    @property
    def group(self):
        if len(self._rule.grants) > 0:
            if self._rule.grants[0].name:
                cg = self.parent._provider.ec2_conn.get_all_security_groups(
                    groupnames=[self._rule.grants[0].name])[0]
                return AWSSecurityGroup(self.parent._provider, cg)
        return None


class AWSContainerObject(BaseContainerObject):

    def __init__(self, provider, key):
        self._provider = provider
        self._key = key

    @property
    def name(self):
        """
        Get this object's name.
        """
        return self._key.name

    def download(self, target_stream):
        """
        Download this object and write its
        contents to the target_stream.
        """
        shutil.copyfileobj(self._key, target_stream)

    def upload(self, data):
        """
        Set the contents of this object to the data read from the source
        string.
        """
        self._key.set_contents_from_string(data)

    def delete(self):
        """
        Delete this object.

        :rtype: bool
        :return: True if successful
        """
        self._key.delete()


class AWSContainer(BaseContainer):

    def __init__(self, provider, bucket):
        self._provider = provider
        self._bucket = bucket

    @property
    def name(self):
        """
        Get this container's name.
        """
        return self._bucket.name

    def get(self, key):
        """
        Retrieve a given object from this container.
        """
        raise NotImplementedError(
            'Container.list not implemented by this provider')

    def list(self):
        """
        List all objects within this container.

        :rtype: ContainerObject
        :return: List of all available ContainerObjects within this container
        """
        objects = self._bucket.list()
        return [AWSContainerObject(self._provider, obj) for obj in objects]

    def delete(self, delete_contents=False):
        """
        Delete this container.
        """
        self._bucket.delete()

    def create_object(self, name):
        key = Key(self._bucket, name)
        return AWSContainerObject(self._provider, key)


class AWSRegion(BaseRegion):

    def __init__(self, provider, aws_region):
        self._provider = provider
        self._aws_region = aws_region

    @property
    def id(self):
        return self._aws_region.name

    @property
    def name(self):
        return self._aws_region.name

    @property
    def zones(self):
        """
        Accesss information about placement zones within this region.
        """
        pass

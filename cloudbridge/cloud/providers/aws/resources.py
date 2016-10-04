"""
DataTypes used by this provider
"""
from cloudbridge.cloud.base.resources import BaseAttachmentInfo
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseLaunchConfig
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSecurityGroup
from cloudbridge.cloud.base.resources import BaseSecurityGroupRule
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseFloatingIP
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import VolumeState
from cloudbridge.cloud.interfaces.services import VolumeService
from datetime import datetime
import hashlib
import inspect
import json

from boto.exception import EC2ResponseError
from boto.s3.key import Key
from retrying import retry


class AWSMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'failed': MachineImageState.ERROR
    }

    def __init__(self, provider, image):
        super(AWSMachineImage, self).__init__(provider)
        if isinstance(image, AWSMachineImage):
            # pylint:disable=protected-access
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
        self._ec2_image.deregister()

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
            # pylint:disable=protected-access
            self._ec2_image = image._ec2_image
        else:
            # image no longer exists
            self._ec2_image.state = "unknown"


class AWSPlacementZone(BasePlacementZone):

    def __init__(self, provider, zone, region):
        super(AWSPlacementZone, self).__init__(provider)
        if isinstance(zone, AWSPlacementZone):
            # pylint:disable=protected-access
            self._aws_zone = zone._aws_zone
            self._aws_region = zone._aws_region
        else:
            self._aws_zone = zone
            self._aws_region = region

    @property
    def id(self):
        """
        Get the zone id

        :rtype: ``str``
        :return: ID for this zone as returned by the cloud middleware.
        """
        return self._aws_zone

    @property
    def name(self):
        """
        Get the zone name.

        :rtype: ``str``
        :return: Name for this zone as returned by the cloud middleware.
        """
        return self._aws_zone

    @property
    def region_name(self):
        """
        Get the region that this zone belongs to.

        :rtype: ``str``
        :return: Name of this zone's region as returned by the cloud middleware
        """
        return self._aws_region


class AWSInstanceType(BaseInstanceType):

    def __init__(self, provider, instance_dict):
        super(AWSInstanceType, self).__init__(provider)
        self._inst_dict = instance_dict

    @property
    def id(self):
        return str(self._inst_dict['instance_type'])

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
        super(AWSInstance, self).__init__(provider)
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
    # pylint:disable=arguments-differ
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
    def instance_type_id(self):
        """
        Get the instance type name.
        """
        return self._ec2_instance.instance_type

    @property
    def instance_type(self):
        """
        Get the instance type.
        """
        return self._provider.compute.instance_types.find(
            name=self._ec2_instance.instance_type)[0]

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
    def zone_id(self):
        """
        Get the placement zone id where this instance is running.
        """
        return self._ec2_instance.placement

    @property
    def security_groups(self):
        """
        Get the security groups associated with this instance.
        """
        # boto instance.groups field returns a ``Group`` object so need to
        # convert that into a ``SecurityGroup`` object before creating a
        # cloudbridge SecurityGroup object
        return [self._provider.security.security_groups.get(group.id)
                for group in self._ec2_instance.groups]

    @property
    def security_group_ids(self):
        """
        Get the security groups IDs associated with this instance.
        """
        return [group.id for group in self._ec2_instance.groups]

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
        if self._ec2_instance.vpc_id:
            aid = self._provider._vpc_conn.get_all_addresses([ip_address])[0]
            return self._provider._ec2_conn.associate_address(
                self._ec2_instance.id, allocation_id=aid.allocation_id)
        else:
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
        super(AWSVolume, self).__init__(provider)
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
        for tag in self._volume.tags or list():
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the volume name.
        """
        self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def description(self):
        for tag in self._volume.tags or list():
            if tag.get('Key') == 'Description':
                return tag.get('Value')
        return None

    @description.setter
    def description(self, value):
        self._volume.create_tags(Tags=[{'Key': 'Description', 'Value': value}])

    @property
    def size(self):
        return self._volume.size

    @property
    def create_time(self):
        return self._volume.create_time

    @property
    def zone_id(self):
        return self._volume.availability_zone

    @property
    def source(self):
        if self._volume.snapshot_id:
            return self._provider.block_store.snapshots.get(
                self._volume.snapshot_id)
        return None

    @property
    def attachments(self):
        return [
            BaseAttachmentInfo(self,
                               x.InstanceId,
                               x.Device)
            for x in self._volume.attachments
        ] if self._volume.attachments else None

    def attach(self, instance, device):
        """
        Attach this volume to an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            AWSInstance) else instance
        self._volume.attach_to_instance(InstanceId=instance_id,
                                        Device=device)

    def detach(self, instance, device, force=False):
        """
        Detach this volume from an instance.
        """
        instance_id = instance.id if isinstance(
            instance,
            AWSInstance) else instance
        self._volume.detach_from_instance(
            InstanceId=instance_id,
            Device=device,
            Force=force)

    def create_snapshot(self, name, description=None):
        """
        Create a snapshot of this Volume.
        """
        snap = AWSSnapshot(
            self._provider,
            self._volume.create_snapshot(
                Description=description))
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
            self._volume.state, VolumeState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this volume by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._volume.reload()
            return True
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.status = 'unknown'
            return False


class AWSSnapshot(BaseSnapshot):

    # Ref: http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/
    # ApiReference-cmd-DescribeSnapshots.html
    SNAPSHOT_STATE_MAP = {
        'pending': SnapshotState.PENDING,
        'deleting': SnapshotState.PENDING,
        'completed': SnapshotState.AVAILABLE,
        'error': SnapshotState.ERROR
    }

    def __init__(self, provider, snapshot):
        super(AWSSnapshot, self).__init__(provider)
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
        for tag in self._snapshot.tags or list():
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the snapshot name.
        """
        self._snapshot.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def description(self):
        for tag in self._snapshot.tags or list():
            if tag.get('Key') == 'Description':
                return tag.get('Value')
        return None

    @description.setter
    def description(self, value):
        self._snapshot.create_tags(Tags=[{
            'Key': 'Description', 'Value': value}])

    @property
    def size(self):
        return self._snapshot.volume_size

    @property
    def volume_id(self):
        return self._snapshot.volume_id

    @property
    def create_time(self):
        return self._snapshot.start_time

    @property
    def state(self):
        return AWSSnapshot.SNAPSHOT_STATE_MAP.get(
            self._snapshot.state, SnapshotState.UNKNOWN)

    def refresh(self):
        """
        Refreshes the state of this snapshot by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._snapshot.reload()
            return True
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.status = 'unknown'
            return False

    def delete(self):
        """
        Delete this snapshot.
        """
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        """
        Create a new Volume from this Snapshot.
        """
        cb_vol = VolumeService(self._provider).create(
            name=self.name,
            size=size,
            zone=placement,
            iops=iops,
            snapshot=self._snapshot)
        cb_vol.name = "Created from {0} ({1})".format(self.id, self.name)
        return cb_vol


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
        return self._key_pair.key_material


class AWSSecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, security_group):
        super(AWSSecurityGroup, self).__init__(provider, security_group)

    @property
    def name(self):
        """
        Return the name of this security group.
        """
        return self._security_group.group_name

    @property
    def rules(self):
        return [AWSSecurityGroupRule(self._provider, r, self)
                for r in self._security_group.ip_permissions]

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

        :rtype: :class:``.SecurityGroupRule``
        :return: Rule object if successful or ``None``.
        """
        try:
            if self._security_group.authorize_ingress(
                    IpProtocol=ip_protocol,
                    FromPort=from_port,
                    ToPort=to_port,
                    CidrIp=cidr_ip):
                return self.get_rule(ip_protocol, from_port, to_port, cidr_ip)
        except EC2ResponseError as ec2e:
            if ec2e.code == "InvalidPermission.Duplicate":
                return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                                     src_group)
            else:
                raise ec2e
        return None

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        for rule in self._security_group.ip_permissions:
            if ip_protocol and rule['IpProtocol'] != ip_protocol:
                continue
            elif from_port and rule['FromPort'] != from_port:
                continue
            elif to_port and rule['ToPort'] != to_port:
                continue
            elif cidr_ip:
                if cidr_ip not in [x['CidrIp'] for x in rule['IpRanges']]:
                    continue
            return AWSSecurityGroupRule(self._provider, rule, self)
        return None

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._security_group.reload()
            return True
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            return False

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not(inspect.isroutine(a)))
        js = {k: v for(k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = [json.loads(r) for r in json_rules]
        return json.dumps(js, sort_keys=True)


class AWSSecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, provider, rule, parent):
        super(AWSSecurityGroupRule, self).__init__(provider, rule, parent)

    @property
    def id(self):
        """
        AWS does not support rule IDs so compose one.
        """
        md5 = hashlib.md5()
        md5.update("{0}-{1}-{2}-{3}".format(
            self.ip_protocol, self.from_port, self.to_port, self.cidr_ip)
                   .encode('ascii'))
        return md5.hexdigest()

    @property
    def ip_protocol(self):
        return self._rule.get('IpProtocol')

    @property
    def from_port(self):
        return self._rule.get('FromPort', 0)

    @property
    def to_port(self):
        return self._rule.get('ToPort', 0)

    @property
    def cidr_ip(self):
        if len(self._rule.get('IpRanges', list())) > 0:
            return self._rule['IpRanges'][0].get('CidrIp')
        return None

    @property
    def group(self):
        # If there's a parent security group, use it
        if self.parent:
            return self.parent
        # If not, fall-back to checking rule group pairs
        if len(self._rule['UserIdGroupPairs']) > 0:
            if self._rule['UserIdGroupPairs'][0]['GroupId']:
                return AWSSecurityGroup(
                    self._provider,
                    self._provider.ec2_conn.SecurityGroup(
                        self._rule['UserIdGroupPairs'][0]['GroupId']))
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        _js = {k: v for(k, v) in attr if not k.startswith('_')}
        _js['group'] = self.group.id if self.group else ''
        _js['parent'] = self.parent.id if self.parent else ''
        return json.dumps(_js, sort_keys=True)

    def delete(self):
        self.group._security_group.revoke_ingress(
            SourceSecurityGroupName=self.group.name)


class AWSBucketObject(BaseBucketObject):

    def __init__(self, provider, key):
        super(AWSBucketObject, self).__init__(provider)
        self._key = key

    @property
    def id(self):
        return self._key.name

    @property
    def name(self):
        """
        Get this object's name.
        """
        return self._key.name

    @property
    def size(self):
        """
        Get this object's size.
        """
        return self._key.size

    @property
    def last_modified(self):
        """
        Get the date and time this object was last modified.
        """
        lm = datetime.strptime(self._key.last_modified,
                               "%Y-%m-%dT%H:%M:%S.%fZ")
        return lm.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def iter_content(self):
        """
        Returns this object's content as an
        iterable.
        """
        return self._key

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


class AWSBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(AWSBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        """
        Get this bucket's name.
        """
        return self._bucket.name

    def get(self, key):
        """
        Retrieve a given object from this bucket.
        """
        key = Key(self._bucket, key)
        if key.exists():
            return AWSBucketObject(self._provider, key)
        return None

    def list(self, limit=None, marker=None):
        """
        List all objects within this bucket.

        :rtype: BucketObject
        :return: List of all available BucketObjects within this bucket.
        """
        objects = [AWSBucketObject(self._provider, obj)
                   for obj in self._bucket.list()]
        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def delete(self, delete_contents=False):
        """
        Delete this bucket.
        """
        self._bucket.delete()

    def create_object(self, name):
        key = Key(self._bucket, name)
        return AWSBucketObject(self._provider, key)


class AWSRegion(BaseRegion):

    def __init__(self, provider, aws_region):
        super(AWSRegion, self).__init__(provider)
        self._aws_region = aws_region

    @property
    def id(self):
        return self.name

    @property
    def name(self):
        return self._aws_region.get('RegionName')

    @property
    def zones(self):
        """
        Accesss information about placement zones within this region.
        """
        return [
            AWSPlacementZone(
                self._provider,
                x['ZoneName'],
                x['RegionName']
            ) for x in
            self._provider.ec2_conn.meta.client.describe_availability_zones(
                Filters=[{
                    'Name': 'region-name',
                    'Values': [self.name]
                }]
            ).get('AvailabilityZones', list())
        ]


class AWSNetwork(BaseNetwork):

    # Ref:
    # docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeVpcs.html
    _NETWORK_STATE_MAP = {
        'pending': NetworkState.PENDING,
        'available': NetworkState.AVAILABLE,
    }

    def __init__(self, provider, network):
        super(AWSNetwork, self).__init__(provider)
        self._vpc = network

    @property
    def id(self):
        return self._vpc.id

    @property
    def name(self):
        """
        Get the network name.

        .. note:: the network must have a (case sensitive) tag ``Name``
        """
        for tag in self._vpc.tags or list():
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the network name.
        """
        self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def external(self):
        """
        For AWS, all VPC networks can be connected to the Internet so always
        return ``True``.
        """
        return True

    @property
    def state(self):
        return AWSNetwork._NETWORK_STATE_MAP.get(
            self._vpc.state, NetworkState.UNKNOWN)

    @property
    def cidr_block(self):
        return self._vpc.cidr_block

    def delete(self):
        return self._vpc.delete()

    def subnets(self):
        return [AWSSubnet(self._provider, x) for x in self._vpc.subnets.all()]

    def create_subnet(self, cidr_block, name=None):
        subnet = AWSSubnet(
            self._provider,
            self._vpc.create_subnet(CidrBlock=cidr_block))
        if name:
            subnet.name = name
        return subnet

    def refresh(self):
        """
        Refreshes the state of this instance by re-querying the cloud provider
        for its latest state.
        """
        try:
            self._vpc.reload()
            return True
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            return False


class AWSSubnet(BaseSubnet):

    def __init__(self, provider, subnet):
        super(AWSSubnet, self).__init__(provider)
        self._subnet = subnet

    @property
    def id(self):
        return self._subnet.id

    @property
    def name(self):
        """
        Get the subnet name.

        .. note:: the subnet must have a (case sensitive) tag ``Name``
        """
        for tag in self._subnet.tags or list():
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the subnet name.
        """
        self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def cidr_block(self):
        return self._subnet.cidr_block

    @property
    def network_id(self):
        return self._subnet.vpc_id

    def delete(self):
        return self._subnet.delete()


class AWSFloatingIP(BaseFloatingIP):

    def __init__(self, provider, floating_ip):
        super(AWSFloatingIP, self).__init__(provider)
        self._ip = floating_ip

    @property
    def id(self):
        return self._ip.allocation_id

    @property
    def public_ip(self):
        return self._ip.public_ip

    @property
    def private_ip(self):
        return self._ip.private_ip_address

    def in_use(self):
        return True if self._ip.instance_id else False

    def delete(self):
        return self._ip.release()


class AWSRouter(BaseRouter):

    def __init__(self, provider, router):
        super(AWSRouter, self).__init__(provider)
        self._router = router
        self._ROUTE_CIDR = '0.0.0.0/0'

    def _route_table(self, subnet_id):
        """
        Get the route table for the VPC to which the supplied subnet belongs.

        Note that only the first route table will be returned in case more
        exist.

        :type subnet_id: ``str``
        :param subnet_id: Filter the route table by the network in which the
                          given subnet belongs.

        :rtype: :class:`boto.vpc.routetable.RouteTable`
        :return: A RouteTable object.
        """
        return self._provider.ec2_conn.route_tables.filter(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [
                    self._provider.ec2_conn.Subnet(subnet_id).vpc_id
                ]
            }]
        )[0]

    @property
    def id(self):
        return self._router.id

    @property
    def name(self):
        """
        Get the router name.

        .. note:: the router must have a (case sensitive) tag ``Name``
        """
        for tag in self._router.tags or list():
            if tag.get('Key') == 'Name':
                return tag.get('Value')
        return None

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        """
        Set the router name.
        """
        self._router.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    def refresh(self):
        try:
            self._router.reload()
            return True
        except (EC2ResponseError, ValueError):
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            return False

    @property
    def state(self):
        self.refresh()  # Explicitly refresh the local object
        if self._router.attachments and \
           self._router.attachments[0]['State'] == 'available':
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self):
        if self.state == RouterState.ATTACHED:
            return self._router.attachments[0]['VpcId']
        return None

    def delete(self):
        return self._router.delete()

    def attach_network(self, network_id):
        return self._router.attach_to_vpc(VpcId=network_id)

    def detach_network(self):
        return self._router.detach_from_vpc(VpcId=network_id)

    def add_route(self, subnet_id):
        """
        Add a default route to this router.

        For AWS, routes are added to a route table. A route table is assoc.
        with a network vs. a subnet so we retrieve the network via the subnet.
        Note that the subnet must belong to the same network as the router
        is attached to.

        Further, only a single route can be added, targeting the Internet
        (i.e., destination CIDR block ``0.0.0.0/0``).
        """
        return self._route_table(subnet_id).create_route(
            DestinationCidrBlock=self._ROUTE_CIDR,
            GatewayId=self.id)

    def remove_route(self, subnet_id):
        """
        Remove the default Internet route from this router.

        .. seealso:: ``add_route`` method
        """
        for route in self._route_table(subnet_id).routes or list():
            if route.gateway_id == self.id:
                route.delete()


class AWSLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AWSLaunchConfig, self).__init__(provider)

    def add_network_interface(self, net_id):
        """
        Extract a subnet within the network identified by ``net_id``.

        AWS requires a subnet ID to be supplied vs. a network (i.e., VPC) ID
        so just pull out one subnet within the network (currently, the first
        one).
        """
        net = self.provider.network.get(net_id)
        sns = net.subnets()
        if sns:
            sn = sns[0]
        self.network_interfaces.append(sn.id)

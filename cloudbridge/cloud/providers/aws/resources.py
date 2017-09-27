"""
DataTypes used by this provider
"""
import hashlib
import inspect

from botocore.exceptions import ClientError

from cloudbridge.cloud.base.resources import BaseAttachmentInfo
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseFloatingIP
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInstanceType
from cloudbridge.cloud.base.resources import BaseInternetGateway
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
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.interfaces.resources import GatewayState
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import SubnetState
from cloudbridge.cloud.interfaces.resources import VolumeState

from .helpers import find_tag_value
from .helpers import trim_empty_params


class AWSMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'transient': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'deregistered': MachineImageState.ERROR,
        'failed': MachineImageState.ERROR,
        'error': MachineImageState.ERROR,
        'invalid': MachineImageState.ERROR
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
        return self._ec2_image.id

    @property
    def name(self):
        try:
            return self._ec2_image.name
        except AttributeError:
            return None

    @property
    def description(self):
        try:
            return self._ec2_image.description
        except AttributeError:
            return None

    @property
    def min_disk(self):
        vols = [bdm.get('Ebs', {}) for bdm in
                self._ec2_image.block_device_mappings if
                bdm.get('DeviceName') == self._ec2_image.root_device_name]
        if vols:
            return vols[0].get('VolumeSize')
        else:
            return None

    def delete(self):
        snapshot_id = [
            bdm.get('Ebs', {}).get('SnapshotId') for bdm in
            self._ec2_image.block_device_mappings if
            bdm.get('DeviceName') == self._ec2_image.root_device_name]

        self._ec2_image.deregister()
        self.wait_for([MachineImageState.UNKNOWN, MachineImageState.ERROR])
        snapshot = self._provider.block_store.snapshots.get(snapshot_id[0])
        if snapshot:
            snapshot.delete()

    @property
    def state(self):
        try:
            return AWSMachineImage.IMAGE_STATE_MAP.get(
                self._ec2_image.state, MachineImageState.UNKNOWN)
        except AttributeError:
            return MachineImageState.UNKNOWN

    def refresh(self):
        self._ec2_image.reload()


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
        return self._aws_zone

    @property
    def name(self):
        return self._aws_zone

    @property
    def region_name(self):
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
        return self._ec2_instance.id

    @property
    def name(self):
        """
        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return find_tag_value(self._ec2_instance.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._ec2_instance.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def public_ips(self):
        return [self._ec2_instance.public_ip_address]

    @property
    def private_ips(self):
        return [self._ec2_instance.private_ip_address]

    @property
    def instance_type_id(self):
        return self._ec2_instance.instance_type

    @property
    def instance_type(self):
        return self._provider.compute.instance_types.find(
            name=self._ec2_instance.instance_type)[0]

    def reboot(self):
        self._ec2_instance.reboot()

    def terminate(self):
        self._ec2_instance.terminate()

    @property
    def image_id(self):
        return self._ec2_instance.image_id

    @property
    def zone_id(self):
        return self._ec2_instance.placement.get('AvailabilityZone')

    @property
    def security_groups(self):
        return [
            self._provider.security.security_groups.get(group_id)
            for group_id in self.security_group_ids
            ]

    @property
    def security_group_ids(self):
        return list(set([
                            group.get('GroupId') for group in
                            self._ec2_instance.security_groups
                            ]))

    @property
    def key_pair_name(self):
        return self._ec2_instance.key_name

    def create_image(self, name):
        self.assert_valid_resource_name(name)

        image = AWSMachineImage(self._provider,
                                self._ec2_instance.create_image(Name=name))
        # Wait for the image to exist
        self._provider.ec2_conn.meta.client.get_waiter('image_exists').wait(
            ImageIds=[image.id])
        # Return the image
        image.refresh()
        return image

    def add_floating_ip(self, ip_address):
        allocation_id = (
            None if not self._ec2_instance.vpc_id else
            ip_address.id if isinstance(ip_address, AWSFloatingIP) else
            [x for x in self._provider.networking.networks.floating_ips
             if x.public_ip == ip_address][0].id)
        params = trim_empty_params({
            'InstanceId': self.id,
            'PublicIp': None if self._ec2_instance.vpc_id else ip_address,
            'AllocationId': allocation_id})
        self._provider.ec2_conn.meta.client.associate_address(**params)
        self.refresh()

    def remove_floating_ip(self, ip_address):
        association_id = (
            None if not self._ec2_instance.vpc_id else
            ip_address._ip.association_id
            if isinstance(ip_address, AWSFloatingIP) else
            [x for x in self._ec2_instance.vpc_addresses.all()
             if x.public_ip == ip_address][0].association_id)
        params = trim_empty_params({
            'PublicIp': None if self._ec2_instance.vpc_id else ip_address,
            'AssociationId': association_id})
        self._provider.ec2_conn.meta.client.disassociate_address(**params)
        self.refresh()

    def add_security_group(self, sg):
        self._ec2_instance.modify_attribute(
            Groups=self.security_group_ids + [sg.id])

    def remove_security_group(self, sg):
        self._ec2_instance.modify_attribute(
            Groups=([sg_id for sg_id in self.security_group_ids
                     if sg_id != sg.id]))

    @property
    def state(self):
        try:
            return AWSInstance.INSTANCE_STATE_MAP.get(
                self._ec2_instance.state['Name'], InstanceState.UNKNOWN)
        except AttributeError:
            return InstanceState.UNKNOWN

    def refresh(self):
        try:
            self._ec2_instance.reload()
        except ClientError:
            # The instance no longer exists and cannot be refreshed.
            # set the state to unknown
            self._ec2_instance.state = {'Name': InstanceState.UNKNOWN}

    def _wait_till_exists(self, timeout=None, interval=None):
        self._ec2_instance.wait_until_exists()


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
        return find_tag_value(self._volume.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def description(self):
        return find_tag_value(self._volume.tags, 'Description')

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
                               a.get('InstanceId'),
                               a.get('Device'))
            for a in self._volume.attachments
            ][0] if self._volume.attachments else None

    def attach(self, instance, device):
        instance_id = instance.id if isinstance(
            instance,
            AWSInstance) else instance
        self._volume.attach_to_instance(InstanceId=instance_id,
                                        Device=device)

    def detach(self, force=False):
        a = self.attachments
        if a:
            self._volume.detach_from_instance(
                InstanceId=a.instance_id,
                Device=a.device,
                Force=force)

    def create_snapshot(self, name, description=None):
        snap = AWSSnapshot(
            self._provider,
            self._volume.create_snapshot(
                Description=description))
        snap.name = name
        return snap

    def delete(self):
        self._volume.delete()

    @property
    def state(self):
        try:
            return AWSVolume.VOLUME_STATE_MAP.get(
                self._volume.state, VolumeState.UNKNOWN)
        except AttributeError:
            return VolumeState.UNKNOWN

    def refresh(self):
        try:
            self._volume.reload()
        except ClientError:
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._volume.state = VolumeState.UNKNOWN


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
        return find_tag_value(self._snapshot.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._snapshot.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def description(self):
        return find_tag_value(self._snapshot.tags, 'Description')

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
        try:
            return AWSSnapshot.SNAPSHOT_STATE_MAP.get(
                self._snapshot.state, SnapshotState.UNKNOWN)
        except AttributeError:
            return SnapshotState.UNKNOWN

    def refresh(self):
        try:
            self._snapshot.reload()
        except ClientError:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._snapshot.state = SnapshotState.UNKNOWN

    def delete(self):
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        cb_vol = self._provider.block_store.volumes.create(
            name=self.name,
            size=size,
            zone=placement,
            snapshot=self.id)
        cb_vol.wait_till_ready()
        cb_vol.name = "from_snap_{0}".format(self.name or self.id)
        return cb_vol


class AWSKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AWSKeyPair, self).__init__(provider, key_pair)

    @property
    def material(self):
        return self._key_pair.key_material


class AWSSecurityGroup(BaseSecurityGroup):

    def __init__(self, provider, security_group):
        super(AWSSecurityGroup, self).__init__(provider, security_group)

    @property
    def name(self):
        return self._security_group.group_name

    @property
    def network_id(self):
        return self._security_group.vpc_id

    @property
    def rules(self):
        return [AWSSecurityGroupRule(self._provider, r, self)
                for r in self._security_group.ip_permissions]

    def add_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        try:
            src_group_id = (
                src_group.id if isinstance(src_group, SecurityGroup)
                else src_group)

            ip_perm_entry = {
                'IpProtocol': ip_protocol,
                'FromPort': from_port,
                'ToPort': to_port,
                'IpRanges': [{'CidrIp': cidr_ip}] if cidr_ip else None,
                'UserIdGroupPairs': [{
                    'GroupId': src_group_id}
                ] if src_group_id else None
            }
            # Filter out empty values to please Boto
            ip_perms = [trim_empty_params(ip_perm_entry)]
            self._security_group.authorize_ingress(IpPermissions=ip_perms)
            self._security_group.reload()
            return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                                 src_group_id)
        except ClientError as ec2e:
            if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
                return self.get_rule(ip_protocol, from_port, to_port, cidr_ip,
                                     src_group)
            else:
                raise ec2e

    def get_rule(self, ip_protocol=None, from_port=None, to_port=None,
                 cidr_ip=None, src_group=None):
        src_group_id = (src_group.id if isinstance(src_group, SecurityGroup)
                        else src_group)
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
            elif src_group_id:
                if src_group_id not in [
                    group_pair.get('GroupId') for group_pair in
                    rule.get('UserIdGroupPairs', [])]:
                    continue
            return AWSSecurityGroupRule(self._provider, rule, self)
        return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return js


class AWSSecurityGroupRule(BaseSecurityGroupRule):

    def __init__(self, provider, rule, parent):
        super(AWSSecurityGroupRule, self).__init__(provider, rule, parent)

    @property
    def id(self):
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
        if len(self._rule.get('IpRanges', [])) > 0:
            return self._rule['IpRanges'][0].get('CidrIp')
        return None

    @property
    def group_id(self):
        if len(self._rule['UserIdGroupPairs']) > 0:
            return self._rule['UserIdGroupPairs'][0]['GroupId']
        else:
            return None

    @property
    def group(self):
        if self.group_id:
            return AWSSecurityGroup(
                self._provider,
                self._provider.ec2_conn.SecurityGroup(self.group_id))
        else:
            return None

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        js['group'] = self.group.id if self.group else ''
        js['parent'] = self.parent.id if self.parent else ''
        return js

    def delete(self):

        ip_perm_entry = {
            'IpProtocol': self.ip_protocol,
            'FromPort': self.from_port,
            'ToPort': self.to_port,
            'IpRanges': [{'CidrIp': self.cidr_ip}] if self.cidr_ip else None,
            'UserIdGroupPairs': [{
                'GroupId': self.group_id}
            ] if self.group_id else None
        }

        # Filter out empty values to please Boto
        ip_perms = [trim_empty_params(ip_perm_entry)]

        self.parent._security_group.revoke_ingress(IpPermissions=ip_perms)
        self.parent._security_group.reload()


class AWSBucketObject(BaseBucketObject):
    class BucketObjIterator():
        CHUNK_SIZE = 4096

        def __init__(self, body):
            self.body = body

        def __iter__(self):
            while True:
                data = self.read(self.CHUNK_SIZE)
                if data:
                    yield data
                else:
                    break

        def read(self, length):
            return self.body.read(amt=length)

        def close(self):
            return self.body.close()

    def __init__(self, provider, obj):
        super(AWSBucketObject, self).__init__(provider)
        self._obj = obj

    @property
    def id(self):
        return self._obj.key

    @property
    def name(self):
        return self.id

    @property
    def size(self):
        return self._obj.size

    @property
    def last_modified(self):
        return self._obj.last_modified.strftime("%Y-%m-%dT%H:%M:%S.%f")

    def iter_content(self):
        return self.BucketObjIterator(self._obj.get().get('Body'))

    def upload(self, data):
        self._obj.put(Body=data)

    def upload_from_file(self, path):
        self._obj.upload_file(path)

    def delete(self):
        self._obj.delete()

    def generate_url(self, expires_in=0):
        return self._provider.s3_conn.meta.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._obj.bucket_name, 'Key': self.id},
            ExpiresIn=expires_in)


class AWSBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(AWSBucket, self).__init__(provider)
        self._bucket = bucket

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        return self._bucket.name

    def get(self, name):
        try:
            obj = self._bucket.Object(name)
            # load() throws an error if object does not exist
            obj.load()
            return AWSBucketObject(self._provider, obj)
        except ClientError:
            return None

    def list(self, limit=None, marker=None, prefix=None):
        if prefix:
            boto_objs = self._bucket.objects.filter(Prefix=prefix)
        else:
            boto_objs = self._bucket.objects.all()
        objects = [AWSBucketObject(self._provider, obj)
                   for obj in boto_objs]

        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        objects = [obj for obj in self if obj.name == name]

        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def delete(self, delete_contents=False):
        self._bucket.delete()

    def create_object(self, name):
        obj = self._bucket.Object(name)
        return AWSBucketObject(self._provider, obj)


class AWSRegion(BaseRegion):

    def __init__(self, provider, aws_region):
        super(AWSRegion, self).__init__(provider)
        self._aws_region = aws_region

    @property
    def id(self):
        return self._aws_region.get('RegionName')

    @property
    def name(self):
        return self.id

    @property
    def zones(self):
        if self.id == self._provider.region_name:  # optimisation
            conn = self._provider.ec2_conn
        else:
            conn = self._provider._conect_ec2_region(region_name=self.id)

        zones = (conn.meta.client.describe_availability_zones()
                 .get('AvailabilityZones', []))
        return [AWSPlacementZone(self._provider, zone.get('ZoneName'),
                                 self.id)
                for zone in zones]


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
        return find_tag_value(self._vpc.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
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
        try:
            return AWSNetwork._NETWORK_STATE_MAP.get(
                self._vpc.state, NetworkState.UNKNOWN)
        except AttributeError:
            return NetworkState.UNKNOWN

    @property
    def cidr_block(self):
        return self._vpc.cidr_block

    def delete(self):
        return self._vpc.delete()

    @property
    def subnets(self):
        return [AWSSubnet(self._provider, s) for s in self._vpc.subnets.all()]

    def refresh(self):
        try:
            self._vpc.reload()
        except ClientError:
            # The network no longer exists and cannot be refreshed.
            # set the status to unknown
            self._vpc.state = NetworkState.UNKNOWN

    def wait_till_ready(self, timeout=None, interval=None):
        self._provider.ec2_conn.meta.client.get_waiter('vpc_available').wait(
            VpcIds=[self.id])
        self.refresh()


class AWSSubnet(BaseSubnet):

    # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html
    _SUBNET_STATE_MAP = {
        'pending': SubnetState.PENDING,
        'available': SubnetState.AVAILABLE,
    }

    def __init__(self, provider, subnet):
        super(AWSSubnet, self).__init__(provider)
        self._subnet = subnet

    @property
    def id(self):
        return self._subnet.id

    @property
    def name(self):
        return find_tag_value(self._subnet.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    @property
    def cidr_block(self):
        return self._subnet.cidr_block

    @property
    def network_id(self):
        return self._subnet.vpc_id

    @property
    def zone(self):
        return AWSPlacementZone(self._provider, self._subnet.availability_zone,
                                self._provider.region_name)

    def delete(self):
        self._subnet.delete()

    @property
    def state(self):
        try:
            return self._SUBNET_STATE_MAP.get(
                self._subnet.state, SubnetState.UNKNOWN)
        except AttributeError:
            return SubnetState.UNKNOWN

    def refresh(self):
        subnet = self._provider.networking.subnets.get(self.id)
        if subnet:
            # pylint:disable=protected-access
            self._subnet = subnet._subnet
        else:
            # subnet no longer exists
            self._subnet.state = SubnetState.UNKNOWN


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

    def __init__(self, provider, route_table):
        super(AWSRouter, self).__init__(provider)
        self._route_table = route_table

    @property
    def id(self):
        return self._route_table.id

    @property
    def name(self):
        return find_tag_value(self._route_table.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._route_table.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    def refresh(self):
        try:
            self._route_table.reload()
        except ClientError:
            self._route_table.associations = None

    @property
    def state(self):
        if self._route_table.associations:
            return RouterState.ATTACHED
        return RouterState.DETACHED

    @property
    def network_id(self):
        return self._route_table.vpc_id

    def delete(self):
        self._route_table.delete()

    def attach_subnet(self, subnet):
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        self._route_table.associate_with_subnet(SubnetId=subnet_id)
        self.refresh()

    def detach_subnet(self, subnet):
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        associations = [a for a in self._route_table.associations
                        if a.subnet_id == subnet_id]
        for a in associations:
            a.delete()
        self.refresh()

    def attach_gateway(self, gateway):
        gw_id = (gateway.id if isinstance(gateway, AWSInternetGateway)
                 else gateway)
        return self._provider.ec2_conn.meta.client.attach_internet_gateway(
            InternetGatewayId=gw_id, VpcId=self._route_table.vpc_id)

    def detach_gateway(self, gateway):
        gw_id = (gateway.id if isinstance(gateway, AWSInternetGateway)
                 else gateway)
        return self._provider.ec2_conn.meta.client.detach_internet_gateway(
            InternetGatewayId=gw_id, VpcId=self._route_table.vpc_id)


class AWSInternetGateway(BaseInternetGateway):

    def __init__(self, provider, gateway):
        super(AWSInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._gateway.state = ''

    @property
    def id(self):
        return self._gateway.id

    @property
    def name(self):
        return find_tag_value(self._gateway.tags, 'Name')

    @name.setter
    # pylint:disable=arguments-differ
    def name(self, value):
        self.assert_valid_resource_name(value)
        self._gateway.create_tags(Tags=[{'Key': 'Name', 'Value': value}])

    def refresh(self):
        try:
            self._gateway.reload()
        except ClientError:
            self._gateway.state = GatewayState.UNKNOWN

    @property
    def state(self):
        if self._gateway.state == GatewayState.UNKNOWN:
            return GatewayState.UNKNOWN
        else:
            return GatewayState.AVAILABLE

    @property
    def network_id(self):
        if self._gateway.attachments:
            return self._gateway.attachments[0].get('VpcId')
        return None

    def delete(self):
        self._gateway.delete()


class AWSLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AWSLaunchConfig, self).__init__(provider)
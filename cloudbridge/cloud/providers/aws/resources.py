"""
DataTypes used by this provider
"""
import hashlib
import inspect
import logging

from botocore.exceptions import ClientError

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import BaseAttachmentInfo
from cloudbridge.cloud.base.resources import BaseBucket
from cloudbridge.cloud.base.resources import BaseBucketContainer
from cloudbridge.cloud.base.resources import BaseBucketObject
from cloudbridge.cloud.base.resources import BaseFloatingIP
from cloudbridge.cloud.base.resources import BaseFloatingIPContainer
from cloudbridge.cloud.base.resources import BaseGatewayContainer
from cloudbridge.cloud.base.resources import BaseInstance
from cloudbridge.cloud.base.resources import BaseInternetGateway
from cloudbridge.cloud.base.resources import BaseKeyPair
from cloudbridge.cloud.base.resources import BaseLaunchConfig
from cloudbridge.cloud.base.resources import BaseMachineImage
from cloudbridge.cloud.base.resources import BaseNetwork
from cloudbridge.cloud.base.resources import BasePlacementZone
from cloudbridge.cloud.base.resources import BaseRegion
from cloudbridge.cloud.base.resources import BaseRouter
from cloudbridge.cloud.base.resources import BaseSnapshot
from cloudbridge.cloud.base.resources import BaseSubnet
from cloudbridge.cloud.base.resources import BaseVMFirewall
from cloudbridge.cloud.base.resources import BaseVMFirewallRule
from cloudbridge.cloud.base.resources import BaseVMFirewallRuleContainer
from cloudbridge.cloud.base.resources import BaseVMType
from cloudbridge.cloud.base.resources import BaseVolume
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.interfaces.exceptions import InvalidValueException
from cloudbridge.cloud.interfaces.resources import GatewayState
from cloudbridge.cloud.interfaces.resources import InstanceState
from cloudbridge.cloud.interfaces.resources import MachineImageState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import SubnetState
from cloudbridge.cloud.interfaces.resources import TrafficDirection
from cloudbridge.cloud.interfaces.resources import VolumeState

from .helpers import BotoEC2Service
from .helpers import find_tag_value
from .helpers import trim_empty_params

log = logging.getLogger(__name__)


class AWSMachineImage(BaseMachineImage):

    IMAGE_STATE_MAP = {
        'pending': MachineImageState.PENDING,
        'transient': MachineImageState.PENDING,
        'available': MachineImageState.AVAILABLE,
        'deregistered': MachineImageState.PENDING,
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
        except (AttributeError, ClientError) as e:
            log.warn("Cannot get name for image {0}: {1}".format(self.id, e))

    @property
    # pylint:disable=arguments-differ
    def label(self):
        """
        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return find_tag_value(self._ec2_image.tags, 'Name')

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._ec2_image.create_tags(Tags=[{'Key': 'Name',
                                           'Value': value or ""}])

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
        snapshot = self._provider.storage.snapshots.get(snapshot_id[0])
        if snapshot:
            snapshot.delete()

    @property
    def state(self):
        try:
            return AWSMachineImage.IMAGE_STATE_MAP.get(
                self._ec2_image.state, MachineImageState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
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
        return self.id

    @property
    def region_name(self):
        return self._aws_region


class AWSVMType(BaseVMType):

    def __init__(self, provider, instance_dict):
        super(AWSVMType, self).__init__(provider)
        self._inst_dict = instance_dict

    @property
    def id(self):
        return str(self._inst_dict['instance_type'])

    @property
    def name(self):
        return self.id

    @property
    def family(self):
        return self._inst_dict.get('family')

    @property
    def vcpus(self):
        vcpus = self._inst_dict.get('vCPU')
        if vcpus == 'N/A':
            return None
        return vcpus

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
        return {key: val for key, val in self._inst_dict.items()
                if key not in ["instance_type", "family", "vCPU", "memory"]}


class AWSInstance(BaseInstance):

    # ref:
    # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
    INSTANCE_STATE_MAP = {
        'pending': InstanceState.PENDING,
        'running': InstanceState.RUNNING,
        'shutting-down': InstanceState.CONFIGURING,
        'terminated': InstanceState.DELETED,
        'stopping': InstanceState.CONFIGURING,
        'stopped': InstanceState.STOPPED
    }

    def __init__(self, provider, ec2_instance):
        super(AWSInstance, self).__init__(provider)
        self._ec2_instance = ec2_instance
        self._unknown_state = False

    @property
    def id(self):
        return self._ec2_instance.id

    @property
    def name(self):
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        """
        .. note:: an instance must have a (case sensitive) tag ``Name``
        """
        return find_tag_value(self._ec2_instance.tags, 'Name')

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
                                              'Value': value or ""}])

    @property
    def public_ips(self):
        return ([self._ec2_instance.public_ip_address]
                if self._ec2_instance.public_ip_address else [])

    @property
    def private_ips(self):
        return ([self._ec2_instance.private_ip_address]
                if self._ec2_instance.private_ip_address else [])

    @property
    def vm_type_id(self):
        return self._ec2_instance.instance_type

    @property
    def vm_type(self):
        return self._provider.compute.vm_types.find(
            name=self._ec2_instance.instance_type)[0]

    def reboot(self):
        self._ec2_instance.reboot()

    def delete(self):
        self._ec2_instance.terminate()

    @property
    def image_id(self):
        return self._ec2_instance.image_id

    @property
    def zone_id(self):
        return self._ec2_instance.placement.get('AvailabilityZone')

    @property
    def subnet_id(self):
        return self._ec2_instance.subnet_id

    @property
    def vm_firewalls(self):
        return [
            self._provider.security.vm_firewalls.get(fw_id)
            for fw_id in self.vm_firewall_ids
        ]

    @property
    def vm_firewall_ids(self):
        return list(set([
            group.get('GroupId') for group in
            self._ec2_instance.security_groups
        ]))

    @property
    def key_pair_id(self):
        return self._ec2_instance.key_name

    def create_image(self, label):
        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')

        image = AWSMachineImage(self._provider,
                                self._ec2_instance.create_image(Name=name))
        # Wait for the image to exist
        self._provider.ec2_conn.meta.client.get_waiter('image_exists').wait(
            ImageIds=[image.id])
        # Add image label
        image.label = label
        # Return the image
        image.refresh()
        return image

    def _get_fip(self, floating_ip):
        """Get a floating IP object based on the supplied allocation ID."""
        return AWSFloatingIP(
            self._provider, list(self._provider.ec2_conn.vpc_addresses.filter(
                AllocationIds=[floating_ip]))[0])

    def add_floating_ip(self, floating_ip):
        fip = (floating_ip if isinstance(floating_ip, AWSFloatingIP)
               else self._get_fip(floating_ip))
        params = trim_empty_params({
            'InstanceId': self.id,
            'PublicIp': None if self._ec2_instance.vpc_id else
            fip.public_ip,
            # pylint:disable=protected-access
            'AllocationId': fip._ip.allocation_id})
        self._provider.ec2_conn.meta.client.associate_address(**params)
        self.refresh()

    def remove_floating_ip(self, floating_ip):
        fip = (floating_ip if isinstance(floating_ip, AWSFloatingIP)
               else self._get_fip(floating_ip))
        params = trim_empty_params({
            'PublicIp': None if self._ec2_instance.vpc_id else
            fip.public_ip,
            # pylint:disable=protected-access
            'AssociationId': fip._ip.association_id})
        self._provider.ec2_conn.meta.client.disassociate_address(**params)
        self.refresh()

    def add_vm_firewall(self, firewall):
        self._ec2_instance.modify_attribute(
            Groups=self.vm_firewall_ids + [firewall.id])

    def remove_vm_firewall(self, firewall):
        self._ec2_instance.modify_attribute(
            Groups=([fw_id for fw_id in self.vm_firewall_ids
                     if fw_id != firewall.id]))

    @property
    def state(self):
        if self._unknown_state:
            return InstanceState.UNKNOWN
        try:
            return AWSInstance.INSTANCE_STATE_MAP.get(
                self._ec2_instance.state['Name'], InstanceState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
            return InstanceState.UNKNOWN

    def refresh(self):
        try:
            self._ec2_instance.reload()
            self._unknown_state = False
        except ClientError:
            # The instance no longer exists and cannot be refreshed.
            # set the state to unknown
            self._unknown_state = True

    # pylint:disable=unused-argument
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
        self._unknown_state = False

    @property
    def id(self):
        return self._volume.id

    @property
    def name(self):
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        try:
            return find_tag_value(self._volume.tags, 'Name')
        except ClientError as e:
            log.warn("Cannot get label for volume {0}: {1}".format(self.id, e))

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

    @property
    def description(self):
        return find_tag_value(self._volume.tags, 'Description')

    @description.setter
    def description(self, value):
        self._volume.create_tags(Tags=[{'Key': 'Description',
                                        'Value': value or ""}])

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
            return self._provider.storage.snapshots.get(
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

    def create_snapshot(self, label, description=None):
        self.assert_valid_resource_label(label)
        snap = AWSSnapshot(
            self._provider,
            self._volume.create_snapshot(
                TagSpecifications=[{'ResourceType': 'snapshot',
                                    'Tags': [{'Key': 'Name',
                                              'Value': label}]}],
                Description=description or ""))
        snap.wait_till_ready()
        return snap

    def delete(self):
        self._volume.delete()

    @property
    def state(self):
        if self._unknown_state:
            return VolumeState.UNKNOWN
        try:
            return AWSVolume.VOLUME_STATE_MAP.get(
                self._volume.state, VolumeState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
            return VolumeState.UNKNOWN

    def refresh(self):
        try:
            self._volume.reload()
            self._unknown_state = False
        except ClientError:
            # The volume no longer exists and cannot be refreshed.
            # set the status to unknown
            self._unknown_state = True


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
        self._unknown_state = False

    @property
    def id(self):
        return self._snapshot.id

    @property
    def name(self):
        return self.id

    @property
    # pylint:disable=arguments-differ
    def label(self):
        try:
            return find_tag_value(self._snapshot.tags, 'Name')
        except ClientError as e:
            log.warn("Cannot get label for snap {0}: {1}".format(self.id, e))

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._snapshot.create_tags(Tags=[{'Key': 'Name',
                                          'Value': value or ""}])

    @property
    def description(self):
        return find_tag_value(self._snapshot.tags, 'Description')

    @description.setter
    def description(self, value):
        self._snapshot.create_tags(Tags=[{
            'Key': 'Description', 'Value': value or ""}])

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
        if self._unknown_state:
            return SnapshotState.UNKNOWN
        try:
            return AWSSnapshot.SNAPSHOT_STATE_MAP.get(
                self._snapshot.state, SnapshotState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
            return SnapshotState.UNKNOWN

    def refresh(self):
        try:
            self._snapshot.reload()
            self._unknown_state = False
        except ClientError:
            # The snapshot no longer exists and cannot be refreshed.
            # set the status to unknown
            self._unknown_state = True

    def delete(self):
        self._snapshot.delete()

    def create_volume(self, placement, size=None, volume_type=None, iops=None):
        label = "from-snap-{0}".format(self.label or self.id)
        cb_vol = self._provider.storage.volumes.create(
            label=label,
            size=size,
            zone=placement,
            snapshot=self.id)
        cb_vol.wait_till_ready()
        return cb_vol


class AWSKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AWSKeyPair, self).__init__(provider, key_pair)


class AWSVMFirewall(BaseVMFirewall):

    def __init__(self, provider, _vm_firewall):
        super(AWSVMFirewall, self).__init__(provider, _vm_firewall)
        self._rule_container = AWSVMFirewallRuleContainer(provider, self)

    @property
    def name(self):
        """
        Return the name of this VM firewall.
        """
        return self._vm_firewall.group_name

    @property
    def label(self):
        try:
            return find_tag_value(self._vm_firewall.tags, 'Name')
        except ClientError:
            return None

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._vm_firewall.create_tags(Tags=[{'Key': 'Name',
                                             'Value': value or ""}])

    @property
    def network_id(self):
        return self._vm_firewall.vpc_id

    @property
    def rules(self):
        return self._rule_container

    def refresh(self):
        self._vm_firewall.reload()

    def to_json(self):
        attr = inspect.getmembers(self, lambda a: not inspect.isroutine(a))
        js = {k: v for (k, v) in attr if not k.startswith('_')}
        json_rules = [r.to_json() for r in self.rules]
        js['rules'] = json_rules
        if js.get('network_id'):
            js.pop('network_id')  # Omit for consistency across cloud providers
        return js


class AWSVMFirewallRuleContainer(BaseVMFirewallRuleContainer):

    def __init__(self, provider, firewall):
        super(AWSVMFirewallRuleContainer, self).__init__(provider, firewall)

    def list(self, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [AWSVMFirewallRule(self.firewall,
                                   TrafficDirection.INBOUND, r)
                 for r in self.firewall._vm_firewall.ip_permissions]
        rules = rules + [
            AWSVMFirewallRule(
                self.firewall, TrafficDirection.OUTBOUND, r)
            for r in self.firewall._vm_firewall.ip_permissions_egress]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self,  direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        src_dest_fw_id = (
            src_dest_fw.id if isinstance(src_dest_fw, AWSVMFirewall)
            else src_dest_fw)

        # pylint:disable=protected-access
        ip_perm_entry = AWSVMFirewallRule._construct_ip_perms(
            protocol, from_port, to_port, cidr, src_dest_fw_id)
        # Filter out empty values to please Boto
        ip_perms = [trim_empty_params(ip_perm_entry)]

        try:
            if direction == TrafficDirection.INBOUND:
                # pylint:disable=protected-access
                self.firewall._vm_firewall.authorize_ingress(
                    IpPermissions=ip_perms)
            elif direction == TrafficDirection.OUTBOUND:
                # pylint:disable=protected-access
                self.firewall._vm_firewall.authorize_egress(
                    IpPermissions=ip_perms)
            else:
                raise InvalidValueException("direction", direction)
            self.firewall.refresh()
            return AWSVMFirewallRule(self.firewall, direction, ip_perm_entry)
        except ClientError as ec2e:
            if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
                return AWSVMFirewallRule(
                    self.firewall, direction, ip_perm_entry)
            else:
                raise ec2e


class AWSVMFirewallRule(BaseVMFirewallRule):

    def __init__(self, parent_fw, direction, rule):
        self._direction = direction
        super(AWSVMFirewallRule, self).__init__(parent_fw, rule)

        # cache id
        md5 = hashlib.md5()
        md5.update(self._name.encode('ascii'))
        self._id = md5.hexdigest()

    @property
    def id(self):
        return self._id

    @property
    def direction(self):
        return self._direction

    @property
    def protocol(self):
        return self._rule.get('IpProtocol')

    @property
    def from_port(self):
        return self._rule.get('FromPort')

    @property
    def to_port(self):
        return self._rule.get('ToPort')

    @property
    def cidr(self):
        if len(self._rule.get('IpRanges') or []) > 0:
            return self._rule['IpRanges'][0].get('CidrIp')
        return None

    @property
    def src_dest_fw_id(self):
        if len(self._rule.get('UserIdGroupPairs') or []) > 0:
            return self._rule['UserIdGroupPairs'][0]['GroupId']
        else:
            return None

    @property
    def src_dest_fw(self):
        if self.src_dest_fw_id:
            return AWSVMFirewall(
                self._provider,
                self._provider.ec2_conn.SecurityGroup(self.src_dest_fw_id))
        else:
            return None

    @staticmethod
    def _construct_ip_perms(protocol, from_port, to_port, cidr,
                            src_dest_fw_id):
        return {
            'IpProtocol': protocol,
            'FromPort': from_port,
            'ToPort': to_port,
            'IpRanges': [{'CidrIp': cidr}] if cidr else None,
            'UserIdGroupPairs': [{
                'GroupId': src_dest_fw_id}
            ] if src_dest_fw_id else None
        }

    def delete(self):
        ip_perm_entry = self._construct_ip_perms(
            self.protocol, self.from_port, self.to_port,
            self.cidr, self.src_dest_fw_id)

        # Filter out empty values to please Boto
        ip_perms = [trim_empty_params(ip_perm_entry)]

        # pylint:disable=protected-access
        if self.direction == TrafficDirection.INBOUND:
            self.firewall._vm_firewall.revoke_ingress(
                IpPermissions=ip_perms)
        else:
            self.firewall._vm_firewall.revoke_egress(
                IpPermissions=ip_perms)
        self.firewall.refresh()


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
        try:
            return self._obj.content_length
        except AttributeError:  # we're dealing with s3.ObjectSummary
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

    def generate_url(self, expires_in):
        return self._provider.s3_conn.meta.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self._obj.bucket_name, 'Key': self.id},
            ExpiresIn=expires_in)

    def refresh(self):
        self._obj.load()


class AWSBucket(BaseBucket):

    def __init__(self, provider, bucket):
        super(AWSBucket, self).__init__(provider)
        self._bucket = bucket
        self._object_container = AWSBucketContainer(provider, self)

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        return self.id

    @property
    def objects(self):
        return self._object_container

    def delete(self, delete_contents=False):
        self._bucket.delete()


class AWSBucketContainer(BaseBucketContainer):

    def __init__(self, provider, bucket):
        super(AWSBucketContainer, self).__init__(provider, bucket)

    def get(self, name):
        try:
            # pylint:disable=protected-access
            obj = self.bucket._bucket.Object(name)
            # load() throws an error if object does not exist
            obj.load()
            return AWSBucketObject(self._provider, obj)
        except ClientError:
            return None

    def list(self, limit=None, marker=None, prefix=None):
        if prefix:
            # pylint:disable=protected-access
            boto_objs = self.bucket._bucket.objects.filter(Prefix=prefix)
        else:
            # pylint:disable=protected-access
            boto_objs = self.bucket._bucket.objects.all()
        objects = [AWSBucketObject(self._provider, obj) for obj in boto_objs]
        return ClientPagedResultList(self._provider, objects,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches),
                                     limit=None, marker=None)

    def create(self, name):
        # pylint:disable=protected-access
        obj = self.bucket._bucket.Object(name)
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
            # pylint:disable=protected-access
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
        self._gtw_container = AWSGatewayContainer(provider, self)
        self._unknown_state = False

    @property
    def id(self):
        return self._vpc.id

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return find_tag_value(self._vpc.tags, 'Name')

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

    @property
    def external(self):
        """
        For AWS, all VPC networks can be connected to the Internet so always
        return ``True``.
        """
        return True

    @property
    def state(self):
        if self._unknown_state:
            return NetworkState.UNKNOWN
        try:
            return AWSNetwork._NETWORK_STATE_MAP.get(
                self._vpc.state, NetworkState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
            return NetworkState.UNKNOWN

    @property
    def cidr_block(self):
        return self._vpc.cidr_block

    def delete(self):
        self._vpc.delete()

    @property
    def subnets(self):
        return [AWSSubnet(self._provider, s) for s in self._vpc.subnets.all()]

    def refresh(self):
        try:
            self._vpc.reload()
            self._unknown_state = False
        except ClientError:
            # The network no longer exists and cannot be refreshed.
            # set the status to unknown
            self._unknown_state = True

    def wait_till_ready(self, timeout=None, interval=None):
        self._provider.ec2_conn.meta.client.get_waiter('vpc_available').wait(
            VpcIds=[self.id])
        self.refresh()

    @property
    def gateways(self):
        return self._gtw_container


class AWSSubnet(BaseSubnet):

    # http://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_DescribeSubnets.html
    _SUBNET_STATE_MAP = {
        'pending': SubnetState.PENDING,
        'available': SubnetState.AVAILABLE,
    }

    def __init__(self, provider, subnet):
        super(AWSSubnet, self).__init__(provider)
        self._subnet = subnet
        self._unknown_state = False

    @property
    def id(self):
        return self._subnet.id

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return find_tag_value(self._subnet.tags, 'Name')

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

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
        if self._unknown_state:
            return SubnetState.UNKNOWN
        try:
            return self._SUBNET_STATE_MAP.get(
                self._subnet.state, SubnetState.UNKNOWN)
        except Exception:
            # Ignore all exceptions when querying state
            return SubnetState.UNKNOWN

    def refresh(self):
        try:
            self._subnet.reload()
            self._unknown_state = False
        except ClientError:
            # subnet no longer exists
            self._unknown_state = True


class AWSFloatingIPContainer(BaseFloatingIPContainer):

    def __init__(self, provider, gateway):
        super(AWSFloatingIPContainer, self).__init__(provider, gateway)
        self.svc = BotoEC2Service(provider=self._provider,
                                  cb_resource=AWSFloatingIP,
                                  boto_collection_name='vpc_addresses')

    def get(self, fip_id):
        log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
        return self.svc.get(fip_id)

    def list(self, limit=None, marker=None):
        log.debug("Listing all floating IPs under gateway %s", self.gateway)
        return self.svc.list(limit=limit, marker=marker)

    def create(self):
        log.debug("Creating a floating IP under gateway %s", self.gateway)
        ip = self._provider.ec2_conn.meta.client.allocate_address(
            Domain='vpc')
        return AWSFloatingIP(
            self._provider,
            self._provider.ec2_conn.VpcAddress(ip.get('AllocationId')))


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

    @property
    def in_use(self):
        return True if self._ip.instance_id else False

    def delete(self):
        self._ip.release()

    def refresh(self):
        self._ip.reload()


class AWSRouter(BaseRouter):

    def __init__(self, provider, route_table):
        super(AWSRouter, self).__init__(provider)
        self._route_table = route_table

    @property
    def id(self):
        return self._route_table.id

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return find_tag_value(self._route_table.tags, 'Name')

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._route_table.create_tags(Tags=[{'Key': 'Name',
                                             'Value': value or ""}])

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

    @property
    def subnets(self):
        return [AWSSubnet(self._provider, rta.subnet)
                for rta in self._route_table.associations if rta.subnet]

    def attach_gateway(self, gateway):
        gw_id = (gateway.id if isinstance(gateway, AWSInternetGateway)
                 else gateway)
        if self._route_table.create_route(
                DestinationCidrBlock='0.0.0.0/0', GatewayId=gw_id):
            return True
        return False

    def detach_gateway(self, gateway):
        gw_id = (gateway.id if isinstance(gateway, AWSInternetGateway)
                 else gateway)
        return self._provider.ec2_conn.meta.client.detach_internet_gateway(
            InternetGatewayId=gw_id, VpcId=self._route_table.vpc_id)


class AWSGatewayContainer(BaseGatewayContainer):

    def __init__(self, provider, network):
        super(AWSGatewayContainer, self).__init__(provider, network)
        self.svc = BotoEC2Service(provider=provider,
                                  cb_resource=AWSInternetGateway,
                                  boto_collection_name='internet_gateways')

    def get_or_create_inet_gateway(self):
        log.debug("Get or create inet gateway on net %s",
                  self._network)
        network_id = self._network.id if isinstance(
            self._network, AWSNetwork) else self._network
        # Don't filter by label because it may conflict with at least the
        # default VPC that most accounts have but that network is typically
        # without a name.
        gtw = self.svc.find(filter_name='attachment.vpc-id',
                            filter_value=network_id)
        if gtw:
            return gtw[0]  # There can be only one gtw attached to a VPC
        # Gateway does not exist so create one and attach to the supplied net
        cb_gateway = self.svc.create('create_internet_gateway')
        cb_gateway._gateway.create_tags(
            Tags=[{'Key': 'Name',
                   'Value': AWSInternetGateway.CB_DEFAULT_INET_GATEWAY_NAME
                   }])
        cb_gateway._gateway.attach_to_vpc(VpcId=network_id)
        return cb_gateway

    def delete(self, gateway):
        log.debug("Service deleting AWS Gateway %s", gateway)
        gateway_id = gateway.id if isinstance(
            gateway, AWSInternetGateway) else gateway
        gateway = self.svc.get(gateway_id)
        if gateway:
            gateway.delete()

    def list(self, limit=None, marker=None):
        log.debug("Listing current AWS internet gateways for net %s.",
                  self._network.id)
        fltr = [{'Name': 'attachment.vpc-id', 'Values': [self._network.id]}]
        return self.svc.list(limit=None, marker=None, Filters=fltr)


class AWSInternetGateway(BaseInternetGateway):

    def __init__(self, provider, gateway):
        super(AWSInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._gateway.state = ''
        self._fips_container = AWSFloatingIPContainer(provider, self)

    @property
    def id(self):
        return self._gateway.id

    @property
    def name(self):
        return find_tag_value(self._gateway.tags, 'Name')

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
        try:
            if self.network_id:
                self._gateway.detach_from_vpc(VpcId=self.network_id)
            self._gateway.delete()
        except ClientError as e:
            log.warn("Error deleting gateway {0}: {1}".format(self.id, e))

    @property
    def floating_ips(self):
        return self._fips_container


class AWSLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AWSLaunchConfig, self).__init__(provider)

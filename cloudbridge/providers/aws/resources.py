"""
DataTypes used by this provider
"""
import hashlib
import inspect
import logging

from botocore.exceptions import ClientError

import tenacity

from cloudbridge.base.resources import BaseAttachmentInfo
from cloudbridge.base.resources import BaseBucket
from cloudbridge.base.resources import BaseBucketObject
from cloudbridge.base.resources import BaseDnsRecord
from cloudbridge.base.resources import BaseDnsZone
from cloudbridge.base.resources import BaseFloatingIP
from cloudbridge.base.resources import BaseInstance
from cloudbridge.base.resources import BaseInternetGateway
from cloudbridge.base.resources import BaseKeyPair
from cloudbridge.base.resources import BaseLaunchConfig
from cloudbridge.base.resources import BaseMachineImage
from cloudbridge.base.resources import BaseNetwork
from cloudbridge.base.resources import BasePlacementZone
from cloudbridge.base.resources import BaseRegion
from cloudbridge.base.resources import BaseRouter
from cloudbridge.base.resources import BaseSnapshot
from cloudbridge.base.resources import BaseSubnet
from cloudbridge.base.resources import BaseVMFirewall
from cloudbridge.base.resources import BaseVMFirewallRule
from cloudbridge.base.resources import BaseVMType
from cloudbridge.base.resources import BaseVolume
from cloudbridge.interfaces.resources import GatewayState
from cloudbridge.interfaces.resources import InstanceState
from cloudbridge.interfaces.resources import MachineImageState
from cloudbridge.interfaces.resources import NetworkState
from cloudbridge.interfaces.resources import RouterState
from cloudbridge.interfaces.resources import SnapshotState
from cloudbridge.interfaces.resources import SubnetState
from cloudbridge.interfaces.resources import VolumeState

from .helpers import find_tag_value
from .helpers import trim_empty_params
from .subservices import AWSBucketObjectSubService
from .subservices import AWSDnsRecordSubService
from .subservices import AWSFloatingIPSubService
from .subservices import AWSGatewaySubService
from .subservices import AWSSubnetSubService
from .subservices import AWSVMFirewallRuleSubService

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._ec2_image.create_tags(Tags=[{'Key': 'Name',
                                           'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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
            # pylint:disable=protected-access
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
        return str(self._inst_dict.get('InstanceType'))

    @property
    def name(self):
        return self.id

    @property
    def family(self):
        # Limited to whether CurrentGeneration or not
        curr = self._inst_dict.get('CurrentGeneration')
        if curr:
            return 'CurrentGeneration'
        return None

    @property
    def vcpus(self):
        vcpus = self._inst_dict.get('VCpuInfo')
        if vcpus:
            return vcpus.get('DefaultVCpus', 0)
        return 0

    @property
    def ram(self):
        ram = self._inst_dict.get('MemoryInfo')
        if ram:
            mib = ram.get('SizeInMiB', 0)
            if mib:
                return mib / 1024
        return 0

    @property
    def size_root_disk(self):
        return 0

    @property
    def size_ephemeral_disks(self):
        storage = self._inst_dict.get('InstanceStorageInfo')
        if storage:
            return storage.get('TotalSizeInGB', 0)
        return 0

    @property
    def num_ephemeral_disks(self):
        storage = self._inst_dict.get('InstanceStorageInfo')
        if storage:
            return storage.get("Disks", {}).get("Count", 0)
        return 0

    @property
    def extra_data(self):
        return {key: val for key, val in self._inst_dict.items()
                if key not in ["InstanceType", "VCpuInfo", "MemoryInfo"]}


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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
                                              'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _wait_for_image(self, image):
        self._provider.ec2_conn.meta.client.get_waiter('image_exists').wait(
            ImageIds=[image.id])

    def create_image(self, label):
        self.assert_valid_resource_label(label)
        name = self._generate_name_from_label(label, 'cb-img')

        image = AWSMachineImage(self._provider,
                                self._ec2_instance.create_image(Name=name))
        # Wait for the image to exist
        self._wait_for_image(image)
        # Add image label
        image.label = label
        # Return the image
        image.refresh()
        return image

    def _get_fip(self, floating_ip):
        """Get a floating IP object based on the supplied allocation ID."""
        return self._provider.networking._floating_ips.get(None, floating_ip)

    def add_floating_ip(self, floating_ip):
        fip = (floating_ip if isinstance(floating_ip, AWSFloatingIP)
               else self._get_fip(floating_ip))
        # pylint:disable=protected-access
        params = trim_empty_params({
            'InstanceId': self.id,
            'PublicIp': None if self._ec2_instance.vpc_id else
            fip.public_ip,
            'AllocationId': fip._ip.allocation_id})
        self._provider.ec2_conn.meta.client.associate_address(**params)
        self.refresh()

    def remove_floating_ip(self, floating_ip):
        fip = (floating_ip if isinstance(floating_ip, AWSFloatingIP)
               else self._get_fip(floating_ip))
        # pylint:disable=protected-access
        params = trim_empty_params({
            'PublicIp': None if self._ec2_instance.vpc_id else
            fip.public_ip,
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
        # refresh again to make sure instance status is in sync
        self._ec2_instance.reload()


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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(Exception),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _wait_till_volume_attached(self, instance_id):
        self.refresh()
        if not self.attachments.instance_id == instance_id:
            raise Exception(f"Volume {self.id} is not yet attached to"
                            f"instance {instance_id}")

    def attach(self, instance, device):
        instance_id = instance.id if isinstance(
            instance,
            AWSInstance) else instance
        self._volume.attach_to_instance(InstanceId=instance_id,
                                        Device=device)
        self._wait_till_volume_attached(instance_id)

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._snapshot.create_tags(Tags=[{'Key': 'Name',
                                          'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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

    def create_volume(self, size=None, volume_type=None, iops=None):
        label = "from-snap-{0}".format(self.label or self.id)
        cb_vol = self._provider.storage.volumes.create(
            label=label,
            size=size,
            snapshot=self.id)
        cb_vol.wait_till_ready()
        return cb_vol


class AWSKeyPair(BaseKeyPair):

    def __init__(self, provider, key_pair):
        super(AWSKeyPair, self).__init__(provider, key_pair)


class AWSVMFirewall(BaseVMFirewall):

    def __init__(self, provider, _vm_firewall):
        super(AWSVMFirewall, self).__init__(provider, _vm_firewall)
        self._rule_container = AWSVMFirewallRuleSubService(provider, self)

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._vm_firewall.create_tags(Tags=[{'Key': 'Name',
                                             'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

    @property
    def description(self):
        try:
            return find_tag_value(self._vm_firewall.tags, 'Description')
        except ClientError:
            return None

    @description.setter
    # pylint:disable=arguments-differ
    def description(self, value):
        self._vm_firewall.create_tags(Tags=[{'Key': 'Description',
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
        self._object_container = AWSBucketObjectSubService(provider, self)

    @property
    def id(self):
        return self._bucket.name

    @property
    def name(self):
        return self.id

    @property
    def objects(self):
        return self._object_container


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
            conn = self._provider._connect_ec2_region(region_name=self.id)

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
        self._unknown_state = False
        self._gtw_container = AWSGatewaySubService(provider, self)
        self._subnet_svc = AWSSubnetSubService(provider, self)

    @property
    def id(self):
        return self._vpc.id

    @property
    def name(self):
        return self.id

    @property
    def label(self):
        return find_tag_value(self._vpc.tags, 'Name')

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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

    @property
    def subnets(self):
        return self._subnet_svc

    def refresh(self):
        try:
            self._vpc.reload()
            self._unknown_state = False
        except ClientError:
            # The network no longer exists and cannot be refreshed.
            # set the status to unknown
            self._unknown_state = True

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _wait_for_vpc(self):
        self._provider.ec2_conn.meta.client.get_waiter('vpc_available').wait(
            VpcIds=[self.id])

    def wait_till_ready(self, timeout=None, interval=None):
        self._wait_for_vpc()
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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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
        return True if self._ip.association_id else False

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(ClientError),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _set_label(self, value):
        self._route_table.create_tags(Tags=[{'Key': 'Name',
                                             'Value': value or ""}])

    @label.setter
    # pylint:disable=arguments-differ
    def label(self, value):
        self.assert_valid_resource_label(value)
        self._set_label(value)

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

    @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                    retry=tenacity.retry_if_exception_type(Exception),
                    wait=tenacity.wait_fixed(5),
                    reraise=True)
    def _wait_till_subnet_attached(self, subnet_id):
        self.refresh()
        association = [a for a in self._route_table.associations
                       if a.subnet_id == subnet_id]
        if not association:
            raise Exception(
                f"Subnet {subnet_id} not attached to route table {self.id}")

    def attach_subnet(self, subnet):
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        self._route_table.associate_with_subnet(SubnetId=subnet_id)
        self._wait_till_subnet_attached(subnet_id)

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


class AWSInternetGateway(BaseInternetGateway):

    def __init__(self, provider, gateway):
        super(AWSInternetGateway, self).__init__(provider)
        self._gateway = gateway
        self._gateway.state = ''
        self._fips_container = AWSFloatingIPSubService(provider, self)

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

    @property
    def floating_ips(self):
        return self._fips_container


class AWSLaunchConfig(BaseLaunchConfig):

    def __init__(self, provider):
        super(AWSLaunchConfig, self).__init__(provider)


class AWSDnsZone(BaseDnsZone):

    def __init__(self, provider, dns_zone):
        super(AWSDnsZone, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_record_container = AWSDnsRecordSubService(provider, self)

    @property
    def id(self):
        # The ID contains a slash, do not allow this
        return self.escape_zone_id(self.aws_id)

    @property
    def aws_id(self):
        return self._dns_zone.get('Id')

    @staticmethod
    def escape_zone_id(value):
        return value.replace("/", "-") if value else None

    @staticmethod
    def unescape_zone_id(value):
        return value.replace("-", "/") if value else None

    @property
    def name(self):
        return self._dns_zone.get('Name')

    @property
    def admin_email(self):
        comment = self._dns_zone.get('Config', {}).get('Comment')
        if comment:
            email_field = comment.split(",")[0].split("=")
            if email_field[0] == "admin_email":
                return email_field[1]
            else:
                return None
        else:
            return None

    @property
    def records(self):
        return self._dns_record_container


class AWSDnsRecord(BaseDnsRecord):

    def __init__(self, provider, dns_zone, dns_record):
        super(AWSDnsRecord, self).__init__(provider)
        self._dns_zone = dns_zone
        self._dns_rec = dns_record

    @property
    def id(self):
        return self._dns_rec.get('Name') + ":" + self._dns_rec.get('Type')

    @property
    def name(self):
        return self._dns_rec.get('Name')

    @property
    def zone_id(self):
        return self._dns_zone.id

    @property
    def type(self):
        return self._dns_rec.get('Type')

    @property
    def data(self):
        return [rec.get('Value') for rec in
                self._dns_rec.get('ResourceRecords')]

    @property
    def ttl(self):
        return self._dns_rec.get('TTL')

    def delete(self):
        # pylint:disable=protected-access
        return self._provider.dns._records.delete(self._dns_zone, self)

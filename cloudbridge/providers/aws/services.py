"""Services implemented by the AWS provider."""
import ipaddress
import logging
import string
import uuid

from botocore.exceptions import ClientError

import tenacity

import cloudbridge.base.helpers as cb_helpers
from cloudbridge.base.middleware import dispatch
from cloudbridge.base.resources import ClientPagedResultList
from cloudbridge.base.resources import ServerPagedResultList
from cloudbridge.base.services import BaseBucketObjectService
from cloudbridge.base.services import BaseBucketService
from cloudbridge.base.services import BaseComputeService
from cloudbridge.base.services import BaseDnsRecordService
from cloudbridge.base.services import BaseDnsService
from cloudbridge.base.services import BaseDnsZoneService
from cloudbridge.base.services import BaseFloatingIPService
from cloudbridge.base.services import BaseGatewayService
from cloudbridge.base.services import BaseImageService
from cloudbridge.base.services import BaseInstanceService
from cloudbridge.base.services import BaseKeyPairService
from cloudbridge.base.services import BaseNetworkService
from cloudbridge.base.services import BaseNetworkingService
from cloudbridge.base.services import BaseRegionService
from cloudbridge.base.services import BaseRouterService
from cloudbridge.base.services import BaseSecurityService
from cloudbridge.base.services import BaseSnapshotService
from cloudbridge.base.services import BaseStorageService
from cloudbridge.base.services import BaseSubnetService
from cloudbridge.base.services import BaseVMFirewallRuleService
from cloudbridge.base.services import BaseVMFirewallService
from cloudbridge.base.services import BaseVMTypeService
from cloudbridge.base.services import BaseVolumeService
from cloudbridge.interfaces.exceptions import DuplicateResourceException
from cloudbridge.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.interfaces.exceptions import InvalidParamException
from cloudbridge.interfaces.exceptions import InvalidValueException
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume

from .helpers import BotoEC2Service
from .helpers import BotoS3Service
from .helpers import trim_empty_params
from .resources import AWSBucket
from .resources import AWSBucketObject
from .resources import AWSDnsRecord
from .resources import AWSDnsZone
from .resources import AWSFloatingIP
from .resources import AWSInstance
from .resources import AWSInternetGateway
from .resources import AWSKeyPair
from .resources import AWSLaunchConfig
from .resources import AWSMachineImage
from .resources import AWSNetwork
from .resources import AWSRegion
from .resources import AWSRouter
from .resources import AWSSnapshot
from .resources import AWSSubnet
from .resources import AWSVMFirewall
from .resources import AWSVMFirewallRule
from .resources import AWSVMType
from .resources import AWSVolume

log = logging.getLogger(__name__)


class AWSSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(AWSSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AWSKeyPairService(provider)
        self._vm_firewalls = AWSVMFirewallService(provider)
        self._vm_firewall_rule_svc = AWSVMFirewallRuleService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self):
        return self._vm_firewall_rule_svc


class AWSKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(AWSKeyPairService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSKeyPair,
                                  boto_collection_name='key_pairs')

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id):
        log.debug("Getting Key Pair Service %s", key_pair_id)
        return self.svc.get(key_pair_id)

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))

        log.debug("Searching for Key Pair %s", name)
        return self.svc.find(filters={'key-name': name})

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name, public_key_material=None):
        AWSKeyPair.assert_valid_resource_name(name)
        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()
        try:
            kp = self.svc.create('import_key_pair', KeyName=name,
                                 PublicKeyMaterial=public_key_material)
            kp.material = private_key
            return kp
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                raise DuplicateResourceException(
                    'Keypair already exists with name {0}'.format(name))
            else:
                raise e

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair):
        key_pair = (key_pair if isinstance(key_pair, AWSKeyPair) else
                    self.get(key_pair))
        if key_pair:
            # pylint:disable=protected-access
            key_pair._key_pair.delete()


class AWSVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(AWSVMFirewallService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVMFirewall,
                                  boto_collection_name='security_groups')

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id):
        log.debug("Getting Firewall Service with the id: %s", vm_firewall_id)
        return self.svc.get(vm_firewall_id)

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, description=None):
        AWSVMFirewall.assert_valid_resource_label(label)
        name = AWSVMFirewall._generate_name_from_label(label, 'cb-fw')
        network_id = network.id if isinstance(network, Network) else network
        obj = self.svc.create('create_security_group', GroupName=name,
                              Description=name,
                              VpcId=network_id)
        obj.label = label
        obj.description = description
        return obj

    @dispatch(event="provider.security.vm_firewalls.find",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        # Filter by name or label
        label = kwargs.pop('label', None)
        log.debug("Searching for Firewall Service %s", label)
        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))
        return self.svc.find(filters={'tag:Name': label})

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall):
        firewall = (vm_firewall if isinstance(vm_firewall, AWSVMFirewall)
                    else self.get(vm_firewall))
        if firewall:
            # pylint:disable=protected-access
            firewall._vm_firewall.delete()


class AWSVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider):
        super(AWSVMFirewallRuleService, self).__init__(provider)

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [AWSVMFirewallRule(firewall,
                                   TrafficDirection.INBOUND, r)
                 for r in firewall._vm_firewall.ip_permissions]
        # pylint:disable=protected-access
        rules = rules + [
            AWSVMFirewallRule(
                firewall, TrafficDirection.OUTBOUND, r)
            for r in firewall._vm_firewall.ip_permissions_egress]
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall,  direction, protocol=None, from_port=None,
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
                firewall._vm_firewall.authorize_ingress(
                    IpPermissions=ip_perms)
            elif direction == TrafficDirection.OUTBOUND:
                # pylint:disable=protected-access
                firewall._vm_firewall.authorize_egress(
                    IpPermissions=ip_perms)
            else:
                raise InvalidValueException("direction", direction)
            firewall.refresh()
            return AWSVMFirewallRule(firewall, direction, ip_perm_entry)
        except ClientError as ec2e:
            if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
                return AWSVMFirewallRule(
                    firewall, direction, ip_perm_entry)
            else:
                raise ec2e

    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall, rule):
        # pylint:disable=protected-access
        ip_perm_entry = rule._construct_ip_perms(
            rule.protocol, rule.from_port, rule.to_port,
            rule.cidr, rule.src_dest_fw_id)

        # Filter out empty values to please Boto
        ip_perms = [trim_empty_params(ip_perm_entry)]

        # pylint:disable=protected-access
        if rule.direction == TrafficDirection.INBOUND:
            firewall._vm_firewall.revoke_ingress(
                IpPermissions=ip_perms)
        else:
            # pylint:disable=protected-access
            firewall._vm_firewall.revoke_egress(
                IpPermissions=ip_perms)
        firewall.refresh()


class AWSStorageService(BaseStorageService):

    def __init__(self, provider):
        super(AWSStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AWSVolumeService(self.provider)
        self._snapshot_svc = AWSSnapshotService(self.provider)
        self._bucket_svc = AWSBucketService(self.provider)
        self._bucket_obj_svc = AWSBucketObjectService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc

    @property
    def _bucket_objects(self):
        return self._bucket_obj_svc


class AWSVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AWSVolumeService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVolume,
                                  boto_collection_name='volumes')

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id):
        return self.svc.get(volume_id)

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Volume Service %s", label)
        return self.svc.find(
            filters={'tag:Name': label,
                     'availability-zone': self.provider.zone_name})

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.find(
            filters={'availability-zone': self.provider.zone_name},
            limit=limit, marker=marker)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label, size, snapshot=None, description=None):
        AWSVolume.assert_valid_resource_label(label)
        zone_name = self.provider.zone_name
        snapshot_id = snapshot.id if isinstance(
            snapshot, AWSSnapshot) and snapshot else snapshot

        cb_vol = self.svc.create('create_volume', Size=size,
                                 AvailabilityZone=zone_name,
                                 SnapshotId=snapshot_id)
        # Wait until ready to tag instance
        cb_vol.wait_till_ready()
        cb_vol.label = label
        if description:
            cb_vol.description = description
        return cb_vol

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, vol):
        volume = vol if isinstance(vol, AWSVolume) else self.get(vol)
        if volume:
            # pylint:disable=protected-access
            volume._volume.delete()


class AWSSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(AWSSnapshotService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSSnapshot,
                                  boto_collection_name='snapshots')

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id):
        return self.svc.get(snapshot_id)

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        # Filter by description or label
        label = kwargs.get('label', None)

        obj_list = []
        if label:
            log.debug("Searching for AWS Snapshot with label %s", label)
            obj_list.extend(self.svc.find(filters={'tag:Name': label},
                                          OwnerIds=['self']))
        else:
            obj_list = list(self)
        filters = ['label']
        return cb_helpers.generic_find(filters, kwargs, obj_list)

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker,
                             OwnerIds=['self'])

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label, volume, description=None):
        AWSSnapshot.assert_valid_resource_label(label)
        volume_id = volume.id if isinstance(volume, AWSVolume) else volume

        cb_snap = self.svc.create('create_snapshot', VolumeId=volume_id)
        # Wait until ready to tag instance
        cb_snap.wait_till_ready()
        cb_snap.label = label
        if cb_snap.description:
            cb_snap.description = description
        return cb_snap

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot):
        snapshot = (snapshot if isinstance(snapshot, AWSSnapshot) else
                    self.get(snapshot))
        if snapshot:
            # pylint:disable=protected-access
            snapshot._snapshot.delete()


class AWSBucketService(BaseBucketService):

    def __init__(self, provider):
        super(AWSBucketService, self).__init__(provider)
        self.svc = BotoS3Service(provider=self.provider,
                                 cb_resource=AWSBucket,
                                 boto_collection_name='buckets')

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        try:
            # Make a call to make sure the bucket exists. There's an edge case
            # where a 403 response can occur when the bucket exists but the
            # user simply does not have permissions to access it. See below.
            self.provider.s3_conn.meta.client.head_bucket(Bucket=bucket_id)
            return AWSBucket(self.provider,
                             self.provider.s3_conn.Bucket(bucket_id))
        except ClientError as e:
            # If 403, it means the bucket exists, but the user does not have
            # permissions to access the bucket. However, limited operations
            # may be permitted (with a session token for example), so return a
            # Bucket instance to allow further operations.
            # http://stackoverflow.com/questions/32331456/using-boto-upload-file-to-s3-
            # sub-folder-when-i-have-no-permissions-on-listing-fo
            if e.response['Error']['Code'] == "403":
                log.warning("AWS Bucket %s already exists but user doesn't "
                            "have enough permissions to list its contents."
                            "Other operations may be available.",
                            bucket_id)
                return AWSBucket(self.provider,
                                 self.provider.s3_conn.Bucket(bucket_id))
        # For all other responses, it's assumed that the bucket does not exist.
        return None

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name, location=None):
        AWSBucket.assert_valid_resource_name(name)
        location = location or self.provider.region_name
        # Due to an API issue in S3, specifying us-east-1 as a
        # LocationConstraint results in an InvalidLocationConstraint.
        # Therefore, it must be special-cased and omitted altogether.
        # See: https://github.com/boto/boto3/issues/125
        # In addition, us-east-1 also behaves differently when it comes
        # to raising duplicate resource exceptions, so perform a manual
        # check
        if location == 'us-east-1':
            try:
                # check whether bucket already exists
                self.provider.s3_conn.meta.client.head_bucket(Bucket=name)
            except ClientError as e:
                if e.response['Error']['Code'] == "404":
                    # bucket doesn't exist, go ahead and create it
                    return self.svc.create('create_bucket', Bucket=name)
            raise DuplicateResourceException(
                    'Bucket already exists with name {0}'.format(name))
        else:
            try:
                return self.svc.create('create_bucket', Bucket=name,
                                       CreateBucketConfiguration={
                                           'LocationConstraint': location
                                        })
            except ClientError as e:
                if e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
                    raise DuplicateResourceException(
                        'Bucket already exists with name {0}'.format(name))
                else:
                    raise

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket):
        b = bucket if isinstance(bucket, AWSBucket) else self.get(bucket)
        if b:
            # pylint:disable=protected-access
            b._bucket.delete()


class AWSBucketObjectService(BaseBucketObjectService):

    def __init__(self, provider):
        super(AWSBucketObjectService, self).__init__(provider)

    def get(self, bucket, object_id):
        try:
            # pylint:disable=protected-access
            obj = bucket._bucket.Object(object_id)
            # load() throws an error if object does not exist
            obj.load()
            return AWSBucketObject(self.provider, obj)
        except ClientError:
            return None

    def list(self, bucket, limit=None, marker=None, prefix=None):
        if prefix:
            # pylint:disable=protected-access
            boto_objs = bucket._bucket.objects.filter(Prefix=prefix)
        else:
            # pylint:disable=protected-access
            boto_objs = bucket._bucket.objects.all()
        objects = [AWSBucketObject(self.provider, obj) for obj in boto_objs]
        return ClientPagedResultList(self.provider, objects,
                                     limit=limit, marker=marker)

    def find(self, bucket, **kwargs):
        # pylint:disable=protected-access
        obj_list = [AWSBucketObject(self.provider, o)
                    for o in bucket._bucket.objects.all()]
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def create(self, bucket, name):
        # pylint:disable=protected-access
        obj = bucket._bucket.Object(name)
        return AWSBucketObject(self.provider, obj)


class AWSComputeService(BaseComputeService):

    def __init__(self, provider):
        super(AWSComputeService, self).__init__(provider)
        self._vm_type_svc = AWSVMTypeService(self.provider)
        self._instance_svc = AWSInstanceService(self.provider)
        self._region_svc = AWSRegionService(self.provider)
        self._images_svc = AWSImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def vm_types(self):
        return self._vm_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class AWSImageService(BaseImageService):

    def __init__(self, provider):
        super(AWSImageService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSMachineImage,
                                  boto_collection_name='images')

    def get(self, image_id):
        log.debug("Getting AWS Image Service with the id: %s", image_id)
        return self.svc.get(image_id)

    def find(self, **kwargs):
        # Filter by name or label
        label = kwargs.pop('label', None)
        # Popped here, not used in the generic find
        owner = kwargs.pop('owners', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        extra_args = {}
        if owner:
            extra_args.update(Owners=owner)

        # The original list is made by combining both searches by "tag:Name"
        # and "AMI name" to allow for searches of public images
        if label:
            log.debug("Searching for AWS Image Service %s", label)
            obj_list = []
            obj_list.extend(
                self.svc.find(filters={'name': label}, **extra_args))
            obj_list.extend(
                self.svc.find(filters={'tag:Name': label}, **extra_args))
            return obj_list
        else:
            return []

    def list(self, filter_by_owner=True, limit=None, marker=None):
        return self.svc.list(Owners=['self'] if filter_by_owner else
                             ['amazon', 'self'],
                             limit=limit, marker=marker)


class AWSInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(AWSInstanceService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSInstance,
                                  boto_collection_name='instances')

    def _resolve_launch_options(self, subnet=None, zone_id=None,
                                vm_firewalls=None):
        """
        Work out interdependent launch options.

        Some launch options are required and interdependent so make sure
        they conform to the interface contract.

        :type subnet: ``Subnet``
        :param subnet: Subnet object within which to launch.

        :type zone_id: ``str``
        :param zone_id: ID of the zone where the launch should happen.

        :type vm_firewalls: ``list`` of ``id``
        :param vm_firewalls: List of firewall IDs.

        :rtype: triplet of ``str``
        :return: Subnet ID, zone ID and VM firewall IDs for launch.

        :raise ValueError: In case a conflicting combination is found.
        """
        if subnet:
            # subnet's zone takes precedence
            zone_id = subnet.zone.id
        if vm_firewalls and isinstance(vm_firewalls, list) and isinstance(
                vm_firewalls[0], VMFirewall):
            vm_firewall_ids = [fw.id for fw in vm_firewalls]
        else:
            vm_firewall_ids = vm_firewalls
        return subnet.id if subnet else None, zone_id, vm_firewall_ids

    def _process_block_device_mappings(self, launch_config):
        """
        Processes block device mapping information
        and returns a Boto BlockDeviceMapping object. If new volumes
        are requested (source is None and destination is VOLUME), they will be
        created and the relevant volume ids included in the mapping.
        """
        bdml = []
        # Assign letters from f onwards
        # http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/device_naming.html
        next_letter = iter(list(string.ascii_lowercase[6:]))
        # assign ephemeral devices from 0 onwards
        ephemeral_counter = 0
        for device in launch_config.block_devices:
            bdm = {}
            if device.is_volume:
                # Generate the device path
                bdm['DeviceName'] = \
                    '/dev/sd' + ('a1' if device.is_root else next(next_letter))
                ebs_def = {}
                if isinstance(device.source, Snapshot):
                    ebs_def['SnapshotId'] = device.source.id
                elif isinstance(device.source, Volume):
                    # TODO: We could create a snapshot from the volume
                    # and use that instead.
                    # Not supported
                    pass
                elif isinstance(device.source, MachineImage):
                    # Not supported
                    pass
                else:
                    # source is None, but destination is volume, therefore
                    # create a blank volume. This requires a size though.
                    if not device.size:
                        raise InvalidConfigurationException(
                            "The source is none and the destination is a"
                            " volume. Therefore, you must specify a size.")
                ebs_def['DeleteOnTermination'] = device.delete_on_terminate \
                    or True
                if device.size:
                    ebs_def['VolumeSize'] = device.size
                if ebs_def:
                    bdm['Ebs'] = ebs_def
            else:  # device is ephemeral
                bdm['VirtualName'] = 'ephemeral%s' % ephemeral_counter
            # Append the config
            bdml.append(bdm)

        return bdml

    def create_launch_config(self):
        return AWSLaunchConfig(self.provider)

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label, image, vm_type, subnet,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        AWSInstance.assert_valid_resource_label(label)
        image_id = image.id if isinstance(image, MachineImage) else image
        vm_size = vm_type.id if \
            isinstance(vm_type, VMType) else vm_type
        subnet = (self.provider.networking.subnets.get(subnet)
                  if isinstance(subnet, str) else subnet)
        zone_name = self.provider.zone_name
        key_pair_name = key_pair.name if isinstance(
            key_pair,
            KeyPair) else key_pair
        if launch_config:
            bdm = self._process_block_device_mappings(launch_config)
        else:
            bdm = None

        subnet_id, zone_id, vm_firewall_ids = \
            self._resolve_launch_options(subnet, zone_name, vm_firewalls)

        placement = {'AvailabilityZone': zone_id} if zone_id else None
        inst = self.svc.create(
            'create_instances',
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            KeyName=key_pair_name,
            SecurityGroupIds=vm_firewall_ids or None,
            UserData=str(user_data) or None,
            InstanceType=vm_size,
            Placement=placement,
            BlockDeviceMappings=bdm,
            SubnetId=subnet_id,
            IamInstanceProfile=kwargs.pop('iam_instance_profile', None)
        )
        if inst and len(inst) == 1:
            # Wait until the resource exists
            # pylint:disable=protected-access
            inst[0]._wait_till_exists()
            # Tag the instance w/ the name
            try:
                inst[0].label = label
            except Exception:
                # It's possible for the label setter to fail, because EC2
                # endpoints have a delay in syncing, and the instance may not
                # yet be visible if a different endpoint is hit. To compensate,
                # we retry in both the label setter, and raise here again just
                # in case the label setter fails for any other reason.
                inst[0].delete()
                raise
            return inst[0]
        raise ValueError(
            'Expected a single object response, got a list: %s' % inst)

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id):
        return self.svc.get(instance_id)

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        return self.svc.find(
            filters={'tag:Name': label,
                     'availability-zone': self.provider.zone_name})

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.find(
            filters={'availability-zone': self.provider.zone_name},
            limit=limit, marker=marker)

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance):
        aws_inst = (instance if isinstance(instance, AWSInstance) else
                    self.get(instance))
        if aws_inst:
            # pylint:disable=protected-access
            aws_inst._ec2_instance.terminate()


class AWSVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(AWSVMTypeService, self).__init__(provider)

    @dispatch(event="provider.compute.vm_types.get",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_type):
        try:
            t = self.provider.ec2_conn.meta.client.describe_instance_types(
                InstanceTypes=[vm_type]).get('InstanceTypes')[0]
        except ClientError as e:
            if 'InvalidInstanceType' in e.response.get('Error',
                                                       {}).get('Code'):
                return None
            else:
                raise e
        return AWSVMType(self.provider, t)

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        client = self.provider.ec2_conn.meta.client
        vmt_list_resp = client.describe_instance_type_offerings(
            LocationType='availability-zone',
            Filters=[{'Name': 'location',
                      'Values': [self.provider.zone_name]}],
            **trim_empty_params({'MaxRestuls': limit, 'NextToken': marker}))
        next_token = vmt_list_resp.get("NextToken")
        vmt_list_names = [x.get("InstanceType")
                          for x in vmt_list_resp.get('InstanceTypeOfferings')]
        # describe_instance_types call can get at most 100 types per request
        chunks = [vmt_list_names[x:x + 100]
                  for x in range(0, len(vmt_list_names), 100)]
        raw_types = []
        for chunk in chunks:
            raw_chunk = client.describe_instance_types(
                InstanceTypes=chunk).get('InstanceTypes')
            raw_types.extend(raw_chunk)
        cb_types = [AWSVMType(self.provider, t) for t in raw_types]
        return ServerPagedResultList(is_truncated=bool(next_token),
                                     marker=next_token,
                                     supports_total=False,
                                     data=cb_types)


class AWSRegionService(BaseRegionService):

    def __init__(self, provider):
        super(AWSRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id):
        log.debug("Getting AWS Region Service with the id: %s",
                  region_id)
        region = [r for r in self if r.id == region_id]
        if region:
            return region[0]
        else:
            return None

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        regions = [
            AWSRegion(self.provider, region) for region in
            self.provider.ec2_conn.meta.client.describe_regions()
            .get('Regions', [])]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self):
        return self.get(self._provider.region_name)


class AWSNetworkingService(BaseNetworkingService):

    def __init__(self, provider):
        super(AWSNetworkingService, self).__init__(provider)
        self._network_service = AWSNetworkService(self.provider)
        self._subnet_service = AWSSubnetService(self.provider)
        self._router_service = AWSRouterService(self.provider)
        self._gateway_service = AWSGatewayService(self.provider)
        self._floating_ip_service = AWSFloatingIPService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service

    @property
    def _gateways(self):
        return self._gateway_service

    @property
    def _floating_ips(self):
        return self._floating_ip_service


class AWSNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(AWSNetworkService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSNetwork,
                                  boto_collection_name='vpcs')

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id):
        return self.svc.get(network_id)

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.find",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Network Service %s", label)
        return self.svc.find(filters={'tag:Name': label})

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label, cidr_block):
        AWSNetwork.assert_valid_resource_label(label)

        cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
        # Wait until ready to tag instance
        cb_net.wait_till_ready()
        if label:
            cb_net.label = label
        self.provider.ec2_conn.meta.client.modify_vpc_attribute(
            VpcId=cb_net.id, EnableDnsHostnames={'Value': True})
        return cb_net

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network):
        network = (network if isinstance(network, AWSNetwork)
                   else self.get(network))
        if network:
            # pylint:disable=protected-access
            network._vpc.delete()

    def get_or_create_default(self):
        # # Look for provided default network
        # for net in self.provider.networking.networks:
        # pylint:disable=protected-access
        #     if net._vpc.is_default:
        #         return net

        # No provider-default, try CB-default instead
        default_nets = self.provider.networking.networks.find(
            label=AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
        if default_nets:
            return default_nets[0]

        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.provider.networking.networks.create(
                label=AWSNetwork.CB_DEFAULT_NETWORK_LABEL,
                cidr_block=AWSNetwork.CB_DEFAULT_IPV4RANGE)


class AWSSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AWSSubnetService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSSubnet,
                                  boto_collection_name='subnets')

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id):
        return self.svc.get(subnet_id)

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network=None, limit=None, marker=None):
        network_id = network.id if isinstance(network, AWSNetwork) else network
        if network_id:
            return self.svc.find(
                filters={'vpc-id': network_id,
                         'availability-zone': self.provider.zone_name},
                limit=limit, marker=marker)
        else:
            return self.svc.find(
                filters={'availability-zone': self.provider.zone_name},
                limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.find",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def find(self, network=None, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Subnet Service %s", label)
        return self.svc.find(
            filters={'tag:Name': label,
                     'availability-zone': self.provider.zone_name})

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, cidr_block):
        AWSSubnet.assert_valid_resource_label(label)
        zone_name = self.provider.zone_name

        network_id = network.id if isinstance(network, AWSNetwork) else network

        subnet = self.svc.create('create_subnet',
                                 VpcId=network_id,
                                 CidrBlock=cidr_block,
                                 AvailabilityZone=zone_name)
        if label:
            subnet.label = label
        return subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet):
        sn = subnet if isinstance(subnet, AWSSubnet) else self.get(subnet)
        if sn:
            # pylint:disable=protected-access
            sn._subnet.delete()

    def get_or_create_default(self):
        zone_name = self.provider.zone_name

        # # Look for provider default subnet in current zone
        # if zone_name:
        #     snl = self.svc.find('availabilityZone', zone_name)
        #
        # else:
        #     snl = self.svc.list()
        #     # Find first available default subnet by sorted order
        #     # of availability zone. Prefer zone us-east-1a over 1e,
        #     # because newer zones tend to have less compatibility
        #     # with different instance types (e.g. c5.large not available
        #     # on us-east-1e as of 14 Dec. 2017).
        #     # pylint:disable=protected-access
        #     snl.sort(key=lambda sn: sn._subnet.availability_zone)
        #
        # for sn in snl:
        #     # pylint:disable=protected-access
        #     if sn._subnet.default_for_az:
        #         return sn

        # If no provider-default subnet has been found, look for
        # cloudbridge-default by label. We suffix labels by availability zone,
        # thus we add the wildcard for the regular expression to find the
        # subnet
        snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")

        if snl:
            # pylint:disable=protected-access
            snl.sort(key=lambda sn: sn._subnet.availability_zone)
            for subnet in snl:
                if subnet.zone.name == zone_name:
                    return subnet

        # No default Subnet exists, try to create a CloudBridge-specific
        # subnet. This involves creating the network, subnets, internet
        # gateway, and connecting it all together so that the network has
        # Internet connectivity.

        # Check if a default net already exists and get it or create on
        default_net = self.provider.networking.networks.get_or_create_default()

        # Get/create an internet gateway for the default network and a
        # corresponding router if it does not already exist.
        # NOTE: Comment this out because the docs instruct users to setup
        # network connectivity manually. There's a bit of discrepancy here
        # though because the provider-default network will have Internet
        # connectivity (unlike the CloudBridge-default network with this
        # being commented) and is hence left in the codebase.
        # default_gtw = default_net.gateways.get_or_create()
        # router_label = "{0}-router".format(
        #   AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
        # default_routers = self.provider.networking.routers.find(
        #     label=router_label)
        # if len(default_routers) == 0:
        #     default_router = self.provider.networking.routers.create(
        #         router_label, default_net)
        #     default_router.attach_gateway(default_gtw)
        # else:
        #     default_router = default_routers[0]

        # Create a subnet in each of the region's zones
        region = self.provider.compute.regions.get(self.provider.region_name)
        default_sn = None

        # Determine how many subnets we'll need for the default network and the
        # number of available zones. We need to derive a non-overlapping
        # network size for each subnet within the parent net so figure those
        # subnets here. `<net>.subnets` method will do this but we need to give
        # it a prefix. Determining that prefix depends on the size of the
        # network and should be incorporate the number of zones. So iterate
        # over potential number of subnets until enough can be created to
        # accommodate the number of available zones. That is where the fixed
        # number comes from in the for loop as that many iterations will yield
        # more potential subnets than any region has zones.
        ip_net = ipaddress.ip_network(AWSNetwork.CB_DEFAULT_IPV4RANGE)
        for x in range(5):
            if len(region.zones) <= len(list(ip_net.subnets(
                    prefixlen_diff=x))):
                prefixlen_diff = x
                break
        subnets = list(ip_net.subnets(prefixlen_diff=prefixlen_diff))

        for i, z in reversed(list(enumerate(region.zones))):
            if zone_name == z.name:
                sn_label = "{0}-{1}".format(AWSSubnet.CB_DEFAULT_SUBNET_LABEL,
                                            z.id[-1])
                log.info("Creating a default CloudBridge subnet %s: %s" %
                         (sn_label, str(subnets[i])))
                sn = self.create(sn_label, default_net, str(subnets[i]))
                # Create a route table entry between the SN and the inet
                # gateway. See note above about why this is commented
                # default_router.attach_subnet(sn)
                default_sn = sn
        return default_sn


class AWSRouterService(BaseRouterService):
    """For AWS, a CloudBridge router corresponds to an AWS Route Table."""

    def __init__(self, provider):
        super(AWSRouterService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSRouter,
                                  boto_collection_name='route_tables')

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id):
        return self.svc.get(router_id)

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Router Service %s", label)
        return self.svc.find(filters={'tag:Name': label})

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network):
        network_id = network.id if isinstance(network, AWSNetwork) else network

        cb_router = self.svc.create('create_route_table', VpcId=network_id)
        if label:
            cb_router.label = label
        return cb_router

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router):
        r = router if isinstance(router, AWSRouter) else self.get(router)
        if r:
            # pylint:disable=protected-access
            r._route_table.delete()


class AWSGatewayService(BaseGatewayService):

    def __init__(self, provider):
        super(AWSGatewayService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=provider,
                                  cb_resource=AWSInternetGateway,
                                  boto_collection_name='internet_gateways')

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network):
        network_id = network.id if isinstance(
            network, AWSNetwork) else network
        # Don't filter by label because it may conflict with at least the
        # default VPC that most accounts have but that network is typically
        # without a name.
        gtw = self.svc.find(filters={'attachment.vpc-id': network_id})
        if gtw:
            return gtw[0]  # There can be only one gtw attached to a VPC
        # Gateway does not exist so create one and attach to the supplied net
        cb_gateway = self.svc.create('create_internet_gateway')

        @tenacity.retry(stop=tenacity.stop_after_attempt(5),
                        retry=tenacity.retry_if_exception_type(ClientError),
                        wait=tenacity.wait_fixed(5),
                        reraise=True)
        def _set_tag(gateway):
            gateway._gateway.create_tags(
                Tags=[{'Key': 'Name',
                       'Value': AWSInternetGateway.CB_DEFAULT_INET_GATEWAY_NAME
                       }])

        _set_tag(cb_gateway)
        cb_gateway._gateway.attach_to_vpc(VpcId=network_id)
        return cb_gateway

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network, gateway):
        gw = (gateway if isinstance(gateway, AWSInternetGateway)
              else self.svc.get(gateway))
        try:
            if gw.network_id:
                # pylint:disable=protected-access
                gw._gateway.detach_from_vpc(VpcId=gw.network_id)
        except ClientError as e:
            log.warn("Error deleting gateway {0}: {1}".format(self.id, e))
        # pylint:disable=protected-access
        gw._gateway.delete()

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network, limit=None, marker=None):
        log.debug("Listing current AWS internet gateways for net %s.",
                  network.id)
        fltr = [{'Name': 'attachment.vpc-id', 'Values': [network.id]}]
        return self.svc.list(limit=None, marker=None, Filters=fltr)


class AWSFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider):
        super(AWSFloatingIPService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSFloatingIP,
                                  boto_collection_name='vpc_addresses')

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway, fip_id):
        log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
        return self.svc.get(fip_id)

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway, limit=None, marker=None):
        return self.svc.list(limit, marker)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway):
        log.debug("Creating a floating IP under gateway %s", gateway)
        ip = self.provider.ec2_conn.meta.client.allocate_address(
            Domain='vpc')
        return AWSFloatingIP(
            self.provider,
            self.provider.ec2_conn.VpcAddress(ip.get('AllocationId')))

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway, fip):
        if isinstance(fip, AWSFloatingIP):
            # pylint:disable=protected-access
            aws_fip = fip._ip
        else:
            aws_fip = self.svc.get_raw(fip)
        aws_fip.release()


class AWSDnsService(BaseDnsService):

    def __init__(self, provider):
        super(AWSDnsService, self).__init__(provider)
        self.client = self._provider.session.client(
            'route53', region_name=self._provider.region_name)

        # Initialize provider services
        self._zone_svc = AWSDnsZoneService(self.provider)
        self._record_svc = AWSDnsRecordService(self.provider)

    @property
    def host_zones(self):
        return self._zone_svc

    @property
    def _records(self):
        return self._record_svc


class AWSDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider):
        super(AWSDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id):
        try:
            dns_zone = self.provider.dns.client.get_hosted_zone(
                Id=AWSDnsZone.unescape_zone_id(dns_zone_id))
            return AWSDnsZone(self.provider, dns_zone.get('HostedZone'))
        except self.provider.dns.client.exceptions.NoSuchHostedZone:
            return None
        except ClientError as exc:
            error_code = exc.response['Error']['Code']
            if any(status in error_code for status in
                   ('NotFound', 'InvalidParameterValue', 'Malformed', '404')):
                log.debug("Object not found: %s", dns_zone_id)
                return None
            else:
                raise exc

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        response = self.provider.dns.client.list_hosted_zones(
            **trim_empty_params({'MaxItems': limit, 'Marker': marker}))
        cb_objs = [AWSDnsZone(self.provider, zone)
                   for zone in response.get('HostedZones')]
        return ServerPagedResultList(is_truncated=response.get('IsTruncated'),
                                     marker=response.get('NextMarker'),
                                     supports_total=False,
                                     data=cb_objs)

    @dispatch(event="provider.dns.host_zones.find",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, self)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    @dispatch(event="provider.dns.host_zones.create",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def create(self, name, admin_email):
        AWSDnsZone.assert_valid_resource_name(name)

        response = self.provider.dns.client.create_hosted_zone(
            Name=name, CallerReference=uuid.uuid4().hex,
            HostedZoneConfig={
                'Comment': 'admin_email=' + admin_email
            }
        )
        return AWSDnsZone(self.provider, response.get('HostedZone'))

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone):
        dns_zone = (dns_zone if isinstance(dns_zone, AWSDnsZone)
                    else self.get(dns_zone))
        if dns_zone:
            self.provider.dns.client.delete_hosted_zone(Id=dns_zone.aws_id)


class AWSDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider):
        super(AWSDnsRecordService, self).__init__(provider)

    def get(self, dns_zone, rec_id):
        try:
            if rec_id and ":" in rec_id:
                rec_name, rec_type = rec_id.split(":")
                response = self.provider.dns.client.list_resource_record_sets(
                    HostedZoneId=dns_zone.aws_id,
                    StartRecordName=rec_name,
                    StartRecordType=rec_type)
                return AWSDnsRecord(self.provider, dns_zone,
                                    response.get('ResourceRecordSets')[0])
            else:
                return None
        except ClientError as exc:
            error_code = exc.response['Error']['Code']
            if any(status in error_code for status in
                   ('NotFound', 'InvalidParameterValue', 'Malformed', '404')):
                log.debug("Object not found: %s", rec_id)
                return None
            else:
                raise exc

    def list(self, dns_zone, limit=None, marker=None):
        response = self.provider.dns.client.list_resource_record_sets(
            **trim_empty_params({
                'HostedZoneId': dns_zone.aws_id,
                'MaxItems': limit,
                'StartRecordIdentifier': marker
            })
        )
        cb_objs = [AWSDnsRecord(self.provider, dns_zone, rec)
                   for rec in response.get('ResourceRecordSets')]
        return ServerPagedResultList(
            is_truncated=response.get('IsTruncated'),
            marker=response.get('NextRecordIdentifier'),
            supports_total=False, data=cb_objs)

    def find(self, dns_zone, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, dns_zone.records)
        return ClientPagedResultList(self.provider, list(matches),
                                     limit=None, marker=None)

    def _to_resource_records(self, data, rec_type):
        if isinstance(data, list):
            records = data
        else:
            records = [data]
        return [{'Value': self._standardize_record(r, rec_type)}
                for r in records]

    def create(self, dns_zone, name, type, data, ttl=None):
        AWSDnsRecord.assert_valid_resource_name(name)

        response = self.provider.dns.client.change_resource_record_sets(
            HostedZoneId=dns_zone.aws_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'CREATE',
                    'ResourceRecordSet': trim_empty_params({
                        'Name': name,
                        'Type': type,
                        'TTL': ttl or 300,
                        'ResourceRecords': self._to_resource_records(
                            data, type)
                    })
                }]
            }
        )
        # FIXME: Since Moto's implementation of route53 doesn't support
        # waiting, this is skipped for mock tests.
        if not self.provider.PROVIDER_ID == 'mock':
            waiter = self.provider.dns.client.get_waiter(
                'resource_record_sets_changed')
            waiter.wait(Id=response.get('ChangeInfo').get('Id'))
        return self.get(dns_zone, name + ":" + type)

    def delete(self, dns_zone, record):
        rec_id = record.id if isinstance(record, AWSDnsRecord) else record

        rec_name, rec_type = rec_id.split(":")
        response = self.provider.dns.client.change_resource_record_sets(
            HostedZoneId=dns_zone.aws_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'DELETE',
                    'ResourceRecordSet': {
                        'Name': rec_name,
                        'Type': rec_type,
                        'TTL': record.ttl,
                        'ResourceRecords': self._to_resource_records(
                            record.data, rec_type)
                    }
                }]
            })
        # FIXME: Since Moto's implementation of route53 doesn't support
        # waiting, this is skipped for mock tests.
        if not self.provider.PROVIDER_ID == 'mock':
            waiter = self.provider.dns.client.get_waiter(
                'resource_record_sets_changed')
            waiter.wait(Id=response.get('ChangeInfo').get('Id'))

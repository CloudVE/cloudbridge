"""Services implemented by the AWS provider."""
import ipaddress
import logging
import string

from botocore.exceptions import ClientError

import cachetools

import requests

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.middleware import implement
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBucketObjectService
from cloudbridge.cloud.base.services import BaseBucketService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseNetworkingService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseRouterService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseStorageService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVMFirewallService
from cloudbridge.cloud.base.services import BaseVMTypeService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions import DuplicateResourceException
from cloudbridge.cloud.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.interfaces.resources import VMType
from cloudbridge.cloud.interfaces.resources import Volume

from .helpers import BotoEC2Service
from .helpers import BotoS3Service
from .resources import AWSBucket
from .resources import AWSBucketObject
from .resources import AWSInstance
from .resources import AWSKeyPair
from .resources import AWSLaunchConfig
from .resources import AWSMachineImage
from .resources import AWSNetwork
from .resources import AWSPlacementZone
from .resources import AWSRegion
from .resources import AWSRouter
from .resources import AWSSnapshot
from .resources import AWSSubnet
from .resources import AWSVMFirewall
from .resources import AWSVMType
from .resources import AWSVolume

log = logging.getLogger(__name__)


class AWSSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(AWSSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AWSKeyPairService(provider)
        self._vm_firewalls = AWSVMFirewallService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls


class AWSKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(AWSKeyPairService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSKeyPair,
                                  boto_collection_name='key_pairs')

    @implement(event_pattern="provider.security.key_pairs.get",
               priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def _get(self, key_pair_id):
        log.debug("Getting Key Pair Service %s", key_pair_id)
        return self.svc.get(key_pair_id)

    @implement(event_pattern="provider.security.key_pairs.list",
               priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.security.key_pairs.find",
               priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'name'))

        log.debug("Searching for Key Pair %s", name)
        return self.svc.find(filter_name='key-name', filter_value=name)

    @implement(event_pattern="provider.security.key_pairs.create",
               priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def _create(self, name, public_key_material=None):
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

    @implement(event_pattern="provider.security.key_pairs.delete",
               priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def _delete(self, key_pair_id):
        aws_kp = self.svc.get_raw(key_pair_id)
        aws_kp.delete()


class AWSVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(AWSVMFirewallService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVMFirewall,
                                  boto_collection_name='security_groups')

    @implement(event_pattern="provider.security.vm_firewalls.get",
               priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def _get(self, vm_firewall_id):
        log.debug("Getting Firewall Service with the id: %s", vm_firewall_id)
        return self.svc.get(vm_firewall_id)

    @implement(event_pattern="provider.security.vm_firewalls.list",
               priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @cb_helpers.deprecated_alias(network_id='network')
    @implement(event_pattern="provider.security.vm_firewalls.create",
               priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, network, description=None):
        name = AWSVMFirewall._generate_name_from_label(label, 'cb-fw')
        network_id = network.id if isinstance(network, Network) else network
        obj = self.svc.create('create_security_group', GroupName=name,
                              Description=description or name,
                              VpcId=network_id)
        obj.label = label
        return obj

    @implement(event_pattern="provider.security.vm_firewalls.find",
               priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        # Filter by name or label
        label = kwargs.pop('label', None)
        log.debug("Searching for Firewall Service %s", label)
        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))
        return self.svc.find(filter_name='tag:Name',
                             filter_value=label)

    @implement(event_pattern="provider.security.vm_firewalls.delete",
               priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def _delete(self, vm_firewall_id):
        aws_fw = self.svc.get_raw(vm_firewall_id)
        aws_fw.delete()


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
    def bucket_objects(self):
        return self._bucket_obj_svc


class AWSVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AWSVolumeService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVolume,
                                  boto_collection_name='volumes')

    @implement(event_pattern="provider.storage.volumes.get",
               priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def _get(self, volume_id):
        return self.svc.get(volume_id)

    @implement(event_pattern="provider.storage.volumes.find",
               priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Volume Service %s", label)
        return self.svc.find(filter_name='tag:Name', filter_value=label)

    @implement(event_pattern="provider.storage.volumes.list",
               priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.storage.volumes.create",
               priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, size, zone, snapshot=None, description=None):
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, AWSSnapshot) and snapshot else snapshot

        cb_vol = self.svc.create('create_volume', Size=size,
                                 AvailabilityZone=zone_id,
                                 SnapshotId=snapshot_id)
        # Wait until ready to tag instance
        cb_vol.wait_till_ready()
        cb_vol.label = label
        if description:
            cb_vol.description = description
        return cb_vol

    @implement(event_pattern="provider.storage.volumes.delete",
               priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def _delete(self, volume_id):
        aws_vol = self.svc.get_raw(volume_id)
        aws_vol.delete()


class AWSSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(AWSSnapshotService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSSnapshot,
                                  boto_collection_name='snapshots')

    @implement(event_pattern="provider.storage.snapshots.get",
               priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def _get(self, snapshot_id):
        return self.svc.get(snapshot_id)

    @implement(event_pattern="provider.storage.snapshots.find",
               priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        # Filter by description or label
        label = kwargs.get('label', None)

        obj_list = []
        if label:
            log.debug("Searching for AWS Snapshot with label %s", label)
            obj_list.extend(self.svc.find(filter_name='tag:Name',
                                          filter_value=label,
                                          OwnerIds=['self']))
        else:
            obj_list = list(self)
        filters = ['label']
        return cb_helpers.generic_find(filters, kwargs, obj_list)

    @implement(event_pattern="provider.storage.snapshots.list",
               priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker,
                             OwnerIds=['self'])

    @implement(event_pattern="provider.storage.snapshots.create",
               priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, volume, description=None):
        volume_id = volume.id if isinstance(volume, AWSVolume) else volume

        cb_snap = self.svc.create('create_snapshot', VolumeId=volume_id)
        # Wait until ready to tag instance
        cb_snap.wait_till_ready()
        cb_snap.label = label
        if cb_snap.description:
            cb_snap.description = description
        return cb_snap

    @implement(event_pattern="provider.storage.snapshots.delete",
               priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def _delete(self, snapshot_id):
        aws_snap = self.svc.get_raw(snapshot_id)
        aws_snap.delete()


class AWSBucketService(BaseBucketService):

    def __init__(self, provider):
        super(AWSBucketService, self).__init__(provider)
        self.svc = BotoS3Service(provider=self.provider,
                                 cb_resource=AWSBucket,
                                 boto_collection_name='buckets')

    @implement(event_pattern="provider.storage.buckets.get",
               priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def _get(self, bucket_id):
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
                            "have enough permissions to access the bucket",
                            bucket_id)
                return AWSBucket(self.provider,
                                 self.provider.s3_conn.Bucket(bucket_id))
        # For all other responses, it's assumed that the bucket does not exist.
        return None

    @implement(event_pattern="provider.storage.buckets.list",
               priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit, marker):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.storage.buckets.create",
               priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def _create(self, name, location):
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

    @implement(event_pattern="provider.storage.buckets.delete",
               priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def _delete(self, bucket_id):
        bucket = self._get(bucket_id)
        if bucket:
            bucket._bucket.delete()


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
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        extra_args = {}
        if owner:
            extra_args.update(Owners=owner)

        # The original list is made by combining both searches by "tag:Name"
        # and "AMI name" to allow for searches of public images
        if label:
            log.debug("Searching for AWS Image Service %s", label)
            obj_list = []
            obj_list.extend(self.svc.find(filter_name='name',
                                          filter_value=label, **extra_args))
            obj_list.extend(self.svc.find(filter_name='tag:Name',
                                          filter_value=label, **extra_args))
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
        if isinstance(vm_firewalls, list) and isinstance(
                vm_firewalls[0], VMFirewall):
            vm_firewall_ids = [fw.id for fw in vm_firewalls]
        else:
            vm_firewall_ids = vm_firewalls
        return subnet.id, zone_id, vm_firewall_ids

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

    @implement(event_pattern="provider.compute.instances.create",
               priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, image, vm_type, subnet, zone,
                key_pair=None, vm_firewalls=None, user_data=None,
                launch_config=None, **kwargs):

        image_id = image.id if isinstance(image, MachineImage) else image
        vm_size = vm_type.id if \
            isinstance(vm_type, VMType) else vm_type
        subnet = (self.provider.networking.subnets.get(subnet)
                  if isinstance(subnet, str) else subnet)
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        key_pair_name = key_pair.name if isinstance(
            key_pair,
            KeyPair) else key_pair
        if launch_config:
            bdm = self._process_block_device_mappings(launch_config)
        else:
            bdm = None

        subnet_id, zone_id, vm_firewall_ids = \
            self._resolve_launch_options(subnet, zone_id, vm_firewalls)

        placement = {'AvailabilityZone': zone_id} if zone_id else None
        inst = self.svc.create('create_instances',
                               ImageId=image_id,
                               MinCount=1,
                               MaxCount=1,
                               KeyName=key_pair_name,
                               SecurityGroupIds=vm_firewall_ids or None,
                               UserData=str(user_data) or None,
                               InstanceType=vm_size,
                               Placement=placement,
                               BlockDeviceMappings=bdm,
                               SubnetId=subnet_id
                               )
        if inst and len(inst) == 1:
            # Wait until the resource exists
            # pylint:disable=protected-access
            inst[0]._wait_till_exists()
            # Tag the instance w/ the name
            inst[0].label = label
            return inst[0]
        raise ValueError(
            'Expected a single object response, got a list: %s' % inst)

    @implement(event_pattern="provider.compute.instances.get",
               priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def _get(self, instance_id):
        return self.svc.get(instance_id)

    @implement(event_pattern="provider.compute.instances.find",
               priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        return self.svc.find(filter_name='tag:Name', filter_value=label)

    @implement(event_pattern="provider.compute.instances.list",
               priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.compute.instances.delete",
               priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def _delete(self, instance_id):
        aws_ins = self.svc.get_raw(instance_id)
        aws_ins.terminate()


class AWSVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(AWSVMTypeService, self).__init__(provider)

    @property
    @cachetools.cached(cachetools.TTLCache(maxsize=1, ttl=24*3600))
    def instance_data(self):
        """
        Fetch info about the available instances.

        To update this information, update the file pointed to by the
        ``provider.AWS_INSTANCE_DATA_DEFAULT_URL`` above. The content for this
        file should be obtained from this repo:
        https://github.com/powdahound/ec2instances.info (in particular, this
        file: https://raw.githubusercontent.com/powdahound/ec2instances.info/
        master/www/instances.json).
        """
        r = requests.get(self.provider.config.get(
            "aws_instance_info_url",
            self.provider.AWS_INSTANCE_DATA_DEFAULT_URL))
        # Some instances are only available in certain regions. Use pricing
        # info to determine and filter out instance types that are not
        # available in the current region
        vm_types_list = r.json()
        return [vm_type for vm_type in vm_types_list
                if vm_type.get('pricing', {}).get(self.provider.region_name)]

    @implement(event_pattern="provider.compute.vm_types.list",
               priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        vm_types = [AWSVMType(self.provider, vm_type)
                    for vm_type in self.instance_data]
        return ClientPagedResultList(self.provider, vm_types,
                                     limit=limit, marker=marker)


class AWSRegionService(BaseRegionService):

    def __init__(self, provider):
        super(AWSRegionService, self).__init__(provider)

    @implement(event_pattern="provider.compute.regions.get",
               priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def _get(self, region_id):
        log.debug("Getting AWS Region Service with the id: %s",
                  region_id)
        region = [r for r in self if r.id == region_id]
        if region:
            return region[0]
        else:
            return None

    @implement(event_pattern="provider.compute.regions.list",
               priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
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

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service


class AWSNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(AWSNetworkService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSNetwork,
                                  boto_collection_name='vpcs')

    @implement(event_pattern="provider.networking.networks.get",
               priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def _get(self, network_id):
        return self.svc.get(network_id)

    @implement(event_pattern="provider.networking.networks.list",
               priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.networking.networks.find",
               priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Network Service %s", label)
        return self.svc.find(filter_name='tag:Name', filter_value=label)

    @implement(event_pattern="provider.networking.networks.create",
               priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, cidr_block):
        AWSNetwork.assert_valid_resource_label(label)

        cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
        # Wait until ready to tag instance
        cb_net.wait_till_ready()
        if label:
            cb_net.label = label
        return cb_net

    @implement(event_pattern="provider.networking.networks.delete",
               priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def _delete(self, network_id):
        net = self.get(network_id)
        net._vpc.delete()

    def get_or_create_default(self):
        # # Look for provided default network
        # for net in self.provider.networking.networks:
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

    @implement(event_pattern="provider.networking.subnets.get",
               priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def _get(self, subnet_id):
        return self.svc.get(subnet_id)

    @implement(event_pattern="provider.networking.subnets.list",
               priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def _list(self, network=None, limit=None, marker=None):
        network_id = network.id if isinstance(network, AWSNetwork) else network
        if network_id:
            return self.svc.find(
                filter_name='vpc-id', filter_value=network_id,
                limit=limit, marker=marker)
        else:
            return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.networking.subnets.find",
               priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Subnet Service %s", label)
        return self.svc.find(filter_name='tag:Name', filter_value=label)

    @implement(event_pattern="provider.networking.subnets.create",
               priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, network, cidr_block, zone):
        zone_name = zone.name if isinstance(
            zone, AWSPlacementZone) else zone

        network_id = network.id if isinstance(network, AWSNetwork) else network

        subnet = self.svc.create('create_subnet',
                                 VpcId=network_id,
                                 CidrBlock=cidr_block,
                                 AvailabilityZone=zone_name)
        if label:
            subnet.label = label
        return subnet

    @implement(event_pattern="provider.networking.subnets.delete",
               priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def _delete(self, subnet_id):
        aws_sn = self.svc.get_raw(subnet_id)
        aws_sn.delete()

    def get_or_create_default(self, zone):
        zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone

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
            snl.sort(key=lambda sn: sn._subnet.availability_zone)
            if not zone_name:
                return snl[0]
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
        # default_gtw = default_net.gateways.get_or_create_inet_gateway()
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
            sn_label = "{0}-{1}".format(AWSSubnet.CB_DEFAULT_SUBNET_LABEL,
                                        z.id[-1])
            log.info("Creating a default CloudBridge subnet %s: %s" %
                     (sn_label, str(subnets[i])))
            sn = self.create(sn_label, default_net, str(subnets[i]), z)
            # Create a route table entry between the SN and the inet gateway
            # See note above about why this is commented
            # default_router.attach_subnet(sn)
            if zone and zone_name == z.name:
                default_sn = sn
        # No specific zone was supplied; return the last created subnet
        # The list was originally reversed to have the last subnet be in zone a
        if not default_sn:
            default_sn = sn
        return default_sn


class AWSRouterService(BaseRouterService):
    """For AWS, a CloudBridge router corresponds to an AWS Route Table."""

    def __init__(self, provider):
        super(AWSRouterService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSRouter,
                                  boto_collection_name='route_tables')

    @implement(event_pattern="provider.networking.routers.get",
               priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def _get(self, router_id):
        return self.svc.get(router_id)

    @implement(event_pattern="provider.networking.routers.find",
               priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def _find(self, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs, 'label'))

        log.debug("Searching for AWS Router Service %s", label)
        return self.svc.find(filter_name='tag:Name', filter_value=label)

    @implement(event_pattern="provider.networking.routers.list",
               priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def _list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    @implement(event_pattern="provider.networking.routers.create",
               priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def _create(self, label, network):
        network_id = network.id if isinstance(network, AWSNetwork) else network

        cb_router = self.svc.create('create_route_table', VpcId=network_id)
        if label:
            cb_router.label = label
        return cb_router

    @implement(event_pattern="provider.networking.routers.delete",
               priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def _delete(self, router_id):
        aws_router = self.svc.get_raw(router_id)
        aws_router.delete()

"""Services implemented by the AWS provider."""
import logging
import string

from botocore.exceptions import ClientError

import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBucketService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseGatewayService
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
from cloudbridge.cloud.interfaces.exceptions \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.interfaces.resources import VMType
from cloudbridge.cloud.interfaces.resources import Volume

import requests

from .helpers import BotoEC2Service
from .helpers import BotoS3Service
from .resources import AWSBucket
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

    def get(self, key_pair_id):
        log.debug("Getting Key Pair Service %s", key_pair_id)
        return self.svc.get(key_pair_id)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for Key Pair %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='key-name', filter_value=name,
                             limit=limit, marker=marker)

    def create(self, name, public_key_material=None):
        log.debug("Creating Key Pair Service %s", name)
        AWSKeyPair.assert_valid_resource_name(name)
        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()
        kp = self.svc.create('import_key_pair', KeyName=name,
                             PublicKeyMaterial=public_key_material)
        kp.material = private_key
        return kp


class AWSVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(AWSVMFirewallService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVMFirewall,
                                  boto_collection_name='security_groups')

    def get(self, firewall_id):
        log.debug("Getting Firewall Service with the id: %s", firewall_id)
        return self.svc.get(firewall_id)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def create(self, name, description, network_id):
        log.debug("Creating Firewall Service with the parameters "
                  "[name: %s id: %s description: %s]", name, network_id,
                  description)
        AWSVMFirewall.assert_valid_resource_name(name)
        return self.svc.create('create_security_group', GroupName=name,
                               Description=description, VpcId=network_id)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for Firewall Service %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='group-name', filter_value=name,
                             limit=limit, marker=marker)

    def delete(self, firewall_id):
        log.info("Deleting Firewall Service with the id %s", firewall_id)
        firewall = self.svc.get(firewall_id)
        if firewall:
            firewall.delete()


class AWSStorageService(BaseStorageService):

    def __init__(self, provider):
        super(AWSStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AWSVolumeService(self.provider)
        self._snapshot_svc = AWSSnapshotService(self.provider)
        self._bucket_svc = AWSBucketService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc


class AWSVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AWSVolumeService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSVolume,
                                  boto_collection_name='volumes')

    def get(self, volume_id):
        log.debug("Getting AWS Volume Service with the id: %s",
                  volume_id)
        return self.svc.get(volume_id)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Volume Service %s with "
                  "the params  [Limit: %s Marker: %s]", name,
                  limit, marker)
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def create(self, name, size, zone, snapshot=None, description=None):
        log.debug("Creating AWS Volume Service with the parameters "
                  "[name: %s size: %s zone: %s snapshot: %s "
                  "description: %s]", name, size, zone, snapshot,
                  description)
        AWSVolume.assert_valid_resource_name(name)

        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, AWSSnapshot) and snapshot else snapshot

        cb_vol = self.svc.create('create_volume', Size=size,
                                 AvailabilityZone=zone_id,
                                 SnapshotId=snapshot_id)
        # Wait until ready to tag instance
        cb_vol.wait_till_ready()
        cb_vol.name = name
        if description:
            cb_vol.description = description
        return cb_vol


class AWSSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(AWSSnapshotService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSSnapshot,
                                  boto_collection_name='snapshots')

    def get(self, snapshot_id):
        log.debug("Getting AWS Snapshot Service with the id: %s",
                  snapshot_id)
        return self.svc.get(snapshot_id)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Snapshot Service %s with "
                  " the params [Limit: %s Marker: %s]", name,
                  limit, marker)
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        log.debug("Creating a new AWS snapshot Service with the "
                  "parameters [name: %s volume: %s description: %s]",
                  name, volume, description)
        AWSSnapshot.assert_valid_resource_name(name)

        volume_id = volume.id if isinstance(volume, AWSVolume) else volume

        cb_snap = self.svc.create('create_snapshot', VolumeId=volume_id)
        # Wait until ready to tag instance
        cb_snap.wait_till_ready()
        cb_snap.name = name
        if cb_snap.description:
            cb_snap.description = description
        return cb_snap


class AWSBucketService(BaseBucketService):

    def __init__(self, provider):
        super(AWSBucketService, self).__init__(provider)
        self.svc = BotoS3Service(provider=self.provider,
                                 cb_resource=AWSBucket,
                                 boto_collection_name='buckets')

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        log.debug("Getting AWS Bucket Service with the id: %s", bucket_id)
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
            if e.response['Error']['Code'] == 403:
                log.warning("AWS Bucket %s already exists but user doesn't "
                            "have enough permissions to access the bucket",
                            bucket_id)
                bucket = self.provider.s3_conn.get_bucket(bucket_id,
                                                          validate=False)
                return AWSBucket(self.provider, bucket)
        # For all other responses, it's assumed that the bucket does not exist.
        return None

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Bucket %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        buckets = [bucket
                   for bucket in self
                   if name == bucket.name]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def create(self, name, location=None):
        log.debug("Creating AWS Bucket with the params "
                  "[name: %s id: %s description: %s]", name, location)
        AWSBucket.assert_valid_resource_name(name)
        loc_constraint = location or self.provider.region_name
        # Due to an API issue in S3, specifying us-east-1 as a
        # LocationConstraint results in an InvalidLocationConstraint.
        # Therefore, it must be special-cased and omitted altogether.
        # See: https://github.com/boto/boto3/issues/125
        if loc_constraint == 'us-east-1':
            return self.svc.create('create_bucket', Bucket=name)
        else:
            return self.svc.create('create_bucket', Bucket=name,
                                   CreateBucketConfiguration={
                                       'LocationConstraint': loc_constraint
                                   })


class AWSImageService(BaseImageService):

    def __init__(self, provider):
        super(AWSImageService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSMachineImage,
                                  boto_collection_name='images')

    def get(self, image_id):
        log.debug("Getting AWS Image Service with the id: %s", image_id)
        return self.svc.get(image_id)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Image Service %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='name', filter_value=name,
                             limit=limit, marker=marker)

    def list(self, filter_by_owner=True, limit=None, marker=None):
        return self.svc.list(Owners=['self'] if filter_by_owner else [],
                             limit=limit, marker=marker)


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


class AWSInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(AWSInstanceService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSInstance,
                                  boto_collection_name='instances')

    def create(self, name, image, vm_type, subnet, zone=None,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        log.debug("Creating AWS Instance Service with the params "
                  "[name: %s image: %s type: %s subnet: %s zone: %s "
                  "key pair: %s firewalls: %s user data: %s config %s "
                  "others: %s]", name, image, vm_type, subnet, zone,
                  key_pair, vm_firewalls, user_data, launch_config, **kwargs)
        AWSInstance.assert_valid_resource_name(name)

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
            inst[0].name = name
            return inst[0]
        raise ValueError(
            'Expected a single object response, got a list: %s' % inst)

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
                ebs_def['DeleteOnTermination'] = device.delete_on_terminate
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

    def get(self, instance_id):
        return self.svc.get(instance_id)

    def find(self, name, limit=None, marker=None):
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)


class AWSVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(AWSVMTypeService, self).__init__(provider)

    @property
    def instance_data(self):
        """
        Fetch info about the available instances.

        To update this information, update the file pointed to by the
        ``provider.AWS_INSTANCE_DATA_DEFAULT_URL`` above. The content for this
        file should be obtained from this repo:
        https://github.com/powdahound/ec2instances.info (in particular, this
        file: https://raw.githubusercontent.com/powdahound/ec2instances.info/
        master/www/instances.json).

        TODO: Needs a caching function with timeout
        """
        r = requests.get(self.provider.config.get(
            "aws_instance_info_url",
            self.provider.AWS_INSTANCE_DATA_DEFAULT_URL))
        return r.json()

    def list(self, limit=None, marker=None):
        vm_types = [AWSVMType(self.provider, vm_type)
                    for vm_type in self.instance_data]
        return ClientPagedResultList(self.provider, vm_types,
                                     limit=limit, marker=marker)


class AWSRegionService(BaseRegionService):

    def __init__(self, provider):
        super(AWSRegionService, self).__init__(provider)

    def get(self, region_id):
        log.debug("Getting AWS Region Service with the id: %s",
                  region_id)
        region = [r for r in self if r.id == region_id]
        if region:
            return region[0]
        else:
            return None

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
    def gateways(self):
        return self._gateway_service


class AWSNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(AWSNetworkService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSNetwork,
                                  boto_collection_name='vpcs')

    def get(self, network_id):
        log.debug("Getting AWS Network Service with the id: %s",
                  network_id)
        return self.svc.get(network_id)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Network Service %s with the "
                  " params [Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def create(self, name, cidr_block):
        log.debug("Creating AWS Network Service with the params "
                  "[name: %s block: %s]", name, cidr_block)
        AWSNetwork.assert_valid_resource_name(name)

        cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
        # Wait until ready to tag instance
        cb_net.wait_till_ready()
        if name:
            cb_net.name = name
        return cb_net


class AWSSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AWSSubnetService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSSubnet,
                                  boto_collection_name='subnets')

    def get(self, subnet_id):
        log.debug("Getting AWS Subnet Service with the id: %s", subnet_id)
        return self.svc.get(subnet_id)

    def list(self, network=None, limit=None, marker=None):
        network_id = network.id if isinstance(network, AWSNetwork) else network
        if network_id:
            return self.svc.find(
                filter_name='vpc-id', filter_value=network_id,
                limit=limit, marker=marker)
        else:
            return self.svc.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Subnet Service %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def create(self, name, network, cidr_block, zone=None):
        log.debug("Creating AWS Subnet Service with the params "
                  "[name: %s network: %s block: %s zone: %s]",
                  name, network, cidr_block, zone)
        AWSSubnet.assert_valid_resource_name(name)

        network_id = network.id if isinstance(network, AWSNetwork) else network

        subnet = self.svc.create('create_subnet',
                                 VpcId=network_id,
                                 CidrBlock=cidr_block,
                                 AvailabilityZone=zone)
        if name:
            subnet.name = name
        return subnet

    def get_or_create_default(self, zone=None):
        if zone:
            snl = self.svc.find('availabilityZone', zone)
        else:
            snl = self.svc.list()
        for sn in snl:
            # pylint:disable=protected-access
            if sn._subnet.default_for_az:
                return sn
        # No provider-default Subnet exists, look for a library-default one
        for sn in snl:
            # pylint:disable=protected-access
            for tag in sn._subnet.tags or {}:
                if (tag.get('Key') == 'Name' and
                        tag.get('Value') == AWSSubnet.CB_DEFAULT_SUBNET_NAME):
                    return sn
        # No provider-default Subnet exists, try to create it (net + subnets)
        default_net = self.provider.networking.networks.create(
            name=AWSNetwork.CB_DEFAULT_NETWORK_NAME, cidr_block='10.0.0.0/16')
        # Create a subnet in each of the region's zones
        region = self.provider.compute.regions.get(self.provider.region_name)
        default_sn = None
        for i, z in enumerate(region.zones):
            sn = self.create(AWSSubnet.CB_DEFAULT_SUBNET_NAME, default_net,
                             '10.0.{0}.0/24'.format(i), z.name)
            if zone and zone == z.name:
                default_sn = sn
        # No specific zone was supplied; return the last created subnet
        if not default_sn:
            default_sn = sn
        return default_sn

    def delete(self, subnet):
        log.debug("Deleting AWS Subnet Service: %s", subnet)
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        self.svc.delete(subnet_id)


class AWSRouterService(BaseRouterService):
    """For AWS, a CloudBridge router corresponds to an AWS Route Table."""

    def __init__(self, provider):
        super(AWSRouterService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSRouter,
                                  boto_collection_name='route_tables')

    def get(self, router_id):
        log.debug("Getting AWS Router Service with the id: %s", router_id)
        return self.svc.get(router_id)

    def find(self, name, limit=None, marker=None):
        log.debug("Searching for AWS Router Service %s with the params "
                  "[Limit: %s Marker: %s]", name, limit, marker)
        return self.svc.find(filter_name='tag:Name', filter_value=name,
                             limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.svc.list(limit=limit, marker=marker)

    def create(self, name, network):
        log.debug("Creating AWS Router Service with the params "
                  "[name: %s network: %s]", name, network)
        AWSRouter.assert_valid_resource_name(name)

        network_id = network.id if isinstance(network, AWSNetwork) else network

        cb_router = self.svc.create('create_route_table', VpcId=network_id)
        if name:
            cb_router.name = name
        return cb_router


class AWSGatewayService(BaseGatewayService):

    def __init__(self, provider):
        super(AWSGatewayService, self).__init__(provider)
        self.svc = BotoEC2Service(provider=self.provider,
                                  cb_resource=AWSInternetGateway,
                                  boto_collection_name='internet_gateways')

    def get_or_create_inet_gateway(self, network, name=None):
        log.debug("Get or create inet gateway %s on net %s", name, network)
        if name:
            AWSInternetGateway.assert_valid_resource_name(name)

        network_id = network.id if isinstance(network, AWSNetwork) else network
        # Don't filter by name because it may conflict with at least the
        # default VPC that most accounts have but that network is typically
        # without a name.
        gtw = self.svc.find(filter_name='attachment.vpc-id',
                            filter_value=network_id)
        if gtw:
            return gtw[0]  # There can be only one gtw attached to a VPC
        # Gateway does not exist so create one and attach to the supplied net
        cb_gateway = self.svc.create('create_internet_gateway')
        if name:
            cb_gateway.name = name
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
        log.debug("Listing current AWS internet gateways.")
        return self.svc.list(limit=None, marker=None)

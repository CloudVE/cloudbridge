"""Services implemented by the AWS provider."""
import string

from botocore.exceptions import ClientError

from cloudbridge.cloud.base.resources import ClientPagedResultList
# from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBlockStoreService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseGatewayService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseInstanceTypesService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseNetworkingService
from cloudbridge.cloud.base.services import BaseObjectStoreService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseRouterService
from cloudbridge.cloud.base.services import BaseSecurityGroupService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import MachineImage
from cloudbridge.cloud.interfaces.resources import PlacementZone
from cloudbridge.cloud.interfaces.resources import SecurityGroup
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import Volume

import requests

from .resources import AWSBucket
from .resources import AWSFloatingIP
from .resources import AWSInstance
from .resources import AWSInstanceType
from .resources import AWSInternetGateway
from .resources import AWSKeyPair
from .resources import AWSLaunchConfig
from .resources import AWSMachineImage
from .resources import AWSNetwork
from .resources import AWSRegion
from .resources import AWSRouter
from .resources import AWSSecurityGroup
from .resources import AWSSnapshot
from .resources import AWSSubnet
from .resources import AWSVolume

# Uncomment to enable logging by default for this module
# import cloudbridge as cb
# cb.set_stream_logger(__name__)


class GenericServiceFilter(object):
    '''
    Generic AWS EC2 service filter interface

    :param AWSCloudProvider provider: AWS EC2 provider interface
    :param str service: Name of the EC2 service to use
    :param BaseCloudResource cb_iface: CloudBridge class to use
    '''
    def __init__(self, provider, boto_conn, service, cb_iface):
        self.provider = provider
        self.boto_conn = boto_conn
        self.service = getattr(self.boto_conn, service)
        self.iface = cb_iface

    def get(self, val, filter_name, wrapper=True):
        '''
        Returns a single resource by filter

        :param str val: Value to filter with
        :param str filter_name: Name of the filter to use
        :param bool wrapper: If True, wraps the resulting Boto
            object in a CloudBridge object
        :returns: Boto resource object or CloudBridge object or None
        '''
        try:
            objs = list(self.service.filter(Filters=[{
                'Name': filter_name,
                'Values': [val]
            }]).limit(1))
            obj = objs[0] if objs else None
            if wrapper:
                return self.iface(self.provider, obj) if obj else None
            return obj
        except ClientError:
            return None

    def list(self, limit=None, marker=None):
        '''Returns a list of resources'''
        objs = [self.iface(self.provider, obj)
                for obj in self.service.limit(limit)]
        return ClientPagedResultList(self.provider, objs,
                                     limit=limit, marker=marker)

    def find(self, val, filter_name, limit=None, marker=None):
        '''
        Returns a list of resources by filter

        :param str val: Value to filter with
        :param str filter_name: Name of the filter to use
        '''
        try:
            objs = [
                self.iface(self.provider, obj)
                for obj in self.service.filter(Filters=[{
                    'Name': filter_name,
                    'Values': [val]
                }])
            ] if val else []
        except ClientError:
            objs = list()
        return ClientPagedResultList(self.provider, objs,
                                     limit=limit, marker=marker)

    def create(self, method, **kwargs):
        '''
        Creates a resource

        :param str method: Service method to invoke
        :param object kwargs: Arguments to be passed as-is to
            the service method
        '''
        res = getattr(self.boto_conn, method)(**kwargs)
        if isinstance(res, list):
            return [self.iface(self.provider, x) if x else None for x in res]
        return self.iface(self.provider, res) if res else None

    def delete(self, val, filter_name):
        '''
        Deletes a resource by filter

        :param str val: Value to filter with
        :param str filter_name: Name of the filter to use
        :returns: False on error, True if the resource
            does not exist or was deleted successfully
        '''
        res = self.get(val, filter_name, wrapper=False)
        if res:
            try:
                res.delete()
            except ClientError:
                return False
        return True


class EC2ServiceFilter(GenericServiceFilter):
    '''
    Generic AWS EC2 service filter interface

    :param AWSCloudProvider provider: AWS EC2 provider interface
    :param str service: Name of the EC2 service to use
    :param BaseCloudResource cb_iface: CloudBridge class to use
    '''
    def __init__(self, provider, service, cb_iface):
        super(EC2ServiceFilter, self).__init__(
            provider, provider.ec2_conn, service, cb_iface)


class S3ServiceFilter(GenericServiceFilter):
    '''
    Generic AWS S3 service filter interface

    :param AWSCloudProvider provider: AWS provider interface
    :param str service: Name of the S3 service to use
    :param BaseCloudResource cb_iface: CloudBridge class to use
    '''
    def __init__(self, provider, service, cb_iface):
        super(S3ServiceFilter, self).__init__(
            provider, provider.s3_conn, service, cb_iface)


class AWSSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(AWSSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = AWSKeyPairService(provider)
        self._security_groups = AWSSecurityGroupService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def security_groups(self):
        return self._security_groups


class AWSKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(AWSKeyPairService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'key_pairs', AWSKeyPair)

    def get(self, key_pair_id):
        return self.iface.get(key_pair_id, 'key-name')

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'key-name', limit=limit, marker=marker)

    def create(self, name):
        AWSKeyPair.assert_valid_resource_name(name)
        return self.iface.create('create_key_pair', KeyName=name)


class AWSSecurityGroupService(BaseSecurityGroupService):

    def __init__(self, provider):
        super(AWSSecurityGroupService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider,
                                      'security_groups', AWSSecurityGroup)

    def get(self, sg_id):
        return self.iface.get(sg_id, 'group-id')

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def create(self, name, description, network_id):
        AWSSecurityGroup.assert_valid_resource_name(name)
        res = self.iface.create('create_security_group', **{
            k: v for k, v in {
                'GroupName': name,
                'Description': description,
                'VpcId': network_id,
            }.items() if v is not None})
        return res

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'group-name', limit=limit, marker=marker)

    def delete(self, group_id):
        sg = self.iface.get(group_id, 'group-id')
        if sg:
            sg.delete()


class AWSBlockStoreService(BaseBlockStoreService):

    def __init__(self, provider):
        super(AWSBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AWSVolumeService(self.provider)
        self._snapshot_svc = AWSSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class AWSVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AWSVolumeService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'volumes', AWSVolume)

    def get(self, volume_id):
        return self.iface.get(volume_id, 'volume-id')

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def create(self, name, size, zone, snapshot=None, description=None):
        AWSVolume.assert_valid_resource_name(name)

        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, AWSSnapshot) and snapshot else snapshot
        params = {
            'Size': size,
            'AvailabilityZone': zone_id,
            'SnapshotId': snapshot_id
        }
        # Filter out empty values to please Boto
        params = {k: v for k, v in params.items()
                  if v is not None}
        cb_vol = self.iface.create('create_volume', **params)
        # Wait until ready to tag instance
        cb_vol.wait_till_ready()
        cb_vol.name = name
        if description:
            cb_vol.description = description
        return cb_vol


class AWSSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(AWSSnapshotService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'snapshots', AWSSnapshot)

    def get(self, snapshot_id):
        return self.iface.get(snapshot_id, 'snapshot-id')

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def create(self, name, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        AWSSnapshot.assert_valid_resource_name(name)

        volume_id = volume.id if isinstance(volume, AWSVolume) else volume

        cb_snap = self.iface.create('create_snapshot', VolumeId=volume_id)
        # Wait until ready to tag instance
        cb_snap.wait_till_ready()
        cb_snap.name = name
        if cb_snap.description:
            cb_snap.description = description
        return cb_snap


class AWSObjectStoreService(BaseObjectStoreService):

    def __init__(self, provider):
        super(AWSObjectStoreService, self).__init__(provider)
        self.iface = S3ServiceFilter(self.provider, 'buckets', AWSBucket)

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
            if e.response['Error']['Code'] == 403:
                bucket = self.provider.s3_conn.get_bucket(bucket_id,
                                                          validate=False)
                return AWSBucket(self.provider, bucket)
        # For all other responses, it's assumed that the bucket does not exist.
        return None

    def find(self, name, limit=None, marker=None):
        buckets = [bucket
                   for bucket in self
                   if name == bucket.name]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def create(self, name, location=None):
        AWSBucket.assert_valid_resource_name(name)

        self.iface.create(
            'create_bucket', Bucket=name,
            CreateBucketConfiguration={
                'LocationConstraint': location or self.provider.region_name
            })
        return self.get(name)


class AWSImageService(BaseImageService):

    def __init__(self, provider):
        super(AWSImageService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'images', AWSMachineImage)

    def get(self, image_id):
        return self.iface.get(image_id, 'image-id')

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'name', limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)


class AWSComputeService(BaseComputeService):

    def __init__(self, provider):
        super(AWSComputeService, self).__init__(provider)
        self._instance_type_svc = AWSInstanceTypesService(self.provider)
        self._instance_svc = AWSInstanceService(self.provider)
        self._region_svc = AWSRegionService(self.provider)
        self._images_svc = AWSImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def instance_types(self):
        return self._instance_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class AWSInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(AWSInstanceService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'instances', AWSInstance)

    def create(self, name, image, instance_type, subnet, zone=None,
               key_pair=None, security_groups=None, user_data=None,
               launch_config=None, **kwargs):
        AWSInstance.assert_valid_resource_name(name)

        image_id = image.id if isinstance(image, MachineImage) else image
        instance_size = instance_type.id if \
            isinstance(instance_type, InstanceType) else instance_type
        subnet = (self.provider.networking.subnets.get(subnet)
                  if isinstance(subnet, str) else subnet)
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        key_pair_name = key_pair.name if isinstance(
            key_pair,
            KeyPair) else key_pair
        if launch_config:
            bdm = self._process_block_device_mappings(launch_config, zone_id)
        else:
            bdm = None

        subnet_id, zone_id, security_group_ids = \
            self._resolve_launch_options(subnet, zone_id, security_groups)

        ress = self.iface.create('create_instances', **{
            k: v for k, v in {
                'ImageId': image_id,
                'MinCount': 1,
                'MaxCount': 1,
                'KeyName': key_pair_name,
                'SecurityGroupIds': security_group_ids or None,
                'UserData': user_data,
                'InstanceType': instance_size,
                'Placement': {
                    'AvailabilityZone': zone_id
                },
                'BlockDeviceMappings': bdm,
                'SubnetId': subnet_id
            }.items() if v is not None
        })
        if ress and len(ress) == 1:
            # Wait until the resource exists
            ress[0].wait_till_exists()
            # Tag the instance w/ the name
            ress[0].name = name
            return ress[0]
        raise ValueError(
            'Expected a single object response, got a list: %s' % ress)

    def _resolve_launch_options(self, subnet=None, zone_id=None,
                                security_groups=None):
        """
        Work out interdependent launch options.

        Some launch options are required and interdependent so make sure
        they conform to the interface contract.

        :type subnet: ``Subnet``
        :param subnet: Subnet object within which to launch.

        :type zone_id: ``str``
        :param zone_id: ID of the zone where the launch should happen.

        :type security_groups: ``list`` of ``id``
        :param zone_id: List of security group IDs.

        :rtype: triplet of ``str``
        :return: Subnet ID, zone ID and security group IDs for launch.

        :raise ValueError: In case a conflicting combination is found.
        """
        if subnet:
            # subnet's zone takes precedence
            zone_id = subnet.zone.id
        if isinstance(security_groups, list) and isinstance(
                security_groups[0], SecurityGroup):
            security_group_ids = [sg.id for sg in security_groups]
        else:
            security_group_ids = security_groups
        return subnet.id, zone_id, security_group_ids

    def _process_block_device_mappings(self, launch_config, zone=None):
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
        return self.iface.get(instance_id, 'instance-id')

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)


class AWSInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(AWSInstanceTypesService, self).__init__(provider)

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
        inst_types = [AWSInstanceType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class AWSRegionService(BaseRegionService):

    def __init__(self, provider):
        super(AWSRegionService, self).__init__(provider)

    def get(self, region_id):
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
        self.iface = EC2ServiceFilter(self.provider, 'vpcs', AWSNetwork)

    def get(self, network_id):
        return self.iface.get(network_id, 'vpc-id')

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def create(self, name, cidr_block):
        AWSNetwork.assert_valid_resource_name(name)

        cb_net = self.iface.create('create_vpc', CidrBlock=cidr_block)
        # Wait until ready to tag instance
        cb_net.wait_till_ready()
        if name:
            cb_net.name = name
        return cb_net

    @property
    def floating_ips(self):
        self.iface_vips = EC2ServiceFilter(self.provider,
                                           'vpc_addresses', AWSFloatingIP)
        return self.iface_vips.list()

    def create_floating_ip(self):
        ip = self.provider.ec2_conn.meta.client.allocate_address(
            Domain='vpc')
        return AWSFloatingIP(
            self.provider,
            self.provider.ec2_conn.VpcAddress(ip.get('AllocationId')))


class AWSSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AWSSubnetService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'subnets', AWSSubnet)

    def get(self, subnet_id):
        return self.iface.get(subnet_id, 'subnet-id')

    def list(self, network=None, limit=None, marker=None):
        network_id = network.id if isinstance(network, AWSNetwork) else network
        if network_id:
            return self.iface.find(network_id, 'VpcId',
                                   limit=limit, marker=marker)
        else:
            return self.iface.list(limit=limit, marker=marker)

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def create(self, name, network, cidr_block, zone=None):
        AWSSubnet.assert_valid_resource_name(name)

        network_id = network.id if isinstance(network, AWSNetwork) else network
        res = self.iface.create('create_subnet', **{
            k: v for k, v in {
                'VpcId': network_id,
                'CidrBlock': cidr_block,
                'AvailabilityZone': zone,
            }.items() if v is not None})
        if name:
            res.name = name
        return res

    def get_or_create_default(self, zone=None):
        if zone:
            snl = self.iface.find(zone, 'availabilityZone')
        else:
            snl = self.iface.service.limit(None)
        for sn in snl:
            if sn.default_for_az:
                return AWSSubnet(self.provider, sn)
        # No provider-default Subnet exists, look for a library-default one
        for sn in snl:
            for tag in sn.tags or {}:
                if (tag.get('Key') == 'Name' and
                        tag.get('Value') == AWSSubnet.CB_DEFAULT_SUBNET_NAME):
                    return AWSSubnet(self.provider, sn)
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
        subnet_id = subnet.id if isinstance(subnet, AWSSubnet) else subnet
        return self.iface.delete(subnet_id, 'subnet-id')


class AWSRouterService(BaseRouterService):
    """For AWS, a CloudBridge router corresponds to an AWS Route Table."""

    def __init__(self, provider):
        super(AWSRouterService, self).__init__(provider)
        self.iface = EC2ServiceFilter(self.provider, 'route_tables', AWSRouter)

    def get(self, router_id):
        return self.iface.get(router_id, 'route-table-id')

    def find(self, name, limit=None, marker=None):
        return self.iface.find(name, 'tag:Name', limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        return self.iface.list(limit=limit, marker=marker)

    def create(self, name, network):
        AWSRouter.assert_valid_resource_name(name)

        network_id = network.id if isinstance(network, AWSNetwork) else network
        res = self.iface.create('create_route_table', **{
            k: v for k, v in {
                'VpcId': network_id
            }.items() if v is not None})
        if name:
            res.name = name
        return res


class AWSGatewayService(BaseGatewayService):

    def __init__(self, provider):
        super(AWSGatewayService, self).__init__(provider)
        self.iface_igws = EC2ServiceFilter(self.provider, 'internet_gateways',
                                           AWSInternetGateway)

    def get_or_create_inet_gateway(self, name):
        AWSInternetGateway.assert_valid_resource_name(name)

        cb_gateway = self.iface_igws.create('create_internet_gateway')
        # self.iface_igws.wait_for_create(cb_gateway.id, 'internet-gateway-id')
        cb_gateway.name = name
        return cb_gateway

    def delete(self, gateway):
        gateway.delete()

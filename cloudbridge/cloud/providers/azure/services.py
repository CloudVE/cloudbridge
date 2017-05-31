import logging
import uuid

from azure.common import AzureException

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseBlockStoreService, \
    BaseComputeService, BaseImageService, BaseInstanceService, \
    BaseInstanceTypesService, \
    BaseNetworkService, \
    BaseObjectStoreService, BaseRegionService, \
    BaseSecurityGroupService, \
    BaseSecurityService, BaseSnapshotService, \
    BaseSubnetService, BaseVolumeService
from cloudbridge.cloud.interfaces.resources import Network,\
    PlacementZone, Snapshot, Subnet, Volume
from cloudbridge.cloud.providers.azure import helpers as azure_helpers

from msrestazure.azure_exceptions import CloudError

from .resources import AzureBucket, AzureInstance, \
    AzureInstanceType, \
    AzureMachineImage, \
    AzureNetwork, AzureRegion, AzureSecurityGroup, \
    AzureSnapshot, AzureSubnet, AzureVolume, \
    IMAGE_NAME, IMAGE_RESOURCE_ID, \
    INSTANCE_NAME, INSTANCE_RESOURCE_ID, \
    NETWORK_NAME, NETWORK_RESOURCE_ID, \
    NETWORK_SECURITY_GROUP_RESOURCE_ID, \
    SECURITY_GROUP_NAME, SNAPSHOT_NAME, \
    SNAPSHOT_RESOURCE_ID, SUBNET_NAME, SUBNET_RESOURCE_ID, \
    VOLUME_NAME, VOLUME_RESOURCE_ID

log = logging.getLogger(__name__)


class AzureSecurityService(BaseSecurityService):
    def __init__(self, provider):
        super(AzureSecurityService, self).__init__(provider)

        # Initialize provider services
        # self._key_pairs = AzureKeyPairService(provider)
        self._security_groups = AzureSecurityGroupService(provider)

    @property
    def key_pairs(self):
        """
        Provides access to key pairs for this provider.

        :rtype: ``object`` of :class:`.KeyPairService`
        :return: a KeyPairService object
        """
        raise NotImplementedError('AzureSecurityService '
                                  'not implemented this property')

    @property
    def security_groups(self):
        """
        Provides access to security groups for this provider.

        :rtype: ``object`` of :class:`.SecurityGroupService`
        :return: a SecurityGroupService object
        """
        return self._security_groups


class AzureSecurityGroupService(BaseSecurityGroupService):
    def __init__(self, provider):
        super(AzureSecurityGroupService, self).__init__(provider)

    def get(self, sg_id):
        try:
            params = azure_helpers.parse_url(
                NETWORK_SECURITY_GROUP_RESOURCE_ID, sg_id)
            sgs = self.provider.azure_client.get_security_group(
                params.get(SECURITY_GROUP_NAME))
            return AzureSecurityGroup(self.provider, sgs)

        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def list(self, limit=None, marker=None):
        sgs = [AzureSecurityGroup(self.provider, sg)
               for sg in self.provider.azure_client.list_security_group()]
        return ClientPagedResultList(self.provider, sgs, limit, marker)

    def create(self, name, description, network_id):
        parameters = {"location": self.provider.region_name,
                      'tags': {'Name': name}}

        if description:
            parameters['tags'].update(Description=description)

        sg = self.provider.azure_client.create_security_group(name, parameters)
        cb_sg = AzureSecurityGroup(self.provider, sg)

        return cb_sg

    def find(self, name, limit=None, marker=None):
        """
        Searches for a security group by a given list of attributes.
        """
        filters = {'Name': name}
        sgs = [AzureSecurityGroup(self.provider, security_group)
               for security_group in azure_helpers.filter(
                self.provider.azure_client.list_security_group(), filters)]

        return ClientPagedResultList(self.provider, sgs,
                                     limit=limit, marker=marker)

    def delete(self, group_id):
        try:
            params = azure_helpers.\
                parse_url(NETWORK_SECURITY_GROUP_RESOURCE_ID,
                          group_id)
            self.provider.azure_client.delete_security_group(
                params.get(SECURITY_GROUP_NAME))
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False


class AzureObjectStoreService(BaseObjectStoreService):
    def __init__(self, provider):
        super(AzureObjectStoreService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist.
        """
        try:
            bucket = self.provider.azure_client.get_container(bucket_id)
            return AzureBucket(self.provider, bucket)

        except AzureException as error:
            log.exception(error)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a bucket by a given list of attributes.
        """
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in
                   self.provider.azure_client.list_containers(prefix=name)]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in self.provider.azure_client.list_containers()]
        return ClientPagedResultList(self.provider, buckets,
                                     limit=limit, marker=marker)

    def create(self, name, location=None):
        """
        Create a new bucket.
        """
        bucket = self.provider.azure_client.create_container(name.lower())
        return AzureBucket(self.provider, bucket)


class AzureBlockStoreService(BaseBlockStoreService):
    def __init__(self, provider):
        super(AzureBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AzureVolumeService(self.provider)
        self._snapshot_svc = AzureSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc


class AzureVolumeService(BaseVolumeService):
    def __init__(self, provider):
        super(AzureVolumeService, self).__init__(provider)

    def get(self, volume_id):
        try:
            params = azure_helpers.parse_url(VOLUME_RESOURCE_ID, volume_id)
            volume = self.provider.azure_client.get_disk(
                params.get(VOLUME_NAME))
            return AzureVolume(self.provider, volume)
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filters = {'Name': name}
        cb_vols = [AzureVolume(self.provider, volume)
                   for volume in azure_helpers.filter(
                self.provider.azure_client.list_disks(), filters)]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        azure_vols = self.provider.azure_client.list_disks()
        cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def create(self, name, size, zone=None, snapshot=None, description=None):
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(
            snapshot, Snapshot) and snapshot else snapshot
        disk_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])
        tags = {'Name': name}
        if description:
            tags.update(Description=description)
        if snapshot_id:
            params = {
                'location': zone_id or self.provider.azure_client.region_name,
                'creation_data': {
                    'create_option': 'copy',
                    'source_uri': snapshot_id
                },
                'tags': tags
            }

            self.provider.azure_client.create_snapshot_disk(disk_name, params)

        else:
            params = {
                'location': zone_id or self.provider.azure_client.region_name,
                'disk_size_gb': size,
                'creation_data': {
                    'create_option': 'empty'
                },
                'tags': tags}

            self.provider.azure_client.create_empty_disk(disk_name, params)

        azure_vol = self.provider.azure_client.get_disk(disk_name)
        cb_vol = AzureVolume(self.provider, azure_vol)

        return cb_vol


class AzureSnapshotService(BaseSnapshotService):
    def __init__(self, provider):
        super(AzureSnapshotService, self).__init__(provider)

    def get(self, ss_id):
        try:
            params = azure_helpers.parse_url(SNAPSHOT_RESOURCE_ID, ss_id)
            snapshot = self.provider.azure_client. \
                get_snapshot(params.get(SNAPSHOT_NAME))
            return AzureSnapshot(self.provider, snapshot)
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
             Searches for a snapshot by a given list of attributes.
        """
        filters = {'Name': name}
        cb_snapshots = [AzureSnapshot(self.provider, snapshot)
                        for snapshot in azure_helpers.filter(
                self.provider.azure_client.list_snapshots(), filters)]
        return ClientPagedResultList(self.provider, cb_snapshots,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
               List all snapshots.
        """
        snaps = [AzureSnapshot(self.provider, obj)
                 for obj in
                 self.provider.azure_client.list_snapshots()]
        return ClientPagedResultList(self.provider, snaps, limit, marker)

    def create(self, name, volume, description=None):
        volume_id = volume.id if isinstance(volume, Volume) else volume
        disk_size = volume.size if isinstance(volume, Volume) else \
            self.provider.block_store.volumes.get(volume_id).size

        tags = {'Name': name}
        snapshot_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])

        if description:
            tags.update(Description=description)

        params = {
            'location': self.provider.azure_client.region_name,
            'creation_data': {
                'create_option': 'Copy',
                'source_uri': volume_id
            },
            'disk_size_gb': disk_size,
            'tags': tags
        }

        self.provider.azure_client. \
            create_snapshot(snapshot_name, params)
        azure_snap = self.provider.azure_client.get_snapshot(snapshot_name)
        cb_snap = AzureSnapshot(self.provider, azure_snap)

        return cb_snap


class AzureComputeService(BaseComputeService):
    def __init__(self, provider):
        super(AzureComputeService, self).__init__(provider)
        self._instance_type_svc = AzureInstanceTypesService(self.provider)
        self._instance_svc = AzureInstanceService(self.provider)
        self._region_svc = AzureRegionService(self.provider)
        self._images_svc = AzureImageService(self.provider)

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


class AzureInstanceService(BaseInstanceService):
    def __init__(self, provider):
        super(AzureInstanceService, self).__init__(provider)

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """

        azure_instances = [instance for instance in
                           self.provider.azure_client.list_instances()]
        cb_instances = [AzureInstance(self.provider, instance)
                        for instance in azure_instances]
        return ClientPagedResultList(self.provider, cb_instances,
                                     limit=limit, marker=marker)

    def get(self, instance_id):
        try:
            params = azure_helpers.parse_url(INSTANCE_RESOURCE_ID, instance_id)
            instance = self.provider.azure_client. \
                get_instance(params.get(INSTANCE_NAME))
            return AzureInstance(self.provider, instance)
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None


class AzureImageService(BaseImageService):
    def __init__(self, provider):
        super(AzureImageService, self).__init__(provider)

    def get(self, image_id):
        try:
            params = azure_helpers.parse_url(IMAGE_RESOURCE_ID, image_id)
            image = self.provider.azure_client. \
                get_image(params.get(IMAGE_NAME))
            return AzureMachineImage(self.provider, image)
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):

        """
         Searches for a image by a given list of attributes.
        """
        filters = {'Name': name}
        cb_images = [AzureMachineImage(self.provider, image)
                     for image in azure_helpers.filter(
                self.provider.azure_client.list_images(), filters)]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        azure_images = self.provider.azure_client.list_images()
        cb_images = [AzureMachineImage(self.provider, img)
                     for img in azure_images]
        return ClientPagedResultList(self.provider, cb_images,
                                     limit=limit, marker=marker)


class AzureInstanceTypesService(BaseInstanceTypesService):

    def __init__(self, provider):
        super(AzureInstanceTypesService, self).__init__(provider)

    @property
    def instance_data(self):
        """
        Fetch info about the available instances.
        """
        r = self.provider.azure_client.list_instance_types()
        return r

    def list(self, limit=None, marker=None):
        inst_types = [AzureInstanceType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class AzureNetworkService(BaseNetworkService):
    def __init__(self, provider):
        super(AzureNetworkService, self).__init__(provider)
        self._subnet_svc = AzureSubnetService(self.provider)

    def get(self, network_id):
        try:
            params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
            network = self.provider.azure_client. \
                get_network(params.get(NETWORK_NAME))
            return AzureNetwork(self.provider, network)

        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def list(self, limit=None, marker=None):
        """
               List all networks.
        """
        networks = [AzureNetwork(self.provider, network)
                    for network in self.provider.azure_client.list_networks()]
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def create(self, name=None):
        network_name = AzureNetwork.CB_DEFAULT_NETWORK_NAME
        if name:
            network_name = "{0}-{1}".format(name, uuid.uuid4().hex[:6])

        params = {
            'location': self.provider.azure_client.region_name,
            'address_space': {
                'address_prefixes': ['10.0.0.0/16']
            },
            'tags': {'Name': name or AzureNetwork.CB_DEFAULT_NETWORK_NAME}
        }

        self.provider.azure_client.create_network(network_name, params)
        network = self.provider.azure_client.get_network(network_name)
        cb_network = AzureNetwork(self.provider, network)

        return cb_network

    @property
    def subnets(self):
        return self._subnet_svc

    def floating_ips(self, network_id=None):
        raise NotImplementedError('AzureNetworkService '
                                  'not implemented this method')

    def create_floating_ip(self):
        raise NotImplementedError('AzureNetworkService '
                                  'not implemented this method')

    def routers(self):
        raise NotImplementedError('AzureNetworkService '
                                  'not implemented this method')

    def create_router(self, name=None):
        raise NotImplementedError('AzureNetworkService '
                                  'not implemented this method')

    def delete(self, network_id):
        """
                Delete an existing network.
                """
        try:
            params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
            self.provider.azure_client. \
                delete_network(params.get(NETWORK_NAME))
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False


class AzureRegionService(BaseRegionService):
    def __init__(self, provider):
        super(AzureRegionService, self).__init__(provider)

    def get(self, region_id):
        region = None
        for azureRegion in self.provider.azure_client.list_locations():
            if azureRegion.id == region_id:
                region = AzureRegion(self.provider, azureRegion)
                break
        return region

    def list(self, limit=None, marker=None):
        regions = [AzureRegion(self.provider, region)
                   for region in self.provider.azure_client.list_locations()]
        return ClientPagedResultList(self.provider, regions,
                                     limit=limit, marker=marker)

    @property
    def current(self):
        # aws sets the name returned from the aws sdk to both the id & name
        # of BaseRegion and as such calling get() with the id works
        # but Azure sdk returns both id & name and are set to
        # the BaseRegion properties
        regions = [region
                   for region in self.provider.
                   azure_client.list_locations()
                   if region.name == self.provider.
                   azure_client.region_name]

        return AzureRegion(self.provider, regions[0])


class AzureSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(AzureSubnetService, self).__init__(provider)

    def get(self, subnet_id):
        try:
            params = azure_helpers.parse_url(SUBNET_RESOURCE_ID, subnet_id)
            subnet = self.provider.azure_client. \
                get_subnet(params.get(NETWORK_NAME), params.get(SUBNET_NAME))
            return AzureSubnet(self.provider, subnet)

        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def list(self, network=None, limit=None, marker=None):
        result_list = []
        if network:
            network_id = network.id \
                if isinstance(network, Network) else network
            params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
            result_list = self.provider.azure_client.list_subnets(
                params.get(NETWORK_NAME)
            )
        else:
            for net in self.provider.azure_client.list_networks():
                result_list.extend(self.provider.azure_client.list_subnets(
                 net.name
                ))
        subnets = [AzureSubnet(self.provider, subnet)
                   for subnet in result_list]
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    def create(self, network, cidr_block, name=None, **kwargs):
        network_id = network.id \
            if isinstance(network, Network) else network
        params = azure_helpers.parse_url(NETWORK_RESOURCE_ID, network_id)
        network_name = params.get(NETWORK_NAME)

        if not name:
            subnet_name = AzureSubnet.CB_DEFAULT_SUBNET_NAME
        else:
            subnet_name = name

        subnet_info = self.provider.azure_client\
            .create_subnet(
                            network_name,
                            subnet_name,
                            {
                                'address_prefix': cidr_block
                            }
                          )

        return AzureSubnet(self.provider, subnet_info)

    def get_or_create_default(self, zone=None):
        default_cdir = '10.0.1.0/24'
        network = None
        subnet = None
        try:
            network = self.provider.azure_client\
                .get_network(AzureNetwork.CB_DEFAULT_NETWORK_NAME)
        except CloudError:
            pass

        if not network:
            self.provider.network.create()
        try:
            subnet = self.provider.azure_client.get_subnet(
                AzureNetwork.CB_DEFAULT_NETWORK_NAME,
                AzureSubnet.CB_DEFAULT_SUBNET_NAME
            )
        except CloudError:
            pass

        if not subnet:
            subnet = self.provider.azure_client.create_subnet(
                AzureNetwork.CB_DEFAULT_NETWORK_NAME,
                AzureSubnet.CB_DEFAULT_SUBNET_NAME,
                {'address_prefix': default_cdir}
            )

        return AzureSubnet(self.provider, subnet)

    def delete(self, subnet):
        try:
            subnet_id = subnet.id if \
                isinstance(subnet, Subnet) else subnet
            params = azure_helpers.\
                parse_url(SUBNET_RESOURCE_ID, subnet_id)
            self.provider.azure_client.delete_subnet(
                params.get(NETWORK_NAME),
                params.get(SUBNET_NAME)
            )
            return True
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return False

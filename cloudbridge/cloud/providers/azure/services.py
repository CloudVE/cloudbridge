import logging

from azure.common import AzureMissingResourceHttpError, AzureException
from msrestazure.azure_exceptions import CloudError

from cloudbridge.cloud.interfaces.resources import PlacementZone, Snapshot, Volume

from .resources import SUBNET_RESOURCE_ID, NETWORK_NAME, SUBNET_NAME, NETWORK_RESOURCE_ID, \
    INSTANCE_RESOURCE_ID, VM_NAME, IMAGE_RESOURCE_ID, RESOURCE_GROUP_NAME, IMAGE_NAME, SNAPSHOT_RESOURCE_ID, \
    SNAPSHOT_NAME, VOLUME_RESOURCE_ID, VOLUME_NAME, NETWORK_SECURITY_GROUP_RESOURCE_ID, SECURITY_GROUP_NAME, \
    AzureVolume

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseObjectStoreService, BaseSecurityGroupService, BaseSecurityService, \
    BaseVolumeService, BaseBlockStoreService, BaseSnapshotService

from cloudbridge.cloud.providers.azure import helpers as azure_helpers

from .resources import AzureBucket, AzureSecurityGroup

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
        raise NotImplementedError('AzureSecurityService not implemented this property')

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
            params = azure_helpers.parse_url(NETWORK_SECURITY_GROUP_RESOURCE_ID, sg_id)
            sgs = self.provider.azure_client.get_security_group(params.get(SECURITY_GROUP_NAME))
            return AzureSecurityGroup(self.provider, sgs)

        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def list(self, limit=None, marker=None):
        sgs = [AzureSecurityGroup(self.provider, sg)
               for sg in self.provider.azure_client.list_security_group()]
        return ClientPagedResultList(self.provider, sgs, limit, marker)

    def create(self, name, description, network_id):
        parameters = {"location": self.provider.region_name}
        sg = self.provider.azure_client.create_security_group(name, parameters)
        cb_sg = AzureSecurityGroup(self.provider, sg)

        if description:
            cb_sg.description = description

        return cb_sg

    def find(self, name, limit=None, marker=None):
        """
        Searches for a security group by a given list of attributes.
        """
        filters = {'name': name}
        sgs = [AzureSecurityGroup(self.provider, security_group)
               for security_group in azure_helpers.filter(
                self.provider.azure_client.list_security_group(), filters)]

        return ClientPagedResultList(self.provider, sgs,
                                     limit=limit, marker=marker)

    def delete(self, group_id):
        params = azure_helpers.parse_url(NETWORK_SECURITY_GROUP_RESOURCE_ID, group_id)
        return self.provider.azure_client.delete_security_group(params.get(SECURITY_GROUP_NAME))


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
        filters = {'name': name}
        buckets = [AzureBucket(self.provider, bucket)
                   for bucket in azure_helpers.filter(self.provider.azure_client.list_containers(), filters)]
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
        bucket = self.provider.azure_client.create_container(name)
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
            volume = self.provider.azure_client.get_disk(params.get(VOLUME_NAME))
            return AzureVolume(self.provider, volume)
        except CloudError as cloudError:
            log.exception(cloudError.message)
            return None

    def find(self, name, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filters = {'name': name}
        cb_vols = [AzureVolume(self.provider, volume)
                   for volume in azure_helpers.filter(self.provider.azure_client.list_disks(), filters)]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        azure_vols = self.provider.azure_client.list_disks()
        cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
        return ClientPagedResultList(self.provider, cb_vols,
                                     limit=limit, marker=marker)

    def create(self, name, size, zone=None, snapshot=None, description=None):
        zone_id = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(snapshot, Snapshot) and snapshot else snapshot
        self.provider.azure_client.create_empty_disk(name, size, zone_id, snapshot_id)
        azure_vol = self.provider.azure_client.get_disk(name)
        cb_vol = AzureVolume(self.provider, azure_vol)
        if description:
            cb_vol.description = description

        return cb_vol


class AzureSnapshotService(BaseSnapshotService):
    def __init__(self, provider):
        super(AzureSnapshotService, self).__init__(provider)

    def get(self, ss_id):
        raise NotImplementedError('AzureSnapShotService not implemented this method')

    def find(self, name, limit=None, marker=None):
        raise NotImplementedError('AzureSnapShotService not implemented this method')

    def list(self, limit=None, marker=None):
        raise NotImplementedError('AzureSnapShotService not implemented this method')

    def create(self, name, volume, description=None):
        raise NotImplementedError('AzureSnapShotService not implemented this method')

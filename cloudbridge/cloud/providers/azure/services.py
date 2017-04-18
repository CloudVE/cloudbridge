import logging

from cloudbridge.cloud.interfaces.resources import PlacementZone
from .resources import SUBNET_RESOURCE_ID, NETWORK_NAME, SUBNET_NAME, NETWORK_RESOURCE_ID, \
    INSTANCE_RESOURCE_ID, VM_NAME, IMAGE_RESOURCE_ID, RESOURCE_GROUP_NAME, IMAGE_NAME, SNAPSHOT_RESOURCE_ID, \
    SNAPSHOT_NAME, VOLUME_RESOURCE_ID, VOLUME_NAME, NETWORK_SECURITY_GROUP_RESOURCE_ID, SECURITY_GROUP_NAME, \
    TemplateUrlParser, AzureVolume, AzureSnapshot

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseObjectStoreService, BaseSecurityGroupService, BaseSecurityService, \
    BaseVolumeService, BaseBlockStoreService

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
        return None

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
        for item in self.provider.azure_client.list_security_group():
            if item.id == sg_id:
                return AzureSecurityGroup(self.provider, item)
        return None

    def list(self, limit=None, marker=None):
        nsg_list = self.provider.azure_client.list_security_group()
        network_security_group = [AzureSecurityGroup(self.provider, sg)
                                  for sg in nsg_list]
        return ClientPagedResultList(self.provider, network_security_group, limit, marker)

        # network_id is similar to resource group in azure
    def create(self, name, description, network_id):
        parameters = {"location": self.provider.region_name}
        result = self.provider.azure_client.create_security_group(name, parameters)
        return AzureSecurityGroup(self.provider, result)

    def find(self, name, limit=None, marker=None):
        raise NotImplementedError(
            "AzureSecurityGroupService does not implement this method")

    def delete(self, group_id):
        for item in self.provider.azure_client.list_security_group():
            if item.id == group_id:
                sg_name = item.name
                self.provider.azure_client.delete_security_group(sg_name)
                return True
        return False


class AzureObjectStoreService(BaseObjectStoreService):
    def __init__(self, provider):
        super(AzureObjectStoreService, self).__init__(provider)

    def get(self, bucket_id):
        log.info("Azure Object Store Service get API with bucket id - " + str(bucket_id))
        object_store = self.provider.azure_client.get_container(bucket_id)
        if object_store:
            return AzureBucket(self.provider, object_store)
        return None

    def find(self, name, limit=None, marker=None):
        object_store = self.provider.azure_client.get_container(name)
        object_stores = []
        if object_store:
            object_stores.append(AzureBucket(self.provider, object_store))

        return ClientPagedResultList(self.provider, object_stores,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        object_stores = [AzureBucket(self.provider, object_store)
                   for object_store in
                   self.provider.azure_client.list_containers()]
        return ClientPagedResultList(self.provider, object_stores,
                                     limit=limit, marker=marker)

    def create(self, name, location=None):
        object_store = self.provider.azure_client.create_container(name)
        return AzureBucket(self.provider, object_store)


class AzureBlockStoreService(BaseBlockStoreService):
    def __init__(self, provider):
        super(AzureBlockStoreService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = AzureVolumeService(self.provider)
        #self._snapshot_svc = AzureSnapshotService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        pass

class AzureVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(AzureVolumeService, self).__init__(provider)

    def get(self, volume_id):
        raise NotImplementedError('AzureVolumeService not imeplemented this method')

    def find(self, name, limit=None, marker=None):
        raise NotImplementedError('AzureVolumeService not imeplemented this method')

    def list(self, limit=None, marker=None):
        raise NotImplementedError('AzureVolumeService not imeplemented this method')

    def create(self, name, size, zone=None, snapshot=None, description=None):
        region = zone.id if isinstance(zone, PlacementZone) else zone
        snapshot_id = snapshot.id if isinstance(snapshot, AzureSnapshot) and snapshot else snapshot
        volume =  self.provider.azure_client.create_empty_disk(name, size, region, snapshot_id)
        return AzureVolume(self.provider, volume)

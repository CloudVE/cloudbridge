from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.services import BaseObjectStoreService, BaseSecurityGroupService, BaseSecurityService

from .resources import AzureBucket, AzureSecurityGroup


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
        nsglist = self.provider.azure_client.list_security_group()
        network_security_group = [AzureSecurityGroup(self.provider, sg)
                                  for sg in nsglist]
        return ClientPagedResultList(self.provider, network_security_group, limit, marker)

    def create(self, name, description, network_id):
        raise NotImplementedError(
            "AzureSecurityGroupService does not implement this method")

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
        raise NotImplementedError(
            "AzureObjectStoreService does not implement this service")

    def find(self, name, limit=None, marker=None):
        object_store = self.provider.azure_client.get_container(name)
        object_stores = []
        if object_store:
            object_stores.append(AzureBucket(self.provider, object_store))

        return ClientPagedResultList(self.provider, object_stores,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        raise NotImplementedError(
            "AzureObjectStoreService does not implement this method")

    def create(self, name, location=None):
        self.provider.azure_client.create_container(name)

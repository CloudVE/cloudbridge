"""
Base implementation for services available through a provider
"""
import logging

from cloudbridge.cloud.interfaces.resources import Router
from cloudbridge.cloud.interfaces.services import BucketService
from cloudbridge.cloud.interfaces.services import CloudService
from cloudbridge.cloud.interfaces.services import ComputeService
from cloudbridge.cloud.interfaces.services import FloatingIPService
from cloudbridge.cloud.interfaces.services import GatewayService
from cloudbridge.cloud.interfaces.services import ImageService
from cloudbridge.cloud.interfaces.services import InstanceService
from cloudbridge.cloud.interfaces.services import KeyPairService
from cloudbridge.cloud.interfaces.services import NetworkService
from cloudbridge.cloud.interfaces.services import NetworkingService
from cloudbridge.cloud.interfaces.services import RegionService
from cloudbridge.cloud.interfaces.services import RouterService
from cloudbridge.cloud.interfaces.services import SecurityService
from cloudbridge.cloud.interfaces.services import SnapshotService
from cloudbridge.cloud.interfaces.services import StorageService
from cloudbridge.cloud.interfaces.services import SubnetService
from cloudbridge.cloud.interfaces.services import VMFirewallService
from cloudbridge.cloud.interfaces.services import VMTypeService
from cloudbridge.cloud.interfaces.services import VolumeService

from .resources import BasePageableObjectMixin

log = logging.getLogger(__name__)


class BaseCloudService(CloudService):

    def __init__(self, provider):
        self._provider = provider

    @property
    def provider(self):
        return self._provider


class BaseComputeService(ComputeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseComputeService, self).__init__(provider)


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)


class BaseStorageService(StorageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseStorageService, self).__init__(provider)


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)


class BaseBucketService(
        BasePageableObjectMixin, BucketService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketService, self).__init__(provider)


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseCloudService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)

    def delete(self, key_pair_id):
        """
        Delete an existing key pair.

        :type key_pair_id: str
        :param key_pair_id: The id of the key pair to be deleted.

        :rtype: ``bool``
        :return:  ``True`` if the key does not exist. Note that this implies
                  that the key may not have been deleted by this method but
                  instead has not existed in the first place.
        """
        log.info("Deleting the existing key pair %s", key_pair_id)
        kp = self.get(key_pair_id)
        if kp:
            kp.delete()
        return True


class BaseVMFirewallService(
        BasePageableObjectMixin, VMFirewallService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMFirewallService, self).__init__(provider)


class BaseVMTypeService(
        BasePageableObjectMixin, VMTypeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMTypeService, self).__init__(provider)

    def get(self, vm_type_id):
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    def find(self, **kwargs):
        name = kwargs.get('name')
        log.info("Searching for VMTypeService with the: name %s ...", name)
        if name:
            return [itype for itype in self if itype.name == name]
        else:
            log.exception("TypeError exception raised. Invalid parameters "
                          "used for search.")
            raise TypeError(
                "Invalid parameters for search. Supported attributes: {name}")


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)

    def find(self, name):
        return [region for region in self if region.name == name]


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkingService, self).__init__(provider)


class BaseNetworkService(
        BasePageableObjectMixin, NetworkService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkService, self).__init__(provider)

    @property
    def subnets(self):
        return [subnet for subnet in self.provider.subnets
                if subnet.network_id == self.id]

    def delete(self, network_id):
        if network_id is None:
            return True
        network = self.get(network_id)
        if network:
            log.info("Deleting network %s", network_id)
            network.delete()


class BaseSubnetService(
        BasePageableObjectMixin, SubnetService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSubnetService, self).__init__(provider)

    def find(self, **kwargs):
        name = kwargs.get('name')
        log.info("Searching for SubnetService with the name: %s ...", name)
        if name:
            return [subnet for subnet in self if subnet.name == name]
        else:
            log.exception("TypeError exception raised. Invalid parameters "
                          "used for search.")
            raise TypeError(
                "Invalid parameters for search. Supported attributes: {name}")


class BaseFloatingIPService(
        BasePageableObjectMixin, FloatingIPService, BaseCloudService):

    def __init__(self, provider):
        super(BaseFloatingIPService, self).__init__(provider)

    def find(self, **kwargs):
        if 'name' in kwargs:
            name = kwargs.get('name')
            log.info("Searching for FloatingIPService with the "
                     "name: %s...", name)
            if name:
                return [fip for fip in self if fip.name == name]
        else:
            log.exception("TypeError exception raised. Invalid parameters "
                          "used for search.")
            raise TypeError(
                "Invalid parameters for search. Supported attributes: {name}")

    def delete(self, fip_id):
        floating_ip = self.get(fip_id)
        if floating_ip:
            floating_ip.delete()


class BaseRouterService(
        BasePageableObjectMixin, RouterService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRouterService, self).__init__(provider)

    def delete(self, router):
        if isinstance(router, Router):
            log.info("Router %s successful deleted.", router)
            router.delete()
        else:
            log.info("Getting router %s", router)
            router = self.get(router)
            if router:
                log.info("Router %s successful deleted.", router)
                router.delete()


class BaseGatewayService(
        GatewayService, BaseCloudService):

    def __init__(self, provider):
        super(BaseGatewayService, self).__init__(provider)

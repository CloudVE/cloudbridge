"""
Base implementation for services available through a provider
"""
import logging

from cloudbridge.cloud.interfaces.exceptions import InvalidParamException
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.services import BucketObjectService
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
from cloudbridge.cloud.interfaces.services import VMFirewallRuleService
from cloudbridge.cloud.interfaces.services import VMFirewallService
from cloudbridge.cloud.interfaces.services import VMTypeService
from cloudbridge.cloud.interfaces.services import VolumeService

from . import helpers as cb_helpers
from .middleware import dispatch
from .resources import BaseNetwork
from .resources import BasePageableObjectMixin
from .resources import BaseRouter
from .resources import BaseSubnet
from .resources import ClientPagedResultList

log = logging.getLogger(__name__)


class BaseCloudService(CloudService):

    STANDARD_EVENT_PRIORITY = 2500

    def __init__(self, provider):
        self._service_event_pattern = provider.PROVIDER_ID
        self._provider = provider
        # discover and register all middleware
        provider.middleware.add(self)

    @property
    def provider(self):
        return self._provider

    @property
    def events(self):
        return self._provider.middleware.events


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin, KeyPairService, BaseCloudService):

    def __init__(self, provider):
        super(BaseKeyPairService, self).__init__(provider)
        self._service_event_pattern += ".security.key_pairs"


class BaseVMFirewallService(
        BasePageableObjectMixin, VMFirewallService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMFirewallService, self).__init__(provider)
        self._service_event_pattern += ".security.vm_firewalls"

    @dispatch(event="security.vm_firewalls.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])


class BaseVMFirewallRuleService(BasePageableObjectMixin,
                                VMFirewallRuleService,
                                BaseCloudService):

    def __init__(self, provider):
        super(BaseVMFirewallRuleService, self).__init__(provider)
        self._provider = provider

    @property
    def provider(self):
        return self._provider

    @dispatch(event="security.vm_firewall_rules.get",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def get(self, firewall, rule_id):
        matches = [rule for rule in firewall.rules if rule.id == rule_id]
        if matches:
            return matches[0]
        else:
            return None

    @dispatch(event="security.vm_firewall_rules.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, firewall, **kwargs):
        obj_list = firewall.rules
        filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
                   'cidr', 'src_dest_fw', 'src_dest_fw_id']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseStorageService(StorageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseStorageService, self).__init__(provider)


class BaseVolumeService(
        BasePageableObjectMixin, VolumeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVolumeService, self).__init__(provider)
        self._service_event_pattern += ".storage.volumes"


class BaseSnapshotService(
        BasePageableObjectMixin, SnapshotService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSnapshotService, self).__init__(provider)
        self._service_event_pattern += ".storage.snapshots"


class BaseBucketService(
        BasePageableObjectMixin, BucketService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketService, self).__init__(provider)
        self._service_event_pattern += ".storage.buckets"

    # Generic find will be used for providers where we have not implemented
    # provider-specific querying for find method
    @dispatch(event="storage.buckets.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])


class BaseBucketObjectService(BucketObjectService, BaseCloudService):

    def __init__(self, provider):
        super(BaseBucketObjectService, self).__init__(provider)
        self._service_event_pattern += ".storage._bucket_objects"
        self._bucket = None


class BaseComputeService(ComputeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseComputeService, self).__init__(provider)


class BaseImageService(
        BasePageableObjectMixin, ImageService, BaseCloudService):

    def __init__(self, provider):
        super(BaseImageService, self).__init__(provider)
        self._service_event_pattern += ".compute.images"


class BaseInstanceService(
        BasePageableObjectMixin, InstanceService, BaseCloudService):

    def __init__(self, provider):
        super(BaseInstanceService, self).__init__(provider)
        self._service_event_pattern += ".compute.instances"


class BaseVMTypeService(
        BasePageableObjectMixin, VMTypeService, BaseCloudService):

    def __init__(self, provider):
        super(BaseVMTypeService, self).__init__(provider)
        self._service_event_pattern += ".compute.vm_types"

    @dispatch(event="compute.vm_types.get",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_type_id):
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    @dispatch(event="compute.vm_types.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseRegionService(
        BasePageableObjectMixin, RegionService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRegionService, self).__init__(provider)
        self._service_event_pattern += ".compute.regions"

    @dispatch(event="compute.regions.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkingService, self).__init__(provider)


class BaseNetworkService(
        BasePageableObjectMixin, NetworkService, BaseCloudService):

    def __init__(self, provider):
        super(BaseNetworkService, self).__init__(provider)
        self._service_event_pattern += ".networking.networks"

    @property
    def subnets(self):
        return [subnet for subnet in self.provider.subnets
                if subnet.network_id == self.id]

    def get_or_create_default(self):
        networks = self.provider.networking.networks.find(
            label=BaseNetwork.CB_DEFAULT_NETWORK_LABEL)

        if networks:
            return networks[0]
        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     BaseNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.provider.networking.networks.create(
                BaseNetwork.CB_DEFAULT_NETWORK_LABEL, '10.0.0.0/16')

    @dispatch(event="networking.networks.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        obj_list = self
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise TypeError("Unrecognised parameters for search: %s."
                            " Supported attributes: %s" % (kwargs,
                                                           ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])


class BaseSubnetService(
        BasePageableObjectMixin, SubnetService, BaseCloudService):

    def __init__(self, provider):
        super(BaseSubnetService, self).__init__(provider)
        self._service_event_pattern += ".networking.subnets"

    @dispatch(event="networking.subnets.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, network=None, **kwargs):
        if not network:
            obj_list = self
        else:
            obj_list = network.subnets
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get_or_create_default(self, zone):
        # Look for a CB-default subnet
        matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
        if matches:
            return matches[0]

        # No provider-default Subnet exists, try to create it (net + subnets)
        network = self.provider.networking.networks.get_or_create_default()
        subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
                             BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
        return subnet


class BaseRouterService(
        BasePageableObjectMixin, RouterService, BaseCloudService):

    def __init__(self, provider):
        super(BaseRouterService, self).__init__(provider)
        self._service_event_pattern += ".networking.routers"

    def get_or_create_default(self, network):
        net_id = network.id if isinstance(network, Network) else network
        routers = self.provider.networking.routers.find(
            label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)
        for router in routers:
            if router.network_id == net_id:
                return router
        else:
            return self.provider.networking.routers.create(
                network=net_id, label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)


class BaseGatewayService(GatewayService, BaseCloudService):

    def __init__(self, provider):
        super(BaseGatewayService, self).__init__(provider)
        self._provider = provider

    @property
    def provider(self):
        return self._provider


class BaseFloatingIPService(FloatingIPService, BaseCloudService):

    def __init__(self, provider):
        super(BaseFloatingIPService, self).__init__(provider)
        self._provider = provider

    @property
    def provider(self):
        return self._provider

    @dispatch(event="networking.floating_ips.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, gateway, **kwargs):
        obj_list = gateway.floating_ips
        filters = ['name', 'public_ip']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

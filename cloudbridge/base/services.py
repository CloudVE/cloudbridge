"""
Base implementation for services available through a provider
"""
import logging
from abc import abstractmethod
from typing import Any
from typing import cast

from cloudbridge.interfaces.exceptions import InvalidParamException
from cloudbridge.interfaces.provider import CloudProvider
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import DnsRecord
from cloudbridge.interfaces.resources import DnsRecordType
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import Instance
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import Region
from cloudbridge.interfaces.resources import ResultList
from cloudbridge.interfaces.resources import Router
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMFirewallRule
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume
from cloudbridge.interfaces.services import BucketObjectService
from cloudbridge.interfaces.services import BucketService
from cloudbridge.interfaces.services import CloudService
from cloudbridge.interfaces.services import ComputeService
from cloudbridge.interfaces.services import DnsRecordService
from cloudbridge.interfaces.services import DnsService
from cloudbridge.interfaces.services import DnsZoneService
from cloudbridge.interfaces.services import FloatingIPService
from cloudbridge.interfaces.services import GatewayService
from cloudbridge.interfaces.services import ImageService
from cloudbridge.interfaces.services import InstanceService
from cloudbridge.interfaces.services import KeyPairService
from cloudbridge.interfaces.services import NetworkService
from cloudbridge.interfaces.services import NetworkingService
from cloudbridge.interfaces.services import RegionService
from cloudbridge.interfaces.services import RouterService
from cloudbridge.interfaces.services import SecurityService
from cloudbridge.interfaces.services import SnapshotService
from cloudbridge.interfaces.services import StorageService
from cloudbridge.interfaces.services import SubnetService
from cloudbridge.interfaces.services import VMFirewallRuleService
from cloudbridge.interfaces.services import VMFirewallService
from cloudbridge.interfaces.services import VMTypeService
from cloudbridge.interfaces.services import VolumeService

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

    def __init__(self, provider: CloudProvider) -> None:
        self._service_event_pattern = "provider"
        self._provider = provider
        # discover and register all middleware
        provider.middleware.add(self)

    @property
    def provider(self) -> CloudProvider:
        return self._provider

    @property
    def events(self) -> Any:
        return self._provider.middleware.events


class BaseSecurityService(SecurityService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseSecurityService, self).__init__(provider)


class BaseKeyPairService(
        BasePageableObjectMixin[KeyPair], KeyPairService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseKeyPairService, self).__init__(provider)
        self._service_event_pattern += ".security.key_pairs"


class BaseVMFirewallService(
        BasePageableObjectMixin[VMFirewall], VMFirewallService,
        BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVMFirewallService, self).__init__(provider)
        self._service_event_pattern += ".security.vm_firewalls"

    @dispatch(event="provider.security.vm_firewalls.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[VMFirewall]:
        obj_list = list(self)
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])


# The pageable mixin's list(limit, marker) intentionally differs from this
# service's list(firewall, limit, marker); the mixin is reused only for its
# iteration helpers, so the signature clash is expected.
class BaseVMFirewallRuleService(  # type: ignore[misc]
        BasePageableObjectMixin[VMFirewallRule],
        VMFirewallRuleService,
        BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVMFirewallRuleService, self).__init__(provider)
        self._provider = provider

    @property
    def provider(self) -> CloudProvider:
        return self._provider

    @dispatch(event="provider.security.vm_firewall_rules.get",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def get(self, firewall: VMFirewall,
            rule_id: str) -> VMFirewallRule | None:
        matches = [rule for rule in firewall.rules if rule.id == rule_id]
        if matches:
            return matches[0]
        else:
            return None

    @dispatch(event="provider.security.vm_firewall_rules.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, firewall: VMFirewall,
             **kwargs: Any) -> ResultList[VMFirewallRule]:
        obj_list = list(firewall.rules)
        filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
                   'cidr', 'src_dest_fw', 'src_dest_fw_id']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseStorageService(StorageService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseStorageService, self).__init__(provider)

    @property
    @abstractmethod
    def _bucket_objects(self) -> BucketObjectService:
        """
        Provider-internal service backing bucket-object operations.

        This is the service that ``bucket.objects`` (BucketObjectSubService)
        and the base multipart-upload code delegate to. It is a base-layer
        implementation detail, deliberately not part of the public
        StorageService interface; every provider's storage service implements
        it.
        """
        pass


class BaseVolumeService(
        BasePageableObjectMixin[Volume], VolumeService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVolumeService, self).__init__(provider)
        self._service_event_pattern += ".storage.volumes"


class BaseSnapshotService(
        BasePageableObjectMixin[Snapshot], SnapshotService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseSnapshotService, self).__init__(provider)
        self._service_event_pattern += ".storage.snapshots"


class BaseBucketService(
        BasePageableObjectMixin[Bucket], BucketService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseBucketService, self).__init__(provider)
        self._service_event_pattern += ".storage.buckets"

    # Generic find will be used for providers where we have not implemented
    # provider-specific querying for find method
    @dispatch(event="provider.storage.buckets.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Bucket]:
        obj_list = list(self)
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

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseBucketObjectService, self).__init__(provider)
        self._service_event_pattern += ".storage._bucket_objects"
        self._bucket: Bucket | None = None


class BaseComputeService(ComputeService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseComputeService, self).__init__(provider)


class BaseImageService(
        BasePageableObjectMixin[MachineImage], ImageService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseImageService, self).__init__(provider)
        self._service_event_pattern += ".compute.images"


class BaseInstanceService(
        BasePageableObjectMixin[Instance], InstanceService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseInstanceService, self).__init__(provider)
        self._service_event_pattern += ".compute.instances"


class BaseVMTypeService(
        BasePageableObjectMixin[VMType], VMTypeService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseVMTypeService, self).__init__(provider)
        self._service_event_pattern += ".compute.vm_types"

    @dispatch(event="provider.compute.vm_types.get",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_type_id: str) -> VMType | None:
        vm_type = (t for t in self if t.id == vm_type_id)
        return next(vm_type, None)

    @dispatch(event="provider.compute.vm_types.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[VMType]:
        obj_list = list(self)
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseRegionService(
        BasePageableObjectMixin[Region], RegionService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseRegionService, self).__init__(provider)
        self._service_event_pattern += ".compute.regions"

    @dispatch(event="provider.compute.regions.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Region]:
        obj_list = list(self)
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseNetworkingService(NetworkingService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseNetworkingService, self).__init__(provider)


class BaseNetworkService(
        BasePageableObjectMixin[Network], NetworkService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseNetworkService, self).__init__(provider)
        self._service_event_pattern += ".networking.networks"

    @property
    def subnets(self) -> list[Subnet]:  # type: ignore[override]
        # NOTE: this base implementation is a stub that every provider
        # overrides; it references attributes that do not exist on the
        # service, so the accesses are typed through ``Any``.
        this: Any = self
        return [subnet for subnet in this.provider.subnets
                if subnet.network_id == this.id]

    def get_or_create_default(self) -> Network:
        networks = self.provider.networking.networks.find(
            label=BaseNetwork.CB_DEFAULT_NETWORK_LABEL)

        if networks:
            return networks[0]
        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     BaseNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.provider.networking.networks.create(
                BaseNetwork.CB_DEFAULT_NETWORK_LABEL, '10.0.0.0/16')

    @dispatch(event="provider.networking.networks.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[Network]:
        obj_list = list(self)
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
        BasePageableObjectMixin[Subnet], SubnetService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseSubnetService, self).__init__(provider)
        self._service_event_pattern += ".networking.subnets"

    @dispatch(event="provider.networking.subnets.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, network: Network | None = None,
             **kwargs: Any) -> ResultList[Subnet]:
        obj_list: Any
        if not network:
            obj_list = self
        else:
            obj_list = network.subnets
        filters = ['label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get_or_create_default(self) -> Subnet:
        # Look for a CB-default subnet
        matches: ResultList[Subnet] = self.find(
            label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
        if matches:
            return matches[0]

        # No provider-default Subnet exists, try to create it (net + subnets)
        networks = cast(BaseNetworkService,
                        self.provider.networking.networks)
        network = networks.get_or_create_default()
        subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
                             BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE)
        return subnet


class BaseRouterService(
        BasePageableObjectMixin[Router], RouterService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseRouterService, self).__init__(provider)
        self._service_event_pattern += ".networking.routers"

    def get_or_create_default(self, network: Network | str) -> Router:
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

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseGatewayService, self).__init__(provider)


class BaseFloatingIPService(FloatingIPService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.find",
              priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    def find(self, gateway: Gateway,
             **kwargs: Any) -> ResultList[FloatingIP]:
        obj_list = list(gateway.floating_ips)
        filters = ['name', 'public_ip']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))


class BaseDnsService(DnsService, BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseDnsService, self).__init__(provider)


class BaseDnsZoneService(BasePageableObjectMixin[DnsZone], DnsZoneService,
                         BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseDnsZoneService, self).__init__(provider)

    def _get_fully_qualified_dns(self, name: str) -> str:
        # Add a trailing dot to fully qualify
        return name + '.' if not name.endswith('.') else name


# The pageable mixin's list(limit, marker) intentionally differs from this
# service's list(dns_zone, limit, marker); the mixin is reused only for its
# iteration helpers, so the signature clash is expected.
class BaseDnsRecordService(  # type: ignore[misc]
        BasePageableObjectMixin[DnsRecord],
        DnsRecordService,
        BaseCloudService):

    def __init__(self, provider: CloudProvider) -> None:
        super(BaseDnsRecordService, self).__init__(provider)

    def _get_fully_qualified_dns(self, name: str) -> str:
        # Add a trailing dot to fully qualify
        return name + '.' if not name.endswith('.') else name

    def _standardize_record(self, value: str, type: str) -> str:
        return (self._get_fully_qualified_dns(value)
                if type in (DnsRecordType.CNAME, DnsRecordType.MX) else value)

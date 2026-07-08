import builtins
import logging
from typing import Any
from typing import TYPE_CHECKING
from typing import cast

from cloudbridge.interfaces.provider import CloudProvider
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import DnsRecord
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import InternetGateway
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import ResultList
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMFirewallRule
from cloudbridge.interfaces.services import BucketObjectService
from cloudbridge.interfaces.subservices import BucketObjectSubService
from cloudbridge.interfaces.subservices import DnsRecordSubService
from cloudbridge.interfaces.subservices import FloatingIPSubService
from cloudbridge.interfaces.subservices import GatewaySubService
from cloudbridge.interfaces.subservices import SubnetSubService
from cloudbridge.interfaces.subservices import VMFirewallRuleSubService

from .resources import BasePageableObjectMixin

if TYPE_CHECKING:
    from .services import BaseStorageService

log = logging.getLogger(__name__)


class BaseBucketObjectSubService(BasePageableObjectMixin[BucketObject],
                                 BucketObjectSubService):

    def __init__(self, provider: CloudProvider, bucket: Bucket) -> None:
        self.__provider = provider
        self.bucket = bucket

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    @property
    def _bucket_objects(self) -> BucketObjectService:
        # ``_bucket_objects`` is a base-layer member (BaseStorageService), not
        # part of the public StorageService interface.
        storage = cast("BaseStorageService", self._provider.storage)
        return storage._bucket_objects

    def get(self, name: str) -> BucketObject | None:
        return self._bucket_objects.get(self.bucket, name)

    def list(self, limit: int | None = None, marker: str | None = None,
             prefix: str | None = None) -> ResultList[BucketObject]:
        return self._bucket_objects.list(self.bucket, limit=limit,
                                         marker=marker, prefix=prefix)

    def find(self, **kwargs: Any) -> ResultList[BucketObject]:
        return self._bucket_objects.find(self.bucket, **kwargs)

    def create(self, name: str) -> BucketObject:
        return self._bucket_objects.create(self.bucket, name)


class BaseGatewaySubService(GatewaySubService,
                            BasePageableObjectMixin[InternetGateway]):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        self._network = network
        self.__provider = provider

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def get_or_create(self) -> InternetGateway:
        return (self._provider.networking
                              ._gateways
                              .get_or_create(self._network))

    def delete(self, gateway: Gateway) -> None:
        return (self._provider.networking
                              ._gateways
                              .delete(self._network, gateway))

    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[InternetGateway]:
        return (self._provider.networking
                              ._gateways
                              .list(self._network, limit, marker))


class BaseVMFirewallRuleSubService(BasePageableObjectMixin[VMFirewallRule],
                                   VMFirewallRuleSubService):

    def __init__(self, provider: CloudProvider,
                 firewall: VMFirewall) -> None:
        self.__provider = provider
        self._firewall = firewall

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def get(self, rule_id: str) -> VMFirewallRule | None:
        return self._provider.security._vm_firewall_rules.get(self._firewall,
                                                              rule_id)

    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[VMFirewallRule]:
        return self._provider.security._vm_firewall_rules.list(self._firewall,
                                                               limit, marker)

    def create(self, direction: TrafficDirection, protocol: str | None = None,
               from_port: int | None = None,
               to_port: int | None = None,
               cidr: str | builtins.list[str] | None = None,
               src_dest_fw: VMFirewall | None = None) -> VMFirewallRule:
        return (self._provider
                    .security
                    ._vm_firewall_rules
                    .create(self._firewall, direction, protocol, from_port,
                            to_port, cidr, src_dest_fw))

    def find(self, **kwargs: Any) -> ResultList[VMFirewallRule]:
        return self._provider.security._vm_firewall_rules.find(self._firewall,
                                                               **kwargs)

    def delete(self, rule_id: str) -> None:
        return (self._provider
                    .security
                    ._vm_firewall_rules
                    .delete(self._firewall, rule_id))


class BaseFloatingIPSubService(FloatingIPSubService,
                               BasePageableObjectMixin[FloatingIP]):

    def __init__(self, provider: CloudProvider, gateway: Gateway) -> None:
        self.__provider = provider
        self.gateway = gateway

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def get(self, fip_id: str) -> FloatingIP | None:
        return self._provider.networking._floating_ips.get(self.gateway,
                                                           fip_id)

    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[FloatingIP]:
        return self._provider.networking._floating_ips.list(self.gateway,
                                                            limit, marker)

    def find(self, **kwargs: Any) -> ResultList[FloatingIP]:
        return self._provider.networking._floating_ips.find(self.gateway,
                                                            **kwargs)

    def create(self) -> FloatingIP:
        return self._provider.networking._floating_ips.create(self.gateway)

    def delete(self, fip: FloatingIP | str) -> None:
        return self._provider.networking._floating_ips.delete(self.gateway,
                                                              fip)


class BaseSubnetSubService(SubnetSubService, BasePageableObjectMixin[Subnet]):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        self.__provider = provider
        self.network = network

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def get(self, subnet_id: str) -> Subnet | None:
        sn = self._provider.networking.subnets.get(subnet_id)
        if sn and sn.network_id != self.network.id:
            log.warning("The SubnetSubService nested in the network '{}' "
                        "returned subnet '{}' which is attached to another "
                        "network '{}'".format(str(self.network), str(sn),
                                              str(sn.network)))
        return sn

    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[Subnet]:
        return self._provider.networking.subnets.list(network=self.network,
                                                      limit=limit,
                                                      marker=marker)

    def find(self, **kwargs: Any) -> ResultList[Subnet]:
        return self._provider.networking.subnets.find(network=self.network,
                                                      **kwargs)

    def create(self, label: str, cidr_block: str) -> Subnet:
        return self._provider.networking.subnets.create(label,
                                                        self.network,
                                                        cidr_block)

    def delete(self, subnet: Subnet | str) -> None:
        return self._provider.networking.subnets.delete(subnet)


class BaseDnsRecordSubService(DnsRecordSubService,
                              BasePageableObjectMixin[DnsRecord]):

    def __init__(self, provider: CloudProvider, dns_zone: DnsZone) -> None:
        self.__provider = provider
        self.dns_zone = dns_zone

    @property
    def _provider(self) -> CloudProvider:
        return self.__provider

    def get(self, rec_id: str) -> DnsRecord | None:
        # pylint:disable=protected-access
        return self._provider.dns._records.get(self.dns_zone, rec_id)

    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[DnsRecord]:
        # pylint:disable=protected-access
        return self._provider.dns._records.list(
            dns_zone=self.dns_zone, limit=limit, marker=marker)

    def find(self, **kwargs: Any) -> ResultList[DnsRecord]:
        # pylint:disable=protected-access
        # find/delete are provider-internal extensions not declared on the
        # DnsRecordService interface; reach them through ``Any``.
        records: Any = self._provider.dns._records
        return cast("ResultList[DnsRecord]",
                    records.find(dns_zone=self.dns_zone, **kwargs))

    def create(self, name: str, type: str, data: str,
               ttl: int | None = None) -> DnsRecord:
        # pylint:disable=protected-access
        return self._provider.dns._records.create(
            self.dns_zone, name, type, data, ttl)

    def delete(self, rec: DnsRecord | str) -> None:
        # pylint:disable=protected-access
        records: Any = self._provider.dns._records
        records.delete(self.dns_zone, rec)

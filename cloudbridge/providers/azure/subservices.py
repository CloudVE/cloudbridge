import logging

from cloudbridge.base.subservices import BaseBucketObjectSubService
from cloudbridge.base.subservices import BaseDnsRecordSubService
from cloudbridge.base.subservices import BaseFloatingIPSubService
from cloudbridge.base.subservices import BaseGatewaySubService
from cloudbridge.base.subservices import BaseSubnetSubService
from cloudbridge.base.subservices import BaseVMFirewallRuleSubService
from cloudbridge.interfaces.provider import CloudProvider
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import VMFirewall

log = logging.getLogger(__name__)


class AzureBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider: CloudProvider, bucket: Bucket) -> None:
        super(AzureBucketObjectSubService, self).__init__(provider, bucket)


class AzureGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(AzureGatewaySubService, self).__init__(provider, network)


class AzureVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider: CloudProvider,
                 firewall: VMFirewall) -> None:
        super(AzureVMFirewallRuleSubService, self).__init__(provider, firewall)


class AzureFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider: CloudProvider, gateway: Gateway) -> None:
        super(AzureFloatingIPSubService, self).__init__(provider, gateway)


class AzureSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(AzureSubnetSubService, self).__init__(provider, network)


class AzureDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider: CloudProvider, dns_zone: DnsZone) -> None:
        super(AzureDnsRecordSubService, self).__init__(provider, dns_zone)

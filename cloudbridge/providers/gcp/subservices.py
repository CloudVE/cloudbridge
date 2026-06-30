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


class GCPBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider: CloudProvider, bucket: Bucket) -> None:
        super(GCPBucketObjectSubService, self).__init__(provider, bucket)


class GCPGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(GCPGatewaySubService, self).__init__(provider, network)


class GCPVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider: CloudProvider, firewall: VMFirewall) -> None:
        super(GCPVMFirewallRuleSubService, self).__init__(provider, firewall)


class GCPFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider: CloudProvider, gateway: Gateway) -> None:
        super(GCPFloatingIPSubService, self).__init__(provider, gateway)


class GCPSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(GCPSubnetSubService, self).__init__(provider, network)


class GCPDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider: CloudProvider, dns_zone: DnsZone) -> None:
        super(GCPDnsRecordSubService, self).__init__(provider, dns_zone)

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


class AWSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider: CloudProvider, bucket: Bucket) -> None:
        super(AWSBucketObjectSubService, self).__init__(provider, bucket)


class AWSGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(AWSGatewaySubService, self).__init__(provider, network)


class AWSVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider: CloudProvider,
                 firewall: VMFirewall) -> None:
        super(AWSVMFirewallRuleSubService, self).__init__(provider, firewall)


class AWSFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider: CloudProvider, gateway: Gateway) -> None:
        super(AWSFloatingIPSubService, self).__init__(provider, gateway)


class AWSSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(AWSSubnetSubService, self).__init__(provider, network)


class AWSDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider: CloudProvider, dns_zone: DnsZone) -> None:
        super(AWSDnsRecordSubService, self).__init__(provider, dns_zone)

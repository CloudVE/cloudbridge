from __future__ import annotations

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


class OpenStackBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider: CloudProvider, bucket: Bucket) -> None:
        super(OpenStackBucketObjectSubService, self).__init__(provider, bucket)


class OpenStackGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(OpenStackGatewaySubService, self).__init__(provider, network)


class OpenStackFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider: CloudProvider, gateway: Gateway) -> None:
        super(OpenStackFloatingIPSubService, self).__init__(provider, gateway)


class OpenStackVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider: CloudProvider, firewall: VMFirewall) -> None:
        super(OpenStackVMFirewallRuleSubService, self).__init__(
            provider, firewall)


class OpenStackSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider: CloudProvider, network: Network) -> None:
        super(OpenStackSubnetSubService, self).__init__(provider, network)


class OpenStackDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider: CloudProvider, dns_zone: DnsZone) -> None:
        super(OpenStackDnsRecordSubService, self).__init__(provider, dns_zone)

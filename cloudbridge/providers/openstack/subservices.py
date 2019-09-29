import logging

from cloudbridge.base.subservices import BaseBucketObjectSubService
from cloudbridge.base.subservices import BaseDnsRecordSubService
from cloudbridge.base.subservices import BaseFloatingIPSubService
from cloudbridge.base.subservices import BaseGatewaySubService
from cloudbridge.base.subservices import BaseSubnetSubService
from cloudbridge.base.subservices import BaseVMFirewallRuleSubService


log = logging.getLogger(__name__)


class OpenStackBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(OpenStackBucketObjectSubService, self).__init__(provider, bucket)


class OpenStackGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider, network):
        super(OpenStackGatewaySubService, self).__init__(provider, network)


class OpenStackFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(OpenStackFloatingIPSubService, self).__init__(provider, gateway)


class OpenStackVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(OpenStackVMFirewallRuleSubService, self).__init__(
            provider, firewall)


class OpenStackSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider, network):
        super(OpenStackSubnetSubService, self).__init__(provider, network)


class OpenStackDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider, dns_zone):
        super(OpenStackDnsRecordSubService, self).__init__(provider, dns_zone)

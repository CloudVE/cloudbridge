import logging

from cloudbridge.base.subservices import BaseBucketObjectSubService
from cloudbridge.base.subservices import BaseDnsRecordSubService
from cloudbridge.base.subservices import BaseFloatingIPSubService
from cloudbridge.base.subservices import BaseGatewaySubService
from cloudbridge.base.subservices import BaseSubnetSubService
from cloudbridge.base.subservices import BaseVMFirewallRuleSubService


log = logging.getLogger(__name__)


class GCPBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(GCPBucketObjectSubService, self).__init__(provider, bucket)


class GCPGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider, network):
        super(GCPGatewaySubService, self).__init__(provider, network)


class GCPVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(GCPVMFirewallRuleSubService, self).__init__(provider, firewall)


class GCPFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(GCPFloatingIPSubService, self).__init__(provider, gateway)


class GCPSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider, network):
        super(GCPSubnetSubService, self).__init__(provider, network)


class GCPDnsRecordSubService(BaseDnsRecordSubService):

    def __init__(self, provider, dns_zone):
        super(GCPDnsRecordSubService, self).__init__(provider, dns_zone)

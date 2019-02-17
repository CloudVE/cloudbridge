import logging

from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseSubnetSubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService


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

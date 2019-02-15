import logging

from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseSubnetSubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService


log = logging.getLogger(__name__)


class GCSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(GCSBucketObjectSubService, self).__init__(provider, bucket)


class GCEGatewaySubService(BaseGatewaySubService):
    def __init__(self, provider, network):
        super(GCEGatewaySubService, self).__init__(provider, network)


class GCEVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(GCEVMFirewallRuleSubService, self).__init__(provider, firewall)


class GCEFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(GCEFloatingIPSubService, self).__init__(provider, gateway)


class GCESubnetSubService(BaseSubnetSubService):

    def __init__(self, provider, network):
        super(GCESubnetSubService, self).__init__(provider, network)

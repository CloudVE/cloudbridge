import logging

from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseSubnetSubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService

log = logging.getLogger(__name__)


class AWSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(AWSBucketObjectSubService, self).__init__(provider, bucket)


class AWSGatewaySubService(BaseGatewaySubService):

    def __init__(self, provider, network):
        super(AWSGatewaySubService, self).__init__(provider, network)


class AWSVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        super(AWSVMFirewallRuleSubService, self).__init__(provider, firewall)


class AWSFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(AWSFloatingIPSubService, self).__init__(provider, gateway)


class AWSSubnetSubService(BaseSubnetSubService):

    def __init__(self, provider, network):
        super(AWSSubnetSubService, self).__init__(provider, network)

import logging

from botocore.exceptions import ClientError

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import \
    BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService
from cloudbridge.cloud.interfaces.exceptions import InvalidValueException
from cloudbridge.cloud.interfaces.resources import TrafficDirection

from .helpers import BotoEC2Service
from .helpers import trim_empty_params
from .resources import AWSFloatingIP
from .resources import AWSVMFirewall
from .resources import AWSVMFirewallRule

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

    def list(self, limit=None, marker=None):
        # pylint:disable=protected-access
        rules = [AWSVMFirewallRule(self.firewall,
                                   TrafficDirection.INBOUND, r)
                 for r in self.firewall._vm_firewall.ip_permissions]
        rules = rules + [
            AWSVMFirewallRule(
                self.firewall, TrafficDirection.OUTBOUND, r)
            for r in self.firewall._vm_firewall.ip_permissions_egress]
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    def create(self,  direction, protocol=None, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        src_dest_fw_id = (
            src_dest_fw.id if isinstance(src_dest_fw, AWSVMFirewall)
            else src_dest_fw)

        # pylint:disable=protected-access
        ip_perm_entry = AWSVMFirewallRule._construct_ip_perms(
            protocol, from_port, to_port, cidr, src_dest_fw_id)
        # Filter out empty values to please Boto
        ip_perms = [trim_empty_params(ip_perm_entry)]

        try:
            if direction == TrafficDirection.INBOUND:
                # pylint:disable=protected-access
                self.firewall._vm_firewall.authorize_ingress(
                    IpPermissions=ip_perms)
            elif direction == TrafficDirection.OUTBOUND:
                # pylint:disable=protected-access
                self.firewall._vm_firewall.authorize_egress(
                    IpPermissions=ip_perms)
            else:
                raise InvalidValueException("direction", direction)
            self.firewall.refresh()
            return AWSVMFirewallRule(self.firewall, direction, ip_perm_entry)
        except ClientError as ec2e:
            if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
                return AWSVMFirewallRule(
                    self.firewall, direction, ip_perm_entry)
            else:
                raise ec2e


class AWSFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(AWSFloatingIPSubService, self).__init__(provider, gateway)
        self.svc = BotoEC2Service(provider=self._provider,
                                  cb_resource=AWSFloatingIP,
                                  boto_collection_name='vpc_addresses')

    def get(self, fip_id):
        log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
        return self.svc.get(fip_id)

    def list(self, limit=None, marker=None):
        log.debug("Listing all floating IPs under gateway %s", self.gateway)
        return self.svc.list(limit=limit, marker=marker)

    def create(self):
        log.debug("Creating a floating IP under gateway %s", self.gateway)
        ip = self._provider.ec2_conn.meta.client.allocate_address(
            Domain='vpc')
        return AWSFloatingIP(
            self._provider,
            self._provider.ec2_conn.VpcAddress(ip.get('AllocationId')))

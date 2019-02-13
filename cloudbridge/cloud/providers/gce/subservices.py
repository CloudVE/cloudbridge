import logging
import uuid

from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.subservices import BaseBucketObjectSubService
from cloudbridge.cloud.base.subservices import BaseFloatingIPSubService
from cloudbridge.cloud.base.subservices import \
    BaseGatewaySubService
from cloudbridge.cloud.base.subservices import BaseVMFirewallRuleSubService

from .resources import GCEFloatingIP
from .resources import GCEInternetGateway
from .resources import GCEVMFirewallRule

log = logging.getLogger(__name__)


class GCSBucketObjectSubService(BaseBucketObjectSubService):

    def __init__(self, provider, bucket):
        super(GCSBucketObjectSubService, self).__init__(provider, bucket)


class GCEVMFirewallRuleSubService(BaseVMFirewallRuleSubService):

    def __init__(self, firewall):
        super(GCEVMFirewallRuleSubService, self).__init__(
                firewall.delegate.provider, firewall)
        self._dummy_rule = None

    def list(self, limit=None, marker=None):
        rules = []
        for firewall in self.firewall.delegate.iter_firewalls(
                self.firewall.name, self.firewall.network.name):
            rule = GCEVMFirewallRule(self.firewall, firewall['id'])
            if rule.is_dummy_rule():
                self._dummy_rule = rule
            else:
                rules.append(rule)
        return ClientPagedResultList(self._provider, rules,
                                     limit=limit, marker=marker)

    @property
    def dummy_rule(self):
        if not self._dummy_rule:
            self.list()
        return self._dummy_rule

    @staticmethod
    def to_port_range(from_port, to_port):
        if from_port is not None and to_port is not None:
            return '%d-%d' % (from_port, to_port)
        elif from_port is not None:
            return from_port
        else:
            return to_port

    def create_with_priority(self, direction, protocol, priority,
                             from_port=None, to_port=None, cidr=None,
                             src_dest_fw=None):
        port = GCEVMFirewallRuleSubService.to_port_range(from_port, to_port)
        src_dest_tag = None
        src_dest_fw_id = None
        if src_dest_fw:
            src_dest_tag = src_dest_fw.name
            src_dest_fw_id = src_dest_fw.id
        if not self.firewall.delegate.add_firewall(
                self.firewall.name, direction, protocol, priority, port, cidr,
                src_dest_tag, self.firewall.description,
                self.firewall.network.name):
            return None
        rules = self.find(direction=direction, protocol=protocol,
                          from_port=from_port, to_port=to_port, cidr=cidr,
                          src_dest_fw_id=src_dest_fw_id)
        if len(rules) < 1:
            return None
        return rules[0]

    def create(self, direction, protocol, from_port=None, to_port=None,
               cidr=None, src_dest_fw=None):
        return self.create_with_priority(direction, protocol, 1000, from_port,
                                         to_port, cidr, src_dest_fw)


class GCEFloatingIPSubService(BaseFloatingIPSubService):

    def __init__(self, provider, gateway):
        super(GCEFloatingIPSubService, self).__init__(provider, gateway)

    def get(self, floating_ip_id):
        fip = self._provider.get_resource('addresses', floating_ip_id)
        return (GCEFloatingIP(self._provider, self.gateway, fip)
                if fip else None)

    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self._provider
                        .gce_compute
                        .addresses()
                        .list(project=self._provider.project_name,
                              region=self._provider.region_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        ips = [GCEFloatingIP(self._provider, self.gateway, ip)
               for ip in response.get('items', [])]
        if len(ips) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(ips))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=ips)

    def create(self):
        region_name = self._provider.region_name
        ip_name = 'ip-{0}'.format(uuid.uuid4())
        response = (self._provider
                    .gce_compute
                    .addresses()
                    .insert(project=self._provider.project_name,
                            region=region_name,
                            body={'name': ip_name})
                    .execute())
        self._provider.wait_for_operation(response, region=region_name)
        return self.get(ip_name)


class GCEGatewaySubService(BaseGatewaySubService):
    _DEFAULT_GATEWAY_NAME = 'default-internet-gateway'
    _GATEWAY_URL_PREFIX = 'global/gateways/'

    def __init__(self, provider, network):
        super(GCEGatewaySubService, self).__init__(provider, network)
        self._default_internet_gateway = GCEInternetGateway(
            provider,
            {'id': (GCEGatewaySubService._GATEWAY_URL_PREFIX +
                    GCEGatewaySubService._DEFAULT_GATEWAY_NAME),
             'name': GCEGatewaySubService._DEFAULT_GATEWAY_NAME})

    def get_or_create_inet_gateway(self, name=None):
        return self._default_internet_gateway

    def delete(self, gateway):
        pass

    def list(self, limit=None, marker=None):
        return ClientPagedResultList(self._provider,
                                     [self._default_internet_gateway],
                                     limit=limit, marker=marker)

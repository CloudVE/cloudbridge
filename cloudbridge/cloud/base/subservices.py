import logging

from cloudbridge.cloud.interfaces.subservices import BucketObjectSubService
from cloudbridge.cloud.interfaces.subservices import FloatingIPSubService
from cloudbridge.cloud.interfaces.subservices import GatewaySubService
from cloudbridge.cloud.interfaces.subservices import VMFirewallRuleSubService

from . import helpers as cb_helpers
from .resources import BasePageableObjectMixin
from .resources import ClientPagedResultList

log = logging.getLogger(__name__)


class BaseBucketObjectSubService(BasePageableObjectMixin,
                                 BucketObjectSubService):

    def __init__(self, provider, bucket):
        self.__provider = provider
        self.bucket = bucket

    @property
    def _provider(self):
        return self.__provider

    def get(self, name):
        return self._provider.storage._bucket_objects.get(self.bucket, name)

    def list(self, limit=None, marker=None, prefix=None):
        return self._provider.storage._bucket_objects.list(self.bucket, limit,
                                                           marker, prefix)

    def find(self, **kwargs):
        return self._provider.storage._bucket_objects.find(self.bucket,
                                                           **kwargs)

    def create(self, name):
        return self._provider.storage._bucket_objects.create(self.bucket, name)


class BaseGatewaySubService(GatewaySubService, BasePageableObjectMixin):

    def __init__(self, provider, network):
        self._network = network
        self.__provider = provider

    @property
    def _provider(self):
        return self.__provider

    def get_or_create_inet_gateway(self):
        return (self._provider.networking
                              ._gateways
                              .get_or_create_inet_gateway(self._network))

    def delete(self, gateway):
        return (self._provider.networking
                              ._gateways
                              .delete(self._network, gateway))

    def list(self, limit=None, marker=None):
        return (self._provider.networking
                              ._gateways
                              .list(self._network, limit, marker))


class BaseVMFirewallRuleSubService(BasePageableObjectMixin,
                                   VMFirewallRuleSubService):

    def __init__(self, provider, firewall):
        self.__provider = provider
        self.firewall = firewall

    @property
    def _provider(self):
        return self.__provider

    def get(self, rule_id):
        matches = [rule for rule in self if rule.id == rule_id]
        if matches:
            return matches[0]
        else:
            return None

    def find(self, **kwargs):
        obj_list = self
        filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
                   'cidr', 'src_dest_fw', 'src_dest_fw_id']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def delete(self, rule_id):
        rule = self.get(rule_id)
        if rule:
            rule.delete()


class BaseFloatingIPSubService(FloatingIPSubService, BasePageableObjectMixin):

    def __init__(self, provider, gateway):
        self.__provider = provider
        self.gateway = gateway

    @property
    def _provider(self):
        return self.__provider

    def find(self, **kwargs):
        obj_list = self
        filters = ['name', 'public_ip']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def delete(self, fip_id):
        floating_ip = self.get(fip_id)
        if floating_ip:
            floating_ip.delete()

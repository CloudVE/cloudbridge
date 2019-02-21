import functools
import operator
import os
import sys
import unittest
import uuid

from cloudbridge.cloud.base import helpers as cb_helpers
from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import TestMockHelperMixin
from cloudbridge.cloud.interfaces.resources import FloatingIpState
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import SubnetState


def parse_bool(val):
    if val:
        return str(val).upper() in ['TRUE', 'YES']
    else:
        return False


def skipIfNoService(services):
    """
    A decorator for skipping tests if the provider
    does not implement a given service.
    """
    def wrap(func):
        """
        The actual wrapper
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            provider = getattr(self, 'provider')
            if provider:
                for service in services:
                    if not provider.has_service(service):
                        self.skipTest("Skipping test because '%s' service is"
                                      " not implemented" % (service,))
            func(self, *args, **kwargs)
        return wrapper
    return wrap


def skipIfPython(op, major, minor):
    """
    A decorator for skipping tests if the python
    version doesn't match
    """
    def stringToOperator(op):
        op_map = {
            "=": operator.eq,
            "==": operator.eq,
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
        }
        return op_map.get(op)

    def wrap(func):
        """
        The actual wrapper
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            op_func = stringToOperator(op)
            if op_func(sys.version_info, (major, minor)):
                self.skipTest(
                    "Skipping test because python version {0} is {1} expected"
                    " version {2}".format(sys.version_info[:2],
                                          op, (major, minor)))
            func(self, *args, **kwargs)
        return wrapper
    return wrap


TEST_DATA_CONFIG = {
    "AWSCloudProvider": {
        # Match the ami value with entry in custom_amis.json for use with moto
        "image": cb_helpers.get_env('CB_IMAGE_AWS', 'ami-aa2ea6d0'),
        "vm_type": cb_helpers.get_env('CB_VM_TYPE_AWS', 't2.nano'),
        "placement": cb_helpers.get_env('CB_PLACEMENT_AWS', 'us-east-1a'),
    },
    'OpenStackCloudProvider': {
        'image': cb_helpers.get_env('CB_IMAGE_OS',
                                    'c66bdfa1-62b1-43be-8964-e9ce208ac6a5'),
        "vm_type": cb_helpers.get_env('CB_VM_TYPE_OS', 'm1.tiny'),
        "placement": cb_helpers.get_env('CB_PLACEMENT_OS', 'nova'),
    },
    'GCPCloudProvider': {
        'image': cb_helpers.get_env(
            'CB_IMAGE_GCP',
            'https://www.googleapis.com/compute/v1/projects/ubuntu-os-cloud/'
            'global/images/ubuntu-1710-artful-v20180126'),
        'vm_type': cb_helpers.get_env('CB_VM_TYPE_GCP', 'f1-micro'),
        'placement': cb_helpers.get_env('GCP_DEFAULT_ZONE', 'us-central1-a'),
    },
    "AzureCloudProvider": {
        "placement":
            cb_helpers.get_env('CB_PLACEMENT_AZURE', 'eastus'),
        "image":
            cb_helpers.get_env('CB_IMAGE_AZURE',
                               'Canonical:UbuntuServer:16.04.0-LTS:latest'),
        "vm_type":
            cb_helpers.get_env('CB_VM_TYPE_AZURE', 'Basic_A2'),
    }
}


def get_provider_test_data(provider, key):
    if "AWSCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("AWSCloudProvider").get(key)
    elif "OpenStackCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("OpenStackCloudProvider").get(key)
    elif "GCPCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("GCPCloudProvider").get(key)
    elif "AzureCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("AzureCloudProvider").get(key)
    return None


def get_or_create_default_subnet(provider):
    """
    Return the default subnet to be used for tests
    """
    return provider.networking.subnets.get_or_create_default(
        zone=get_provider_test_data(provider, 'placement'))


def cleanup_subnet(subnet):
    if subnet:
        subnet.delete()
        subnet.wait_for([SubnetState.UNKNOWN],
                        terminal_states=[SubnetState.ERROR])


def cleanup_network(network):
    """
    Delete the supplied network, first deleting any contained subnets.
    """
    if network:
        try:
            for sn in network.subnets:
                with cb_helpers.cleanup_action(lambda: cleanup_subnet(sn)):
                    pass
        finally:
            network.delete()
            network.wait_for([NetworkState.UNKNOWN],
                             terminal_states=[NetworkState.ERROR])


def cleanup_fip(fip):
    if fip:
        fip.delete()
        fip.wait_for([FloatingIpState.UNKNOWN],
                     terminal_states=[FloatingIpState.ERROR])


def get_test_gateway(provider):
    """
    Get an internet gateway for testing.

    This includes creating a network for the gateway, which is also returned.
    """
    sn = get_or_create_default_subnet(provider)
    net = sn.network
    return net.gateways.get_or_create()


def cleanup_gateway(gateway):
    """
    Delete the supplied network and gateway.
    """
    with cb_helpers.cleanup_action(lambda: gateway.delete()):
        pass


def create_test_instance(
        provider, instance_label, subnet, launch_config=None,
        key_pair=None, vm_firewalls=None, user_data=None):

    instance = provider.compute.instances.create(
        instance_label, get_provider_test_data(provider, 'image'),
        get_provider_test_data(provider, 'vm_type'),
        subnet=subnet,
        zone=get_provider_test_data(provider, 'placement'),
        key_pair=key_pair,
        vm_firewalls=vm_firewalls,
        launch_config=launch_config,
        user_data=user_data)

    return instance


def get_test_instance(provider, label, key_pair=None, vm_firewalls=None,
                      subnet=None, user_data=None):
    launch_config = None
    instance = create_test_instance(
        provider,
        label,
        subnet=subnet,
        key_pair=key_pair,
        vm_firewalls=vm_firewalls,
        launch_config=launch_config,
        user_data=user_data)
    instance.wait_till_ready()
    return instance


def get_test_fixtures_folder():
    return os.path.join(os.path.dirname(__file__), '../fixtures/')


def delete_instance(instance):
    if instance:
        instance.delete()
        instance.wait_for([InstanceState.DELETED, InstanceState.UNKNOWN],
                          terminal_states=[InstanceState.ERROR])


def cleanup_test_resources(instance=None, vm_firewall=None,
                           key_pair=None, network=None):
    """Clean up any combination of supplied resources."""
    with cb_helpers.cleanup_action(
            lambda: cleanup_network(network) if network else None):
        with cb_helpers.cleanup_action(
                lambda: key_pair.delete() if key_pair else None):
            with cb_helpers.cleanup_action(
                    lambda: vm_firewall.delete() if vm_firewall else None):
                delete_instance(instance)


def get_uuid():
    return str(uuid.uuid4())[:6]


class ProviderTestBase(unittest.TestCase):

    _provider = None

    def setUp(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.setUpMock()

    def tearDown(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.tearDownMock()
        self._provider = None

    def get_provider_wait_interval(self, provider_class):
        if issubclass(provider_class, TestMockHelperMixin):
            return 0
        else:
            return 1

    def create_provider_instance(self):
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        factory = CloudProviderFactory()
        provider_class = factory.get_provider_class(provider_name)
        config = {'default_wait_interval':
                  self.get_provider_wait_interval(provider_class),
                  'default_result_limit': 5}
        return provider_class(config, factory)

    @property
    def provider(self):
        if not self._provider:
            self._provider = self.create_provider_instance()
        return self._provider

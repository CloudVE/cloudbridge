import functools
import os
import sys
import unittest

from contextlib import contextmanager

from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import TestMockHelperMixin

from six import reraise


def parse_bool(val):
    if val:
        return str(val).upper() in ['TRUE', 'YES']
    else:
        return False


@contextmanager
def cleanup_action(cleanup_func):
    """
    Context manager to carry out a given
    cleanup action after carrying out a set
    of tasks, or when an exception occurs.
    If any errors occur during the cleanup
    action, those are ignored, and the original
    traceback is preserved.

    :params func: This function is called if
    an exception occurs or at the end of the
    context block. If any exceptions raised
        by func are ignored.
    Usage:
        with cleanup_action(lambda e: print("Oops!")):
            do_something()
    """
    try:
        yield
    except Exception:
        ex_class, ex_val, ex_traceback = sys.exc_info()
        try:
            cleanup_func()
        except Exception as e:
            print("Error during exception cleanup: {0}".format(e))
        reraise(ex_class, ex_val, ex_traceback)
    try:
        cleanup_func()
    except Exception as e:
        print("Error during cleanup: {0}".format(e))


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


TEST_DATA_CONFIG = {
    "AWSCloudProvider": {
        "image": os.environ.get('CB_IMAGE_AWS', 'ami-5ac2cd4d'),
        "instance_type": os.environ.get('CB_INSTANCE_TYPE_AWS', 't2.nano'),
        "placement": os.environ.get('CB_PLACEMENT_AWS', 'us-east-1a'),
    },
    "OpenStackCloudProvider": {
        "image": os.environ.get('CB_IMAGE_OS',
                                '842b949c-ea76-48df-998d-8a41f2626243'),
        "instance_type": os.environ.get('CB_INSTANCE_TYPE_OS', 'm1.tiny'),
        "placement": os.environ.get('CB_PLACEMENT_OS', 'nova'),
    }
}


def get_provider_test_data(provider, key):
    if "AWSCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("AWSCloudProvider").get(key)
    elif "OpenStackCloudProvider" in provider.name:
        return TEST_DATA_CONFIG.get("OpenStackCloudProvider").get(key)
    return None


def create_test_network(provider, name):
    """
    Create a network with one subnet, returning the network and subnet objects.
    """
    net = provider.network.create(name=name)
    cidr_block = (net.cidr_block).split('/')[0] or '10.0.0.1'
    sn = net.create_subnet(cidr_block='{0}/28'.format(cidr_block), name=name,
                           zone=get_provider_test_data(provider, 'placement'))
    return net, sn


def delete_test_network(network):
    """
    Delete the supplied network, first deleting any contained subnets.
    """
    with cleanup_action(lambda: network.delete()):
        for sn in network.subnets():
            sn.delete()


def create_test_instance(
        provider, instance_name, subnet, launch_config=None,
        key_pair=None, security_groups=None):
    return provider.compute.instances.create(
        instance_name,
        get_provider_test_data(provider, 'image'),
        get_provider_test_data(provider, 'instance_type'),
        subnet=subnet,
        zone=get_provider_test_data(provider, 'placement'),
        key_pair=key_pair,
        security_groups=security_groups,
        launch_config=launch_config)


def get_test_instance(provider, name, key_pair=None, security_groups=None,
                      subnet=None):
    launch_config = None
    instance = create_test_instance(
        provider,
        name,
        subnet=subnet,
        key_pair=key_pair,
        security_groups=security_groups,
        launch_config=launch_config)
    instance.wait_till_ready()
    return instance


def get_test_fixtures_folder():
    return os.path.join(os.path.dirname(__file__), 'fixtures/')


def delete_test_instance(instance):
    if instance:
        instance.terminate()
        instance.wait_for([InstanceState.TERMINATED, InstanceState.UNKNOWN],
                          terminal_states=[InstanceState.ERROR])


def cleanup_test_resources(instance=None, network=None, security_group=None,
                           key_pair=None):
    """Clean up any combination of supplied resources."""
    with cleanup_action(lambda: delete_test_network(network)
                        if network else None):
        with cleanup_action(lambda: key_pair.delete() if key_pair else None):
            with cleanup_action(lambda: security_group.delete()
                                if security_group else None):
                delete_test_instance(instance)


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
        provider_name = os.environ.get("CB_TEST_PROVIDER", "aws")
        use_mock_drivers = parse_bool(
            os.environ.get("CB_USE_MOCK_PROVIDERS", "True"))
        factory = CloudProviderFactory()
        provider_class = factory.get_provider_class(provider_name,
                                                    get_mock=use_mock_drivers)
        config = {'default_wait_interval':
                  self.get_provider_wait_interval(provider_class)}
        return provider_class(config)

    @property
    def provider(self):
        if not self._provider:
            self._provider = self.create_provider_instance()
        return self._provider
